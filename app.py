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
          def init_db():
  conn = get_connection()
  cursor = conn.cursor()

  # Eski tabloyu tamamen kaldırıp güncel yapıyla baştan oluşturmak için:
  cursor.execute("DROP TABLE IF EXISTS parcalar;")
  cursor.execute("DROP TABLE IF EXISTS sistemler;")

  # 1. Sistemler Tablosu (bolge sütunu dahil)
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