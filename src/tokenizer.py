"""
tokenizer.py
Tahap 2: Tokenization
Memecah teks menjadi unit-unit kecil (token) menggunakan spaCy tokenizer.
"""

import spacy

_nlp_blank = None


def _get_blank_tokenizer():
    """
    Memuat tokenizer kosong (blank) bahasa Indonesia.
    Tidak memerlukan model NER, hanya tokenizer rule-based spaCy.
    Lazy-loaded agar tidak membebani import saat modul ini di-import
    bersama modul lain yang juga memuat model spaCy.
    """
    global _nlp_blank
    if _nlp_blank is None:
        _nlp_blank = spacy.blank("id")  # tokenizer khusus aturan bahasa Indonesia
    return _nlp_blank


def tokenize(text: str) -> list[str]:
    """
    Memecah teks menjadi list token menggunakan spaCy.

    Args:
        text: teks mentah hasil ekstraksi

    Returns:
        List token (kata, tanda baca, dsb.)
    """
    nlp = _get_blank_tokenizer()
    doc = nlp(text)
    return [token.text for token in doc]


def tokenize_with_offsets(text: str) -> list[dict]:
    """
    Tokenisasi dengan menyertakan posisi karakter (offset) tiap token.
    Berguna untuk debugging/visualisasi tahap tokenisasi.

    Returns:
        List of dict: [{"text": str, "start": int, "end": int}, ...]
    """
    nlp = _get_blank_tokenizer()
    doc = nlp(text)
    return [
        {"text": token.text, "start": token.idx, "end": token.idx + len(token.text)}
        for token in doc
    ]


if __name__ == "__main__":
    contoh = "Nama saya Budi Santoso. Email: budi@gmail.com"
    print("Input  :", contoh)
    print("Tokens :", tokenize(contoh))
