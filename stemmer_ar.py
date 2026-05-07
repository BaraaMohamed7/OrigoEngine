import re


ARABIC_PREFIX_PATTERNS = [
    r"^وال",
    r"^بال",
    r"^كال",
    r"^لل",
    r"^وال",
    r"^وبال",
    r"^فبال",
    r"^فال",
    r"^ال",
    r"^وب",
    r"^ول",
    r"^فب",
    r"^فل",
    r"^فك",
    r"^وك",
    r"^لل",
    r"^لل",
    r"^و",
    r"^ب",
    r"^ك",
    r"^ل",
    r"^ف",
]

ARABIC_SUFFIX_PATTERNS = [
    r"ها$",
    r"ة$",
    r"يه$",
    r"ية$",
    r"ان$",
    r"ين$",
    r"ون$",
    r"ات$",
    r"تم$",
    r"كم$",
    r"نا$",
    r"هم$",
    r"هن$",
    r"يا$",
    r"يل$",
    r"يا$",
]


def _remove_prefix(word: str) -> str:
    for pattern in ARABIC_PREFIX_PATTERNS:
        new_word = re.sub(pattern, "", word)
        if len(new_word) >= 2 and new_word != word:
            return new_word
    return word


def _remove_suffix(word: str) -> str:
    for pattern in ARABIC_SUFFIX_PATTERNS:
        new_word = re.sub(pattern, "", word)
        if len(new_word) >= 2 and new_word != word:
            return new_word
    return word


def isri_stem(word: str) -> str:
    if len(word) <= 2:
        return word

    word = _remove_prefix(word)
    if len(word) <= 2:
        return word

    word = _remove_suffix(word)
    if len(word) <= 2:
        return word

    word = _remove_prefix(word)
    if len(word) <= 2:
        return word

    word = _remove_suffix(word)
    if len(word) <= 2:
        return word

    return word
