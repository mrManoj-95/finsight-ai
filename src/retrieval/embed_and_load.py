import json
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from retrieval.db import engine

model = SentenceTransformer("BAAI/bge-base-en-v1.5")

def load_chunks(path="data/processed/chunks.jsonl"):
    with open(path) as f:
        return [json.loads(line) for line in f]

def embed_and_insert(batch_size=32):
    records = load_chunks()
    texts = [r["text"] for r in records]
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True, normalize_embeddings=True)

    with engine.connect() as conn:
        for r, emb in zip(records, embeddings):
            conn.execute(
                text("""
                    INSERT INTO chunks (doc_id, ticker, form, filing_date, item, chunk_index, text, embedding)
                    VALUES (:doc_id, :ticker, :form, :filing_date, :item, :chunk_index, :text, :embedding)
                """),
                {
                    "doc_id": r["doc_id"], "ticker": r["ticker"], "form": r["form"],
                    "filing_date": r["filing_date"], "item": r["item"],
                    "chunk_index": r["chunk_index"], "text": r["text"],
                    "embedding": str(emb.tolist()),
                },
            )
        conn.commit()
    print(f"Inserted {len(records)} chunks.")

if __name__ == "__main__":
    embed_and_insert()