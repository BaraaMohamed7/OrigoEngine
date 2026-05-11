# OrigoEngine — Overview & Architecture

## What Is This Project?

A **bilingual (English + Arabic) search engine** built from scratch. Given a text query, it:

1. Detects the language
2. Preprocesses (tokenizes, removes stopwords, stems)
3. Searches a positional inverted index
4. Corrects spelling mistakes
5. Ranks results by TF-IDF cosine similarity
6. Evaluates accuracy with precision/recall

No external NLP/search libraries are used for the core logic — everything is implemented manually.

---

## Project Structure

```
OrigoEngine/
├── run.py                       Entry point — run with: python run.py
├── data/
│   ├── corpus/
│   │   ├── en/                  5 English documents
│   │   └── ar/                  5 Arabic documents
│   ├── stopwords/
│   │   ├── english_stopwords.txt
│   │   └── arabic_stopwords.txt
│   └── index_data/              Auto-generated (index.json, doc_store.json)
├── src/
│   ├── __init__.py
│   ├── language_detector.py     Detects Arabic vs English
│   ├── stemmer_en.py            Porter Stemmer (English)
│   ├── stemmer_ar.py            ISRI Stemmer (Arabic)
│   ├── preprocessing.py         Tokenize → stop-words → stem (both languages)
│   ├── indexer.py               Builds positional inverted index
│   ├── kgram_index.py           K-gram index for spelling correction
│   ├── query_engine.py          Boolean + proximity search
│   ├── spelling.py              Jaccard + Levenshtein correction
│   ├── ranking.py               TF-IDF + cosine similarity
│   ├── evaluation.py            Precision & recall
│   └── main.py                  Interactive REPL
├── IR_Project_Plan.md           Original project specification
├── BUILD_PLAN.md                Build plan (solo + team)
├── OVERVIEW.md                  Architecture & module docs (this file)
└── EXPLANATION.md               Line-by-line code explanation
```

---

## Data Flow (Full Pipeline)

```
User types: "machine /2 learning"
                    │
                    ▼
         ┌─────────────────────┐
         │  language_detector   │  ← detects "english"
         └─────────┬───────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  preprocessing.py   │
         │                     │
         │  English path:       │
         │   lowercase          │
         │   tokenize (regex)   │
         │   remove stopwords   │
         │   porter stem        │
         │                     │
         │  Arabic path:        │
         │   normalize arabic   │
         │   tokenize (regex)   │
         │   remove stopwords   │
         │   ISRI stem          │
         │                     │
         │  Output: [(stem, pos), ...]
         └─────────┬───────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  query_engine.py    │  ← parse /k vs boolean
         └─────────┬───────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
   Boolean Search    Proximity Search
   (AND/OR of terms)  (|pos1-pos2| ≤ k)
          │                 │
          └────────┬────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  spelling.py        │  ← if term not in index,
         │                     │     suggest via k-gram + edit distance
         └─────────┬───────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  ranking.py         │  ← TF-IDF vectors → cosine similarity
         └─────────┬───────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  Ranked results     │  [(doc_id, score), ...]
         └─────────────────────┘
```

---

## Module Summary (Phase 1 — Already Built)

### `language_detector.py`

**Purpose:** Decide if a piece of text is Arabic or English.

**How it works:**
- Scans the text for characters in the Arabic Unicode block (`\u0600`–`\u06FF`)
- If any Arabic character is found → `"arabic"`, otherwise → `"english"`
- Edge case: empty string defaults to `"english"`

**Key function:** `detect_language(text) → "arabic" | "english"`

---

### `stemmer_en.py` — Porter Stemmer

**Purpose:** Reduce English words to their root form by stripping suffixes in 5 ordered steps.

**How it works:**

The Porter algorithm is a rule-based suffix stripper. It processes a word through sequential steps. Each step checks if the word ends in certain suffixes and, if the **measure** (m) of the remaining stem is high enough, removes or replaces the suffix.

**Key concept — Measure (m):**
The number of VC (vowel-consonant) sequences in a word after removing the suffix.

```
TR      → m=0  (just consonants)
TREE    → m=0  (just one vowel sequence, no VC pair)
TROUBLE→ m=1  (TR-OU-BLE → VC)
TROUBLES→ m=2 (TROUB-LES → VCVC)
```

**The 5 steps:**

| Step | What it does | Example |
|------|------|---------|
| 1a | Remove plural/possessive | `sses`→`ss`, `ies`→`i`, `s`→ removed |
| 1b | Remove `eed`, `ed`, `ing` | `agreed`→`agree`, `running`→`run` |
| 1c | Turn trailing `y` to `i` | `happy`→`happi` |
| 2 | Remove double suffixes (m>0) | `ational`→`ate`, `ization`→`ize` |
| 3 | Remove more suffixes (m>0) | `icate`→`ic`, `fulness`→`ful`→`` |
| 4 | Remove even more suffixes (m>1) | `ance`→removed, `ment`→removed |
| 5a | Remove trailing `e` (m>1) | `probate`→`probat` |
| 5b | Remove double `ll` (m>1) | `controll`→`control` |

**Helper functions:**

| Function | What it does |
|----------|------|
| `_is_consonant(word, i)` | Is character at position i a consonant? `y` depends on context |
| `_measure(word)` | Count of VC sequences (the "m" value) |
| `_has_vowel(word)` | Does the word contain at least one vowel? |
| `_ends_double_consonant(word)` | Does it end with two identical consonants? |
| `_cvc(word)` | Does it end consonant-vowel-consonant (and not w/x/y)? |

**Key function:** `porter_stem(word) → stemmed_word`

---

### `stemmer_ar.py` — ISRI Stemmer (Simplified)

**Purpose:** Strip Arabic prefixes and suffixes to get the word root.

**How it works:**

Arabic words are built from a root (usually 3 consonants) with layered prefixes and suffixes. The ISRI stemmer doesn't do full root extraction — it does **light stemming**: removing common prefixes and suffixes.

**Prefix patterns removed (by regex):**

| Prefix | Arabic | Example |
|--------|--------|---------|
| `وال` | و+ال | والكتاب → كتاب |
| `بال` | ب+ال | بالكتاب → كتاب |
| `ال` | ال | الكتاب → كتاب |
| `و` | و | وكتاب → كتاب |
| `ب` | ب | بكتاب → كتاب |

**Suffix patterns removed (by regex):**

| Suffix | Arabic | Example |
|--------|--------|---------|
| `ة` | ة | الكتابة → الكتاب |
| `ين` | ين | الكاتبين → الكاتب |
| `ون` | ون | الكاتبون → الكاتب |
| `ات` | ات | الجامعات → الجامف |

**The algorithm:**
1. Remove prefix (if stem ≥ 2 chars)
2. Remove suffix (if stem ≥ 2 chars)
3. Try removing prefix again
4. Try removing suffix again

This two-pass approach catches cases like `والكتابة` → remove `وال` → `كتابة` → remove `ة` → `كتاب`.

**Key function:** `isri_stem(word) → stemmed_word`

---

### `preprocessing.py` — The Pipeline Orchestrator

**Purpose:** Tie together language detection, normalization, tokenization, stopword removal, and stemming into a single `preprocess()` function.

**How it works — English path:**

```
"Information Retrieval is great"
    → lowercase:     "information retrieval is great"
    → tokenize:      ["information", "retrieval", "is", "great"]
    → remove stops:  ["information", "retrieval", "great"]   (position 0, 1, 3)
    → porter stem:   [("inform", 0), ("retriev", 1), ("great", 3)]
```

**How it works — Arabic path:**

```
"الذكاء الاصطناعي هو فرع"
    → normalize:     "الذكاء الاصطناعي هو فرع"  (handles أ→ا, ى→ي, ة→ه)
    → tokenize:      ["الذكاء", "الاصطناعي", "هو", "فرع"]
    → remove stops:  ["الذكاء", "الاصطناعي", "فرع"]
    → ISRI stem:     [("ذكاء", 0), ("اصطناعي", 1), ("فرع", 3)]
```

**Why positions matter:**

Notice position `3` in `("great", 3)` — `is` was at position 2 but got removed as a stopword. The position `2` is gone. This is critical for **proximity search** later, where we need to check if two terms appear within k words of each other in the **original document**.

**Arabic normalization (`normalize_arabic`):**

| Input | Rule | Output |
|-------|------|--------|
| `أ` `إ` `آ` | → `ا` | Unifies alif forms |
| `ى` | → `ي` | Alif maqsura → ya |
| `ة` | → `ه` | Ta marbuta → ha |
| `َ ُ ِ ً ٌ ٍ ّ ْ` | Remove | Diacritics (tashkeel) |
| `ـ` | Remove | Tatweel |

**Key functions:**

| Function | Signature | Returns |
|----------|-----------|---------|
| `preprocess(text, lang=None)` | `str, str→"arabic"\|"english"` → `list[(str, int)]` | List of (stemmed_term, original_position) |
| `preprocess_english(text)` | `str` → `list[(str, int)]` | English pipeline |
| `preprocess_arabic(text)` | `str` → `list[(str, int)]` | Arabic pipeline |
| `normalize_arabic(text)` | `str` → `str` | Normalized Arabic text |
| `tokenize_english(text)` | `str` → `list[str]` | Split on non-alpha |
| `tokenize_arabic(text)` | `str` → `list[str]` | Extract Arabic character sequences |

**Stopword loading:** Uses a singleton pattern with global variables (`_ENGLISH_STOPWORDS`, `_ARABIC_STOPWORDS`). First call loads from file, subsequent calls reuse the cached set. This avoids reading the file on every call.

---

### `indexer.py` — Positional Inverted Index Builder

**Purpose:** Read all corpus documents, preprocess them, and build two data structures:

1. **Positional Inverted Index** — maps each term to its occurrences across documents, with positions
2. **Document Store** — metadata about each document (term count, raw text, language)

**Index structure:**

```python
index = {
    "term": {
        "en/en_001.txt": [0, 5, 12],
        "en/en_003.txt": [2, 8],
    }
}
```

**Doc store structure:**

```python
doc_store = {
    "en/en_001.txt": {
        "total_terms": 32,       # count of (stemmed, non-stopword) terms
        "raw_text": "Computer science...",
        "language": "english",
    }
}
```

**How it works:**

```
For each .txt file in corpus/en/ and corpus/ar/:
    1. Read the file
    2. Detect language
    3. Preprocess (tokenize → stopwords → stem) → get [(term, position), ...]
    4. For each (term, position):
         index[term][doc_id].append(position)
    5. Store doc metadata in doc_store
```

**Why positions matter:** Positions enable **proximity search** (Phase 4). If "machine" is at position 4 and "learn" is at position 5 in the same document, `|4 - 5| = 1 ≤ k` means they're within k=2 words of each other.

**Key functions:**

| Function | Returns | Purpose |
|----------|---------|---------|
| `build_index(corpus_path)` | `(index, doc_store)` | Build both data structures from corpus |
| `save_index(index, doc_store, dir)` | `None` | Save to JSON files |
| `load_index(dir)` | `(index, doc_store)` | Load from JSON files |
| `get_all_docs(corpus_path)` | `list[str]` | List all .txt files in corpus |
| `get_doc_id(doc_path)` | `str` | Convert file path to `"en/en_001.txt"` format |

**Index saved to:** `index_data/index.json` and `index_data/doc_store.json`

**Current stats:** 10 documents indexed, 659 unique terms (357 English, 302 Arabic).

---

### `query_engine.py` — Boolean & Proximity Search

**Purpose:** Parse a user query, detect its type (boolean or proximity), preprocess it, and search the index.

**Query types:**

| Type | Example | Behavior |
|------|---------|----------|
| Boolean (AND) | `machine learning` | All terms must appear in the same doc |
| Proximity | `machine /2 learning` | Both terms within k positions of each other |

**How it works:**

```
User types: "machine /2 learning"
    ↓
parse_query() → detects "/2" → ("proximity", "machine", 2, "learning")
    ↓
preprocess each term → ["machin"], ["learn"]
    ↓
proximity_search("machin", "learn", 2, index)
    ↓
For each doc containing BOTH terms:
    check |position_machin - position_learn| ≤ 2
    ↓
Return matching doc IDs
```

**Key functions:**

| Function | Returns | Purpose |
|----------|---------|---------|
| `parse_query(query)` | `("proximity", t1, k, t2)` or `("boolean", [words])` | Detect query type |
| `boolean_search(terms, index)` | `set` of doc IDs | AND intersection of posting lists |
| `proximity_search(t1, t2, k, index)` | `set` of doc IDs | Docs where t1 and t2 are within k positions |
| `search(query, index)` | `(type, doc_set, term_list)` | Full pipeline: parse → preprocess → search |

---

### `kgram_index.py` — K-gram Index for Spelling

**Purpose:** Build a bi-gram (2-gram) index from all terms in the main index. Used by the spelling corrector to find candidate corrections.

**How k-grams work:**

```
Term: "hello"
Padded: "$hello$"
2-grams: ["$h", "he", "el", "ll", "lo", "o$"]

Index maps each 2-gram → set of terms containing it:
  "$h" → {"hello", "help", "house", ...}
  "he" → {"hello", "help", "she", ...}
```

**Key functions:**

| Function | Returns | Purpose |
|----------|---------|---------|
| `get_kgrams(term, k=2)` | `list[str]` | Generate k-grams for a term |
| `build_kgram_index(index, k=2)` | `dict[str, set]` | Build full k-gram index from main index |

**Current stats:** 729 unique 2-grams generated from 659 terms.

---

### `spelling.py` — Spelling Correction

**Purpose:** If a query term is not in the index, suggest the closest matching term using k-gram Jaccard similarity for filtering and Levenshtein distance for ranking.

**Correction flow:**

```
User types: "machne"
    ↓
Is "machne" in index?  → No
    ↓
Get k-grams of "machne": ["$m", "ma", "ac", "ch", "hn", "ne", "e$"]
    ↓
Collect all terms sharing any k-gram with "machne" from k-gram index
    ↓
Filter by Jaccard ≥ 0.3
    ↓
Rank remaining candidates by Levenshtein distance (ascending)
    ↓
Return best match: "machin"
```

**Key functions:**

| Function | Returns | Purpose |
|----------|---------|---------|
| `jaccard(kgrams_a, kgrams_b)` | `float` (0.0–1.0) | Similarity between two k-gram sets |
| `levenshtein(s1, s2)` | `int` | Minimum edit distance between two strings |
| `suggest_correction(word, index, kgram_index, k=2)` | `str` or `None` | Best suggestion, or None if word is already correct |

**Levenshtein DP:** Classic dynamic programming table. `dp[i][j]` = minimum edits to transform `s1[:i]` into `s2[:j]`. Time complexity: O(m×n).

---

### `ranking.py` — TF-IDF & Cosine Similarity

**Purpose:** Given candidate documents from search, rank them by relevance using TF-IDF weighted cosine similarity.

**Formulas:**

| Metric | Formula |
|--------|---------|
| TF(t, d) | `count(t in d) / total_terms(d)` |
| IDF(t) | `log(N / df(t))` where N = total docs, df = docs containing t |
| TF-IDF(t, d) | `TF × IDF` |
| Cosine(Q, D) | `Σ(q_i × d_i) / (|Q| × |D|)` |

**How ranking works:**

```
Query terms: ["machin", "learn"]
Candidate docs: {"en/en_001.txt", "en/en_003.txt"}

1. Build query vector: {term: IDF(term)}
   → {"machin": 0.51, "learn": 0.69}

2. For each candidate doc, build doc vector: {term: TF-IDF(term, doc)}
   → e.g. en_001: {"machin": 0.094, "learn": 0.094}

3. Compute cosine similarity between query and doc vectors

4. Sort docs by score descending
```

**Key functions:**

| Function | Returns | Purpose |
|----------|---------|---------|
| `compute_tf(term, doc_id, index, doc_store)` | `float` | Term frequency in a document |
| `compute_idf(term, index, total_docs)` | `float` | Inverse document frequency |
| `compute_tfidf(term, doc_id, index, doc_store, total_docs)` | `float` | TF × IDF |
| `cosine_similarity(q_vec, d_vec)` | `float` | Cosine between two vectors |
| `rank_documents(terms, docs, index, doc_store, total_docs)` | `list[(doc_id, score)]` | Ranked results |

---

### `evaluation.py` — Precision & Recall

**Purpose:** Evaluate search accuracy against manually defined ground truth queries.

**Ground truth:** A dictionary mapping 13 queries (English + Arabic) to their expected relevant documents. These were defined by inspecting the corpus and verifying against the index.

**Formulas:**

```
Precision = |Retrieved ∩ Relevant| / |Retrieved|
Recall    = |Retrieved ∩ Relevant| / |Relevant|
```

**Evaluation report output:**

```
Query                        Type        Precision  Recall RelRet  Ret  Rel
--------------------------------------------------------------------------------
machine learning             boolean        1.0000  1.0000      1    1    1
quantum computing            boolean        1.0000  1.0000      1    1    1
الذكاء الاصطناعي             boolean        1.0000  1.0000      3    3    3
...
AVERAGE                                     1.0000  0.9744
```

**Key functions:**

| Function | Returns | Purpose |
|----------|---------|---------|
| `evaluate(query, retrieved, ground_truth)` | `dict` | Calculate precision, recall, and counts |
| `run_evaluation(index, doc_store)` | `list[dict]` | Run all ground truth queries and evaluate each |
| `print_evaluation_report(results)` | `None` | Print formatted evaluation table |

---

### `main.py` — Interactive CLI

**Purpose:** Ties all modules together into an interactive search engine REPL.

**Startup flow:**

```
1. Check if index_data/ exists → load cached index
2. If not → build index from corpus/ → save to disk
3. Build k-gram index from main index
4. Print stats and available commands
```

**Commands:**

| Command | Action |
|---------|--------|
| `<query>` | Search (boolean AND or proximity `/k`) |
| `eval` | Run evaluation report |
| `rebuild` | Rebuild index from corpus |
| `help` | Show usage instructions |
| `quit` | Exit |

**Query flow:**

```
User types: "machine learning"
    ↓ parse query → boolean, terms=["machine", "learning"]
    ↓ preprocess → ["machin", "learn"]
    ↓ spelling check each term → "machin" ✓, "learn" ✓
    ↓ boolean_search → {"en/en_001.txt"}
    ↓ rank_documents → sorted by cosine similarity
    ↓ display results with scores and text previews
```

**Spelling correction interaction:**

```
User types: "compter scence"
    ↓ "compter" not in index
    ↓ suggest: "comput"? (y/n): y
    ↓ "scence" not in index
    ↓ suggest: "scienc"? (y/n): y
    ↓ search for "comput scienc" → results
```
