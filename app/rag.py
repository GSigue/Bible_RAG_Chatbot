import os
import pickle
from typing import List, Dict, Any

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


INDEX_PATH = "data/processed/index.faiss"
CHUNKS_PATH = "data/processed/chunks.pkl"


def load_faiss_index() -> faiss.Index:
    return faiss.read_index(INDEX_PATH)


def load_chunks() -> List[str]:
    with open(CHUNKS_PATH, "rb") as f:
        return pickle.load(f)


def get_query_embedding(question: str) -> np.ndarray:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[question],
    )

    embedding = response.data[0].embedding
    return np.array([embedding], dtype="float32")


def rewrite_query(question: str, history: List[Dict[str, str]] | None = None) -> str:
    history = history or []

    conversation_history = "\n".join(
        [f"{msg['role'].title()}: {msg['content']}" for msg in history]
    )

    prompt = f"""
Rewrite the user's question into a clear standalone Bible search query.

Rules:
- Use recent conversation only to resolve vague references.
- Do not answer the question.
- Return only the rewritten search query.
- Keep it concise.

Recent conversation:
{conversation_history if conversation_history else "No prior conversation."}

User question:
{question}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        return response.choices[0].message.content.strip()

    except Exception:
        return question


def retrieve_context(question: str, top_k: int = 5) -> List[Dict[str, Any]]:
    index = load_faiss_index()
    chunks = load_chunks()

    query_embedding = get_query_embedding(question)

    distances, indices = index.search(query_embedding, top_k)

    results = []

    for distance, idx in zip(distances[0], indices[0]):
        results.append(
            {
                "chunk_id": int(idx),
                "distance": float(distance),
                "text": chunks[idx],
            }
        )

    return results


def rerank_chunks(
    question: str,
    chunks: List[Dict[str, Any]],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    chunk_text = "\n\n".join(
        [
            f"Chunk ID: {chunk['chunk_id']}\nText: {chunk['text'][:1200]}"
            for chunk in chunks
        ]
    )

    prompt = f"""
You are a retrieval reranker.

Your job is to select the most relevant Bible chunks for answering the user's question.

User question:
{question}

Candidate chunks:
{chunk_text}

Instructions:
- Choose the {top_k} most relevant chunk IDs.
- Prefer chunks that directly answer the question.
- Ignore chunks that only mention similar words but are not useful.
- Return only the chunk IDs as a comma-separated list.
- Do not explain.

Example output:
12, 45, 90
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        selected_text = response.choices[0].message.content.strip()

        selected_ids = []
        for part in selected_text.split(","):
            part = part.strip()
            if part.isdigit():
                selected_ids.append(int(part))

        valid_ids = set(chunk["chunk_id"] for chunk in chunks)

        selected = [
            chunk
            for chunk in chunks
            if chunk["chunk_id"] in selected_ids and chunk["chunk_id"] in valid_ids
        ]

        if not selected:
            return chunks[:top_k]

        return selected[:top_k]

    except Exception:
        return chunks[:top_k]


def generate_answer(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
    history: List[Dict[str, str]] | None = None,
) -> str:
    history = history or []

    conversation_history = "\n".join(
        [f"{msg['role'].title()}: {msg['content']}" for msg in history]
    )

    context = "\n\n".join(
        [
            f"Chunk {chunk['chunk_id']}:\n{chunk['text']}"
            for chunk in retrieved_chunks
        ]
    )

    prompt = f"""
You are a Christian Bible Q&A assistant.

Your job is to answer everyday life questions using the Bible context provided.

Rules:
- Use ONLY the exact Bible text provided in the context.
- Do NOT use any outside knowledge, memory, or assumptions for Bible facts.
- Use recent conversation history only to understand follow-up questions.
- Do NOT add any verse or quote that is not explicitly present in the context.
- Only quote text that appears verbatim in the provided chunks.
- If a verse reference is not clearly present, do NOT guess it.
- If the context is insufficient, say: "The retrieved passages do not provide enough detail to answer fully."
- Be compassionate, practical, and clear.
- Do not present yourself as a pastor, therapist, or final spiritual authority.
- Encourage the user to seek wise counsel when appropriate.

Recent conversation history:
{conversation_history if conversation_history else "No prior conversation."}

User question:
{question}

Bible context:
{context}

Answer format:
1. Short compassionate answer
2. Relevant Scripture from the provided context
3. Explanation in everyday language
4. Practical application
5. Gentle note if needed
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a careful Christian Bible assistant grounded strictly in retrieved Scripture context.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Sorry, something went wrong while generating the answer: {e}"


if __name__ == "__main__":
    question = "What does the Bible say about anxiety?"

    results = retrieve_context(question, top_k=12)
    reranked = rerank_chunks(question, results, top_k=5)

    print("Retrieved chunks:")
    for result in reranked:
        print("Chunk ID:", result["chunk_id"], "Distance:", result["distance"])

    print("\nGenerating answer...\n")

    answer = generate_answer(question, reranked)

    print(answer)