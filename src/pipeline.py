"""
pipeline.py
Orchestrator: menjalankan seluruh pipeline NLP secara berurutan.
Text Extraction -> Tokenization -> Regex Detection -> NER Detection
-> PII Merging -> Masking/Redaction -> Statistik
"""

from src.extractor import extract_text, extract_text_from_bytes
from src.tokenizer import tokenize
from src.regex_detector import regex_detect
from src.ner_detector import ner_detect
from src.masker import merge_spans, mask_text, get_statistics


def run_pipeline(text: str, mode: str = "specific") -> dict:
    """
    Menjalankan pipeline PII redaction lengkap terhadap teks mentah.

    Args:
        text: teks mentah (hasil ekstraksi atau input langsung)
        mode: "specific" untuk label per kategori, "generic" untuk [REDACTED]

    Returns:
        Dict berisi seluruh hasil tiap tahapan:
        {
            "original_text": str,
            "tokens": list[str],
            "regex_spans": list[dict],
            "ner_spans": list[dict],
            "merged_spans": list[dict],
            "redacted_text": str,
            "statistics": dict,
        }
    """
    # Tahap 2: Tokenization
    tokens = tokenize(text)

    # Tahap 3: Regex Detection
    regex_spans = regex_detect(text)

    # Tahap 4: NER Detection
    ner_spans = ner_detect(text)

    # Tahap 5: PII Merging
    merged_spans = merge_spans(regex_spans, ner_spans)

    # Tahap 6: Masking / Redaction
    redacted_text = mask_text(text, merged_spans, mode=mode)

    # Statistik
    statistics = get_statistics(merged_spans)

    return {
        "original_text": text,
        "tokens": tokens,
        "regex_spans": regex_spans,
        "ner_spans": ner_spans,
        "merged_spans": merged_spans,
        "redacted_text": redacted_text,
        "statistics": statistics,
    }


def run_pipeline_from_file(file_path: str, mode: str = "specific") -> dict:
    """Menjalankan pipeline langsung dari path file (.txt/.pdf/.docx)."""
    text = extract_text(file_path)
    return run_pipeline(text, mode=mode)


def run_pipeline_from_bytes(file_bytes: bytes, filename: str, mode: str = "specific") -> dict:
    """Menjalankan pipeline langsung dari bytes file upload (dipakai Streamlit)."""
    text = extract_text_from_bytes(file_bytes, filename)
    return run_pipeline(text, mode=mode)


if __name__ == "__main__":
    contoh = (
        "Nama    : Budi Santoso\n"
        "Jabatan : Manajer Operasional\n"
        "Email   : budi.santoso@perusahaan.co.id\n"
        "No HP   : 081234567890\n"
        "NIK     : 3578012345670001\n"
        "Alamat  : Jl. Merdeka No. 10, Surabaya, Jawa Timur\n"
        "Kontrak : PKS-20241001\n"
        "Nilai   : Rp 75.000.000\n\n"
        "Budi Santoso bekerja di PT Maju Bersama yang berlokasi di Surabaya.\n"
        "Hubungi beliau melalui email atau nomor telepon di atas untuk konfirmasi."
    )

    hasil = run_pipeline(contoh, mode="specific")

    print("=" * 60)
    print("TEKS ASLI")
    print("=" * 60)
    print(hasil["original_text"])

    print("\n" + "=" * 60)
    print("TEKS TERANONIMISASI")
    print("=" * 60)
    print(hasil["redacted_text"])

    print("\n" + "=" * 60)
    print("STATISTIK DETEKSI PII")
    print("=" * 60)
    total = 0
    for label, count in hasil["statistics"].items():
        print(f"{label:15}: {count}")
        total += count
    print(f"{'TOTAL':15}: {total}")
