from sentence_transformers import SentenceTransformer, CrossEncoder
from sqlalchemy import text
from retrieval.db import engine

embed_model = SentenceTransformer("BAAI/bge-base-en-v1.5")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def vector_search(query: str, ticker: str = None, k: int = 20):
    q_emb = embed_model.encode(query, normalize_embeddings=True).tolist()
    filter_clause = "AND ticker = :ticker" if ticker else ""
    sql = f"""
        SELECT id, doc_id, ticker, form, item, chunk_index, text,
               1 - (embedding <=> :q_emb) AS score
        FROM chunks
        WHERE 1=1 {filter_clause}
        ORDER BY embedding <=> :q_emb
        LIMIT :k
    """
    params = {"q_emb": str(q_emb), "k": k}
    if ticker:
        params["ticker"] = ticker
    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


def lexical_search(query: str, ticker: str = None, k: int = 20):
    """Independent full-corpus lexical search via Postgres's native full-text
    search — queries the persisted GIN index directly, no in-memory index to
    build, cache, or refresh. websearch_to_tsquery accepts natural-language-ish
    input (handles quoted phrases, OR, - for exclusion) rather than requiring
    the stricter to_tsquery syntax."""
    filter_clause = "AND ticker = :ticker" if ticker else ""
    sql = f"""
        SELECT id, doc_id, ticker, form, item, chunk_index, text,
               ts_rank(text_search, websearch_to_tsquery('english', :query)) AS bm25_score
        FROM chunks
        WHERE text_search @@ websearch_to_tsquery('english', :query) {filter_clause}
        ORDER BY bm25_score DESC
        LIMIT :k
    """
    params = {"query": query, "k": k}
    if ticker:
        params["ticker"] = ticker
    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


def reciprocal_rank_fusion(result_lists: list, k: int = 60, id_key: str = "id"):
    """RRF: score(doc) = sum over lists of 1 / (k + rank_in_that_list).
    A doc appearing near the top of BOTH lists gets boosted; a doc unique to
    just one list (e.g. an exact keyword hit vector search missed) still surfaces
    instead of being silently dropped. k=60 is the standard constant from the
    original RRF paper / most production hybrid-search implementations."""
    fused_scores = {}
    doc_lookup = {}
    for results in result_lists:
        for rank, doc in enumerate(results):
            doc_id = doc[id_key]
            doc_lookup[doc_id] = doc
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (k + rank + 1)
    ranked_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)
    return [{**doc_lookup[i], "rrf_score": fused_scores[i]} for i in ranked_ids]


def hybrid_search(query: str, ticker: str = None, top_k: int = 8):
    vec_results = vector_search(query, ticker=ticker, k=20)
    lex_results = lexical_search(query, ticker=ticker, k=20)

    fused = reciprocal_rank_fusion([vec_results, lex_results])[:30]

    # Cross-encoder reranks the fused candidate pool for final precision
    pairs = [(query, r["text"]) for r in fused]
    rerank_scores = reranker.predict(pairs)
    for r, s in zip(fused, rerank_scores):
        r["rerank_score"] = float(s)

    return sorted(fused, key=lambda x: x["rerank_score"], reverse=True)[:top_k]