def _is_consonant(word: str, i: int) -> bool:
    ch = word[i]
    if ch in "aeiou":
        return False
    if ch == "y":
        if i == 0:
            return True
        return not _is_consonant(word, i - 1)
    return True


def _measure(word: str) -> int:
    n = len(word)
    if n == 0:
        return 0
    i = 0
    m = 0
    while i < n and _is_consonant(word, i):
        i += 1
    while i < n:
        while i < n and not _is_consonant(word, i):
            i += 1
        if i >= n:
            break
        m += 1
        while i < n and _is_consonant(word, i):
            i += 1
    return m


def _has_vowel(word: str) -> bool:
    for i in range(len(word)):
        if not _is_consonant(word, i):
            return True
    return False


def _ends_double_consonant(word: str) -> bool:
    if len(word) < 2:
        return False
    return word[-1] == word[-2] and _is_consonant(word, len(word) - 1)


def _cvc(word: str) -> bool:
    n = len(word)
    if n < 3:
        return False
    if not _is_consonant(word, n - 1):
        return False
    if _is_consonant(word, n - 2):
        return False
    if not _is_consonant(word, n - 3):
        return False
    if word[-1] in "wxy":
        return False
    return True


def _replace_suffix(word: str, suffix: str, replacement: str) -> str:
    if not word.endswith(suffix):
        return word
    return word[: -len(suffix)] + replacement


def _strip_suffix(word: str, suffix: str) -> str:
    if not word.endswith(suffix):
        return word
    return word[: -len(suffix)]


def porter_stem(word: str) -> str:
    if len(word) <= 2:
        return word

    word = word.lower()

    if word.endswith("'s'"):
        word = word[:-3]
    elif word.endswith("'s"):
        word = word[:-2]
    elif word.endswith("'"):
        word = word[:-1]

    word = word.replace("y'", "y")

    # Step 1a
    if word.endswith("sses"):
        word = _replace_suffix(word, "sses", "ss")
    elif word.endswith("ies"):
        word = _replace_suffix(word, "ies", "i")
    elif word.endswith("ss"):
        pass
    elif word.endswith("s"):
        word = _strip_suffix(word, "s")

    # Step 1b
    m = _measure
    step1b_extra = False
    if word.endswith("eed"):
        stem = word[:-3]
        if m(stem) > 0:
            word = _replace_suffix(word, "eed", "ee")
    elif word.endswith("ed"):
        stem = word[:-2]
        if _has_vowel(stem):
            word = stem
            step1b_extra = True
    elif word.endswith("ed"):
        pass
    elif word.endswith("ing"):
        stem = word[:-3]
        if _has_vowel(stem):
            word = stem
            step1b_extra = True

    if step1b_extra:
        if word.endswith("at") or word.endswith("bl") or word.endswith("iz"):
            word = word + "e"
        elif _ends_double_consonant(word) and word[-1] not in "lsz":
            word = word[:-1]
        elif m(word) == 1 and _cvc(word):
            word = word + "e"

    # Step 1c
    if word.endswith("y"):
        stem = word[:-1]
        if _has_vowel(stem):
            word = stem + "i"

    # Step 2
    step2_map = {
        "ational": "ate",
        "tional": "tion",
        "enci": "ence",
        "anci": "ance",
        "izer": "ize",
        "abli": "able",
        "alli": "al",
        "entli": "ent",
        "eli": "e",
        "ousli": "ous",
        "ization": "ize",
        "ation": "ate",
        "ator": "ate",
        "alism": "al",
        "iveness": "ive",
        "fulness": "ful",
        "ousness": "ous",
        "aliti": "al",
        "iviti": "ive",
        "biliti": "ble",
    }
    for suffix, replacement in step2_map.items():
        if word.endswith(suffix):
            stem = word[: -len(suffix)]
            if m(stem) > 0:
                word = stem + replacement
            break

    # Step 3
    step3_map = {
        "icate": "ic",
        "ative": "",
        "alize": "al",
        "iciti": "ic",
        "ical": "ic",
        "ful": "",
        "ness": "",
    }
    for suffix, replacement in step3_map.items():
        if word.endswith(suffix):
            stem = word[: -len(suffix)]
            if m(stem) > 0:
                word = stem + replacement
            break

    # Step 4
    step4_suffixes = [
        "al",
        "ance",
        "ence",
        "er",
        "ic",
        "able",
        "ible",
        "ant",
        "ement",
        "ment",
        "ent",
        "ion",
        "ou",
        "ism",
        "ate",
        "iti",
        "ous",
        "ive",
        "ize",
    ]
    for suffix in step4_suffixes:
        if word.endswith(suffix):
            stem = word[: -len(suffix)]
            if suffix == "ion":
                if m(stem) > 1 and len(stem) > 0 and stem[-1] in "st":
                    word = stem
            else:
                if m(stem) > 1:
                    word = stem
            break

    # Step 5a
    if word.endswith("e"):
        stem = word[:-1]
        if m(stem) > 1:
            word = stem
        elif m(stem) == 1 and not _cvc(stem):
            word = stem

    # Step 5b
    if _ends_double_consonant(word) and word[-1] == "l" and m(word) > 1:
        word = word[:-1]

    return word
