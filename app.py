"""
app.py
PrivacyGuard AI - Antarmuka Streamlit
Entry point aplikasi: upload dokumen, pilih mode redaksi, lihat hasil
side-by-side, statistik deteksi PII, dan unduh dokumen yang sudah diredaksi.
"""

import streamlit as st
import pandas as pd

from src.pipeline import run_pipeline, run_pipeline_from_bytes

st.set_page_config(
    page_title="PrivacyGuard AI",
    page_icon="🛡️",
    layout="wide",
)

# ── Header ──────────────────────────────────────────────
st.title("🛡️ PrivacyGuard AI")
st.caption(
    "Sistem Redaksi Data Pribadi (PII) pada Dokumen Teks — "
    "Tokenization · Regex Matching · NER · Masking"
)
st.divider()

# ── Sidebar: input & opsi ───────────────────────────────
with st.sidebar:
    st.header("⚙️ Pengaturan")

    input_method = st.radio(
        "Sumber input",
        ["Upload Dokumen", "Tulis / Tempel Teks"],
        index=0,
    )

    mode_label = st.radio(
        "Mode Redaksi",
        ["Label Spesifik ([PERSON], [EMAIL], ...)", "Generik ([REDACTED])"],
        index=0,
    )
    mode = "specific" if mode_label.startswith("Label") else "generic"

    st.divider()
    st.caption(
        "Format file didukung: **.txt**, **.pdf**, **.docx**\n\n"
        "Kategori PII yang dideteksi: PERSON, EMAIL, PHONE, NIK, "
        "LOCATION, ORG, CONTRACT_ID, AMOUNT."
    )

# ── Ambil teks input ─────────────────────────────────────
raw_text = None
filename = None
result = None

if input_method == "Upload Dokumen":
    uploaded_file = st.file_uploader(
        "Unggah dokumen", type=["txt", "pdf", "docx"]
    )
    if uploaded_file is not None:
        filename = uploaded_file.name
        file_bytes = uploaded_file.read()
        try:
            with st.spinner("Mengekstrak teks dari dokumen..."):
                result = run_pipeline_from_bytes(file_bytes, filename, mode=mode)
            raw_text = result["original_text"]
        except Exception as e:
            st.error(f"Gagal memproses dokumen: {e}")
            result = None
else:
    text_input = st.text_area(
        "Tempel teks di sini",
        height=220,
        placeholder=(
            "Contoh:\nNama saya Budi Santoso. Email saya budi@gmail.com. "
            "Saya tinggal di Surabaya. Hubungi saya di 081234567890."
        ),
    )
    if st.button("🔍 Proses Teks", type="primary"):
        if text_input.strip():
            raw_text = text_input
            with st.spinner("Menjalankan pipeline NLP..."):
                result = run_pipeline(text_input, mode=mode)
            filename = "input_manual.txt"
        else:
            st.warning("Silakan masukkan teks terlebih dahulu.")
            result = None
    else:
        result = None

# ── Tampilkan hasil ──────────────────────────────────────
if raw_text is not None and result is not None:

    st.subheader("📄 Perbandingan Dokumen")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Teks Asli**")
        st.text_area("original", result["original_text"], height=320, label_visibility="collapsed")

    with col2:
        st.markdown("**Teks Teranonimisasi**")
        st.text_area("redacted", result["redacted_text"], height=320, label_visibility="collapsed")

    st.divider()

    # ── Statistik ──
    st.subheader("📊 Statistik Deteksi PII")

    stats = result["statistics"]
    total = sum(stats.values())

    if total == 0:
        st.info("Tidak ada PII yang terdeteksi pada dokumen ini.")
    else:
        col_a, col_b = st.columns([1, 1])

        with col_a:
            df_stats = pd.DataFrame(
                [{"Kategori": k, "Jumlah": v} for k, v in stats.items()]
            ).sort_values("Jumlah", ascending=False)
            st.dataframe(df_stats, hide_index=True, use_container_width=True)
            st.metric("Total PII Terdeteksi", total)

        with col_b:
            st.bar_chart(df_stats.set_index("Kategori"))

        with st.expander("🔎 Detail Span PII yang Terdeteksi"):
            df_spans = pd.DataFrame(result["merged_spans"])
            if not df_spans.empty:
                df_spans = df_spans[["label", "text", "start", "end", "source"]]
                df_spans.columns = ["Kategori", "Teks Terdeteksi", "Posisi Awal", "Posisi Akhir", "Sumber Deteksi"]
                st.dataframe(df_spans, hide_index=True, use_container_width=True)

    st.divider()

    # ── Download ──
    st.subheader("⬇️ Unduh Hasil")
    out_name = (filename.rsplit(".", 1)[0] if filename else "dokumen") + "_redacted.txt"
    st.download_button(
        label="Unduh Dokumen Teranonimisasi (.txt)",
        data=result["redacted_text"],
        file_name=out_name,
        mime="text/plain",
    )

else:
    st.info("👈 Unggah dokumen atau tempel teks pada sidebar untuk memulai.")

    st.divider()
    st.subheader("ℹ️ Cara Kerja Sistem Deteksi PII")
    st.markdown(
        "PrivacyGuard AI menjalankan **pipeline NLP 6 tahap**: "
        "Ekstraksi Teks → Tokenisasi → Regex Detection → NER Detection → PII Merging → Masking. "
        "Setiap kategori PII ditangani oleh metode yang paling sesuai dengan karakteristiknya — "
        "ada yang cukup dengan pola karakter, ada yang butuh pemahaman konteks kalimat."
    )

    st.divider()

    # ── Metode 1: Regex ──────────────────────────────────────
    st.markdown("### Metode 1 — Regex (Rule-Based Pattern Matching)")
    st.markdown(
        "Digunakan untuk PII yang memiliki **format baku dan tidak ambigu**. "
        "Deteksi dilakukan murni berdasarkan pola karakter tanpa perlu memahami konteks kalimat. "
        "Jika polanya cocok, entitas langsung ditandai — deterministik dan cepat."
    )

    _regex_items = [
        (
            "[EMAIL]", "budi@gmail.com", "xxx@domain.ext",
            "Email selalu mengandung `@` dan memiliki struktur domain yang jelas. "
            "Tidak ada kata biasa yang mengandung `@`, sehingga tidak ada risiko salah deteksi.",
        ),
        (
            "[PHONE]", "081234567890", "08xx / +62xx (7–11 digit)",
            "Nomor HP Indonesia selalu diawali `08`, `+62`, atau `628`. "
            "Awalan ini sangat spesifik sehingga pola karakter sudah cukup untuk identifikasi.",
        ),
        (
            "[NIK]", "3578012345670001", "Tepat 16 digit angka",
            "NIK selalu terdiri dari 16 digit angka berturut-turut. "
            "Panjang yang tetap dan format yang tidak ambigu menjadikannya ideal untuk regex.",
        ),
        (
            "[CONTRACT_ID]", "PKS-20241001", "2–5 huruf kapital + tanda '-' + angka",
            "Nomor kontrak mengikuti konvensi kode alfanumerik berpola. "
            "Format seperti `PKS-2024xxxx` konsisten dan mudah dibedakan dari teks biasa.",
        ),
        (
            "[AMOUNT]", "Rp 75.000.000", "Rp diikuti angka format ribuan IDR",
            "Nilai uang Rupiah selalu diawali `Rp` dengan format pemisah ribuan yang khas. "
            "Awalan `Rp` menjadi penanda deterministik yang tidak ditemukan di konteks lain.",
        ),
    ]

    for label, contoh, pola, penjelasan in _regex_items:
        with st.expander(f"**{label}** — contoh: `{contoh}`"):
            c1, c2 = st.columns([1, 2])
            c1.markdown(f"**Pola yang dicari**\n\n`{pola}`")
            c2.markdown(f"**Mengapa Regex?**\n\n{penjelasan}")

    st.divider()

    # ── Metode 2: NER + Gazetteer ─────────────────────────────
    st.markdown("### Metode 2 — NER + Gazetteer (Named Entity Recognition)")
    st.markdown(
        "Digunakan untuk PII yang **tidak memiliki pola karakter yang bisa diandalkan** "
        "dan bergantung pada pemahaman konteks kalimat. "
        "Model NER spaCy (`xx_ent_wiki_sm`, dilatih pada data multibahasa termasuk Indonesia) "
        "mengenali entitas berdasarkan posisi dan hubungannya dalam kalimat. "
        "**Gazetteer** (kamus kata kunci) ditambahkan untuk meningkatkan recall pada istilah "
        "khas Indonesia yang sering luput dari model."
    )

    _ner_items = [
        (
            "[PERSON]", "Budi Santoso, Siti Rahma", "NER",
            "Nama orang tidak memiliki pola karakter khusus — `Budi` atau `Maju` bisa muncul "
            "sebagai nama orang maupun kata biasa (`maju` = berkembang). "
            "Model NER membaca konteks: *\"Nama saya Budi\"* → `Budi` dikenali sebagai PERSON "
            "karena posisinya setelah frasa penanda subjek.",
        ),
        (
            "[LOCATION]", "Surabaya, Jl. Merdeka No. 10", "NER + Gazetteer",
            "Nama kota dan provinsi Indonesia sangat bervariasi dan tidak berpola secara karakter. "
            "NER mengenali `Surabaya` dari konteks kalimat, sementara Gazetteer menambah pola "
            "eksplisit seperti `Jl.`, `Kota`, `Kabupaten`, `Kecamatan` untuk alamat yang sering "
            "luput dari model.",
        ),
        (
            "[ORG]", "PT Maju Bersama, Universitas Airlangga", "NER + Gazetteer",
            "Nama organisasi terlalu bervariasi untuk dipola dengan regex. "
            "Gazetteer mendeteksi awalan khas Indonesia seperti `PT`, `CV`, `Universitas`, `RSUD`, "
            "`Kementerian`, `Dinas` lalu mengambil rangkaian kata yang mengikutinya sebagai nama org.",
        ),
    ]

    for label, contoh, metode, penjelasan in _ner_items:
        with st.expander(f"**{label}** — contoh: `{contoh}`"):
            c1, c2 = st.columns([1, 2])
            c1.markdown(f"**Metode deteksi**\n\n`{metode}`")
            c2.markdown(f"**Mengapa bukan Regex?**\n\n{penjelasan}")

    st.divider()

    # ── Prioritas & Merge ─────────────────────────────────────
    st.markdown("### Penggabungan Hasil (PII Merging)")
    st.markdown(
        "Hasil Regex dan NER digabungkan. Jika keduanya mendeteksi entitas yang **tumpang tindih "
        "pada posisi yang sama**, **Regex menang** — karena pola deterministik lebih presisi "
        "dibanding inferensi kontekstual NER. Span yang lebih panjang juga diprioritaskan "
        "untuk menghindari deteksi parsial (misal: `Universitas Airlangga` lebih baik dari sekadar `Airlangga`)."
    )

st.divider()
st.caption("PrivacyGuard AI — Proyek UAS NLP — Kelompok 4 — D4 Teknik Informatika, Universitas Airlangga")
