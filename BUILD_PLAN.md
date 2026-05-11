# OrigoEngine — Build Plan

Two versions: **Solo** and **Team (3–5)**. Both are time-independent — phases are ordered by dependency, not by week.

---

## Dependency Map

```
Phase 1 (Corpus)
    ↓
Phase 2 (Preprocessing) ← depends on corpus to test
    ↓
Phase 3 (Index)          ← depends on preprocessing
    ↓
Phase 4 (Query Engine)   ← depends on index
    ↓
Phase 5 (Spelling)       ← depends on index (k-gram built from index)
    ↓
Phase 6 (Ranking)        ← depends on index + doc_store
    ↓
Phase 7 (Evaluation)     ← depends on everything above
    ↓
Phase 8 (CLI)            ← depends on everything above
```

Phases 4, 5, 6 can proceed in parallel once Phase 3 is done.

---

## Version A — Solo

### Milestone 1: Corpus + Preprocessing

| Step | Deliverable | Edge Cases to Handle |
|------|-------------|---------------------|
| 1.1 | 10 English docs (~50 words each) in `corpus/en/` | Mixed case, punctuation, numbers in text |
| 1.2 | 10 Arabic docs (~50 words each) in `corpus/ar/` | Diacritics, tatweel, mixed Arabic/English |
| 1.3 | Stop-word files in `stopwords/` | Empty files, duplicates |
| 1.4 | `language_detector.py` | Empty string, numbers-only, mixed-language text |
| 1.5 | English pipeline in `preprocessing.py` | Empty input, single-word input, all-stopwords input |
| 1.6 | `stemmer_en.py` (Porter) | Empty string, single char, already-stemmed words, words with numbers |
| 1.7 | Arabic normalization in `preprocessing.py` | Text with no Arabic, all-diacritics text, mixed symbols |
| 1.8 | `stemmer_ar.py` (ISRI) | Empty string, short words (1-2 chars), prefixes/suffixes only |
| 1.9 | Arabic pipeline in `preprocessing.py` | Empty input, all-stopwords input |

**Validation:** Write a small test script or manual check that feeds every doc through both pipelines and inspects the token/position output. Confirm positions survive stop-word removal.

---

### Milestone 2: Indexing

| Step | Deliverable | Edge Cases to Handle |
|------|-------------|---------------------|
| 2.1 | `indexer.py` — builds positional inverted index | Empty doc, doc with one word, identical docs |
| 2.2 | Build `doc_store` alongside index | Zero-length doc, UTF-8 encoding issues |

**Validation:** Print the full index. Manually verify a few entries against the raw docs. Check that positions are correct.

---

### Milestone 3: Query Engine + Spelling + Ranking (parallel)

| Step | Deliverable | Edge Cases to Handle |
|------|-------------|---------------------|
| 3.1 | `query_engine.py` — single/multi-word AND search | No results, single word, query with stopwords only |
| 3.2 | `query_engine.py` — proximity `/k` search | `k=0`, overlapping terms, terms not in index |
| 3.3 | `kgram_index.py` — 2-gram index builder | Single-char terms, very short terms |
| 3.4 | `spelling.py` — Levenshtein distance | Empty strings, identical strings, very different strings |
| 3.5 | `spelling.py` — Jaccard + full correction pipeline | Word already in index, no candidates found, multiple equally-close candidates |
| 3.6 | `ranking.py` — TF-IDF calculation | Term not in doc, term in all docs (IDF → 0), doc with zero terms |
| 3.7 | `ranking.py` — Cosine similarity | Zero vectors, single-dimension vectors |
| 3.8 | `ranking.py` — `rank_documents()` | Empty candidate set, single candidate |

**Validation:** Run 5+ test queries manually. Check proximity results by hand. Feed misspelled words and verify suggestions. Confirm ranking order makes sense.

---

### Milestone 4: Evaluation

| Step | Deliverable | Edge Cases to Handle |
|------|-------------|---------------------|
| 4.1 | Define 5 ground-truth queries in `evaluation.py` | Queries that return zero results, queries matching all docs |
| 4.2 | `evaluate()` function with precision/recall | Division by zero (no retrieved, no relevant) |

**Validation:** Run evaluation, produce the report table. Precision + recall should be between 0 and 1.

---

### Milestone 5: CLI + Polish

| Step | Deliverable | Edge Cases to Handle |
|------|-------------|---------------------|
| 5.1 | `main.py` — interactive REPL | Empty input, `quit`, very long query |
| 5.2 | Wire all modules together | Any module not yet imported, index not built |
| 5.3 | Minimal README — how to run, example queries | — |
| 5.4 | Final edge-case pass | test with empty docs, single-char queries, Arabic-only, English-only, mixed |

---

## Version B — Team (3–5)

### How Roles Work

Each milestone has **owners** listed as suggestions — swap freely. Every milestone ends with a **integration check** where the team meets to verify pieces connect. Use a shared Git repo; branch per milestone, merge after integration check.

---

### Milestone 1: Corpus + Preprocessing

| Step | Deliverable | Owner(s) | Edge Cases |
|------|-------------|----------|-------------|
| 1.1 | 10 English docs in `corpus/en/` | A | Punctuation, numbers, mixed case |
| 1.2 | 10 Arabic docs in `corpus/ar/` | B | Diacritics, tatweel, mixed script |
| 1.3 | Stop-word files | A or B | — |
| 1.4 | `language_detector.py` | C | Empty string, numbers-only, mixed |
| 1.5 | English pipeline + `stemmer_en.py` | A | All-stopwords input, single word |
| 1.6 | Arabic pipeline + `stemmer_ar.py` + normalization | B | All-stopwords, diacritics-heavy |
| 1.7 | Unit test helpers (shared) | C or D | — |

**Integration check:** Run both pipelines on all 20 docs. Compare output with each other's machines. Ensure positions are preserved.

---

### Milestone 2: Indexing

| Step | Deliverable | Owner(s) | Edge Cases |
|------|-------------|----------|-------------|
| 2.1 | `indexer.py` — positional inverted index | C | Empty doc, identical docs |
| 2.2 | `doc_store` builder | C | Zero-length doc |
| 2.3 | Save/load index to JSON for sharing | D | Encoding issues |

**Integration check:** All team members rebuild the index from the corpus. Compare results — they must be identical.

---

### Milestone 3: Query Engine + Spelling + Ranking

Split into parallel tracks. Assign one track per person.

**Track Alpha — Query Engine** (owner: D or E)

| Step | Deliverable | Edge Cases |
|------|-------------|-------------|
| 3A.1 | Single/multi-word AND search | No results, stopword-only query |
| 3A.2 | Proximity `/k` search | `k=0`, terms not in index |

**Track Beta — Spelling Correction** (owner: A)

| Step | Deliverable | Edge Cases |
|------|-------------|-------------|
| 3B.1 | `kgram_index.py` | Short terms |
| 3B.2 | Levenshtein distance | Empty strings |
| 3B.3 | Jaccard + correction pipeline | Word already correct, no candidates |

**Track Gamma — Ranking** (owner: B)

| Step | Deliverable | Edge Cases |
|------|-------------|-------------|
| 3C.1 | TF-IDF calculation | Term in all docs (IDF=0) |
| 3C.2 | Cosine similarity | Zero vectors |
| 3C.3 | `rank_documents()` | Empty candidate set |

**Integration check:** All three tracks merge. Run test queries end-to-end through query → spelling → ranking. Verify results manually.

---

### Milestone 4: Evaluation

| Step | Deliverable | Owner(s) | Edge Cases |
|------|-------------|----------|-------------|
| 4.1 | Ground-truth definition (5 queries) | All together | — |
| 4.2 | `evaluation.py` | C | Division by zero |
| 4.3 | Generate report table | C | — |

**Integration check:** Compare evaluation results. If precision/recall is very low, debug the pipeline — usually a stemming or normalization issue.

---

### Milestone 5: CLI + Polish

| Step | Deliverable | Owner(s) | Edge Cases |
|------|-------------|----------|-------------|
| 5.1 | `main.py` — REPL loop | D | Empty input, quit |
| 5.2 | Wire all modules | D + everyone reviews | Import errors, missing index |
| 5.3 | README | E | — |
| 5.4 | Edge-case pass (all) | Everyone tests 2–3 edge cases each | — |

---

## Team Size Quick Reference

| Team Size | Track Split (Milestone 3) | Adjustments |
|-----------|--------------------------|-------------|
| 3 | Alpha: 1, Beta: 1, Gamma: 1 | Owner C handles indexing in M2, then joins Alpha |
| 4 | Alpha: 1, Beta: 1, Gamma: 2 | Extra person on ranking (takes evaluation too) |
| 5 | Alpha: 1, Beta: 1, Gamma: 1, QA: 1, Docs/CLI: 1 | Dedicated QA for edge-case testing from M3 onward |

---

## Edge Cases Checklist (Professor Typically Tests These)

- [x] Empty string or whitespace-only input — handled: returns empty result
- [x] Query with only stopwords — handled: returns empty terms (fixed Arabic stopwords normalization)
- [x] Query with terms not in the index — handled: returns empty doc set
- [x] Proximity query with `k=0` — handled: only exact same position matches
- [x] Proximity query where both terms are the same — handled: returns docs where term appears (|pos-pos|=0≤k)
- [x] Arabic text with heavy diacritics — handled: normalization strips all diacritics
- [x] Arabic text with tatweel characters — handled: normalization removes tatweel
- [x] Mixed Arabic + English in a single query — handled: detected as Arabic, only Arabic tokens extracted
- [x] Single-character terms — handled: Porter skips ≤2 chars, ISRI skips ≤2 chars
- [x] Very long queries (10+ terms) — handled: AND intersection filters down correctly
- [ ] Documents that are identical — handled by indexer (both get indexed)
- [ ] Documents with very few words (1–2) — handled: TF denominator still valid
- [x] Term appearing in all documents (IDF should be 0 or near-0) — handled: IDF approaches 0, term ranked low
- [x] Misspelled word with no close candidates — handled: returns None
- [x] Misspelled word with exact match (already correct) — handled: returns None
- [x] Division by zero guards in TF/IDF/cosine/precision/recall — all verified

---

## File Checklist

```
ir_project/
├── corpus/
│   ├── en/ (en_001–en_010)
│   └── ar/ (ar_001–ar_010)
├── stopwords/
│   ├── english_stopwords.txt
│   └── arabic_stopwords.txt
├── language_detector.py
├── preprocessing.py
├── stemmer_en.py
├── stemmer_ar.py
├── indexer.py
├── kgram_index.py
├── query_engine.py
├── spelling.py
├── ranking.py
├── evaluation.py
└── main.py
```
