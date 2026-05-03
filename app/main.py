from fastapi import FastAPI
from pydantic import BaseModel

from app.rag import (
    retrieve_context,
    generate_answer,
    rewrite_query,
    rerank_chunks,
)
from app.memory import init_db, save_message, get_recent_history


app = FastAPI(title="Bible RAG Chatbot API")


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
def home():
    return {"message": "Bible RAG Chatbot API is running"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    history = get_recent_history(request.session_id)

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