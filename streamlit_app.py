import streamlit as st
import pandas as pd
import datetime
import altair as alt
from fpdf import FPDF

# Fungsi hitung umur lengkap
def hitung_umur(tgl_lahir):
    today = datetime.date.today()
    umur = today - tgl_lahir
    tahun = umur.days // 365
    bulan = (umur.days % 365) // 30
    hari = (umur.days % 365) % 30
    umur_bulan = round(umur.days / 30.4375, 1)
    return tahun, bulan, hari, umur_bulan

# Fungsi ambil data WHO
def load_data_who(gender):
    if gender == "Laki-laki":
        return pd.read_excel("hfa-boys-z-who-2007-exp.xlsx")
    else:
        return pd.read_excel("hfa-girls-z-who-2007-exp.xlsx")

# Fungsi analisis status
def analisis_status(tb, umur_bulan, data_who):
    if umur_bulan < 24 or umur_bulan > 228:
        return "Umur di luar jangkauan WHO", "⚠️"
    df = data_who[data_who['Month'] == round(umur_bulan)]
    if df.empty:
        return "Data tidak ditemukan", "❓"
    row = df.iloc[0]
    if tb < row['-2SD']:
        return "Risiko Stunting", "🚨"
    elif tb < row['-1SD']:
        return "Perlu Perhatian", "⚠️"
    elif tb <= row['+1SD']:
        return "Normal & Sehat", "✅"
    else:
        return "Risiko Overgrowth", "📈"

# Fungsi saran bergizi
def get_saran(status):
    saran = {
        "Risiko Stunting": "Perbanyak asupan protein, sayur dan buah. Pantau pertumbuhan secara rutin.",
        "Perlu Perhatian": "Perbaiki pola makan dan tidur. Konsumsi makanan sehat seimbang.",
        "Normal & Sehat": "Pertahankan pola hidup sehat dan rutin olahraga.",
        "Risiko Overgrowth": "Batasi gula & makanan berlemak. Aktif bergerak dan makan teratur.",
    }
    return saran.get(status, "")

# PDF Generator
def buat_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for key, val in data.items():
        pdf.cell(200, 10, txt=f"{key}: {val}", ln=True)
    return pdf.output(dest='S').encode('latin1')

# Tampilan Streamlit
st.set_page_config(page_title="Deteksi Stunting Anak", layout="centered")
st.title("📏 Deteksi Pertumbuhan Anak SD")
st.markdown("Isi data berikut untuk mengetahui status pertumbuhan anak berdasarkan standar WHO.")

nama = st.text_input("Nama Anak")
tgl_lahir = st.date_input("Tanggal Lahir", min_value=datetime.date(2000,1,1), max_value=datetime.date.today())
gender = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
kelas = st.text_input("Kelas")
tinggi = st.number_input("Tinggi Badan (cm)", min_value=30.0, max_value=200.0)
berat = st.number_input("Berat Badan (kg)", min_value=5.0, max_value=100.0)

data_file = "data_anak.csv"

if st.button("🔍 Analisis"):
    if nama and kelas:
        tahun, bulan, hari, umur_bulan = hitung_umur(tgl_lahir)
        umur_text = f"{tahun} tahun, {bulan} bulan, {hari} hari"
        data_who = load_data_who(gender)
        status, ikon = analisis_status(tinggi, umur_bulan, data_who)
        saran = get_saran(status)

        warna = {
            "Risiko Stunting": "#FF6961",
            "Perlu Perhatian": "#FFD700",
            "Normal & Sehat": "#77DD77",
            "Risiko Overgrowth": "#84B6F4"
        }

        st.markdown(f"### Hasil Analisis: {ikon} **{status}**")
        st.markdown(f"🗓️ Umur: **{umur_text}**  \n🍱 Saran: *{saran}*")
        st.markdown(
            f'<div style="background-color:{warna.get(status)};padding:10px;border-radius:10px;color:black;"><b>{status}</b><br>{saran}</div>',
            unsafe_allow_html=True
        )

        # Simpan ke data
        new_data = pd.DataFrame([{
            "Nama": nama, "Tanggal Lahir": tgl_lahir, "Umur": umur_text,
            "Jenis Kelamin": gender, "Kelas": kelas,
            "Tinggi (cm)": tinggi, "Berat (kg)": berat,
            "Status": status, "Saran": saran
        }])
        try:
            existing = pd.read_csv(data_file)
            all_data = pd.concat([existing, new_data], ignore_index=True)
        except FileNotFoundError:
            all_data = new_data
        all_data.to_csv(data_file, index=False)

        # Download PDF
        pdf_binary = buat_pdf(new_data.iloc[0].to_dict())
        st.download_button("📄 Download Hasil PDF", data=pdf_binary, file_name=f"{nama}_hasil.pdf")

# Unduh semua data CSV
if st.button("📥 Download Semua Data CSV"):
    try:
        df_all = pd.read_csv(data_file)
        st.download_button("📊 Unduh Data CSV", data=df_all.to_csv(index=False), file_name="semua_data_anak.csv")
    except FileNotFoundError:
        st.error("Belum ada data disimpan.")

# Grafik batang
st.subheader("📊 Visualisasi Status Pertumbuhan")
try:
    df_all = pd.read_csv(data_file)
    kelas_gb = df_all.groupby(['Kelas', 'Jenis Kelamin', 'Status']).size().reset_index(name='Jumlah')
    pivot_df = kelas_gb.pivot_table(index=['Kelas', 'Jenis Kelamin'], columns='Status', values='Jumlah', fill_value=0).reset_index()

    melted = pivot_df.melt(id_vars=['Kelas', 'Jenis Kelamin'], var_name='Status', value_name='Jumlah')
    chart = alt.Chart(melted).mark_bar().encode(
        x='Kelas:N',
        y='Jumlah:Q',
        color='Status:N',
        column='Jenis Kelamin:N'
    ).properties(width=200, height=300)

    st.altair_chart(chart)
except Exception as e:
    st.info("Belum ada data untuk divisualisasikan.")
