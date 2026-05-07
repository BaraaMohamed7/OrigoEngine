import math


def compute_tf(term: str, doc_id: str, index: dict, doc_store: dict) -> float:
    positions = index.get(term, {}).get(doc_id, [])
    count = len(positions) if isinstance(positions, list) else 0
    total_terms = doc_store.get(doc_id, {}).get("total_terms", 0)
    return count / total_terms if total_terms > 0 else 0.0


def compute_idf(term: str, index: dict, total_docs: int) -> float:
    df = len(index.get(term, {}))
    return math.log(total_docs / df) if df > 0 else 0.0


def compute_tfidf(
    term: str, doc_id: str, index: dict, doc_store: dict, total_docs: int
) -> float:
    return compute_tf(term, doc_id, index, doc_store) * compute_idf(
        term, index, total_docs
    )


def cosine_similarity(query_vector: dict, doc_vector: dict) -> float:
    dot_product = sum(
        query_vector.get(t, 0) * doc_vector.get(t, 0) for t in query_vector
    )

    query_magnitude = math.sqrt(sum(v**2 for v in query_vector.values()))
    doc_magnitude = math.sqrt(sum(v**2 for v in doc_vector.values()))

    if query_magnitude == 0 or doc_magnitude == 0:
        return 0.0

    return dot_product / (query_magnitude * doc_magnitude)


def rank_documents(
    query_terms: list,
    candidate_docs: set,
    index: dict,
    doc_store: dict,
    total_docs: int,
) -> list[tuple[str, float]]:
    if not candidate_docs or not query_terms:
        return []

    query_vector = {term: compute_idf(term, index, total_docs) for term in query_terms}

    scores = {}
    for doc_id in candidate_docs:
        doc_vector = {
            term: compute_tfidf(term, doc_id, index, doc_store, total_docs)
            for term in query_terms
        }
        scores[doc_id] = cosine_similarity(query_vector, doc_vector)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


if __name__ == "__main__":
    import json
    import os
    from query_engine import search

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "index_data")
    with open(os.path.join(output_dir, "index.json"), "r", encoding="utf-8") as f:
        index = json.load(f)
    with open(os.path.join(output_dir, "doc_store.json"), "r", encoding="utf-8") as f:
        doc_store = json.load(f)

    total_docs = len(doc_store)

    print("=== TF-IDF Tests ===")
    term = "comput"
    for doc_id in index.get(term, {}):
        tf = compute_tf(term, doc_id, index, doc_store)
        idf = compute_idf(term, index, total_docs)
        tfidf = compute_tfidf(term, doc_id, index, doc_store, total_docs)
        print(f"  '{term}' in {doc_id}: tf={tf:.6f}, idf={idf:.4f}, tfidf={tfidf:.6f}")

    print(f"\n  IDF for common vs rare terms:")
    print(
        f"    'comput' (in {len(index.get('comput', {}))} docs): idf={compute_idf('comput', index, total_docs):.4f}"
    )
    rare_term = list(index.keys())[0]
    print(
        f"    '{rare_term}' (in {len(index.get(rare_term, {}))} docs): idf={compute_idf(rare_term, index, total_docs):.4f}"
    )

    print("\n=== Cosine Similarity + Ranking Tests ===")
    queries = ["computer science", "machine learning", "ocean ecosystem"]
    for q in queries:
        qtype, docs, terms = search(q, index)
        ranked = rank_documents(terms, docs, index, doc_store, total_docs)
        print(f"\n  Query: '{q}' → terms={terms}")
        for doc_id, score in ranked:
            print(f"    {doc_id}: score={score:.6f}")

    print("\n=== Edge Cases ===")
    print(
        f"  Empty candidate set: {rank_documents(['comput'], set(), index, doc_store, total_docs)}"
    )
    print(
        f"  Empty terms: {rank_documents([], {'en/doc01.txt'}, index, doc_store, total_docs)}"
    )
    print(
        f"  Non-existent term TF: {compute_tf('xyz', 'en/doc01.txt', index, doc_store):.6f}"
    )
    print(f"  Non-existent term IDF: {compute_idf('xyz', index, total_docs):.6f}")
