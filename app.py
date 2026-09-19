import sqlite3
import pandas as pd
import streamlit as st

# Sayfa Ayarları
st.set_page_config(
    page_title="Sistem ve Parça Takip", page_icon="💻", layout="wide"
)

st.title("💻 Sistem ve Parça Takip Uygulaması")
st.markdown("---")


# --- VERİTABANI BAĞLANTISI ---
def get_connection():
  conn = sqlite3.connect("sistem_takip.db")
  return conn


def init_db():
  conn = get_connection()
  cursor = conn.cursor()
  # Örnek Tablo: Sistemler
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS sistemler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sistem_adi TEXT NOT NULL,
            kategori TEXT,
            durum TEXT,
            aciklama TEXT,
            tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
  conn.commit()
  conn.close()


# Veritabanını başlat
init_db()

# --- KENAR ÇUCUĞU (MENÜ) ---
menu = st.sidebar.selectbox(
    "Menü",
    ["Sistemleri Listele", "Yeni Sistem Ekle", "Parça / Stok Durumu", "Arama"],
)

conn = get_connection()

if menu == "Sistemleri Listele":
  st.subheader("📋 Kayıtlı Sistemler")

  # Verileri oku
  df = pd.read_sql_query(
      "SELECT * FROM sistemler ORDER BY id DESC", conn
  )

  if not df.empty:
    st.dataframe(df, use_container_width=True)

    # Silme İşlemi için Seçim
    silinecek_id = st.selectbox(
        "Silmek İstediğiniz Kaydın ID Numarası", options=[0] + list(df["id"])
    )
    if silinecek_id != 0:
      if st.button("Seçili Kaydı Sil"):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sistemler WHERE id = ?", (silinecek_id,))
        conn.commit()
        st.success(f"ID {silinecek_id} başarıyla silindi!")
        st.rerun()
  else:
    st.info(
        "Henüz kayıtlı bir sistem yok. Sol menüden 'Yeni Sistem Ekle' diyerek"
        " başlayabilirsin."
    )

elif menu == "Yeni Sistem Ekle":
  st.subheader("➕ Yeni Sistem / Cihaz Ekle")

  with st.form("yeni_sistem_formu"):
    sistem_adi = st.text_input("Sistem / Cihaz Adı")
    kategori = st.selectbox(
        "Kategori",
        ["Bilgisayar / Sunucu", "Ağ Cihazı", "Parça / Donanım", "Diğer"],
    )
    durum = st.selectbox(
        "Durum", ["Aktif / Çalışıyor", "Bakımda", "Arızalı", "Depoda"]
    )
    aciklama = st.text_area("Açıklama / Notlar")

    submit_button = st.form_submit_button(label="Kaydet")

    if submit_button:
      if sistem_adi.strip() != "":
        cursor = conn.cursor()
        cursor.execute(
            """
                    INSERT INTO sistemler (sistem_adi, kategori, durum, aciklama)
                    VALUES (?, ?, ?, ?)
                """,
            (sistem_adi, kategori, durum, aciklama),
        )
        conn.commit()
        st.success("Sistem başarıyla kaydedildi!")
      else:
        st.error("Lütfen sistem adını boş bırakmayın.")

elif menu == "Parça / Stok Durumu":
  st.subheader("🔧 Parça ve Donanım Durumu")
  st.write(
      "Burada donanım bileşenlerini, termal macun değişim tarihlerini veya yedek"
      " parçaları takip edebilirsin."
  )
  # İhtiyacına göre buraya parça tablosu da ekleyebiliriz.
  df = pd.read_sql_query("SELECT * FROM sistemler", conn)
  if not df.empty:
    st.metric(
        label="Toplam Kayıtlı Cihaz/Bileşen", value=len(df)
    )

elif menu == "Arama":
  st.subheader("🔍 Hızlı Arama")
  arama_kelimesi = st.text_input("Aramak istediğiniz kelimeyi girin:")

  if arama_kelimesi:
    query = "SELECT * FROM sistemler WHERE sistem_adi LIKE ? OR aciklama LIKE ?"
    arama_param = f"%{arama_kelimesi}%"
    df_sonuc = pd.read_sql_query(
        query, conn, params=(arama_param, arama_param)
    )

    if not df_sonuc.empty:
      st.success(f"{len(df_sonuc)} sonuç bulundu:")
      st.dataframe(df_sonuc, use_container_width=True)
    else:
      st.warning("Eşleşen kayıt bulunamadı.")

conn.close()