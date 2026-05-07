from .query_engine import search
from .ranking import rank_documents


GROUND_TRUTH = {
    "computer science": {
        "relevant": {"en/doc01.txt", "en/doc03.txt", "en/doc07.txt"},
    },
    "machine learning": {
        "relevant": {"en/doc01.txt", "en/doc03.txt", "en/doc05.txt"},
    },
    "artificial intelligence": {
        "relevant": {"en/doc01.txt", "en/doc03.txt"},
    },
    "ocean ecosystem": {
        "relevant": {"en/doc06.txt"},
    },
    "basketball championship": {
        "relevant": {"en/doc02.txt"},
    },
    "ancient history": {
        "relevant": {"en/doc04.txt"},
    },
    "data structures": {
        "relevant": {"en/doc01.txt", "en/doc10.txt"},
    },
    "renewable energy": {
        "relevant": {"en/doc09.txt"},
    },
    "robot": {
        "relevant": {"en/doc07.txt"},
    },
    "space exploration": {
        "relevant": {"en/doc08.txt"},
    },
    "الذكاء الاصطناعي": {
        "relevant": {"ar/doc01.txt", "ar/doc05.txt", "ar/doc08.txt"},
    },
    "الحضارة الإسلامية": {
        "relevant": {"ar/doc04.txt"},
    },
    "تقنية المعلومات": {
        "relevant": {"ar/doc03.txt"},
    },
}


def evaluate(query: str, retrieved: set, ground_truth: set) -> dict:
    relevant_retrieved = retrieved & ground_truth

    precision = len(relevant_retrieved) / len(retrieved) if len(retrieved) > 0 else 0.0
    recall = (
        len(relevant_retrieved) / len(ground_truth) if len(ground_truth) > 0 else 0.0
    )

    return {
        "query": query,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "relevant_retrieved": len(relevant_retrieved),
        "total_retrieved": len(retrieved),
        "total_relevant": len(ground_truth),
    }


def run_evaluation(index: dict, doc_store: dict) -> list[dict]:
    total_docs = len(doc_store)
    results = []

    for query, data in GROUND_TRUTH.items():
        qtype, doc_set, terms = search(query, index)
        ranked = rank_documents(terms, doc_set, index, doc_store, total_docs)
        retrieved = set(doc_id for doc_id, score in ranked)

        eval_result = evaluate(query, retrieved, data["relevant"])
        eval_result["type"] = qtype
        eval_result["terms"] = terms
        results.append(eval_result)

    return results


def print_evaluation_report(results: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("EVALUATION REPORT")
    print("=" * 80)
    print(
        f"{'Query':<28} {'Type':<11} {'Precision':>9} {'Recall':>7} "
        f"{'RelRet':>6} {'Ret':>4} {'Rel':>4}"
    )
    print("-" * 80)

    avg_precision = 0
    avg_recall = 0

    for r in results:
        print(
            f"{r['query']:<28} {r['type']:<11} {r['precision']:>9.4f} {r['recall']:>7.4f} "
            f"{r['relevant_retrieved']:>6} {r['total_retrieved']:>4} {r['total_relevant']:>4}"
        )
        avg_precision += r["precision"]
        avg_recall += r["recall"]

    n = len(results)
    print("-" * 80)
    print(f"{'AVERAGE':<28} {'':11} {avg_precision / n:>9.4f} {avg_recall / n:>7.4f}")
    print("=" * 80)


if __name__ == "__main__":
    import os
    from .indexer import load_index

    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", "index_data"
    )
    index, doc_store = load_index(output_dir)

    results = run_evaluation(index, doc_store)
    print_evaluation_report(results)
