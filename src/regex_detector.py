"""
regex_detector.py
Tahap 3: Regex Detection (Rule-Based Matching)
Mendeteksi pola PII berformat baku: email, nomor HP, NIK, nilai uang, nomor kontrak.
"""

import re

# Pola regex untuk tiap kategori PII berpola baku.
# Urutan penting: pola yang lebih spesifik/panjang dicek lebih dulu
# agar tidak "dimakan" oleh pola lain yang lebih umum.
PATTERNS = {
    "NIK": r"\b[0-9]{16}\b",
    "EMAIL": r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
    "PHONE": r"(?:\+62|62|0)8[1-9][0-9]{6,10}\b",
    "AMOUNT": r"Rp\.?\s?[0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?",
    "CONTRACT_ID": r"\b[A-Z]{2,5}[\-/][0-9]{4,10}\b",
}


def regex_detect(text: str) -> list[dict]:
    """
    Mendeteksi seluruh PII berpola baku pada teks menggunakan regex.

    Args:
        text: teks mentah/hasil ekstraksi

    Returns:
        List span PII: [{"start": int, "end": int, "text": str, "label": str}, ...]
        diurutkan berdasarkan posisi awal (start) lalu panjang span (descending),
        agar span yang lebih panjang diprioritaskan saat resolusi overlap.
    """
    results = []
    for label, pattern in PATTERNS.items():
        for m in re.finditer(pattern, text):
            results.append(
                {
                    "start": m.start(),
                    "end": m.end(),
                    "text": m.group(),
                    "label": label,
                    "source": "regex",
                }
            )

    results = _resolve_overlaps(results)
    results.sort(key=lambda s: s["start"])
    return results


def _resolve_overlaps(spans: list[dict]) -> list[dict]:
    """
    Jika ada span regex yang saling tumpang tindih (mis. NIK 16 digit
    yang sebagian cocok juga dengan pola lain), span yang lebih panjang
    dipertahankan dan span yang lebih pendek/overlap dibuang.
    """
    if not spans:
        return spans

    spans_sorted = sorted(spans, key=lambda s: (s["start"], -(s["end"] - s["start"])))
    kept = []
    last_end = -1
    for span in spans_sorted:
        if span["start"] >= last_end:
            kept.append(span)
            last_end = span["end"]
    return kept


if __name__ == "__main__":
    contoh = (
        "Email saya budi.santoso@gmail.com, No HP 081234567890, "
        "NIK 3578012345670001, Nilai kontrak Rp 75.000.000, "
        "Nomor kontrak PKS-20241001."
    )
    for span in regex_detect(contoh):
        print(f"{span['label']:15} : {span['text']}")
