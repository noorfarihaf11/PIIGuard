"""
ner_detector.py
Tahap 4: Named Entity Recognition (NER)
Mendeteksi entitas kontekstual (PERSON, LOCATION, ORG) yang tidak memiliki
pola baku sehingga tidak dapat ditangkap oleh Regex.

Catatan implementasi:
spaCy tidak menyediakan model resmi berlabel 'id_core_news_sm'. Untuk bahasa
Indonesia, model yang tersedia secara resmi adalah model multi-language
'xx_ent_wiki_sm' yang dilatih di atas data multibahasa (termasuk Indonesia)
bersumber dari Wikipedia. Model ini hanya mengenali 3 label: PER, LOC, MISC.

Karena akurasi model multi-language ini masih terbatas untuk teks bahasa
Indonesia informal/semi-formal (seperti pada dokumen kerja sehari-hari),
modul ini menambahkan lapisan gazetteer/dictionary-based matching sebagai
pelengkap untuk meningkatkan recall pada kasus-kasus umum (nama dengan gelar,
kata kunci organisasi, dan kata kunci lokasi administratif Indonesia).
"""

import re
import spacy

_nlp_ner = None

MODEL_NAME = "xx_ent_wiki_sm"

# Mapping label spaCy -> label PII pada sistem
LABEL_MAP = {
    "PER": "PERSON",
    "PERSON": "PERSON",
    "LOC": "LOCATION",
    "GPE": "LOCATION",
    "ORG": "ORG",
}

# Kata kunci pelengkap (gazetteer) untuk organisasi & lokasi administratif
# Indonesia yang sering tidak tertangkap oleh model multi-language.
ORG_KEYWORDS = r"(?:PT|CV|UD|Universitas|Fakultas|Yayasan|Kementerian|Dinas|RSUD|Rumah Sakit)\s+[A-Z][\w&\.]*(?:\s+[A-Z][\w&\.]*){0,4}"
LOCATION_KEYWORDS = (
    r"(?:Jl\.|Jalan)\s+[A-Z][^,\n]{2,60}?(?=[,\n]|$)"
    r"|(?:Kota|Kabupaten|Provinsi|Kecamatan|Kelurahan)\s+[A-Z][\w\s]{2,30}?(?=[,\.\n]|$)"
)


def _get_ner_model():
    """
    Memuat model NER spaCy (xx_ent_wiki_sm), lazy-loaded.
    Jalankan `python -m spacy download xx_ent_wiki_sm` sebelum pertama kali pakai.
    """
    global _nlp_ner
    if _nlp_ner is None:
        try:
            _nlp_ner = spacy.load(MODEL_NAME)
        except OSError as e:
            raise OSError(
                f"Model '{MODEL_NAME}' belum terinstal.\n"
                f"Jalankan: python -m spacy download {MODEL_NAME}"
            ) from e
    return _nlp_ner


def ner_detect(text: str) -> list[dict]:
    """
    Mendeteksi entitas PERSON, LOCATION, ORG menggunakan model spaCy
    multi-language, dilengkapi gazetteer matching untuk pola umum
    Bahasa Indonesia yang sering luput dari model.

    Args:
        text: teks mentah/hasil ekstraksi

    Returns:
        List span PII: [{"start": int, "end": int, "text": str, "label": str}, ...]
    """
    nlp = _get_ner_model()
    doc = nlp(text)

    results = []
    for ent in doc.ents:
        label = LABEL_MAP.get(ent.label_)
        if label is None:
            continue  # abaikan label MISC dan label lain di luar cakupan PII
        results.append(
            {
                "start": ent.start_char,
                "end": ent.end_char,
                "text": ent.text,
                "label": label,
                "source": "ner",
            }
        )

    results.extend(_gazetteer_detect(text))
    results = _dedupe_overlaps(results)
    results.sort(key=lambda s: s["start"])
    return results


def _gazetteer_detect(text: str) -> list[dict]:
    """
    Lapisan pelengkap berbasis pola kata kunci untuk menangkap organisasi
    dan lokasi administratif Indonesia yang umum, sebagai mitigasi atas
    keterbatasan recall model xx_ent_wiki_sm pada teks Bahasa Indonesia.
    """
    extra = []

    for m in re.finditer(ORG_KEYWORDS, text):
        extra.append(
            {
                "start": m.start(),
                "end": m.end(),
                "text": m.group().strip(),
                "label": "ORG",
                "source": "gazetteer",
            }
        )

    for m in re.finditer(LOCATION_KEYWORDS, text):
        extra.append(
            {
                "start": m.start(),
                "end": m.end(),
                "text": m.group().strip(),
                "label": "LOCATION",
                "source": "gazetteer",
            }
        )

    return extra


def _dedupe_overlaps(spans: list[dict]) -> list[dict]:
    """
    Menghapus span yang tumpang tindih, memprioritaskan span yang lebih
    panjang (umumnya hasil gazetteer yang lebih lengkap, mis. 'Universitas
    Airlangga' dibanding hanya 'Airlangga' dari model NER).
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
    contoh = "Budi Santoso bekerja di PT Maju Bersama di Surabaya."
    for span in ner_detect(contoh):
        print(f"{span['label']:10} : {span['text']}  (source={span['source']})")
