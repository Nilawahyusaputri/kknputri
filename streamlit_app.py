import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime, date
import math

# ===================== Fungsi =====================
def hitung_umur(tgl_lahir):
    today = date.today()
    umur_hari = (today - tgl_lahir).days
    tahun = umur_hari // 365
    bulan = (umur_hari % 365) // 30
    hari = (umur_hari % 365) % 30
    umur_bulan = round(umur_hari / 30.44)  # pembulatan ke bulan
    return tahun, bulan, hari, umur_bulan

def load_lms(gender):
    if gender == "Laki-laki":
        df = pd.read_excel("data/hfa-boys-z-who-2007-exp.xlsx")
    else:
        df = pd.read_excel("data/hfa-girls-z-who-2007-exp.xlsx")
    return df[['Month', 'L', 'M', 'S']]

def hitung_zscore(tinggi, umur_bulan, lms_df):
    row = lms_df[lms_df['Month'] == umur_bulan]
    if row.empty:
        return None
    L = float(row['L'])
    M = float(row['M'])
    S = float(row['S'])
    if L == 0:
        z = math.log(tinggi / M) / S
    else:
        z = ((tinggi / M) ** L - 1) / (L * S)
    return round(z, 2)

def get_status(z):
    if z < -3:
        return "Stunting Berat", "stunting"
    elif -3 <= z < -2:
        return "Stunting", "butuh_perhatian"
    elif -2 <= z <= 2:
        return "Normal", "sehat"
    else:
        return "Risiko Overgrowth", "risiko"

def saran_status(status):
    return {
        "Stunting Berat": "Segera periksa ke fasilitas kesehatan. Berikan makanan tinggi protein dan rutin ukur tinggi.",
        "Stunting": "Perhatikan asupan makanan bergizi, rutin pantau pertumbuhan anak.",
        "Normal": "Pertahankan pola makan sehat dan aktif bermain.",
        "Risiko Overgrowth": "Kendalikan konsumsi gula & lemak berlebih, tetap aktif bergerak."
    }[status]

def buat_pdf(nama, umur_str, gender, kelas, berat, tinggi, status, zscore, saran):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Hasil Deteksi Stunting", ln=1, align='C')
    pdf.ln(10)
    pdf.cell(100, 10, txt=f"Nama: {nama}", ln=1)
    pdf.cell(100, 10, txt=f"Umur: {umur_str}", ln=1)
    pdf.cell(100, 10, txt=f"Jenis Kelamin: {gender}", ln=1)
    pdf.cell(100, 10, txt=f"Kelas: {kelas}", ln=1)
    pdf.cell(100, 10, txt=f"Berat Badan: {berat} kg", ln=1)
    pdf.cell(100, 10, txt=f"Tinggi Badan: {tinggi} cm", ln=1)
    pdf.cell(100, 10, txt=f"Z-Score: {zscore}", ln=1)
    pdf.cell(100, 10, txt=f"Status: {status}", ln=1)
    pdf.multi_cell(0, 10, txt=f"Saran: {saran}")
    filename = f"hasil_{nama.replace(' ', '_')}.pdf"
    pdf.output(filename)
    return filename

# ===================== Streamlit App =====================
st.set_page_config(page_title="Deteksi Stunting", layout="wide")
st.title("📏 Deteksi Stunting Anak SD - KKN")

with st.form("form_input"):
    nama = st.text_input("Nama Anak")
    tgl_lahir = st.date_input("Tanggal Lahir")
    gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
    kelas = st.selectbox("Kelas", ["1", "2", "3", "4", "5", "6"])
    berat = st.number_input("Berat Badan (kg)", min_value=5.0, max_value=100.0, step=0.1)
    tinggi = st.number_input("Tinggi Badan (cm)", min_value=50.0, max_value=200.0, step=0.1)
    submitted = st.form_submit_button("Deteksi Sekarang")

if submitted:
    tahun, bulan, hari, umur_bulan = hitung_umur(tgl_lahir)
    umur_str = f"{tahun} tahun {bulan} bulan {hari} hari"
    lms_df = load_lms(gender)
    zscore = hitung_zscore(tinggi, umur_bulan, lms_df)

    if zscore is None:
        st.error("Data LMS untuk umur tersebut tidak tersedia.")
    else:
        status, avatar = get_status(zscore)
        saran = saran_status(status)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Status", status)
            st.write(f"Z-Score: {zscore}")
            st.write(f"Umur: {umur_str}")
            st.write("Saran:")
            st.info(saran)
        with col2:
            avatar_path = f"avatars/{gender.lower()}_{avatar}.png"
            st.image(avatar_path, width=250, caption="Gambaran Anak")

        filename = buat_pdf(nama, umur_str, gender, kelas, berat, tinggi, status, zscore, saran)
        with open(filename, "rb") as f:
            st.download_button("📄 Download Hasil dalam PDF", f, file_name=filename)

        # Simpan ke DataFrame dan tampilkan
        if "data_anak" not in st.session_state:
            st.session_state.data_anak = []
        st.session_state.data_anak.append({
            "Nama": nama,
            "Umur": umur_str,
            "Kelas": kelas,
            "Gender": gender,
            "Berat": berat,
            "Tinggi": tinggi,
            "Z-Score": zscore,
            "Status": status
        })

        df = pd.DataFrame(st.session_state.data_anak)
        st.subheader("📊 Rekapitulasi Deteksi")
        st.dataframe(df, use_container_width=True)

        # Visualisasi
        st.subheader("📈 Grafik Status Berdasarkan Kelas")
        fig, ax = plt.subplots()
        kelas_status = df.groupby(["Kelas", "Status"]).size().unstack().fillna(0)
        kelas_status.plot(kind='bar', stacked=True, ax=ax)
        st.pyplot(fig)

        # Download Dataframe CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Semua Data (CSV)", csv, file_name="rekap_stunting.csv", mime='text/csv')
