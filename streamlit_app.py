import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from fpdf import FPDF
import os

# ---------------------------
# Fungsi bantu
# ---------------------------
def hitung_umur(tgl_lahir):
    today = datetime.today()
    umur = today - tgl_lahir
    tahun = umur.days // 365
    bulan = (umur.days % 365) // 30
    hari = (umur.days % 365) % 30
    total_bulan = tahun * 12 + bulan
    return tahun, bulan, hari, total_bulan

def hitung_z_score(nilai, L, M, S):
    if L == 0:
        z = np.log(nilai / M) / S
    else:
        z = ((nilai / M) ** L - 1) / (L * S)
    return z

def get_lms_row(df, umur_bulan):
    closest = df.iloc[(df['Month'] - umur_bulan).abs().argsort()[:1]]
    return closest.iloc[0]

def tentukan_status_hfa(z):
    if z < -3:
        return "Stunting Berat"
    elif z < -2:
        return "Stunting"
    else:
        return "Normal"

def muat_lms_data(gender):
    if gender == 'Laki-laki':
        return pd.read_csv("data/hfa_boys.csv")
    else:
        return pd.read_csv("data/hfa_girls.csv")

def avatar_path(gender, status):
    key = f"{gender.lower()}_{status.lower().replace(' ', '_')}"
    return f"avatars/{key}.png"

def buat_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Hasil Deteksi Stunting", ln=True, align='C')
    pdf.ln(10)

    for key, val in data.items():
        pdf.cell(200, 10, txt=f"{key}: {val}", ln=True)

    out_path = f"hasil_{data['Nama']}.pdf"
    pdf.output(out_path)
    return out_path

# ---------------------------
# Streamlit App
# ---------------------------
st.set_page_config(page_title="Deteksi Stunting SD", layout="centered")
st.title("📏 Deteksi Stunting untuk Anak SD")

st.markdown("---")
st.markdown("### Masukkan Data Anak")

nama = st.text_input("Nama Anak")
kls = st.selectbox("Kelas", ["1", "2", "3", "4", "5", "6"])
gender = st.radio("Jenis Kelamin", ["Laki-laki", "Perempuan"], horizontal=True)
tgl_lahir = st.date_input("Tanggal Lahir")
tinggi = st.number_input("Tinggi Badan Anak (cm)", min_value=50.0, max_value=200.0, step=0.1)

if st.button("🔍 Deteksi Stunting"):
    if nama and tgl_lahir and tinggi:
        tahun, bulan, hari, umur_bulan = hitung_umur(tgl_lahir)
        df_lms = muat_lms_data(gender)
        row = get_lms_row(df_lms, umur_bulan)

        z_hfa = hitung_z_score(tinggi, row['L'], row['M'], row['S'])
        status = tentukan_status_hfa(z_hfa)

        st.success(f"Status: {status} (Z-score = {z_hfa:.2f})")

        # Tampilkan avatar
        path = avatar_path(gender, status)
        if os.path.exists(path):
            st.image(path, width=200)

        # Saran
        st.markdown("### 💡 Saran dan Tips")
        if status == "Normal":
            st.info("Anak tumbuh dengan baik. Pertahankan pola makan sehat dan rutin aktivitas fisik!")
        elif status == "Stunting":
            st.warning("Anak mengalami stunting. Perbaiki pola makan, tambahkan protein hewani, dan kunjungi posyandu/tenaga kesehatan.")
        else:
            st.error("Anak mengalami stunting berat. Butuh intervensi segera dan pemantauan pertumbuhan.")

        # Simpan hasil
        hasil_data = {
            "Nama": nama,
            "Kelas": kls,
            "Jenis Kelamin": gender,
            "Tgl Lahir": str(tgl_lahir),
            "Umur": f"{tahun} th {bulan} bln",
            "Tinggi": f"{tinggi} cm",
            "Z-score HFA": f"{z_hfa:.2f}",
            "Status": status
        }

        if st.checkbox("📄 Download Hasil dalam PDF"):
            pdf_path = buat_pdf(hasil_data)
            with open(pdf_path, "rb") as f:
                st.download_button("📥 Unduh PDF", data=f, file_name=pdf_path)
    else:
        st.error("Lengkapi semua data terlebih dahulu.")
