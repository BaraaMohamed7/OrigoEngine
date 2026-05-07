import os
import json
from language_detector import detect_language
from preprocessing import preprocess


def get_all_docs(corpus_path: str) -> list[str]:
    docs = []
    for lang_dir in ["en", "ar"]:
        dir_path = os.path.join(corpus_path, lang_dir)
        if not os.path.isdir(dir_path):
            continue
        for filename in sorted(os.listdir(dir_path)):
            if filename.endswith(".txt"):
                docs.append(os.path.join(dir_path, filename))
    return docs


def get_doc_id(doc_path: str) -> str:
    parts = doc_path.replace("\\", "/").split("/")
    lang_dir = parts[-2]
    filename = parts[-1]
    return f"{lang_dir}/{filename}"


def build_index(corpus_path: str) -> tuple[dict, dict]:
    index: dict[str, dict[str, list[int]]] = {}
    doc_store: dict[str, dict] = {}

    for doc_path in get_all_docs(corpus_path):
        doc_id = get_doc_id(doc_path)

        with open(doc_path, "r", encoding="utf-8") as f:
            text = f.read()

        if not text.strip():
            doc_store[doc_id] = {
                "total_terms": 0,
                "raw_text": text,
                "language": "english",
            }
            continue

        lang = detect_language(text)
        tokens_with_positions = preprocess(text, lang)

        for term, position in tokens_with_positions:
            if term not in index:
                index[term] = {}
            if doc_id not in index[term]:
                index[term][doc_id] = []
            index[term][doc_id].append(position)

        doc_store[doc_id] = {
            "total_terms": len(tokens_with_positions),
            "raw_text": text,
            "language": lang,
        }

    return index, doc_store


def save_index(index: dict, doc_store: dict, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    with open(os.path.join(output_dir, "doc_store.json"), "w", encoding="utf-8") as f:
        json.dump(doc_store, f, ensure_ascii=False, indent=2)


def load_index(output_dir: str) -> tuple[dict, dict]:
    with open(os.path.join(output_dir, "index.json"), "r", encoding="utf-8") as f:
        index = json.load(f)
    with open(os.path.join(output_dir, "doc_store.json"), "r", encoding="utf-8") as f:
        doc_store = json.load(f)
    return index, doc_store


if __name__ == "__main__":
    corpus_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index_data")

    print("Building index...")
    index, doc_store = build_index(corpus_path)

    print(f"Indexed {len(doc_store)} documents")
    print(f"Vocabulary size: {len(index)} terms")

    print("\nSample index entries (first 10 terms):")
    for i, (term, postings) in enumerate(index.items()):
        if i >= 10:
            break
        docs = {doc_id: positions for doc_id, positions in postings.items()}
        print(f"  '{term}' → {docs}")

    print("\nDoc store summary:")
    for doc_id, info in doc_store.items():
        print(f"  {doc_id}: {info['total_terms']} terms, lang={info['language']}")

    save_index(index, doc_store, output_dir)
    print(f"\nIndex saved to {output_dir}/")
