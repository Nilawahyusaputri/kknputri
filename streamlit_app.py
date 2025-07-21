import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, date
from fpdf import FPDF
import os

# ===========================
# Fungsi bantu
# ===========================
def hitung_umur(tgl_lahir: str):
    tgl_lahir = datetime.strptime(tgl_lahir, "%Y-%m-%d")
    today = date.today()
    delta = today - tgl_lahir.date()
    tahun = delta.days // 365
    bulan = (delta.days % 365) // 30
    hari = (delta.days % 365) % 30
    umur_bulan = delta.days // 30
    return tahun, bulan, hari, umur_bulan

def load_lms(gender):
    if gender == 'Laki-laki':
        df = pd.read_csv("data/hfa_boys.csv")
    else:
        df = pd.read_csv("data/hfa_girls.csv")
    return df[['Month', 'L', 'M', 'S']]

def z_score(nilai, L, M, S):
    if L == 0:
        return np.log(nilai / M) / S
    else:
        return ((nilai / M) ** L - 1) / (L * S)

def get_status_hfa(z):
    if z < -3:
        return "Stunting Berat"
    elif z < -2:
        return "Stunting"
    else:
        return "Normal"

def get_avatar(gender, status):
    base = gender.lower().replace("-", "")
    status = status.lower().replace(" ", "_")
    file_name = f"avatars/{base}_{status}.png"
    return file_name if os.path.exists(file_name) else None

def saran_status(status):
    if status == "Stunting Berat":
        return "Segera konsultasikan dengan petugas kesehatan. Berikan asupan gizi tinggi dan seimbang."
    elif status == "Stunting":
        return "Perhatikan pola makan dan asupan gizi anak. Tingkatkan konsumsi makanan kaya protein dan vitamin."
    else:
        return "Pertahankan pola hidup sehat dan gizi seimbang agar tumbuh kembang tetap optimal."

def buat_pdf(nama, kelas, umur, tinggi, gender, status, saran):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Hasil Deteksi Stunting", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Nama: {nama}", ln=True)
    pdf.cell(200, 10, txt=f"Kelas: {kelas}", ln=True)
    pdf.cell(200, 10, txt=f"Umur: {umur}", ln=True)
    pdf.cell(200, 10, txt=f"Jenis Kelamin: {gender}", ln=True)
    pdf.cell(200, 10, txt=f"Tinggi Badan: {tinggi} cm", ln=True)
    pdf.cell(200, 10, txt=f"Status HFA: {status}", ln=True)
    pdf.multi_cell(0, 10, txt=f"Saran: {saran}")
    pdf_path = f"hasil_{nama.replace(' ', '_')}.pdf"
    pdf.output(pdf_path)
    return pdf_path

# ===========================
# Streamlit App
# ===========================
st.set_page_config(page_title="Deteksi Stunting Anak SD", layout="centered")
st.title("📊 Deteksi Stunting Anak SD")

with st.form("form_input"):
    nama = st.text_input("Nama Anak")
    kelas = st.selectbox("Kelas", ["1", "2", "3", "4", "5", "6"])
    gender = st.radio("Jenis Kelamin", ["Laki-laki", "Perempuan"])
    tgl_lahir = st.date_input("Tanggal Lahir", min_value=date(2010,1,1), max_value=date.today())
    tinggi = st.number_input("Tinggi Badan (cm)", min_value=50.0, max_value=200.0, step=0.1)
    submit = st.form_submit_button("Deteksi")

if submit:
    tahun, bulan, hari, umur_bulan = hitung_umur(str(tgl_lahir))
    umur_str = f"{tahun} tahun {bulan} bulan {hari} hari"
    lms_data = load_lms(gender)
    row = lms_data[lms_data['Month'] == umur_bulan]

    if row.empty:
        st.error("Umur anak di luar rentang referensi WHO.")
    else:
        L = float(row['L'].values[0])
        M = float(row['M'].values[0])
        S = float(row['S'].values[0])
        z = z_score(tinggi, L, M, S)
        status = get_status_hfa(z)
        saran = saran_status(status)

        col1, col2 = st.columns([1,2])
        with col1:
            avatar = get_avatar(gender, status)
            if avatar:
                st.image(avatar, width=150)
        with col2:
            st.subheader(f"Status: {status}")
            st.markdown(f"**Umur:** {umur_str}")
            st.markdown(f"**Z-Score HFA:** {z:.2f}")
            st.markdown(f"**Saran:** {saran}")

        # Simpan hasil ke tabel global
        if "hasil_data" not in st.session_state:
            st.session_state.hasil_data = []

        st.session_state.hasil_data.append({
            "Nama": nama,
            "Kelas": kelas,
            "Jenis Kelamin": gender,
            "Umur": umur_str,
            "Tinggi": tinggi,
            "Z-score HFA": round(z, 2),
            "Status": status
        })

        pdf_path = buat_pdf(nama, kelas, umur_str, tinggi, gender, status, saran)
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Unduh Hasil PDF", f, file_name=pdf_path)

if "hasil_data" in st.session_state:
    st.subheader("📋 Data Anak yang Telah Diperiksa")
    df = pd.DataFrame(st.session_state.hasil_data)
    st.dataframe(df, use_container_width=True)

    st.subheader("📊 Grafik Berdasarkan Status")
    fig, ax = plt.subplots()
    df["Status"].value_counts().plot(kind="bar", color="skyblue", ax=ax)
    ax.set_ylabel("Jumlah Anak")
    ax.set_title("Distribusi Status HFA")
    st.pyplot(fig)
