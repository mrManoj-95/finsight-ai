from retrieval.hybrid_search import hybrid_search

def test_hybrid_search_returns_results():
    results = hybrid_search("what are the main risk factors", ticker="AAPL", top_k=5)
    assert len(results) > 0
    assert "text" in results[0]