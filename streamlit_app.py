import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
import os

# Fungsi menghitung umur dan umur dalam bulan
def hitung_umur(tgl_lahir):
    today = date.today()
    umur = today - tgl_lahir
    tahun = umur.days // 365
    bulan = (umur.days % 365) // 30
    hari = (umur.days % 365) % 30
    umur_bulan = tahun * 12 + bulan
    return tahun, bulan, hari, umur_bulan

# Fungsi memuat data LMS dari file Excel
def load_lms(gender):
    if gender == "Laki-laki":
        df = pd.read_excel("data/hfa_boys.xlsx")
    else:
        df = pd.read_excel("data/hfa_girls.xlsx")
    return df[['Month', 'L', 'M', 'S']]

# Fungsi menghitung Z-Score menggunakan rumus WHO LMS
def hitung_zscore(l, m, s, nilai):
    if l == 0:
        return np.log(nilai / m) / s
    else:
        return ((nilai / m)**l - 1) / (l * s)

# Fungsi menentukan status gizi berdasarkan Z-Score HFA
def interpretasi_hfa(z):
    if z < -3:
        return "Stunting"
    elif -3 <= z < -2:
        return "Butuh Perhatian"
    elif -2 <= z <= 2:
        return "Tumbuh Baik"
    else:
        return "Risiko Overheight"

# Fungsi memilih avatar berdasarkan gender dan status
def pilih_avatar(gender, status):
    filename = f"avatars/{gender.lower()}_{status.lower().replace(' ', '_')}.png"
    if os.path.exists(filename):
        return filename
    else:
        return None

# Fungsi saran berdasarkan status
def saran_status(status):
    if status == "Stunting":
        return "Perbanyak konsumsi makanan bergizi, terutama protein hewani dan rutin cek ke posyandu."
    elif status == "Butuh Perhatian":
        return "Perhatikan asupan harian dan pastikan tidur cukup serta aktif bergerak."
    elif status == "Tumbuh Baik":
        return "Pertahankan pola makan sehat dan gaya hidup aktif."
    elif status == "Risiko Overheight":
        return "Tidak umum, tapi pastikan pertumbuhan seimbang dan konsultasikan ke tenaga kesehatan."

# Fungsi membuat PDF hasil
def buat_pdf(nama, gender, umur_text, tinggi, zscore, status, saran):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "HASIL DETEKSI STUNTING", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Nama: {nama}", ln=True)
    pdf.cell(200, 10, f"Jenis Kelamin: {gender}", ln=True)
    pdf.cell(200, 10, f"Umur: {umur_text}", ln=True)
    pdf.cell(200, 10, f"Tinggi Badan: {tinggi} cm", ln=True)
    pdf.cell(200, 10, f"Z-Score HFA: {zscore:.2f}", ln=True)
    pdf.cell(200, 10, f"Status: {status}", ln=True)
    pdf.multi_cell(0, 10, f"Saran: {saran}")
    filepath = f"hasil_pdf/{nama.replace(' ', '_')}.pdf"
    os.makedirs("hasil_pdf", exist_ok=True)
    pdf.output(filepath)
    return filepath

# Streamlit App
st.set_page_config(page_title="Deteksi Stunting SD", layout="wide")
st.title("📏 Aplikasi Deteksi Stunting Anak SD")

# Input Form
with st.form("form_anak"):
    nama = st.text_input("Nama Anak")
    gender = st.radio("Jenis Kelamin", ["Laki-laki", "Perempuan"])
    tgl_lahir = st.date_input("Tanggal Lahir", min_value=date(2010, 1, 1))
    tinggi = st.number_input("Tinggi Badan (cm)", min_value=50.0, max_value=200.0, step=0.1)
    submit = st.form_submit_button("Deteksi")

if submit:
    tahun, bulan, hari, umur_bulan = hitung_umur(tgl_lahir)
    umur_text = f"{tahun} tahun {bulan} bulan {hari} hari"
    lms_data = load_lms(gender)

    if umur_bulan not in lms_data['Month'].values:
        st.error("Umur dalam bulan tidak tersedia dalam standar WHO.")
    else:
        row = lms_data[lms_data['Month'] == umur_bulan].iloc[0]
        zscore = hitung_zscore(row['L'], row['M'], row['S'], tinggi)
        status = interpretasi_hfa(zscore)
        saran = saran_status(status)
        avatar_path = pilih_avatar(gender, status)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"### 👶 Nama: {nama}")
            st.markdown(f"- Jenis Kelamin: {gender}")
            st.markdown(f"- Umur: {umur_text}")
            st.markdown(f"- Tinggi Badan: {tinggi} cm")
            st.markdown(f"- Z-Score: {zscore:.2f}")
            st.markdown(f"- **Status: {status}**")
            st.info(saran)

        with col2:
            if avatar_path:
                st.image(avatar_path, width=200)
            else:
                st.markdown("*(Avatar belum tersedia)*")

        pdf_path = buat_pdf(nama, gender, umur_text, tinggi, zscore, status, saran)
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Download Hasil PDF", f, file_name=os.path.basename(pdf_path))
