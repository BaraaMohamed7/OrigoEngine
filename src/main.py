import os
import re
from .indexer import build_index, save_index, load_index
from .query_engine import search, proximity_search
from .kgram_index import build_kgram_index
from .spelling import suggest_correction
from .ranking import rank_documents
from .evaluation import run_evaluation, print_evaluation_report


def format_result(doc_id: str, score: float, doc_store: dict) -> str:
    info = doc_store.get(doc_id, {})
    lang = info.get("language", "unknown")
    raw_text = info.get("raw_text", "")
    preview = raw_text[:120] + "..." if len(raw_text) > 120 else raw_text
    return f"  {doc_id:<18} | {lang:<8} | score={score:.4f}\n  {preview}"


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "..", "data")
    corpus_path = os.path.join(data_dir, "corpus")
    index_dir = os.path.join(data_dir, "index_data")

    print("=" * 60)
    print("  OrigoEngine — Bilingual Search Engine")
    print("=" * 60)

    index_path = os.path.join(index_dir, "index.json")
    if os.path.exists(index_path):
        print("Loading existing index...")
        index, doc_store = load_index(index_dir)
    else:
        print("Building index from corpus...")
        index, doc_store = build_index(corpus_path)
        save_index(index, doc_store, index_dir)
        print(f"Index saved to {index_dir}/")

    total_docs = len(doc_store)
    kgram_index = build_kgram_index(index, k=2)

    print(f"Indexed {total_docs} documents | {len(index)} unique terms")
    print()
    print("Commands:")
    print("  <query>       Search for terms (AND / proximity /k)")
    print("  eval          Run evaluation report")
    print("  rebuild       Rebuild index from corpus")
    print("  help          Show this message")
    print("  quit          Exit")
    print()

    while True:
        try:
            query = input("OrigoEngine> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not query:
            continue

        if query.lower() == "quit":
            print("Goodbye!")
            break

        if query.lower() == "help":
            print("\nCommands:")
            print("  <query>       Search for terms (AND / proximity /k)")
            print("  eval          Run evaluation report")
            print("  rebuild       Rebuild index from corpus")
            print("  help          Show this message")
            print("  quit          Exit")
            print()
            print("Query types:")
            print("  boolean:      machine learning")
            print("  proximity:    machine /2 learning")
            print()
            continue

        if query.lower() == "rebuild":
            print("Rebuilding index from corpus...")
            index, doc_store = build_index(corpus_path)
            save_index(index, doc_store, index_dir)
            kgram_index = build_kgram_index(index, k=2)
            total_docs = len(doc_store)
            print(f"Rebuilt: {total_docs} docs, {len(index)} terms")
            continue

        if query.lower() == "eval":
            results = run_evaluation(index, doc_store)
            print_evaluation_report(results)
            continue

        qtype, doc_set, terms = search(query, index)

        if not terms:
            print("  No searchable terms found (all words may be stopwords).")
            print()
            continue

        corrected_terms = []
        for term in terms:
            if term not in index:
                suggestion = suggest_correction(term, index, kgram_index)
                if suggestion:
                    print(
                        f"  Term '{term}' not found. Did you mean: '{suggestion}'? (y/n): ",
                        end="",
                    )
                    try:
                        response = input().strip().lower()
                    except (KeyboardInterrupt, EOFError):
                        print()
                        response = "n"
                    if response == "y":
                        corrected_terms.append(suggestion)
                    else:
                        corrected_terms.append(term)
                else:
                    print(
                        f"  Term '{term}' not found in index and no suggestions available."
                    )
                    corrected_terms.append(term)
            else:
                corrected_terms.append(term)

        if qtype == "proximity":
            term1, term2 = (
                corrected_terms[0],
                corrected_terms[1] if len(corrected_terms) > 1 else corrected_terms[0],
            )

            parsed = re.search(r"(\S+)\s*/(\d+)\s*(\S+)", query)
            k = int(parsed.group(2)) if parsed else 1
            doc_set = proximity_search(term1, term2, k, index)
            print(f"\n  [Proximity Search] {term1} /{k} {term2}")
        else:
            doc_set = set()
            if corrected_terms:
                first = corrected_terms[0]
                doc_set = set(index.get(first, {}).keys())
                for term in corrected_terms[1:]:
                    doc_set &= set(index.get(term, {}).keys())

        if not doc_set:
            print("  No results found.")
            print()
            continue

        ranked = rank_documents(corrected_terms, doc_set, index, doc_store, total_docs)

        print(f"\n  [{qtype.capitalize()} Search] {' '.join(corrected_terms)}")
        print(f"  {len(ranked)} result(s):\n")
        for doc_id, score in ranked:
            print(format_result(doc_id, score, doc_store))
            print()

        print()


if __name__ == "__main__":
    main()
