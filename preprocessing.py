import re
import os

from language_detector import detect_language
from stemmer_en import porter_stem
from stemmer_ar import isri_stem

STOPWORDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stopwords")

_ENGLISH_STOPWORDS: set | None = None
_ARABIC_STOPWORDS: set | None = None


def _load_stopwords(filename: str) -> set:
    filepath = os.path.join(STOPWORDS_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def get_english_stopwords() -> set:
    global _ENGLISH_STOPWORDS
    if _ENGLISH_STOPWORDS is None:
        _ENGLISH_STOPWORDS = _load_stopwords("english_stopwords.txt")
    return _ENGLISH_STOPWORDS


def get_arabic_stopwords() -> set:
    global _ARABIC_STOPWORDS
    if _ARABIC_STOPWORDS is None:
        _ARABIC_STOPWORDS = _load_stopwords("arabic_stopwords.txt")
    return _ARABIC_STOPWORDS


def normalize_arabic(text: str) -> str:
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = text.replace("\u0640", "")
    text = re.sub(r"[إأآ]", "ا", text)
    text = text.replace("ى", "ي")
    text = text.replace("ة", "ه")
    return text


def tokenize_english(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]+", text)


def tokenize_arabic(text: str) -> list[str]:
    return re.findall(r"[\u0600-\u06FF]+", text)


def preprocess_english(text: str) -> list[tuple[str, int]]:
    text = text.lower()
    tokens = tokenize_english(text)
    stopwords = get_english_stopwords()

    all_with_pos = []
    for i, token in enumerate(tokens):
        if token not in stopwords:
            stemmed = porter_stem(token)
            if stemmed:
                all_with_pos.append((stemmed, i))
    return all_with_pos


def preprocess_arabic(text: str) -> list[tuple[str, int]]:
    text = normalize_arabic(text)
    tokens = tokenize_arabic(text)
    stopwords = get_arabic_stopwords()

    all_with_pos = []
    for i, token in enumerate(tokens):
        if token not in stopwords:
            stemmed = isri_stem(token)
            if stemmed:
                all_with_pos.append((stemmed, i))
    return all_with_pos


def preprocess(text: str, lang: str | None = None) -> list[tuple[str, int]]:
    if not text or not text.strip():
        return []
    if lang is None:
        lang = detect_language(text)
    if lang == "arabic":
        return preprocess_arabic(text)
    return preprocess_english(text)
