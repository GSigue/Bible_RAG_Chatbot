from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse



from app.rag import (
    retrieve_context,
    generate_answer,
    rewrite_query,
    rerank_chunks,
)
from app.memory import (
    init_db,
    save_message,
    get_recent_history,
    save_usage_event,
    get_recent_usage_events,
)


app = FastAPI(title="Bible RAG Chatbot API")

limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

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


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")

@app.get("/admin/usage")
def usage_report():
    return {
        "recent_questions": get_recent_usage_events(limit=50)
    }
def home():
    return {"message": "Bible RAG Chatbot API is running"}

@limiter.limit("5/minute")
@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, _request: Request):
    history = get_recent_history(request.session_id)
    
    save_usage_event(request.session_id, request.question)

    rewritten_query = rewrite_query(request.question, history)

    print("Original question:", request.question)
    print("Rewritten query:", rewritten_query)

    candidate_chunks = retrieve_context(rewritten_query, top_k=12)

    retrieved_chunks = rerank_chunks(
        request.question,
        candidate_chunks,
        top_k=5,
    )

    answer = generate_answer(
        request.question,
        retrieved_chunks,
        history=history,
    )

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
    }