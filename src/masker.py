"""
masker.py
Tahap 5 & 6: PII Merging dan Masking / Redaction
Menggabungkan hasil Regex + NER (menangani overlap), lalu mengganti
setiap span PII dengan label redaksi yang sesuai.
"""


def merge_spans(regex_spans: list[dict], ner_spans: list[dict]) -> list[dict]:
    """
    Menggabungkan hasil deteksi Regex dan NER menjadi satu list span PII
    tanpa overlap. Prioritas diberikan kepada Regex untuk entitas berpola
    baku (EMAIL, PHONE, NIK, AMOUNT, CONTRACT_ID), dan kepada NER untuk
    entitas kontekstual (PERSON, LOCATION, ORG).

    Args:
        regex_spans: hasil dari regex_detector.regex_detect()
        ner_spans: hasil dari ner_detector.ner_detect()

    Returns:
        List span PII gabungan, terurut berdasarkan posisi awal,
        tanpa tumpang tindih.
    """
    # Regex didahulukan: jika ada overlap, regex menang karena polanya
    # pasti (mis. format email/NIK tidak ambigu), sedangkan NER bisa salah
    # mengenali konteks.
    all_spans = list(regex_spans) + list(ner_spans)

    all_spans.sort(key=lambda s: (s["start"], 0 if s["source"] == "regex" else 1, -(s["end"] - s["start"])))

    merged = []
    last_end = -1
    for span in all_spans:
        if span["start"] >= last_end:
            merged.append(span)
            last_end = span["end"]
        # span yang overlap dengan span sebelumnya (yang sudah dipertahankan)
        # otomatis dibuang di sini

    merged.sort(key=lambda s: s["start"])
    return merged


def mask_text(text: str, pii_spans: list[dict], mode: str = "specific") -> str:
    """
    Mengganti setiap span PII pada teks dengan label redaksi.

    Args:
        text: teks asli
        pii_spans: list span PII hasil merge_spans()
        mode: "specific" -> label per kategori, mis. [PERSON], [EMAIL]
              "generic"   -> seluruh PII diganti [REDACTED]

    Returns:
        Teks hasil redaksi (teranonimisasi)
    """
    # Urutkan dari belakang (posisi start terbesar dulu) agar penggantian
    # tidak menggeser indeks karakter span berikutnya yang belum diproses.
    sorted_spans = sorted(pii_spans, key=lambda s: s["start"], reverse=True)

    result = text
    for span in sorted_spans:
        if mode == "specific":
            replacement = f"[{span['label']}]"
        elif mode == "generic":
            replacement = "[REDACTED]"
        else:
            raise ValueError("mode harus 'specific' atau 'generic'")

        result = result[: span["start"]] + replacement + result[span["end"] :]

    return result


def get_statistics(pii_spans: list[dict]) -> dict:
    """
    Menghitung statistik jumlah PII yang terdeteksi per kategori.

    Args:
        pii_spans: list span PII hasil merge_spans()

    Returns:
        Dict {label: jumlah}, contoh: {"PERSON": 2, "EMAIL": 1, ...}
    """
    stats = {}
    for span in pii_spans:
        label = span["label"]
        stats[label] = stats.get(label, 0) + 1
    return stats


if __name__ == "__main__":
    from regex_detector import regex_detect
    from ner_detector import ner_detect

    contoh = (
        "Nama saya Budi Santoso, bekerja di PT Maju Bersama. "
        "Hubungi via budi@gmail.com atau 081234567890. "
        "Saya tinggal di Surabaya."
    )

    regex_spans = regex_detect(contoh)
    ner_spans = ner_detect(contoh)
    merged = merge_spans(regex_spans, ner_spans)

    print("=== TEKS ASLI ===")
    print(contoh)
    print("\n=== HASIL REDAKSI (specific) ===")
    print(mask_text(contoh, merged, mode="specific"))
    print("\n=== HASIL REDAKSI (generic) ===")
    print(mask_text(contoh, merged, mode="generic"))
    print("\n=== STATISTIK ===")
    for label, count in get_statistics(merged).items():
        print(f"{label:15}: {count}")
