def get_kgrams(term: str, k: int = 2) -> list[str]:
    padded = f"${term}$"
    return [padded[i : i + k] for i in range(len(padded) - k + 1)]


def build_kgram_index(index: dict, k: int = 2) -> dict[str, set[str]]:
    kgram_index: dict[str, set[str]] = {}
    for term in index.keys():
        for kgram in get_kgrams(term, k):
            if kgram not in kgram_index:
                kgram_index[kgram] = set()
            kgram_index[kgram].add(term)
    return kgram_index


if __name__ == "__main__":
    import json
    import os

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index_data")
    with open(os.path.join(output_dir, "index.json"), "r", encoding="utf-8") as f:
        index = json.load(f)

    kgram_index = build_kgram_index(index, k=2)

    print(f"Total k-grams: {len(kgram_index)}")
    print("\nSample k-gram entries (first 10):")
    for i, (kgram, terms) in enumerate(kgram_index.items()):
        if i >= 10:
            break
        print(f"  '{kgram}' → {sorted(list(terms))[:5]}... ({len(terms)} terms)")

    print("\nK-grams for 'comput':")
    if "comput" in index:
        kgrams = get_kgrams("comput", k=2)
        print(f"  {kgrams}")

    print("\nK-grams for 'machin':")
    if "machin" in index:
        kgrams = get_kgrams("machin", k=2)
        print(f"  {kgrams}")
