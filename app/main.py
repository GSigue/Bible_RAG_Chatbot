import os

from fastapi import FastAPI, Request, HTTPException, Header
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse

from app.rag import (
    retrieve_context,
    generate_answer,
    rewrite_query,
)
from app.memory import (
    init_db,
    save_message,
    get_recent_history,
    save_usage_event,
    get_recent_usage_events,
    get_cached_answer,
    save_cached_answer,
)


app = FastAPI(title="Bible Guidance API")

limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change-this-local-key")


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"message": "Too many requests. Please slow down."},
    )


class ChatRequest(BaseModel):
    question: str
    session_id: str = "default-session"


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    cached: bool = False


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def home():
    return {"message": "Bible Guidance API is running"}


@limiter.limit("10/minute")
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, request_obj: Request):
    history = get_recent_history(request.session_id)

    save_usage_event(request.session_id, request.question)

    # 1. Check cache first
    cached_answer = get_cached_answer(request.question)

    if cached_answer:
        save_message(request.session_id, "user", request.question)
        save_message(request.session_id, "assistant", cached_answer)

        return {
            "answer": cached_answer,
            "sources": [],
            "cached": True,
        }

    # 2. Only rewrite query if there is conversation history
    if history:
        rewritten_query = rewrite_query(request.question, history)
    else:
        rewritten_query = request.question

    print("Original question:", request.question)
    print("Rewritten query:", rewritten_query)

    # 3. Retrieve fewer chunks for speed
    retrieved_chunks = retrieve_context(rewritten_query, top_k=4)

    # 4. Generate answer
    answer = generate_answer(
        request.question,
        retrieved_chunks,
        history=history,
    )

    # 5. Cache answer for repeated questions
    save_cached_answer(request.question, answer)

    # 6. Save conversation memory
    save_message(request.session_id, "user", request.question)
    save_message(request.session_id, "assistant", answer)

    return {
        "answer": answer,
        "sources": [
            {
                "chunk_id": chunk["chunk_id"],
                "distance": chunk["distance"],
                "preview": chunk["text"][:300],
            }
            for chunk in retrieved_chunks
        ],
        "cached": False,
    }


@app.get("/admin/usage")
def usage_report(x_admin_key: str | None = Header(default=None)):
    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {
        "recent_questions": get_recent_usage_events(limit=50)
    }