from .kgram_index import get_kgrams


def jaccard(kgrams_a: set, kgrams_b: set) -> float:
    intersection = len(kgrams_a & kgrams_b)
    union = len(kgrams_a | kgrams_b)
    return intersection / union if union > 0 else 0.0


def levenshtein(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)

    if m == 0:
        return n
    if n == 0:
        return m

    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],
                    dp[i][j - 1],
                    dp[i - 1][j - 1],
                )

    return dp[m][n]


def suggest_correction(
    misspelled: str, index: dict, kgram_index: dict, k: int = 2
) -> str | None:
    if misspelled in index:
        return None

    query_kgrams = set(get_kgrams(misspelled, k))

    candidates = set()
    for kgram in query_kgrams:
        candidates |= kgram_index.get(kgram, set())

    filtered = [
        c for c in candidates if jaccard(query_kgrams, set(get_kgrams(c, k))) >= 0.3
    ]

    ranked = sorted(filtered, key=lambda c: levenshtein(misspelled, c))

    return ranked[0] if ranked else None


if __name__ == "__main__":
    import json
    import os
    from kgram_index import build_kgram_index

    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", "index_data"
    )
    with open(os.path.join(output_dir, "index.json"), "r", encoding="utf-8") as f:
        index = json.load(f)

    kgram_index = build_kgram_index(index, k=2)

    print("=== Levenshtein Distance Tests ===")
    pairs = [
        ("speling", "spelling"),
        ("korrect", "correct"),
        ("comput", "comput"),
        ("machin", "machine"),
        ("", "hello"),
        ("abc", "abc"),
    ]
    for s1, s2 in pairs:
        dist = levenshtein(s1, s2)
        print(f'  lev("{s1}", "{s2}") = {dist}')

    print("\n=== Jaccard Similarity Tests ===")
    words = [("comput", "comput"), ("comput", "compit"), ("hello", "world")]
    for a, b in words:
        sim = jaccard(set(get_kgrams(a, 2)), set(get_kgrams(b, 2)))
        print(f"  jaccard({get_kgrams(a, 2)}, {get_kgrams(b, 2)}) = {sim:.4f}")

    print("\n=== Spelling Correction Tests ===")
    misspelled_words = ["compter", "machne", "speling", "scence", "nonexistent"]
    for word in misspelled_words:
        suggestion = suggest_correction(word, index, kgram_index)
        print(
            f'  "{word}" → {f"Did you mean: {suggestion}" if suggestion else "No suggestion"}'
        )

    print("\n=== Word already in index ===")
    print(f'  "comput" → {suggest_correction("comput", index, kgram_index)}')
