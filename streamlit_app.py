import streamlit as st
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
import os
import re

st.set_page_config(page_title="Deteksi Stunting SD", layout="centered")
st.title("📏 Deteksi Stunting untuk Anak SD")

# Fungsi hitung umur
def hitung_umur(tgl_lahir):
    today = datetime.date.today()
    umur = today - tgl_lahir
    tahun = umur.days // 365
    bulan = (umur.days % 365) // 30
    hari = (umur.days % 365) % 30
    umur_bulan = tahun * 12 + bulan
    return tahun, bulan, hari, umur_bulan

# Fungsi load LMS dari Excel
def load_lms(gender):
    if gender == "Laki-laki":
        df = pd.read_excel("data/hfa-boys-z-who-2007-exp.xlsx")
    else:
        df = pd.read_excel("data/hfa-girls-z-who-2007-exp.xlsx")
    df = df.rename(columns={"Month": "UmurBulan"})
    return df

# Fungsi hitung z-score tinggi badan untuk umur (HFA)
def hitung_zscore(umur_bulan, tinggi, gender):
    lms_df = load_lms(gender)
    row = lms_df[lms_df["UmurBulan"] == umur_bulan]
    if row.empty:
        return None
    L = float(row["L"])
    M = float(row["M"])
    S = float(row["S"])
    z = ((tinggi / M)**L - 1) / (L * S)
    return round(z, 2)

# Fungsi klasifikasi HFA
def klasifikasi_hfa(z):
    if z < -3:
        return "Stunting (Severely)", "stunting"
    elif -3 <= z < -2:
        return "Stunting", "stunting"
    elif -2 <= z <= 2:
        return "Normal", "normal"
    else:
        return "Tinggi", "tinggi"

# Fungsi buat PDF hasil anak
def buat_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Hasil Deteksi Stunting Anak", ln=True, align="C")
    pdf.ln(10)
    for key, value in data.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)
    os.makedirs("pdf", exist_ok=True)
    nama_bersih = re.sub(r'[^a-zA-Z0-9_]', '_', data['Nama Anak'])
    nama_file = f"pdf/Hasil_{nama_bersih}.pdf"
    pdf.output(nama_file)
    return nama_file

# Input Data Anak
with st.form("form_anak"):
    nama = st.text_input("Nama Anak")
    tgl_lahir = st.date_input("Tanggal Lahir")
    gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
    tinggi = st.number_input("Tinggi Badan (cm)", min_value=50.0, max_value=200.0)
    berat = st.number_input("Berat Badan (kg)", min_value=5.0, max_value=100.0)
    kelas = st.text_input("Kelas")
    submit = st.form_submit_button("Deteksi")

# Tempat penyimpanan hasil
if "data_anak" not in st.session_state:
    st.session_state.data_anak = []

# Proses jika tombol ditekan
if submit:
    tahun, bulan, hari, umur_bulan = hitung_umur(tgl_lahir)
    z = hitung_zscore(umur_bulan, tinggi, gender)

    if z is None:
        st.warning("Umur belum tersedia dalam standar WHO.")
    else:
        status, kategori = klasifikasi_hfa(z)

        st.subheader("📊 Hasil Analisis")
        st.write(f"**Umur:** {tahun} tahun {bulan} bulan")
        st.write(f"**Z-score:** {z}")
        st.write(f"**Status:** {status}")

        # Tampilkan avatar
        avatar_path = f"avatars/{kategori}_{'boy' if gender=='Laki-laki' else 'girl'}.png"
        try:
            if os.path.exists(avatar_path):
                with open(avatar_path, "rb") as img_file:
                    st.image(img_file.read(), width=250, caption="Gambaran Anak")
            else:
                st.info("🖼️ Avatar tidak tersedia.")
        except Exception as e:
            st.warning(f"Gagal memuat avatar: {e}")

        hasil_data = {
            "Nama Anak": nama,
            "Tanggal Lahir": tgl_lahir.strftime("%Y-%m-%d"),
            "Jenis Kelamin": gender,
            "Umur (bulan)": umur_bulan,
            "Tinggi Badan (cm)": tinggi,
            "Berat Badan (kg)": berat,
            "Kelas": kelas,
            "Z-score": z,
            "Status": status
        }

        st.session_state.data_anak.append(hasil_data)

        # Buat PDF individual
        pdf_path = buat_pdf(hasil_data)
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download PDF Hasil Anak Ini", f, file_name=os.path.basename(pdf_path))

# Tampilkan Data Semua Anak
if st.session_state.data_anak:
    st.subheader("📋 Data Semua Anak yang Sudah Diperiksa")
    df_all = pd.DataFrame(st.session_state.data_anak)
    st.dataframe(df_all, use_container_width=True)

    csv = df_all.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Semua Data (CSV)", csv, file_name="data_semua_anak.csv", mime="text/csv")
