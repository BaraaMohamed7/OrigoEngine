# Information Retrieval — Bilingual Search Engine
## Complete Project Plan

---

## Table of Contents
1. [Project Summary](#1-project-summary)
2. [Concepts You Must Understand](#2-concepts-you-must-understand)
3. [Architecture Overview](#3-architecture-overview)
4. [File & Folder Structure](#4-file--folder-structure)
5. [Phase 1 — Corpus Creation](#phase-1--corpus-creation)
6. [Phase 2 — Preprocessing Pipelines](#phase-2--preprocessing-pipelines)
7. [Phase 3 — Positional Inverted Index](#phase-3--positional-inverted-index)
8. [Phase 4 — Query Engine](#phase-4--query-engine)
9. [Phase 5 — Spelling Correction](#phase-5--spelling-correction)
10. [Phase 6 — Ranked Retrieval (TF-IDF + Cosine)](#phase-6--ranked-retrieval-tf-idf--cosine)
11. [Phase 7 — Evaluation](#phase-7--evaluation)
12. [Phase 8 — CLI Interface](#phase-8--cli-interface)
13. [Libraries Reference](#libraries-reference)
14. [What to Implement Yourself vs Use a Library](#what-to-implement-yourself-vs-use-a-library)

---

## 1. Project Summary

Build a **bilingual (English + Arabic) search engine** that:
- Preprocesses text through language-specific pipelines
- Builds a **Positional Inverted Index** from a 20-document corpus
- Supports **single-word, multi-word, and proximity queries**
- Provides **spelling correction** suggestions
- **Ranks results** using TF-IDF weighted Cosine Similarity
- Evaluates accuracy using **Precision & Recall**

### Removed Requirements (Confirmed)
- ~~Phrase Queries~~
- ~~Wildcard Queries (k-gram for wildcards)~~
- ~~Speed benchmarking~~

> k-gram index is still needed — for **spelling correction only**

---

## 2. Concepts You Must Understand

### 2.1 Tokenization
Splitting raw text into individual terms (tokens).
```
"Information Retrieval is fun" → ["Information", "Retrieval", "is", "fun"]
```
For Arabic you must handle right-to-left text and split on spaces/punctuation using regex.

---

### 2.2 Stop-word Removal
High-frequency words that carry no meaning for retrieval are filtered out.
- English: "the", "is", "a", "of", "and"
- Arabic: "في", "من", "على", "إلى", "هذا"

You use a pre-built list (from NLTK or a file) — no need to build it from scratch.

---

### 2.3 Stemming
Reducing a word to its root/base form so that variations match.

**English — Porter Stemmer (implement yourself):**
```
"running" → "run"
"studies" → "studi"
"information" → "inform"
```
The Porter Stemmer is a rule-based algorithm with 5 sequential steps (Step 1a, 1b, 1c, 2, 3, 4, 5a, 5b). Each step applies suffix-stripping rules based on the measure `m` (number of VC sequences in the stem).

Key concept: **measure m**
- VC = vowel-consonant sequence
- `m=0`: TR, EE, TREE
- `m=1`: TROUBLE, OAKS
- `m=2`: TROUBLES, PRIVATE

**Arabic — ISRI Stemmer (implement yourself or use NLTK's version):**
Handles Arabic-specific prefixes (وال، بال، كال) and suffixes (ات، ون، ين).
```
"الجامعات" → "جامع"
"يدرسون"  → "درس"
```

---

### 2.4 Arabic Normalization
Before stemming Arabic text, you must normalize it:

| Problem | Rule |
|---------|------|
| Alif forms: `أ إ آ` | Replace all with `ا` |
| Alif Maqsura: `ى` | Replace with `ي` |
| Ta Marbuta: `ة` | Replace with `ه` (optional) |
| Diacritics (Tashkeel): `َ ُ ِ ً ٌ ٍ ّ ْ` | Remove entirely |
| Tatweel: `ـ` | Remove entirely |

This is done with simple `str.replace()` and `re.sub()` — implement yourself.

---

### 2.5 Positional Inverted Index
The core data structure of your search engine.

**Structure:**
```python
{
  "term": {
    doc_id_1: [pos1, pos2, pos3],
    doc_id_2: [pos1, pos2],
  }
}
```

**Example:**
```
Doc 1: "the cat sat on the mat"
Doc 2: "the cat is fat"

Index:
{
  "cat": {1: [1], 2: [1]},
  "sat": {1: [2]},
  "mat": {1: [5]},
  "fat": {2: [3]}
}
```

**Why "Positional"?** Because storing positions lets you answer proximity queries like "find docs where 'cat' appears within 2 words of 'mat'."

**Building the index:**
```
For each document:
  For each token after preprocessing:
    record (term → doc_id → position)
```

---

### 2.6 Proximity Search (`/k` operator)
Query: `word1 /k word2`
Meaning: find documents where `word1` and `word2` appear within `k` words of each other.

**Algorithm:**
1. Get posting list for `word1`: positions in each doc
2. Get posting list for `word2`: positions in each doc
3. For docs that appear in **both** lists:
   - For every position `p1` of word1 and every position `p2` of word2:
   - If `|p1 - p2| <= k` → document qualifies

```python
def proximity_search(term1, term2, k, index):
    docs1 = index.get(term1, {})
    docs2 = index.get(term2, {})
    common_docs = set(docs1.keys()) & set(docs2.keys())
    results = []
    for doc in common_docs:
        for p1 in docs1[doc]:
            for p2 in docs2[doc]:
                if abs(p1 - p2) <= k:
                    results.append(doc)
                    break
    return results
```

---

### 2.7 K-gram Index (for Spelling Correction only)
A k-gram is a sequence of k consecutive characters.
For `k=2` (bigrams):
```
"hello" → ["$h", "he", "el", "ll", "lo", "o$"]
```
`$` = start/end marker.

You build an index: `{kgram → [terms that contain this kgram]}`

This is used to find **candidate corrections** for misspelled words.

---

### 2.8 Spelling Correction
When a query term is not in your index, you suggest corrections using two metrics:

**Step 1 — Jaccard Similarity (filter candidates)**
```
Jaccard(A, B) = |A ∩ B| / |A ∪ B|
```
Where A = kgrams of misspelled word, B = kgrams of candidate word.
Pick candidates with Jaccard > threshold (e.g., 0.3).

**Step 2 — Levenshtein Distance (rank candidates)**
Minimum edit distance between two strings (insert, delete, substitute).
```
edit("speling", "spelling") = 1  (insert 'l')
edit("korrect", "correct") = 1   (substitute 'k'→'c')
```

DP table approach — implement this yourself:
```
dp[i][j] = min edit distance between s1[:i] and s2[:j]
```

Pick the candidate with the **lowest edit distance** → "Did you mean: X?"

---

### 2.9 TF-IDF Weighting

**TF (Term Frequency):** How often does term `t` appear in document `d`?
```
tf(t, d) = count of t in d / total terms in d
```

**IDF (Inverse Document Frequency):** How rare is the term across all documents?
```
idf(t) = log(N / df(t))
```
Where `N` = total number of documents, `df(t)` = number of docs containing `t`.

**TF-IDF:**
```
tfidf(t, d) = tf(t, d) * idf(t)
```

Higher TF-IDF = term is frequent in this doc but rare overall → very relevant.

---

### 2.10 Cosine Similarity
Measures the angle between a query vector and a document vector.

```
cosine(Q, D) = (Q · D) / (|Q| * |D|)
```

**Process:**
1. Represent each document as a TF-IDF vector (one dimension per unique term)
2. Represent the query as a TF-IDF vector
3. Compute dot product divided by product of magnitudes
4. Sort documents by score descending

```
Q  = [0.5, 0.0, 0.3, 0.0]   ← query vector
D1 = [0.4, 0.1, 0.2, 0.0]   ← doc 1 vector
D2 = [0.0, 0.6, 0.0, 0.8]   ← doc 2 vector

cosine(Q, D1) = high  → D1 is relevant
cosine(Q, D2) = low   → D2 is not relevant
```

---

### 2.11 Precision & Recall

**Precision:** Of the documents you retrieved, how many are actually relevant?
```
Precision = |Retrieved ∩ Relevant| / |Retrieved|
```

**Recall:** Of all relevant documents, how many did you retrieve?
```
Recall = |Retrieved ∩ Relevant| / |Relevant|
```

**How to evaluate:**
1. Pick 3-5 test queries
2. Manually define the "ground truth" (which docs should appear for this query)
3. Run your engine → get retrieved docs
4. Calculate precision & recall

> You define the ground truth yourself since you control the corpus — make it reasonable.

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Language   │
                    │  Detector   │  ← detect Arabic vs English
                    └──────┬──────┘
           ┌───────────────┴───────────────┐
           ▼                               ▼
   ┌───────────────┐               ┌───────────────┐
   │ English Pipeline│             │ Arabic Pipeline│
   │ Tokenize       │             │ Normalize       │
   │ Remove Stops   │             │ Remove Stops    │
   │ Porter Stem    │             │ ISRI Stem       │
   └───────┬───────┘             └───────┬─────────┘
           └───────────────┬─────────────┘
                           │
                  ┌────────▼────────┐
                  │  Query Parser   │
                  │                 │
                  │ single/multi?   │
                  │ proximity /k?   │
                  │ term in index?  │
                  └────────┬────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──┐  ┌──────▼──┐  ┌─────▼──────┐
       │ Boolean │  │Proximity│  │  Spelling  │
       │ Search  │  │ Search  │  │ Correction │
       └──────┬──┘  └──────┬──┘  └─────┬──────┘
              └────────────┴────────────┘
                           │
                  ┌────────▼────────┐
                  │   TF-IDF +      │
                  │ Cosine Ranking  │
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │  Ranked Results │
                  │  Displayed      │
                  └─────────────────┘
```

---

## 4. File & Folder Structure

```
ir_project/
│
├── corpus/
│   ├── en/
│   │   ├── doc01.txt
│   │   ├── doc02.txt
│   │   └── ... (doc10.txt)
│   └── ar/
│       ├── doc01.txt
│       ├── doc02.txt
│       └── ... (doc10.txt)
│
├── stopwords/
│   ├── english_stopwords.txt     ← from NLTK (allowed)
│   └── arabic_stopwords.txt      ← from NLTK or manual list (allowed)
│
├── preprocessing.py    ← English & Arabic pipelines
├── stemmer_en.py       ← Porter Stemmer (implement yourself)
├── stemmer_ar.py       ← ISRI Stemmer (implement yourself)
├── indexer.py          ← Positional Inverted Index builder
├── kgram_index.py      ← K-gram index for spelling correction
├── query_engine.py     ← Single/multi-word + proximity queries
├── spelling.py         ← Levenshtein + Jaccard spelling correction
├── ranking.py          ← TF-IDF + Cosine Similarity
├── evaluation.py       ← Precision & Recall calculator
├── language_detector.py← Simple language detection (Arabic chars?)
└── main.py             ← CLI entry point
```

---

## Phase 1 — Corpus Creation

### Goal
Create 20 text files (~50 words each): 10 English, 10 Arabic.

### Guidelines
- Pick a **consistent theme** per language (makes evaluation easier)
- Good English topics: technology, sports, history, science, nature
- Good Arabic topics: similar themes in Arabic
- Each file = one text paragraph, plain `.txt`, UTF-8 encoded

### Ground Truth Preparation
After writing documents, create a simple reference table:

| Query | Expected Doc IDs |
|-------|-----------------|
| `"computer science"` | en/doc01, en/doc03 |
| `"machine /2 learning"` | en/doc05 |
| `"الذكاء الاصطناعي"` | ar/doc02, ar/doc07 |

You'll use this table in Phase 7 for evaluation.

### Output
- `corpus/en/doc01.txt` ... `doc10.txt`
- `corpus/ar/doc01.txt` ... `doc10.txt`
- A reference table (can be in a `.json` or just in `evaluation.py`)

---

## Phase 2 — Preprocessing Pipelines

### Goal
Transform raw text into clean, stemmed tokens.

### 2A — Language Detector (`language_detector.py`)
Simple rule: if the text contains Arabic Unicode characters (`\u0600`–`\u06FF`) → Arabic, else → English.

```python
import re

def detect_language(text: str) -> str:
    if re.search(r'[\u0600-\u06FF]', text):
        return 'arabic'
    return 'english'
```

### 2B — English Pipeline (`preprocessing.py`)

```
raw text
   → lowercase
   → tokenize (split on non-alpha: re.findall(r'[a-zA-Z]+', text))
   → remove stopwords
   → Porter stem each token
   → return list of (token, original_position)
```

### 2C — Arabic Normalization (`preprocessing.py`)
Implement these rules yourself with `str.replace()` and `re.sub()`:

```python
def normalize_arabic(text: str) -> str:
    # Remove diacritics (tashkeel)
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
    # Remove tatweel
    text = text.replace('\u0640', '')
    # Normalize alif forms
    text = re.sub(r'[إأآ]', 'ا', text)
    # Normalize alif maqsura
    text = text.replace('ى', 'ي')
    # Normalize ta marbuta
    text = text.replace('ة', 'ه')
    return text
```

### 2D — Arabic Pipeline (`preprocessing.py`)

```
raw arabic text
   → normalize
   → tokenize (split on non-Arabic chars)
   → remove Arabic stopwords
   → ISRI stem each token
   → return list of (token, original_position)
```

### Key Concept
The pipeline must return **positions** alongside tokens. Position = index of the token in the original token list (before stop-word removal — keep original positions).

### Output
```python
preprocess("Information retrieval is great", lang='english')
# → [("inform", 0), ("retriev", 1), ("great", 3)]
#     term         original_position (2 was "is" = stopword, but position counts)
```

---

## Phase 3 — Positional Inverted Index

### Goal
Build the main index from all documents.

### Data Structure
```python
index = {
    "term": {
        "en/doc01": [0, 5, 12],
        "en/doc03": [2, 8],
    }
}
```

### Building Process (`indexer.py`)

```python
def build_index(corpus_path: str) -> dict:
    index = {}
    for doc_path in get_all_docs(corpus_path):
        doc_id = get_doc_id(doc_path)   # e.g. "en/doc01"
        text = read_file(doc_path)
        lang = detect_language(text)
        tokens_with_positions = preprocess(text, lang)

        for term, position in tokens_with_positions:
            if term not in index:
                index[term] = {}
            if doc_id not in index[term]:
                index[term][doc_id] = []
            index[term][doc_id].append(position)

    return index
```

### Also build a Document Store
Store raw term counts per document (needed for TF-IDF):

```python
doc_store = {
    "en/doc01": {"total_terms": 45, "raw_text": "...", "language": "english"},
    "ar/doc01": {"total_terms": 48, "raw_text": "...", "language": "arabic"},
}
```

### Output
- `index` dict (can optionally save to JSON for debugging)
- `doc_store` dict

---

## Phase 4 — Query Engine

### Goal
Parse and execute user queries against the index.

### Query Types to Support

#### Type 1 — Single/Multi-word Query
Input: `"machine learning"`
Process:
1. Preprocess query → `["machin", "learn"]`
2. For each term → get posting list from index
3. Return **intersection** of doc sets (AND logic) OR **union** (OR logic — your choice, document it)

```python
def boolean_search(terms: list, index: dict) -> set:
    if not terms:
        return set()
    result = set(index.get(terms[0], {}).keys())
    for term in terms[1:]:
        result &= set(index.get(term, {}).keys())  # AND
    return result
```

#### Type 2 — Proximity Query
Input: `"machine /2 learning"`
Parse: detect `/k` pattern using regex → extract `term1`, `k`, `term2`

```python
import re

def parse_query(query: str):
    proximity_pattern = r'(\w+)\s*/(\d+)\s*(\w+)'
    match = re.search(proximity_pattern, query)
    if match:
        term1, k, term2 = match.group(1), int(match.group(2)), match.group(3)
        return ("proximity", term1, k, term2)
    else:
        return ("boolean", query.split())
```

Then implement proximity logic as described in Section 2.6.

### Output
A function `search(query, index) → list of doc_ids`

---

## Phase 5 — Spelling Correction

### Goal
If a query term doesn't exist in the index → suggest the closest real term.

### K-gram Index (`kgram_index.py`)
Build alongside the main index:

```python
def get_kgrams(term: str, k: int = 2) -> list:
    padded = f"${term}$"
    return [padded[i:i+k] for i in range(len(padded) - k + 1)]

def build_kgram_index(index: dict, k: int = 2) -> dict:
    kgram_index = {}
    for term in index.keys():
        for kgram in get_kgrams(term, k):
            if kgram not in kgram_index:
                kgram_index[kgram] = set()
            kgram_index[kgram].add(term)
    return kgram_index
```

### Jaccard Similarity (`spelling.py`)

```python
def jaccard(kgrams_a: set, kgrams_b: set) -> float:
    intersection = len(kgrams_a & kgrams_b)
    union = len(kgrams_a | kgrams_b)
    return intersection / union if union > 0 else 0.0
```

### Levenshtein Distance (`spelling.py`)
Implement yourself using DP:

```python
def levenshtein(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])

    return dp[m][n]
```

### Full Correction Flow (`spelling.py`)

```python
def suggest_correction(misspelled: str, index: dict, kgram_index: dict, k: int = 2):
    if misspelled in index:
        return None  # no correction needed

    query_kgrams = set(get_kgrams(misspelled, k))
    candidates = set()

    for kgram in query_kgrams:
        candidates |= kgram_index.get(kgram, set())

    # Filter by Jaccard
    filtered = [
        c for c in candidates
        if jaccard(query_kgrams, set(get_kgrams(c, k))) >= 0.3
    ]

    # Rank by Levenshtein
    ranked = sorted(filtered, key=lambda c: levenshtein(misspelled, c))

    return ranked[0] if ranked else None
```

---

## Phase 6 — Ranked Retrieval (TF-IDF + Cosine)

### Goal
Given a set of candidate documents from Phase 4, rank them by relevance.

### TF-IDF Calculation (`ranking.py`)
Implement the formulas manually:

```python
import math

def compute_tf(term: str, doc_id: str, index: dict, doc_store: dict) -> float:
    count = len(index.get(term, {}).get(doc_id, []))
    total_terms = doc_store[doc_id]["total_terms"]
    return count / total_terms if total_terms > 0 else 0.0

def compute_idf(term: str, index: dict, total_docs: int) -> float:
    df = len(index.get(term, {}))  # number of docs containing term
    return math.log(total_docs / df) if df > 0 else 0.0

def compute_tfidf(term: str, doc_id: str, index: dict, doc_store: dict, total_docs: int) -> float:
    return compute_tf(term, doc_id, index, doc_store) * compute_idf(term, index, total_docs)
```

### Cosine Similarity (`ranking.py`)

```python
def cosine_similarity(query_vector: dict, doc_vector: dict) -> float:
    dot_product = sum(query_vector.get(t, 0) * doc_vector.get(t, 0) for t in query_vector)

    query_magnitude = math.sqrt(sum(v**2 for v in query_vector.values()))
    doc_magnitude = math.sqrt(sum(v**2 for v in doc_vector.values()))

    if query_magnitude == 0 or doc_magnitude == 0:
        return 0.0
    return dot_product / (query_magnitude * doc_magnitude)
```

### Full Ranking Flow

```python
def rank_documents(query_terms: list, candidate_docs: set, index, doc_store, total_docs):
    # Build query vector (treat each query term as tf=1)
    query_vector = {
        term: compute_idf(term, index, total_docs)
        for term in query_terms
    }

    scores = {}
    for doc_id in candidate_docs:
        doc_vector = {
            term: compute_tfidf(term, doc_id, index, doc_store, total_docs)
            for term in query_terms
        }
        scores[doc_id] = cosine_similarity(query_vector, doc_vector)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

---

## Phase 7 — Evaluation

### Goal
Calculate Precision and Recall for 3-5 test queries.

### Setup (`evaluation.py`)

Define ground truth manually:
```python
GROUND_TRUTH = {
    "computer science": {"en/doc01", "en/doc03", "en/doc07"},
    "machine /2 learning": {"en/doc05", "en/doc08"},
    "الذكاء الاصطناعي": {"ar/doc02", "ar/doc07"},
    "sports championship": {"en/doc04"},
    "تقنية المعلومات": {"ar/doc01", "ar/doc03", "ar/doc05"},
}
```

### Calculation

```python
def evaluate(query: str, retrieved: set, ground_truth: set):
    relevant_retrieved = retrieved & ground_truth

    precision = len(relevant_retrieved) / len(retrieved) if retrieved else 0.0
    recall = len(relevant_retrieved) / len(ground_truth) if ground_truth else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "relevant_retrieved": len(relevant_retrieved),
        "total_retrieved": len(retrieved),
        "total_relevant": len(ground_truth),
    }
```

### Report Table (include in documentation)

| Query | Precision | Recall | Retrieved | Relevant Retrieved |
|-------|-----------|--------|-----------|-------------------|
| `computer science` | 0.67 | 1.0 | 3 | 3 |
| `machine /2 learning` | 1.0 | 0.5 | 1 | 1 |
| `الذكاء الاصطناعي` | 1.0 | 1.0 | 2 | 2 |
| `sports championship` | 1.0 | 1.0 | 1 | 1 |
| `تقنية المعلومات` | 0.67 | 0.67 | 3 | 2 |

*(these are example numbers — yours will vary)*

---

## Phase 8 — CLI Interface

### Goal
A simple command-line interface that ties everything together.

### `main.py` Sample Interaction

```
Welcome to Bilingual Search Engine
===================================
Enter query (or 'quit' to exit): machine /2 learning

[Proximity Search] machine /2 learning
Preprocessing query... [EN]

Results (ranked by TF-IDF Cosine Similarity):
----------------------------------------------
1. en/doc05  | Score: 0.8234
2. en/doc08  | Score: 0.6120

Enter query: speling correction
Term 'speling' not found. Did you mean: "spelling"? (y/n): y

[Boolean Search] spelling correction
...
```

### Flow in `main.py`

```
1. Load corpus → build index, kgram_index, doc_store
2. Loop:
   a. Read query from user
   b. Detect language
   c. Parse query type (proximity or boolean)
   d. Preprocess query terms
   e. Check each term in index → spelling correction if missing
   f. Execute search → get candidate docs
   g. Rank candidates with TF-IDF cosine
   h. Display ranked results
```

---

## Libraries Reference

| Library | What to use it for | Write yourself |
|---------|-------------------|----------------|
| `re` | Regex tokenization, normalization | N/A |
| `math` | `log()`, `sqrt()` for TF-IDF/cosine | N/A |
| `nltk.corpus.stopwords` | English & Arabic stop-word lists | allowed (just data) |
| `os`, `pathlib` | File traversal | N/A |
| `json` | Save/load index for debugging | N/A |

**Do NOT use:**
- `nltk.stem.PorterStemmer` → implement yourself
- `nltk.stem.ISRIStemmer` → implement yourself (or justify usage)
- `sklearn` anything → no TF-IDF or cosine from sklearn
- `whoosh`, `elasticsearch` → obviously not

---

## What to Implement Yourself vs Use a Library

| Component | Implement Yourself | Use Library |
|-----------|-------------------|-------------|
| Porter Stemmer | YES | NO |
| ISRI Stemmer | YES | Only if justified |
| Arabic Normalization | YES | NO |
| Stop-word lists | NO (just data) | YES — NLTK |
| Positional Inverted Index | YES | NO |
| K-gram Index | YES | NO |
| Levenshtein Distance | YES | NO |
| Jaccard Similarity | YES | NO |
| TF-IDF formula | YES | NO |
| Cosine Similarity | YES | NO |
| Precision & Recall | YES | NO |
| Tokenization (regex) | YES | NO |
| File I/O | NO | YES — os/pathlib |

**Estimated library usage: ~10-15% of total codebase**

---

## Quick Reference — Key Formulas

```
TF(t, d)      = count(t in d) / total_terms(d)
IDF(t)        = log(N / df(t))
TF-IDF(t, d)  = TF(t, d) × IDF(t)

Cosine(Q, D)  = Σ(q_i × d_i) / (|Q| × |D|)

Jaccard(A, B) = |A ∩ B| / |A ∪ B|

Precision     = |Retrieved ∩ Relevant| / |Retrieved|
Recall        = |Retrieved ∩ Relevant| / |Relevant|

Proximity     = |pos1 - pos2| ≤ k
```
