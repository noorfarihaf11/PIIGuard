# Flowchart Pipeline PrivacyGuard AI

```mermaid
flowchart TD
    A([🟢 MULAI]) --> B[Input Pengguna]

    B --> C{Sumber Input?}
    C -->|Upload File| D{Format File?}
    C -->|Teks Manual| E[Teks Mentah]

    D -->|.txt| F1[Baca langsung UTF-8]
    D -->|.pdf| F2[Ekstraksi via PyMuPDF]
    D -->|.docx| F3[Ekstraksi via python-docx]

    F1 & F2 & F3 --> E

    E --> G["⚙️ TAHAP 2: Tokenisasi\nspaCy blank 'id'\n→ List Token"]

    E --> H["⚙️ TAHAP 3: Regex Detection\n─────────────────\n📧 EMAIL → pola xxx@domain.ext\n📱 PHONE → awalan 08/+62\n🪪 NIK → 16 digit angka\n💰 AMOUNT → Rp X.XXX.XXX\n📄 CONTRACT_ID → XX-YYYYYYY"]

    E --> I["⚙️ TAHAP 4: NER Detection\n─────────────────\n🧠 Model: spaCy xx_ent_wiki_sm\n👤 PERSON → konteks kalimat\n📍 LOCATION → konteks + Gazetteer\n🏢 ORG → konteks + Gazetteer\n\nGazetteer: PT, CV, Universitas,\nJl., Kota, Kabupaten, RSUD, ..."]

    G --> G2[/"Token List\n[Budi, Santoso, bekerja, ...]"/]

    H --> H2[/"Regex Spans\n[{EMAIL, 5-19}, {PHONE, 25-36}, ...]"/]
    I --> I2[/"NER Spans\n[{PERSON, 0-13}, {ORG, 25-40}, ...]"/]

    H2 & I2 --> J["⚙️ TAHAP 5: PII Merging\n─────────────────\n• Gabung Regex + NER spans\n• Jika overlap → Regex menang\n• Span lebih panjang diprioritaskan"]

    J --> K[/"Merged PII Spans\n(tanpa tumpang tindih)"/]

    K --> L{Mode Redaksi?}

    L -->|Spesifik| M1["⚙️ TAHAP 6: Masking\nGanti tiap span dengan\n[PERSON], [EMAIL], [NIK], ..."]
    L -->|Generik| M2["⚙️ TAHAP 6: Masking\nGanti tiap span dengan\n[REDACTED]"]

    M1 & M2 --> N[Teks Teranonimisasi]
    K --> O[Statistik Deteksi PII\nper Kategori]

    G2 & N & O --> P([🔴 SELESAI\nOutput ke UI])
```

## Catatan Penting

| Langkah | Ada? | Keterangan |
|---|---|---|
| Ekstraksi Teks | ✅ | .txt / .pdf / .docx |
| Case Folding | ❌ | Sengaja tidak dilakukan — regex CONTRACT_ID & gazetteer butuh huruf kapital |
| Cleaning / Normalisasi | ❌ | Teks digunakan as-is dari hasil ekstraksi |
| Tokenisasi | ✅ | spaCy blank "id" — output dikembalikan ke UI sebagai informasi tambahan |
| Regex Detection | ✅ | Bekerja pada raw text (bukan token) |
| NER Detection | ✅ | Bekerja pada raw text; model spaCy melakukan tokenisasi internalnya sendiri |
| PII Merging | ✅ | Resolusi overlap dengan prioritas Regex |
| Masking | ✅ | Mode spesifik atau generik |
