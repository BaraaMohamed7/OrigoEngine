# OrigoEngine — Line-by-Line Code Explanation

---

## `language_detector.py`

```
Line 1:  import re                          ← import regex module
Line 4:  def detect_language(text: str) → str:
Line 5:      if not text or not text.strip(): ← if empty string or only whitespace
Line 6:          return "english"             ← default to english (safe fallback)
Line 7:      if re.search(r"[\u0600-\u06FF]", text):
                                             ← search for ANY character in the Arabic Unicode block
                                             ← U+0600 to U+06FF covers Arabic letters, diacritics, punctuation
Line 8:          return "arabic"             ← found Arabic character → it's Arabic text
Line 9:      return "english"                ← no Arabic characters found → treat as English
```

**Key insight:** This is intentionally simple. A single Arabic character anywhere in the text makes the whole text "Arabic." This works well because our corpus documents are purely one language. For mixed-language queries, the Arabic pipeline handles it since Arabic characters would still be present.

---

## `stemmer_en.py` — Porter Stemmer

### Helper functions

```
Line 1:  def _is_consonant(word: str, i: int) → bool:
Line 2:      ch = word[i]                     ← get character at position i
Line 3:      if ch in "aeiou":                ← vowels are clearly not consonants
Line 4:          return False
Line 5:      if ch == "y":                    ← 'y' is special — it's a consonant OR vowel
Line 6:          if i == 0:                    ← if it's the first letter of the word
Line 7:              return True               ← at position 0, 'y' is always a consonant (e.g. "yes")
Line 8:          return not _is_consonant(word, i - 1)
                                             ← otherwise, 'y' is consonant if the character BEFORE it is a vowel
                                             ← "happy" → h(V) a(C) p(C) y(?) → y follows consonant p, so y is vowel
                                             ← "yes"  → y is first letter → consonant
Line 9:      return True                      ← everything else (b,c,d,f,g,h,...) is a consonant
```

```
Line 12: def _measure(word: str) → int:
                                             ← The "measure" m counts VC (vowel-consonant) sequences
Line 13:     n = len(word)
Line 14:     if n == 0:                      ← empty word has measure 0
Line 15:         return 0
Line 16:     i = 0                           ← pointer walking through the word
Line 17:     m = 0                           ← VC counter
Line 18:     while i < n and _is_consonant(word, i):
Line 19:         i += 1                       ← skip leading consonants (e.g. "TR" in "TROUBLE")
                                             ← this puts us at the first vowel
Line 20:     while i < n:                    ← now we're in the alternating V/C region
Line 21:         while i < n and not _is_consonant(word, i):
Line 22:             i += 1                  ← skip through vowels (a V block)
Line 23:         if i >= n:
Line 24:             break                   ← no consonant after this vowel block → stop
Line 25:         m += 1                       ← we found a V followed by a C → that's one VC unit
Line 26:         while i < n and _is_consonant(word, i):
Line 27:             i += 1                  ← skip through consonants (a C block)
                                             ← loop back to find next V block
Line 28:     return m                        ← total VC count = measure
                                             ← e.g. TREE → m=0, TROUBLE → m=1, TROUBLES → m=2
```

```
Line 31: def _has_vowel(word: str) → bool:
Line 32:     for i in range(len(word)):       ← check every character position
Line 33:         if not _is_consonant(word, i): ← if it's NOT a consonant → it's a vowel
Line 34:             return True               ← found at least one vowel
Line 35:     return False                      ← no vowels at all
```

```
Line 38: def _ends_double_consonant(word: str) → bool:
Line 39:     if len(word) < 2:                ← need at least 2 chars to have a double
Line 40:         return False
Line 41:     return word[-1] == word[-2] and _is_consonant(word, len(word) - 1)
                                             ← two conditions: last two chars are the SAME letter,
                                             ← AND it's a consonant (not "oo", "ee" which are vowels)
                                             ← e.g. "hopping" ends in double consonant "pp"
```

```
Line 44: def _cvc(word: str) → bool:
                                             ← Checks if word ends consonant-vowel-consonant
                                             ← and the last consonant is not w, x, or y
Line 45:     n = len(word)
Line 46:     if n < 3:                        ← can't have CVC with fewer than 3 chars
Line 47:         return False
Line 48:     if not _is_consonant(word, n - 1): ← last char must be consonant
Line 49:         return False
Line 50:     if _is_consonant(word, n - 2):    ← second-to-last must be vowel (NOT consonant)
Line 51:         return False
Line 52:     if not _is_consonant(word, n - 3): ← third-to-last must be consonant
Line 53:         return False
Line 54:     if word[-1] in "wxy":             ← the final consonant can't be w/x/y (special cases)
Line 55:         return False
Line 56:     return True                       ← all checks passed → ends in CVC pattern
```

```
Line 59: def _replace_suffix(word, suffix, replacement) → str:
Line 60:     if not word.endswith(suffix):
Line 61:         return word                    ← no match → return unchanged
Line 62:     return word[:-len(suffix)] + replacement
                                              ← strip suffix, append replacement
                                              ← e.g. _replace_suffix("running", "ning", "n") → "run" + "n" → "runn"? No...
                                              ← actually used like: _replace_suffix("sses", "sses", "ss") → "ss"
```

```
Line 65: def _strip_suffix(word, suffix) → str:
Line 66:     if not word.endswith(suffix):
Line 67:         return word                    ← no match → unchanged
Line 68:     return word[:-len(suffix)]        ← just remove the suffix, no replacement
                                              ← e.g. _strip_suffix("runs", "s") → "run"
```

### Main function: `porter_stem`

```
Line 71: def porter_stem(word: str) → str:
Line 72:     if len(word) <= 2:
Line 73:         return word                    ← words of 0-2 chars can't be stemmed further
Line 74:
Line 75:     word = word.lower()                ← Porter stemmer works on lowercase only
```

#### Apostrophe handling
```
Line 77:     if word.endswith("'s'"):           ← possessive like "king's'"
Line 78:         word = word[:-3]
Line 79:     elif word.endswith("'s"):          ← possessive like "king's"
Line 80:         word = word[:-2]
Line 81:     elif word.endswith("'"):            ← trailing apostrophe
Line 82:         word = word[:-1]
Line 84:     word = word.replace("y'", "y")    ← handle leftover y'
```

#### Step 1a — Remove plurals and possessive s
```
Line 87:     if word.endswith("sses"):          ← "sses" → "ss"  (e.g. "stresses" → "stress")
Line 88:         word = _replace_suffix(word, "sses", "ss")
Line 89:     elif word.endswith("ies"):        ← "ies" → "i"    (e.g. "ponies" → "poni")
Line 90:         word = _replace_suffix(word, "ies", "i")
Line 91:     elif word.endswith("ss"):          ← "ss" → keep as-is (e.g. "stress" stays "stress")
Line 92:         pass
Line 93:     elif word.endswith("s"):           ← "s" → remove    (e.g. "cats" → "cat")
Line 94:         word = _strip_suffix(word, "s")
```

#### Step 1b — Remove -eed, -ed, -ing
```
Line 97:     m = _measure                       ← alias for readability
Line 98:     step1b_extra = False              ← flag: do we need the extra 1b adjustments?
Line 99:     if word.endswith("eed"):           ← "eed" → "ee" IF stem measure > 0
Line 100:        stem = word[:-3]              ←   e.g. "agreed" → stem "agr" has m=1 → "agree"
Line 101:        if m(stem) > 0:               ←   but "feed" → stem "f" has m=0 → stays "feed"
Line 102:            word = _replace_suffix(word, "eed", "ee")
Line 103:    elif word.endswith("ed"):         ← "ed" → remove IF stem has a vowel
Line 104:        stem = word[:-2]              ←   e.g. "running" won't match here (it's "ing")
Line 105:        if _has_vowel(stem):          ←   e.g. "walked" → stem "walk" has vowel 'a'
Line 106:            word = stem                ←   remove "ed"
Line 107:            step1b_extra = True        ←   flag that we did this — may need extra fix
Line 108:    elif word.endswith("ed"):          ← duplicate condition (no-op, defensive)
Line 109:        pass
Line 110:    elif word.endswith("ing"):        ← "ing" → remove IF stem has a vowel
Line 111:        stem = word[:-3]              ←   e.g. "running" → stem "runn" has vowel 'u'
Line 112:        if _has_vowel(stem):
Line 113:            word = stem                ←   remove "ing" → "runn"
Line 114:            step1b_extra = True
```

#### Step 1b extra — Fix-up after removing -ed/-ing
```
Line 116:    if step1b_extra:                  ← only runs if we stripped ed/ing
Line 117:        if word.endswith("at") or word.endswith("bl") or word.endswith("iz"):
Line 118:            word = word + "e"           ← "bloated" → "bloat" → "bloate" → needs 'e' back → "blocate"? No...
                                              ←   actually: "bating" → "bat" ends in "at" → "bate"
                                              ←   prevents words like "bat" that should be "bate"
Line 119:        elif _ends_double_consonant(word) and word[-1] not in "lsz":
Line 120:            word = word[:-1]            ←   e.g. "running" → "runn" → double consonant 'nn' → strip one → "run"
                                              ←   but "falling" → "fall" → double 'll' is in "lsz" → keep "fall"
Line 121:        elif m(word) == 1 and _cvc(word):
Line 122:            word = word + "e"           ←   short words with CVC ending need an 'e'
                                              ←   e.g. "hop" (m=1, CVC) → "hope" for correct eventual stemming
```

#### Step 1c — Turn trailing y → i
```
Line 125:    if word.endswith("y"):
Line 126:        stem = word[:-1]               ←   e.g. "happy" → stem = "happ"
Line 127:        if _has_vowel(stem):           ←   only if stem has a vowel (prevents "sky" → "ski")
Line 128:            word = stem + "i"          ←   "happy" → "happi"
```

#### Step 2 — Remove derivational suffixes (m > 0)
```
Line 131:    step2_map = {                     ← each suffix → replacement
Line 132:        "ational": "ate",             ← e.g. "relational" → "relate" (stem m≥1)
Line 133:        "tional": "tion",             ← e.g. "conditional" → "condition"
Line 134:        "enci": "ence",               ← e.g. "excellenci" → "excellence"? Actually "-dependenci" → "depend" ...
Line 135:        "anci": "ance",
Line 136:        "izer": "ize",
Line 137:        "abli": "able",               ← some implementations use "ably" → "able"
Line 138:        "alli": "al",                 ← e.g. "strictalli" → "strictal"
Line 139:        "entli": "ent",
Line 140:        "eli": "e",                   ← e.g. "happili" → "happile" ... → "e"
Line 141:        "ousli": "ous",
Line 142:        "ization": "ize",              ← e.g. "organization" → "organize"
Line 143:        "ation": "ate",                ← e.g. "information" → "informate"
Line 144:        "ator": "ate",
Line 145:        "alism": "al",
Line 146:        "iveness": "ive",
Line 147:        "fulness": "ful",
Line 148:        "ousness": "ous",
Line 149:        "aliti": "al",
Line 150:        "iviti": "ive",
Line 151:        "biliti": "ble",               ← e.g. "possibiliti" → "possible"
Line 152:    }
Line 153:    for suffix, replacement in step2_map.items():
Line 154:        if word.endswith(suffix):        ← does the word end with this suffix?
Line 155:            stem = word[:-len(suffix)]  ← get the stem (word minus suffix)
Line 156:            if m(stem) > 0:             ← only replace if stem's measure > 0
Line 157:                word = stem + replacement ← apply the replacement
Line 158:            break                       ← only one suffix can match, so stop after first
```

#### Step 3 — More suffix removal (m > 0)
```
Line 161:    step3_map = {
Line 162:        "icate": "ic",                 ← e.g. "replicate" → "replicic"? After step 2...
Line 163:        "ative": "",                   ← e.g. "formativet" → "form"
Line 164:        "alize": "al",
Line 165:        "iciti": "ic",
Line 166:        "ical": "ic",
Line 167:        "ful": "",
Line 168:        "ness": "",                    ← e.g. "happiness" → "happiless" → ... eventually "happi"
Line 169:    }
Line 170:    for suffix, replacement in step3_map.items():
Line 171:        if word.endswith(suffix):
Line 172:            stem = word[:-len(suffix)]
Line 173:            if m(stem) > 0:
Line 174:                word = stem + replacement
Line 175:            break
```

#### Step 4 — Strip common suffixes (m > 1, stricter)
```
Line 178:    step4_suffixes = [                 ← ordered list of suffixes to try removing
Line 179:        "al", "ance", "ence", "er", "ic", "able", "ible",
Line 180:        "ant", "ement", "ment", "ent", "ion", "ou", "ism",
Line 181:        "ate", "iti", "ous", "ive", "ize",
Line 182:    ]
Line 199:    for suffix in step4_suffixes:
Line 200:        if word.endswith(suffix):
Line 201:            stem = word[:-len(suffix)]
Line 202:            if suffix == "ion":          ← special case: "ion" only removed if stem ends in s/t
Line 203:                if m(stem) > 1 and len(stem) > 0 and stem[-1] in "st":
Line 204:                    word = stem           ← e.g. "adoption" → adopt (m>1, ends in 't')
Line 205:            else:
Line 206:                if m(stem) > 1:           ← all other suffixes require m>1
Line 207:                    word = stem
Line 208:            break
```

#### Step 5a — Remove trailing e
```
Line 211:    if word.endswith("e"):
Line 212:        stem = word[:-1]
Line 213:        if m(stem) > 1:                  ← if stem is long enough, remove 'e'
Line 214:            word = stem                    ← e.g. "probate" → "probat"
Line 215:        elif m(stem) == 1 and not _cvc(stem):
Line 216:            word = stem                  ← remove e if stem has m=1 but doesn't end CVC
```

#### Step 5b — Remove double ll
```
Line 219:    if _ends_double_consonant(word) and word[-1] == "l" and m(word) > 1:
Line 220:        word = word[:-1]               ← e.g. "controll" → "control"
Line 221:
Line 222:    return word                          ← final stemmed result
```

---

## `stemmer_ar.py` — ISRI Arabic Stemmer

### Configuration lists

```
Line 4:  ARABIC_PREFIX_PATTERNS = [...]          ← regex patterns for Arabic prefixes
                                              ← Each pattern matches the START of a word (anchored by ^)
                                              ← "r"^ال"" means: if word starts with ال, remove it
                                              ← ordered from longest to shortest prefix? Not exactly —
                                              ← the function tries them in order and returns on FIRST match

Line 29: ARABIC_SUFFIX_PATTERNS = [...]          ← regex patterns for Arabic suffixes
                                              ← Each pattern matches the END of a word (anchored by $)
                                              ← "r"ة$"" means: if word ends with ة, remove it
```

### Prefix/suffix removal

```
Line 49: def _remove_prefix(word: str) → str:
Line 50:     for pattern in ARABIC_PREFIX_PATTERNS:
Line 51:         new_word = re.sub(pattern, "", word)   ← try removing this prefix
Line 52:         if len(new_word) >= 2 and new_word != word:  ← only accept if result ≥ 2 chars
Line 53:             return new_word                      ← and something actually changed
Line 54:     return word                                 ← no prefix matched → return original
                                              ← NOTE: returns on FIRST matching prefix
                                              ← So ordering matters: "وال" before "ال" ensures
                                              ← we strip the longer prefix first
```

```
Line 57: def _remove_suffix(word: str) → str:
Line 58:     for pattern in ARABIC_SUFFIX_PATTERNS:    ← same logic as prefix removal
Line 59:         new_word = re.sub(pattern, "", word)  ← try removing this suffix
Line 60:         if len(new_word) >= 2 and new_word != word:  ← accept if result ≥ 2 chars
Line 61:             return new_word
Line 62:     return word
```

### Main function: `isri_stem`

```
Line 65: def isri_stem(word: str) → str:
Line 66:     if len(word) <= 2:               ← too short to stem
Line 67:         return word
Line 68:
Line 69:     word = _remove_prefix(word)       ← Pass 1: remove prefix (e.g. الكتابة → كتابة)
Line 70:     if len(word) <= 2:               ← did we strip too much? if yes, stop
Line 71:         return word
Line 72:
Line 73:     word = _remove_suffix(word)       ← Pass 1: remove suffix (e.g. كتابة → كتاب)
Line 74:     if len(word) <= 2:
Line 75:         return word
Line 76:
Line 77:     word = _remove_prefix(word)       ← Pass 2: try prefix again after suffix removal
                                              ←   sometimes suffix removal reveals another prefix
Line 78:     if len(word) <= 2:
Line 79:         return word
Line 80:
Line 81:     word = _remove_suffix(word)       ← Pass 2: try suffix again
Line 82:     if len(word) <= 2:
Line 83:         return word
Line 84:
Line 85:     return word                        ← what's left is the stem
```

**Why two passes?** Consider `والجامعات`:
- Pass 1 prefix: remove `وال` → `جامعات`
- Pass 1 suffix: remove `ات` → `جامع`
- Second pass catches cases where the first pass only partially strips

---

## `preprocessing.py` — Pipeline Orchestrator

### Imports and configuration

```
Line 1:  import re                               ← regex for tokenization and normalization
Line 2:  import os                               ← file path handling for stopwords
Line 4:  from language_detector import detect_language  ← detect Arabic vs English
Line 5:  from stemmer_en import porter_stem     ← English stemmer
Line 6:  from stemmer_ar import isri_stem        ← Arabic stemmer
Line 8:  STOPWORDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stopwords")
                                              ← path to the stopwords/ directory
                                              ← uses __file__ so it works regardless of cwd
Line 10: _ENGLISH_STOPWORDS: set | None = None  ← cached stopwords (starts as None)
Line 11: _ARABIC_STOPWORDS: set | None = None   ← cached stopwords (starts as None)
```

### Stopword loading (singleton pattern)

```
Line 14: def _load_stopwords(filename: str) → set:
Line 15:     filepath = os.path.join(STOPWORDS_DIR, filename)  ← build full path
Line 16:     with open(filepath, "r", encoding="utf-8") as f:  ← open with UTF-8 (important for Arabic)
Line 17:         return {line.strip() for line in f if line.strip()}
                                              ← read file, strip whitespace, skip blank lines
                                              ← returns a set for O(1) lookup during preprocessing
```

```
Line 20: def get_english_stopwords() → set:
Line 21:     global _ENGLISH_STOPWORDS          ← refer to module-level variable
Line 22:     if _ENGLISH_STOPWORDS is None:     ← first call? load from file
Line 23:         _ENGLISH_STOPWORDS = _load_stopwords("english_stopwords.txt")
Line 24:     return _ENGLISH_STOPWORDS           ← subsequent calls: return cached set
                                              ← This is called "lazy loading" or "singleton pattern"
```

```
Line 27: def get_arabic_stopwords() → set:     ← same pattern as English
Line 28:     global _ARABIC_STOPWORDS
Line 29:     if _ARABIC_STOPWORDS is None:
Line 30:         _ARABIC_STOPWORDS = _load_stopwords("arabic_stopwords.txt")
Line 31:     return _ARABIC_STOPWORDS
```

### Arabic normalization

```
Line 34: def normalize_arabic(text: str) → str:
Line 35:     text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
                                              ← remove Arabic diacritics (tashkeel)
                                              ← U+064B–U+065F: fathatan, dammatan, kasratan,
                                              ←   fatha, damma, kasra, shadda, sukun
                                              ← U+0670: superscript alif
Line 36:     text = text.replace("\u0640", "")  ← remove tatweel (kashida) — elongation character
Line 37:     text = re.sub(r"[إأآ]", "ا", text)  ← unify alif variants → plain alif
                                              ←   إ (hamza below) → ا
                                              ←   أ (hamza above) → ا
                                              ←   آ (madda) → ا
Line 38:     text = text.replace("ى", "ي")     ← alif maqsura → ya
                                              ←   ى looks like alif but is actually a ya variant
Line 39:     text = text.replace("ة", "ه")     ← ta marbuta → ha
                                              ←   ة at word end → ه so "الكتابة" and "الكتابه" match
Line 40:     return text
```

### Tokenizers

```
Line 43: def tokenize_english(text: str) → list[str]:
Line 44:     return re.findall(r"[a-zA-Z]+", text)
                                              ← extract all sequences of English letters
                                              ← ignores numbers, punctuation, spaces
                                              ← "Hello, world! 123" → ["Hello", "world"]
```

```
Line 47: def tokenize_arabic(text: str) → list[str]:
Line 48:     return re.findall(r"[\u0600-\u06FF]+", text)
                                              ← extract all sequences of Arabic characters
                                              ← U+0600–U+06FF covers Arabic block
                                              ← ignores Latin letters, numbers, punctuation
                                              ← "الذكاء الاصطناعي is great" → ["الذكاء", "الاصطناعي"]
```

### English pipeline

```
Line 51: def preprocess_english(text: str) → list[tuple[str, int]]:
Line 52:     text = text.lower()               ← step 1: lowercase everything
                                              ←   "Information Retrieval" → "information retrieval"
Line 53:     tokens = tokenize_english(text)   ← step 2: split into tokens
                                              ←   ["information", "retrieval", "is", "great"]
Line 54:     stopwords = get_english_stopwords()  ← step 3: get cached stopword set
Line 56:     all_with_pos = []                  ← result list: (stemmed_term, original_position)
Line 57:     for i, token in enumerate(tokens):  ← i = position in original token list
Line 58:         if token not in stopwords:     ← step 3: skip stop words
                                              ←   "is" is a stopword → skip it (but its position 2 is still recorded)
Line 59:             stemmed = porter_stem(token) ← step 4: stem the token
Line 60:             if stemmed:               ← step 5: skip empty stems (safety check)
Line 61:                 all_with_pos.append((stemmed, i))
Line 62:     return all_with_pos
```

**Example walkthrough:**
```
Input: "Information retrieval is great"
    text.lower():     "information retrieval is great"
    tokenize:          ["information", "retrieval", "is", "great"]
                          i=0             i=1         i=2     i=3
    remove stopwords:  ["information", "retrieval",       "great"]
    stem:              [  "inform",      "retriev",        "great"]
    output:            [("inform", 0), ("retriev", 1), ("great", 3)]
                                                              ↑ position 2 is "is" (removed)
```

### Arabic pipeline

```
Line 65: def preprocess_arabic(text: str) → list[tuple[str, int]]:
Line 66:     text = normalize_arabic(text)      ← step 1: normalize Arabic text
                                              ←   handle أ→ا, ى→ي, ة→ه, remove diacritics
Line 67:     tokens = tokenize_arabic(text)      ← step 2: extract Arabic words
Line 68:     stopwords = get_arabic_stopwords() ← step 3: get cached stopword set
Line 70:     all_with_pos = []
Line 71:     for i, token in enumerate(tokens): ← i = position in token list
Line 72:         if token not in stopwords:     ← skip Arabic stop words
Line 73:             stemmed = isri_stem(token)  ← step 4: apply ISRI stemming
Line 74:             if stemmed:                  ← skip empty results
Line 75:                 all_with_pos.append((stemmed, i))
Line 76:     return all_with_pos
```

### Main entry point

```
Line 79: def preprocess(text: str, lang: str | None = None) → list[tuple[str, int]]:
Line 80:     if not text or not text.strip():   ← handle empty/whitespace input
Line 81:         return []                       ← return empty result (no crash)
Line 82:     if lang is None:                   ← caller didn't specify language?
Line 83:         lang = detect_language(text)    ← auto-detect using Arabic Unicode check
Line 84:     if lang == "arabic":               ← route to Arabic pipeline
Line 85:         return preprocess_arabic(text)
Line 86:     return preprocess_english(text)    ← default: English pipeline
```

**Why `lang` is optional:** Sometimes you already know the language (e.g., reading from `corpus/en/`). Passing `lang="english"` skips the detection step. When the user types a query, `lang=None` triggers auto-detection.

---

## `indexer.py` — Positional Inverted Index Builder

### Imports

```
Line 1:  import json                              ← for saving/loading index to JSON
Line 2:  import os                               ← file path handling
Line 3:  from language_detector import detect_language  ← determine doc language
Line 4:  from preprocessing import preprocess     ← tokenize, remove stops, stem
```

### `get_all_docs(corpus_path)`

```
Line 7:  def get_all_docs(corpus_path: str) → list[str]:
Line 8:      docs = []                            ← collect all .txt file paths
Line 9:      for lang_dir in ["en", "ar"]:        ← check both subdirectories
Line 10:         dir_path = os.path.join(corpus_path, lang_dir)  ← e.g. "corpus/en"
Line 11:         if not os.path.isdir(dir_path):   ← skip if directory doesn't exist
Line 12:             continue
Line 13:         for filename in sorted(os.listdir(dir_path)):  ← alphabetical order
Line 14:             if filename.endswith(".txt"):  ← only process .txt files
Line 15:                 docs.append(os.path.join(dir_path, filename))
Line 16:     return docs                           ← e.g. ["corpus/en/doc01.txt", ..., "corpus/ar/doc10.txt"]
```

**Why `sorted`?** Ensures deterministic order — doc01 comes before doc02. Important for reproducibility and debugging.

### `get_doc_id(doc_path)`

```
Line 19: def get_doc_id(doc_path: str) → str:
Line 20:     parts = doc_path.replace("\\", "/").split("/")  ← normalize Windows paths
                                              ← "corpus/en/doc01.txt" → ["corpus", "en", "doc01.txt"]
Line 21:     lang_dir = parts[-2]              ← second-to-last part = "en" or "ar"
Line 22:     filename = parts[-1]             ← last part = "doc01.txt"
Line 23:     return f"{lang_dir}/{filename}"   ← "en/doc01.txt"
```

**Why this ID format?** The ID `"en/doc01.txt"` encodes both the language and the document number. This is what gets stored as the key in the index. When the user sees search results, they know immediately which language the doc is in.

### `build_index(corpus_path)` — The Main Function

```
Line 26: def build_index(corpus_path: str) → tuple[dict, dict]:
                                              ← returns (index, doc_store) — two dicts
Line 27:     index: dict[str, dict[str, list[int]]] = {}
                                              ← type annotation: term → {doc_id → [positions]}
                                              ← e.g. "comput" → {"en/doc01.txt": [0, 6, 18], "en/doc07.txt": [2]}
Line 28:     doc_store: dict[str, dict] = {}  ← type annotation: doc_id → metadata
Line 30:     for doc_path in get_all_docs(corpus_path):  ← iterate over all 20 docs
Line 31:         doc_id = get_doc_id(doc_path)  ← e.g. "en/doc01.txt"
Line 33:         with open(doc_path, "r", encoding="utf-8") as f:
Line 34:             text = f.read()           ← read entire file content as string
                                              ← encoding="utf-8" is critical for Arabic text
Line 36:         if not text.strip():          ← EDGE CASE: empty document
Line 37:             doc_store[doc_id] = {
Line 38:                 "total_terms": 0,     ← no terms in empty doc
Line 39:                 "raw_text": text,
Line 40:                 "language": "english", ← default language for empty doc
Line 41:             }
Line 42:             continue                   ← skip to next doc (don't add anything to index)
Line 44:         lang = detect_language(text)   ← detect "arabic" or "english"
Line 45:         tokens_with_positions = preprocess(text, lang)
                                              ← run the full preprocessing pipeline
                                              ← returns [("inform", 0), ("retriev", 1), ("great", 3), ...]
Line 47:         for term, position in tokens_with_positions:
Line 48:             if term not in index:     ← first time seeing this term?
Line 49:                 index[term] = {}       ← create its posting dict
Line 50:             if doc_id not in index[term]:
                                              ← first time this term appears in this doc?
Line 51:                 index[term][doc_id] = []  ← create position list
Line 52:             index[term][doc_id].append(position)
                                              ← add position to the list
                                              ← e.g. "comput" appears at position 0 in doc01
                                              ← later at position 6 → index["comput"]["en/doc01.txt"] = [0, 6]
Line 54:         doc_store[doc_id] = {
Line 55:             "total_terms": len(tokens_with_positions),
                                              ← number of INDEXED terms (after stopword removal + stemming)
                                              ← NOT the raw word count — this is the term count used for TF calculation
Line 56:             "raw_text": text,          ← store original text for display in search results
Line 57:             "language": lang,          ← store language for query-time pipeline selection
Line 58:         }
Line 60:     return index, doc_store            ← return both data structures
```

**Why store `total_terms`?** This is the denominator in the TF formula: `tf(t, d) = count(t in d) / total_terms(d)`. Without it, we can't calculate TF-IDF in Phase 6.

**Why store `raw_text`?** When the CLI displays search results, the user wants to see the original document, not the stemmed/normalized version.

### `save_index()` and `load_index()`

```
Line 63: def save_index(index, doc_store, output_dir) → None:
Line 64:     os.makedirs(output_dir, exist_ok=True)  ← create "index_data/" if it doesn't exist
Line 65:     with open(os.path.join(output_dir, "index.json"), "w", encoding="utf-8") as f:
Line 66:         json.dump(index, f, ensure_ascii=False, indent=2)
                                              ← ensure_ascii=False: preserves Arabic characters
                                              ← indent=2: human-readable formatting
Line 67:     with open(os.path.join(output_dir, "doc_store.json"), "w", encoding="utf-8") as f:
Line 68:         json.dump(doc_store, f, ensure_ascii=False, indent=2)
```

```
Line 71: def load_index(output_dir) → tuple[dict, dict]:
Line 72:     with open(os.path.join(output_dir, "index.json"), "r", encoding="utf-8") as f:
Line 73:         index = json.load(f)            ← deserialize JSON back to Python dict
Line 74:     with open(os.path.join(output_dir, "doc_store.json"), "r", encoding="utf-8") as f:
Line 75:         doc_store = json.load(f)
Line 76:     return index, doc_store
```

**Why save/load?** Building the index takes time (reading 20 files, preprocessing each). By saving to JSON, later phases can load it instantly instead of rebuilding. This also makes debugging easier — you can inspect the JSON files directly.

### `__main__` block

```
Line 79: if __name__ == "__main__":
Line 80:     corpus_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corpus")
                                              ← path to corpus/ relative to script location
Line 81:     output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index_data")
                                              ← output to index_data/ folder
Line 83:     print("Building index...")
Line 84:     index, doc_store = build_index(corpus_path)  ← main build call
Line 86:     print(f"Indexed {len(doc_store)} documents")
Line 87:     print(f"Vocabulary size: {len(index)} terms")
                                              ← len(index) = number of unique terms across all docs
                                              ← our corpus: ~494 unique terms
Line 89:     print("\nSample index entries (first 10 terms):")
Line 90:     for i, (term, postings) in enumerate(index.items()):
Line 91:         if i >= 10:
Line 92:             break
Line 93:         docs = {doc_id: positions for doc_id, positions in postings.items()}
Line 94:         print(f"  '{term}' → {docs}")
Line 95:
Line 96:     print("\nDoc store summary:")
Line 97:     for doc_id, info in doc_store.items():
Line 98:         print(f"  {doc_id}: {info['total_terms']} terms, lang={info['language']}")
Line 100:    save_index(index, doc_store, output_dir)  ← persist to disk
Line 101:    print(f"\nIndex saved to {output_dir}/")
```

**What gets saved:**
- `index_data/index.json` — the full positional inverted index
- `index_data/doc_store.json` — document metadata (term count, raw text, language)