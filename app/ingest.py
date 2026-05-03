import os
import pickle
from typing import List

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_pdf_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text = []

    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()

        if page_text:
            text.append(page_text)
        else:
            print(f"Warning: Page {i} has no extractable text.")

    return "\n".join(text)


def chunk_text(text: str, chunk_size: int = 180, overlap: int = 40) -> List[str]:
    """
    Word-based chunking.
    chunk_size and overlap are measured in words.
    """
    words = text.split()

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])

        if chunk.strip():
            chunks.append(chunk)

        start = end - overlap

    return chunks


def get_embeddings(texts: List[str]) -> np.ndarray:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )

    embeddings = [item.embedding for item in response.data]
    return np.array(embeddings, dtype="float32")


def embed_in_batches(chunks: List[str], batch_size: int = 100) -> np.ndarray:
    all_embeddings = []

    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        batch = chunks[start:end]

        print(f"Embedding chunks {start} to {min(end, len(chunks))}...")

        batch_embeddings = get_embeddings(batch)
        all_embeddings.append(batch_embeddings)

    return np.vstack(all_embeddings)


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    return index


def save_index_and_chunks(index: faiss.IndexFlatL2, chunks: List[str]) -> None:
    os.makedirs("data/processed", exist_ok=True)

    faiss.write_index(index, "data/processed/index.faiss")

    with open("data/processed/chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)

    print("Saved FAISS index to data/processed/index.faiss")
    print("Saved chunks to data/processed/chunks.pkl")


if __name__ == "__main__":
    pdf_path = "data/raw/sample.pdf"

    print("Loading PDF...")
    text = load_pdf_text(pdf_path)

    print("Chunking text...")
    chunks = chunk_text(text)

    print("Total characters:", len(text))
    print("Total chunks:", len(chunks))

    print("Embedding all chunks...")
    embeddings = embed_in_batches(chunks, batch_size=100)

    print("Embeddings shape:", embeddings.shape)

    print("Building FAISS index...")
    index = build_faiss_index(embeddings)

    print("Vectors in FAISS index:", index.ntotal)

    print("Saving index and chunks...")
    save_index_and_chunks(index, chunks)

    print("Ingestion complete.")