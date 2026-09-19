import sqlite3
import pandas as pd
import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Sistem ve Parça Bakım Takip", page_icon="🛠️", layout="wide"
)

st.title("🛠️ Sistem ve Parça Bakım Takip Paneli")
st.markdown("---")


# --- VERİTABANI BAĞLANTISI VE TABLOLAR ---
def get_connection():
  conn = sqlite3.connect("sistem_takip.db")
  return conn


def init_db():
  conn = get_connection()
  cursor = conn.cursor()

  # 1. Sistemler Tablosu
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS sistemler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bolge TEXT,
            sistem_adi TEXT NOT NULL,
            durum TEXT,
            aciklama TEXT,
            tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

  # 2. Parça Takip Tablosu
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS parcalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sistem_id INTEGER,
            parca_adi TEXT NOT NULL,
            seri_no TEXT,
            durum TEXT,
            notlar TEXT,
            FOREIGN KEY(sistem_id) REFERENCES sistemler(id)
        )
    """)

  # 3. Günlük İş Notları / Log Tablosu
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS notlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            baslik TEXT,
            icerik TEXT
        )
    """)
  conn.commit()
  conn.close()


init_db()
conn = get_connection()

# --- SEKMELER (TABS) ---
tab1, tab2, tab3, tab4 = st.tabs(
    ["💻 Sistemler", "🔧 Parça Takip", "📝 Günlük İş Notları", "🔍 Detaylı Arama"]
)

# ----------------- SEKME 1: SİSTEMLER -----------------
with tab1:
  st.subheader("Bölgeler Bazlı Sistem Yönetimi")

  col1, col2 = st.columns(2)
  with col1:
    with st.form("yeni_sistem_form"):
      st.markdown("### Yeni Sistem Ekle")
      bolge = st.text_input("Bölge / Lokasyon")
      sistem_adi = st.text_input("Sistem Adı")
      durum = st.selectbox(
          "Durum", ["Aktif", "Bakımda", "Arızalı", "Yedekte"]
      )
      aciklama = st.text_area("Açıklama")
      kaydet = st.form_submit_button("Sistemi Kaydet")

      if kaydet and sistem_adi:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sistemler (bolge, sistem_adi, durum, aciklama) VALUES"
            " (?, ?, ?, ?)",
            (bolge, sistem_adi, durum, aciklama),
        )
        conn.commit()
        st.success("Sistem başarıyla eklendi!")
        st.rerun()

  with col2:
    st.markdown("### Kayıtlı Sistem Listesi")
    df_sistemler = pd.read_sql_query(
        "SELECT * FROM sistemler ORDER BY id DESC", conn
    )
    if not df_sistemler.empty:
      st.dataframe(df_sistemler, use_container_width=True)

      sil_id = st.selectbox(
          "Silinecek Sistem ID", [0] + list(df_sistemler["id"]), key="sil_sistem"
      )
      if sil_id != 0 and st.button("Seçili Sistemi Sil"):
        c = conn.cursor()
        c.execute("DELETE FROM sistemler WHERE id = ?", (sil_id,))
        conn.commit()
        st.warning(f"Sistem ID {sil_id} silindi.")
        st.rerun()
    else:
      st.info("Kayıtlı sistem bulunmuyor.")

# ----------------- SEKME 2: PARÇA TAKİP -----------------
with tab2:
  st.subheader("Donanım ve Parça Envanteri")

  df_sis = pd.read_sql_query("SELECT id, sistem_adi FROM sistemler", conn)

  if not df_sis.empty:
    sistem_secenekleri = dict(zip(df_sis["sistem_adi"], df_sis["id"]))

    with st.form("parca_form"):
      secilen_sistem = st.selectbox(
          "Bağlı Olduğu Sistem", list(sistem_secenekleri.keys())
      )
      parca_adi = st.text_input("Parça / Bileşen Adı")
      seri_no = st.text_input("Seri Numarası")
      parca_durum = st.selectbox(
          "Parça Durumu", ["Sağlam", "Değişmesi Gerekiyor", "Arızalı"]
      )
      parca_not = st.text_area("Parça Notları / Termal Tarihi vb.")
      parca_kaydet = st.form_submit_button("Parçayı Kaydet")

      if parca_kaydet and parca_adi:
        s_id = sistem_secenekleri[secilen_sistem]
        c = conn.cursor()
        c.execute(
            "INSERT INTO parcalar (sistem_id, parca_adi, seri_no, durum,"
            " notlar) VALUES (?, ?, ?, ?, ?)",
            (s_id, parca_adi, seri_no, parca_durum, parca_not),
        )
        conn.commit()
        st.success("Parça eklendi!")
        st.rerun()

    st.markdown("---")
    st.markdown("### Tüm Parçalar")
    df_parcalar = pd.read_sql_query(
        """
            SELECT p.id, s.sistem_adi, p.parca_adi, p.seri_no, p.durum, p.notlar 
            FROM parcalar p 
            LEFT JOIN sistemler s ON p.sistem_id = s.id
        """,
        conn,
    )
    if not df_parcalar.empty:
      st.dataframe(df_parcalar, use_container_width=True)
    else:
      st.info("Kayıtlı parça yok.")
  else:
    st.warning("Önce 'Sistemler' sekmesinden bir sistem eklemelisiniz.")

# ----------------- SEKME 3: GÜNLÜK İŞ NOTLARI -----------------
with tab3:
  st.subheader("Günlük Bakım ve İş Notları")

  with st.form("not_form"):
    baslik = st.text_input("Not Başlığı / Konu")
    icerik = st.text_area("İş Detayları / Notlar")
    not_kaydet = st.form_submit_button("Notu Kaydet")

    if not_kaydet and baslik:
      c = conn.cursor()
      c.execute(
          "INSERT INTO notlar (baslik, icerik) VALUES (?, ?)", (baslik, icerik)
      )
      conn.commit()
      st.success("Not eklendi!")
      st.rerun()

  df_notlar = pd.read_sql_query(
      "SELECT * FROM notlar ORDER BY tarih DESC", conn
  )
  if not df_notlar.empty:
    for index, row in df_notlar.iterrows():
      with st.expander(f"📌 {row['baslik']} ({row['tarih']})"):
        st.write(row["icerik"])
  else:
    st.info("Henüz günlük not eklenmemiş.")

# ----------------- SEKME 4: DETAYLI ARAMA -----------------
with tab4:
  st.subheader("Hızlı Arama ve Filtreleme")
  kelime = st.text_input(
      "Aramak istediğiniz kelime (Sistem, parça veya açıklama içinde):"
  )

  if kelime:
    q = f"%{kelime}%"
    res_sistem = pd.read_sql_query(
        "SELECT * FROM sistemler WHERE sistem_adi LIKE ? OR bolge LIKE ? OR"
        " aciklama LIKE ?",
        conn,
        params=(q, q, q),
    )
    st.markdown("### Sistem Sonuçları")
    if not res_sistem.empty:
      st.dataframe(res_sistem, use_container_width=True)
    else:
      st.info("Eşleşen sistem bulunamadı.")

conn.close()