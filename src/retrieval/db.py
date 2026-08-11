from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

DDL = """
    CREATE EXTENSION IF NOT EXISTS vector;

    CREATE TABLE IF NOT EXISTS chunks (
        id SERIAL PRIMARY KEY,
        doc_id TEXT NOT NULL,
        ticker TEXT NOT NULL,
        form TEXT NOT NULL,
        filing_date DATE,
        item TEXT,
        chunk_index INT,
        text TEXT NOT NULL,
        embedding vector(768),
        text_search tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
    );

    CREATE INDEX IF NOT EXISTS chunks_embedding_idx
        ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

    CREATE INDEX IF NOT EXISTS chunks_ticker_idx ON chunks (ticker);

    CREATE INDEX IF NOT EXISTS chunks_fts_idx ON chunks USING GIN (text_search);

    CREATE TABLE IF NOT EXISTS financial_facts (
        id SERIAL PRIMARY KEY,
        ticker TEXT NOT NULL,
        fiscal_period TEXT NOT NULL,
        metric TEXT NOT NULL,
        value NUMERIC,
        source_doc_id TEXT
    );
"""

def init_db():
    with engine.connect() as conn:
        for stmt in DDL.split(";"):
            if stmt.strip():
                conn.execute(text(stmt))
        conn.commit()

if __name__ == "__main__":
    init_db()
    print("DB initialized.")