import datetime
import io
import os
import shutil
import sqlite3
import traceback
import pandas as pd
import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Sistem ve Parça Takip Sistemi", page_icon="⚙️", layout="wide"
)

try:
  DB_DOSYASI = "sistem_takip.db"
  UPLOAD_FOLDER = "yuklenen_dosyalar"
  AUTOSAVE_FOLDER = "otomatik_yedekler"

  for folder in [UPLOAD_FOLDER, AUTOSAVE_FOLDER]:
    if not os.path.exists(folder):
      os.makedirs(folder)

  # --- TÜRKÇE BÜYÜK HARF DÖNÜŞÜMÜ ---
  def tr_upper(text):
    if not isinstance(text, str):
      return str(text) if text is not None else ""
    return (
        text.replace("i", "İ")
        .replace("ı", "I")
        .replace("ş", "Ş")
        .replace("ğ", "Ğ")
        .replace("ü", "Ü")
        .replace("ö", "Ö")
        .replace("ç", "Ç")
        .upper()
    )

  # --- OTOMATİK EXCEL YEDEKLEME FONKSİYONU ---
  def otomatik_yedekle():
    """Her veri işleminde verilerin otomatik Excel yedeğini alır (Son 10 yedek saklanır)."""
    try:
      timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
      backup_path = os.path.join(AUTOSAVE_FOLDER, f"autosave_{timestamp}.xlsx")
      latest_backup = os.path.join(
          AUTOSAVE_FOLDER, "sistem_takip_latest_autosave.xlsx"
      )

      with sqlite3.connect(DB_DOSYASI) as conn:
        df_p = pd.read_sql_query("SELECT * FROM parcalar", conn)
        df_n = pd.read_sql_query("SELECT * FROM gunluk_notlar", conn)
        df_l = pd.read_sql_query("SELECT * FROM islem_loglari", conn)
        df_g = pd.read_sql_query("SELECT * FROM parca_gecmis", conn)

      with pd.ExcelWriter(backup_path, engine="openpyxl") as writer:
        df_p.to_excel(writer, sheet_name="Parcalar", index=False)
        df_n.to_excel(writer, sheet_name="Gunluk_Notlar", index=False)
        df_l.to_excel(writer, sheet_name="Loglar", index=False)
        df_g.to_excel(writer, sheet_name="Parca_Gecmisi", index=False)

      shutil.copy2(backup_path, latest_backup)

      # Son 10 otomatik Excel yedeğini tut, eskileri temizle
      yedekler = sorted(
          [
              os.path.join(AUTOSAVE_FOLDER, f)
              for f in os.listdir(AUTOSAVE_FOLDER)
              if f.startswith("autosave_") and f.endswith(".xlsx")
          ],
          key=os.path.getmtime,
      )
      if len(yedekler) > 10:
        for eski_yedek in yedekler[:-10]:
          os.remove(eski_yedek)
    except Exception as ex:
      print(f"Otomatik Excel yedekleme hatası: {ex}")

  # --- TARİH DÖNÜŞÜM YARDIMCILARI ---
  def str_to_date(tarih_str):
    if not tarih_str or pd.isna(tarih_str):
      return datetime.date.today()
    try:
      return datetime.datetime.strptime(
          str(tarih_str).strip(), "%d.%m.%Y"
      ).date()
    except ValueError:
      return datetime.date.today()

  # --- VERİTABANI BAŞLATMA VE MIGRATION ---
  def veritabanini_hazirla():
    with sqlite3.connect(DB_DOSYASI) as conn:
      cursor = conn.cursor()
      cursor.execute(
          "CREATE TABLE IF NOT EXISTS parcalar (id INTEGER PRIMARY KEY"
          " AUTOINCREMENT)"
      )
      cursor.execute(
          "CREATE TABLE IF NOT EXISTS islem_loglari (id INTEGER PRIMARY KEY"
          " AUTOINCREMENT, zaman TEXT, islem_turu TEXT, detay TEXT)"
      )
      cursor.execute(
          "CREATE TABLE IF NOT EXISTS gunluk_notlar (id INTEGER PRIMARY KEY"
          " AUTOINCREMENT, tarih TEXT, bolge TEXT, detay TEXT)"
      )
      cursor.execute(
          "CREATE TABLE IF NOT EXISTS parca_gecmis (id INTEGER PRIMARY KEY"
          " AUTOINCREMENT, parca_sn TEXT, tarih TEXT, islem TEXT, aciklama"
          " TEXT)"
      )

      beklenen_kolonlar = {
          "bolge": "TEXT",
          "sistem_adi": "TEXT",
          "sistem_pn": "TEXT",
          "sistem_sn": "TEXT",
          "parca_adi": "TEXT",
          "parca_pn": "TEXT",
          "parca_sn": "TEXT",
          "durum": "TEXT",
          "onarim_tarih": "TEXT",
          "aciklama": "TEXT",
          "dosya_adi": "TEXT",
      }

      cursor.execute("PRAGMA table_info(parcalar)")
      mevcut_kolonlar = [kol[1] for kol in cursor.fetchall()]

      for kolon_adi, kolon_tipi in beklenen_kolonlar.items():
        if kolon_adi not in mevcut_kolonlar:
          cursor.execute(
              f"ALTER TABLE parcalar ADD COLUMN {kolon_adi} {kolon_tipi}"
          )

  def log_yaz(islem_turu, detay):
    try:
      zaman = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
      with sqlite3.connect(DB_DOSYASI) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO islem_loglari (zaman, islem_turu, detay) VALUES (?,"
            " ?, ?)",
            (zaman, islem_turu, detay),
        )
      # Her işlem sonrası otomatik Excel yedeklemesi yap
      otomatik_yedekle()
    except Exception as e:
      print(f"Log yazılamadı: {e}")

  veritabanini_hazirla()

  # --- ÖZEL SİYAH TEMA VE ÇERÇEVE CSS ---
  st.markdown(
      """
    <style>
    .stApp {
        background-color: #121212;
        color: #e0e0e0;
    }
    .metric-card {
        background-color: #1e1e1e;
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 12px 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .metric-title {
        font-size: 13px;
        color: #a0a0a0;
        font-weight: 600;
        margin-bottom: 4px;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 22px;
        color: #ffffff;
        font-weight: 700;
    }
    .autosave-badge {
        font-size: 12px;
        color: #2ecc71;
        background-color: #1b382b;
        padding: 4px 8px;
        border-radius: 4px;
        border: 1px solid #2ecc71;
    }
    </style>
    """,
      unsafe_allow_html=True,
  )

  # --- ÜST BAŞLIK VE OTOMATİK KAYIT İNDİKATÖRÜ ---
  col_head1, col_head2 = st.columns([7, 3])
  with col_head1:
    st.markdown("### ⚙️ Sistem ve Parça Takip Sistemi")
  with col_head2:
    st.markdown(
        "<div style='text-align: right; padding-top: 10px;'><span"
        ' class="autosave-badge">🟢 Otomatik Excel Yedekleme Aktif</span></div>',
        unsafe_allow_html=True,
    )

  # Verileri Çek
  with sqlite3.connect(DB_DOSYASI) as conn:
    df_parcalar = pd.read_sql_query("SELECT * FROM parcalar", conn)

  # İstatistik Hesaplama
  toplam = len(df_parcalar)
  faal = (
      len(df_parcalar[df_parcalar["durum"] == "FAAL"])
      if not df_parcalar.empty and "durum" in df_parcalar.columns
      else 0
  )
  yedek = (
      len(df_parcalar[df_parcalar["durum"] == "YEDEK PARÇA"])
      if not df_parcalar.empty and "durum" in df_parcalar.columns
      else 0
  )
  onarimda = (
      len(df_parcalar[df_parcalar["durum"] == "ONARIMDA"])
      if not df_parcalar.empty and "durum" in df_parcalar.columns
      else 0
  )
  gayri = (
      len(df_parcalar[df_parcalar["durum"] == "GAYRI FAAL"])
      if not df_parcalar.empty and "durum" in df_parcalar.columns
      else 0
  )

  # Kritik onarım hesaplama (30 gün+)
  kritik = 0
  kritik_liste = []
  if (
      not df_parcalar.empty
      and "onarim_tarih" in df_parcalar.columns
      and "durum" in df_parcalar.columns
  ):
    bugun = datetime.date.today()
    for _, row in df_parcalar[df_parcalar["durum"] == "ONARIMDA"].iterrows():
      o_tarih = row["onarim_tarih"]
      if o_tarih:
        try:
          baslangic = datetime.datetime.strptime(
              str(o_tarih).strip(), "%d.%m.%Y"
          ).date()
          gecen_gun = (bugun - baslangic).days
          if gecen_gun >= 30:
            kritik += 1
            kritik_liste.append(
                f"• **B
