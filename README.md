# PrivacyGuard AI

Sistem Redaksi Data Pribadi (PII) pada Dokumen Teks menggunakan Tokenization,
Regex Matching, dan Named Entity Recognition (NER).

Proyek UAS — Mata Kuliah Natural Language Processing
D4 Teknik Informatika, Fakultas Vokasi, Universitas Airlangga — Kelompok 4

## Instalasi

```bash
# 1. Buat virtual environment (opsional tapi disarankan)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download model spaCy untuk NER multi-language
python -m spacy download xx_ent_wiki_sm

# 4. Download model tokenizer blank Bahasa Indonesia (otomatis tersedia di spaCy core,
#    tidak perlu download tambahan)
```

## Menjalankan Aplikasi

```bash
streamlit run app.py
```

Aplikasi akan terbuka otomatis di browser pada `http://localhost:8501`.

## Menjalankan Pipeline via CLI (tanpa UI)

```bash
python -m src.pipeline
```

## Menjalankan Unit Test

```bash
pip install pytest
pytest tests/test_pipeline.py -v
```

## Struktur Folder

```
privacyguard-ai/
├── app.py                  # Entry point Streamlit
├── requirements.txt
├── src/
│   ├── extractor.py        # Tahap 1: Text extraction (PDF, DOCX, TXT)
│   ├── tokenizer.py        # Tahap 2: Tokenization
│   ├── regex_detector.py   # Tahap 3: Rule-based PII detection
│   ├── ner_detector.py     # Tahap 4: spaCy NER detection
│   ├── masker.py           # Tahap 5 & 6: Merging + Masking
│   └── pipeline.py         # Orchestrator seluruh tahapan
├── data/
│   ├── sample_docs/        # Dokumen dummy untuk testing/demo
│   └── output/             # (opsional) hasil redaksi tersimpan
└── tests/
    └── test_pipeline.py    # Unit test per modul
```

## Catatan Penting: Model NER

spaCy tidak menyediakan model resmi bernama `id_core_news_sm`. Untuk bahasa
Indonesia, model resmi yang tersedia adalah `xx_ent_wiki_sm` (model
multi-language berbasis Wikipedia, label: PER, LOC, MISC).

Karena recall model ini masih terbatas pada teks Bahasa Indonesia informal,
`ner_detector.py` menambahkan lapisan **gazetteer matching** (pencocokan kata
kunci) untuk pola organisasi (PT, CV, Universitas, dst.) dan lokasi
administratif (Jl., Kota, Kabupaten, dst.) yang umum dijumpai pada dokumen
kerja di Indonesia.

Jika ingin akurasi NER yang lebih tinggi, alternatif pengembangan lanjutan
dapat menggunakan model IndoBERT NER dari HuggingFace (lihat referensi
penelitian terkait pada laporan, Bab II).

## Kategori PII yang Dideteksi

| Kategori | Label | Metode Deteksi |
|---|---|---|
| Nama Orang | `[PERSON]` | NER |
| Lokasi/Alamat | `[LOCATION]` | NER + Gazetteer |
| Organisasi | `[ORG]` | NER + Gazetteer |
| Email | `[EMAIL]` | Regex |
| Nomor HP | `[PHONE]` | Regex |
| NIK | `[NIK]` | Regex |
| Nomor Kontrak | `[CONTRACT_ID]` | Regex |
| Nilai Uang (IDR) | `[AMOUNT]` | Regex |
