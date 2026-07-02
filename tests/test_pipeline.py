"""
test_pipeline.py
Unit test sederhana untuk tiap modul pipeline PrivacyGuard AI.
Jalankan dengan: pytest tests/test_pipeline.py -v
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tokenizer import tokenize
from src.regex_detector import regex_detect
from src.masker import merge_spans, mask_text, get_statistics


def test_tokenize_basic():
    text = "Nama saya Budi Santoso."
    tokens = tokenize(text)
    assert "Budi" in tokens
    assert "Santoso" in tokens
    assert "." in tokens


def test_regex_detect_email():
    text = "Email saya budi@gmail.com"
    spans = regex_detect(text)
    labels = [s["label"] for s in spans]
    assert "EMAIL" in labels
    assert spans[0]["text"] == "budi@gmail.com"


def test_regex_detect_phone():
    text = "Hubungi saya di 081234567890"
    spans = regex_detect(text)
    labels = [s["label"] for s in spans]
    assert "PHONE" in labels


def test_regex_detect_nik():
    text = "NIK: 3578012345670001"
    spans = regex_detect(text)
    labels = [s["label"] for s in spans]
    assert "NIK" in labels


def test_regex_detect_amount():
    text = "Nilai kontrak Rp 75.000.000"
    spans = regex_detect(text)
    labels = [s["label"] for s in spans]
    assert "AMOUNT" in labels


def test_regex_detect_contract_id():
    text = "Nomor kontrak PKS-20241001"
    spans = regex_detect(text)
    labels = [s["label"] for s in spans]
    assert "CONTRACT_ID" in labels


def test_regex_no_overlap():
    """Memastikan tidak ada span regex yang saling tumpang tindih."""
    text = "Email: budi.santoso@perusahaan.co.id, NIK: 3578012345670001"
    spans = regex_detect(text)
    spans_sorted = sorted(spans, key=lambda s: s["start"])
    for i in range(len(spans_sorted) - 1):
        assert spans_sorted[i]["end"] <= spans_sorted[i + 1]["start"]


def test_mask_text_specific_mode():
    text = "Email saya budi@gmail.com"
    spans = regex_detect(text)
    masked = mask_text(text, spans, mode="specific")
    assert "[EMAIL]" in masked
    assert "budi@gmail.com" not in masked


def test_mask_text_generic_mode():
    text = "Email saya budi@gmail.com"
    spans = regex_detect(text)
    masked = mask_text(text, spans, mode="generic")
    assert "[REDACTED]" in masked
    assert "budi@gmail.com" not in masked


def test_merge_spans_no_overlap():
    regex_spans = [
        {"start": 0, "end": 5, "text": "Hello", "label": "EMAIL", "source": "regex"}
    ]
    ner_spans = [
        {"start": 10, "end": 15, "text": "World", "label": "PERSON", "source": "ner"}
    ]
    merged = merge_spans(regex_spans, ner_spans)
    assert len(merged) == 2


def test_merge_spans_regex_priority_on_overlap():
    """Jika regex dan NER overlap pada posisi yang sama, regex harus menang."""
    regex_spans = [
        {"start": 0, "end": 10, "text": "budi@x.com", "label": "EMAIL", "source": "regex"}
    ]
    ner_spans = [
        {"start": 0, "end": 4, "text": "budi", "label": "PERSON", "source": "ner"}
    ]
    merged = merge_spans(regex_spans, ner_spans)
    assert len(merged) == 1
    assert merged[0]["label"] == "EMAIL"


def test_get_statistics():
    spans = [
        {"start": 0, "end": 4, "text": "Budi", "label": "PERSON", "source": "ner"},
        {"start": 10, "end": 14, "text": "Sari", "label": "PERSON", "source": "ner"},
        {"start": 20, "end": 30, "text": "budi@x.com", "label": "EMAIL", "source": "regex"},
    ]
    stats = get_statistics(spans)
    assert stats["PERSON"] == 2
    assert stats["EMAIL"] == 1


def test_mask_preserves_text_outside_spans():
    text = "Halo budi@gmail.com selamat pagi"
    spans = regex_detect(text)
    masked = mask_text(text, spans, mode="specific")
    assert masked.startswith("Halo ")
    assert masked.endswith(" selamat pagi")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
