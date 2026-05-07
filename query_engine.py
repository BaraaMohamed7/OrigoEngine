import re
from language_detector import detect_language
from preprocessing import preprocess


def parse_query(query: str):
    proximity_pattern = r"(\S+)\s*/(\d+)\s*(\S+)"
    match = re.search(proximity_pattern, query)

    if match:
        term1 = match.group(1)
        k = int(match.group(2))
        term2 = match.group(3)
        return ("proximity", term1, k, term2)
    else:
        return ("boolean", query.split())


def boolean_search(terms: list, index: dict) -> set:
    if not terms:
        return set()

    first_term = terms[0]
    result = set(index.get(first_term, {}).keys())

    for term in terms[1:]:
        result &= set(index.get(term, {}).keys())

    return result


def proximity_search(term1: str, term2: str, k: int, index: dict) -> set:
    postings1 = index.get(term1, {})
    postings2 = index.get(term2, {})

    common_docs = set(postings1.keys()) & set(postings2.keys())

    results = set()
    for doc_id in common_docs:
        positions1 = postings1[doc_id]
        positions2 = postings2[doc_id]
        found = False
        for p1 in positions1:
            for p2 in positions2:
                if abs(p1 - p2) <= k:
                    results.add(doc_id)
                    found = True
                    break
            if found:
                break

    return results


def search(query: str, index: dict) -> tuple[str, set, list]:
    parsed = parse_query(query)

    if parsed[0] == "proximity":
        _, raw_term1, k, raw_term2 = parsed
        lang = detect_language(raw_term1 + " " + raw_term2)

        tokens1 = preprocess(raw_term1, lang)
        tokens2 = preprocess(raw_term2, lang)

        if not tokens1 or not tokens2:
            return ("proximity", set(), [])

        term1 = tokens1[0][0]
        term2 = tokens2[0][0]
        result_docs = proximity_search(term1, term2, k, index)
        return ("proximity", result_docs, [term1, term2])

    else:
        _, raw_terms = parsed
        if not raw_terms:
            return ("boolean", set(), [])

        lang = detect_language(" ".join(raw_terms))
        preprocessed = preprocess(" ".join(raw_terms), lang)

        terms = [term for term, pos in preprocessed]

        if not terms:
            return ("boolean", set(), [])

        result_docs = boolean_search(terms, index)
        return ("boolean", result_docs, terms)


if __name__ == "__main__":
    import json
    import os

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index_data")
    with open(os.path.join(output_dir, "index.json"), "r", encoding="utf-8") as f:
        index = json.load(f)

    print("=== Boolean Search Tests ===")
    queries = [
        "computer science",
        "machine learning",
        "ocean ecosystem",
        "data structures",
    ]
    for q in queries:
        qtype, docs, terms = search(q, index)
        print(f"  Query: '{q}' → terms={terms}, type={qtype}")
        print(f"    Results: {sorted(docs)}")

    print("\n=== Proximity Search Tests ===")
    prox_queries = ["machine /2 learning", "computer /1 science", "solar /3 energy"]
    for q in prox_queries:
        qtype, docs, terms = search(q, index)
        print(f"  Query: '{q}' → terms={terms}, type={qtype}")
        print(f"    Results: {sorted(docs)}")

    print("\n=== Edge Cases ===")
    edge_cases = ["", "nonexistentterm", "the"]
    for q in edge_cases:
        qtype, docs, terms = search(q, index)
        print(f"  Query: '{q}' → terms={terms}, type={qtype}, docs={docs}")
