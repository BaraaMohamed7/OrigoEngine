# OrigoEngine — Bilingual Search Engine

A bilingual (English + Arabic) search engine built from scratch with positional inverted indexing, proximity search, spelling correction, and TF-IDF cosine ranking.

## Prerequisites

- Python 3.10+ (uses `|` union type syntax)
- No external packages required — only Python standard library (`re`, `math`, `os`, `json`)

## Installation

```bash
git clone <repo-url>
cd OrigoEngine
```

No `pip install` needed. All dependencies are Python built-ins.

## Usage

### Interactive Search

```bash
python run.py
```

This starts an interactive REPL:

```
============================================================
  OrigoEngine — Bilingual Search Engine
============================================================
Loading existing index...
Indexed 20 documents | 947 unique terms

Commands:
  <query>       Search for terms (AND / proximity /k)
  eval          Run evaluation report
  rebuild       Rebuild index from corpus
  help          Show this message
  quit          Exit

OrigoEngine>
```

### Query Types

| Type | Syntax | Example |
|------|--------|---------|
| Boolean (AND) | `word1 word2 ...` | `machine learning` |
| Proximity | `word1 /k word2` | `machine /2 learning` |

### Example Queries

```
OrigoEngine> machine learning
OrigoEngine> computer /1 science
OrigoEngine> الذكاء الاصطناعي
OrigoEngine> renewable /3 energy
OrigoEngine> eval
OrigoEngine> quit
```

If a term is not found, the engine suggests a correction:

```
OrigoEngine> compter scence
  Term 'compter' not found. Did you mean: 'comput'? (y/n): y
  Term 'scence' not found. Did you mean: 'scienc'? (y/n): y
```

### Run Evaluation

Inside the REPL:

```
OrigoEngine> eval
```

### Rebuild Index

If you modify corpus documents:

```
OrigoEngine> rebuild
```

Or delete `data/index_data/` and relaunch — the engine will rebuild automatically.

## Project Structure

```
OrigoEngine/
├── run.py                       Entry point — run with: python run.py
├── data/
│   ├── corpus/
│   │   ├── en/en_001-010.txt    10 English documents
│   │   └── ar/ar_001-010.txt    10 Arabic documents
│   ├── stopwords/
│   │   ├── english_stopwords.txt
│   │   └── arabic_stopwords.txt
│   └── index_data/              Auto-generated (index.json, doc_store.json)
├── src/
│   ├── __init__.py
│   ├── language_detector.py     Detects Arabic vs English
│   ├── stemmer_en.py            Porter Stemmer (from scratch)
│   ├── stemmer_ar.py            ISRI Arabic Stemmer (from scratch)
│   ├── preprocessing.py         English + Arabic preprocessing pipelines
│   ├── indexer.py               Positional inverted index builder
│   ├── kgram_index.py           2-gram index for spelling correction
│   ├── query_engine.py          Boolean + proximity search
│   ├── spelling.py              Jaccard + Levenshtein spelling correction
│   ├── ranking.py               TF-IDF + cosine similarity
│   ├── evaluation.py            Precision & recall evaluation
│   └── main.py                  Interactive CLI REPL
├── IR_Project_Plan.md           Original project specification
├── BUILD_PLAN.md                Build plan (solo + team versions)
├── OVERVIEW.md                  Architecture & module documentation
└── EXPLANATION.md               Line-by-line code explanation
```

## What Each Module Does

| Module | What it does | Key function |
|--------|-------------|-------------|
| `language_detector.py` | Detects Arabic vs English text | `detect_language(text)` |
| `stemmer_en.py` | Reduces English words to stems | `porter_stem(word)` |
| `stemmer_ar.py` | Strips Arabic prefixes/suffixes | `isri_stem(word)` |
| `preprocessing.py` | Full pipeline: tokenize → stop → stem | `preprocess(text, lang)` |
| `indexer.py` | Builds positional inverted index | `build_index(corpus_path)` |
| `kgram_index.py` | Builds 2-gram index for spelling | `build_kgram_index(index)` |
| `query_engine.py` | Boolean AND & proximity /k search | `search(query, index)` |
| `spelling.py` | Suggests corrections for unknown terms | `suggest_correction(word, index, kgram_index)` |
| `ranking.py` | Ranks results by TF-IDF cosine | `rank_documents(terms, docs, ...)` |
| `evaluation.py` | Precision & recall metrics | `run_evaluation(index, doc_store)` |
| `main.py` | Interactive CLI | `python run.py` |

## Algorithms Implemented From Scratch

| Algorithm | File | What it does |
|----------|------|-------------|
| Porter Stemmer | `stemmer_en.py` | 5-step English suffix stripping |
| ISRI Stemmer | `stemmer_ar.py` | Arabic prefix/suffix removal |
| Positional Inverted Index | `indexer.py` | Term → {doc → [positions]} |
| K-gram Index | `kgram_index.py` | 2-gram → set of terms |
| Jaccard Similarity | `spelling.py` | Set intersection/union filtering |
| Levenshtein Distance | `spelling.py` | DP edit distance |
| TF-IDF Weighting | `ranking.py` | TF × IDF scoring |
| Cosine Similarity | `ranking.py` | Vector angle between query and doc |
| Boolean AND Search | `query_engine.py` | Posting list intersection |
| Proximity Search | `query_engine.py` | Position-based /k operator |
