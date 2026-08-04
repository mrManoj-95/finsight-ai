import tiktoken

enc = tiktoken.get_encoding("cl100k_base")

def chunk_text(text: str, max_tokens=400, overlap=50):
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        chunks.append(enc.decode(chunk_tokens))
        start += max_tokens - overlap
    return chunks


def build_chunk_records(ticker, form, filing_date, item_num, text, doc_id):
    chunks = chunk_text(text)
    return [
        {
            "doc_id": doc_id,
            "ticker": ticker,
            "form": form,
            "filing_date": filing_date,
            "item": item_num,
            "chunk_index": i,
            "text": c,
        }
        for i, c in enumerate(chunks)
    ]