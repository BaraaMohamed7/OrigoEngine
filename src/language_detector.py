import re


def detect_language(text: str) -> str:
    if not text or not text.strip():
        return "english"
    if re.search(r"[\u0600-\u06FF]", text):
        return "arabic"
    return "english"
