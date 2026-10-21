from io import BytesIO
import datetime
import time
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Sistem ve Parça Takip Sistemi", page_icon="⚙️", layout="wide"
)

# --- BURAYI KENDİ BİLGİLERİNİZLE DOLDURUN ---
WEB_APP_URL = "BURAYA_GOOGLE_APPS_SCRIPT_WEB_APP_URL_YAZIN"
TABLO_ID = "TABLO_ID_BURAYA"  # Örn: 1BxiMVs0XRA5nFM...
SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{TABLO_ID}/gviz/tq?tqx=out:csv&sheet=parcalar"
)


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


# Verileri Google Sheets'ten Okuma
@st.cache_data(ttl=0)
def verileri_getir():
  try:
    return pd.read_csv(SHEET_CSV_URL)
  except Exception:
    return pd.DataFrame(columns=[
        "id",
        "bolge",
        "sistem_adi",
        "sistem_pn",
        "sistem_sn",
        "parca_adi",
        "parca_pn",
        "parca_sn",
        "durum",
        "onarim_tarih",
        "aciklama",
    ])


df_parcalar = verileri_getir()

st.title("⚙️ Sistem ve Parça Takip Sistemi")

# Metrik İstatistikleri
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
ankara = (
    len(df_parcalar[df_parcalar["durum"] == "ANKARA'DA / SEVK EDİLDİ"])
    if not df_parcalar.empty and "durum" in df_parcalar.columns
    else 0
)
gayri = (
    len(df_parcalar[df_parcalar["durum"] == "GAYRI FAAL"])
    if not df_parcalar.empty and "durum" in df_parcalar.columns
    else 0
)

# Üst Metrik Kartları
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Toplam", toplam)
col2.metric("Faal", faal)
col3.metric("Yedek", yedek)
col4.metric("Onarımda", onarimda)
col5.metric("🏛️ Ankara'da", ankara)
col6.metric("Gayri Faal", gayri)

st.markdown("---")

# Sekmeler
tab_takip, tab_ankara, tab_ekle, tab_yonetim = st.tabs([
    "📋 Tüm Liste & Arama",
    "🏛️ Ankara'daki Parçalar",
    "➕ Yeni Kayıt Ekle",
    "⚙️ Dışa Aktar",
])

# 1. TÜM LİSTE & ARAMA SEKMESİ
with tab_takip:
  st.subheader("Sistem ve Parça Listesi")
  if not df_parcalar.empty:
    arama = st.text_input(
        "🔍 Arama Yap (Sistem, Parça, SN, PN veya Bölge):", ""
    )
    df_goster = df_parcalar.copy()

    if arama:
      mask = df_goster.astype(str).apply(
          lambda row: row.str.contains(arama, case=False).any(), axis=1
      )
      df_goster = df_goster[mask]

    st.dataframe(df_goster, use_container_width=True, hide_index=True)
  else:
    st.info("Henüz kayıt bulunmuyor.")

# 2. ANKARA TAKİP SEKMESİ
with tab_ankara:
  st.subheader("🏛️ Ankara'ya Sevk Edilen Parçalar")
  if not df_parcalar.empty and "durum" in df_parcalar.columns:
    df_ankara = df_parcalar[
        df_parcalar["durum"] == "ANKARA'DA / SEVK EDİLDİ"
    ]
    if not df_ankara.empty:
      st.dataframe(df_ankara, use_container_width=True, hide_index=True)
    else:
      st.success("Şu anda Ankara'da bulunan / sevk edilmiş parça yok.")
  else:
    st.info("Henüz kayıt bulunmuyor.")

# 3. YENİ KAYIT EKLEME SEKMESİ
with tab_ekle:
  st.subheader("Yeni Sistem / Parça Kaydı Ekle")
  with st.form("yeni_kayit_formu", clear_on_submit=True):
    e_bolge = st.text_input("Bölüm / Bölge")
    e_sistem = st.text_input("Sistem Adı")
    e_s_pn = st.text_input("Sistem Parça Numarası (PN)")
    e_s_sn = st.text_input("Sistem Seri Numarası (SN)")
    e_parca = st.text_input("Parça Adı")
    e_p_pn = st.text_input("Parça PN")
    e_p_sn = st.text_input("Parça SN")

    e_durum = st.selectbox("Durum", [
        "FAAL",
        "YEDEK PARÇA",
        "ONARIMDA",
        "ANKARA'DA / SEVK EDİLDİ",
        "GAYRI FAAL",
    ])

    e_tarih = st.text_input(
        "Sevk / Onarım Başlangıç Tarihi (GG.AA.YYYY)",
        value=datetime.datetime.now().strftime("%d.%m.%Y"),
    )
    e_aciklama = st.text_area(
        "Açıklama (Örn: Kargo takip no, arıza detayları vb.)"
    )

    submit_yeni = st.form_submit_button("Sisteme Kaydet")

    if submit_yeni:
      if not e_bolge or not e_sistem or not e_parca:
        st.warning("Lütfen Bölge, Sistem Adı ve Parça Adı alanlarını doldurun!")
      else:
        yeni_id = (
            int(df_parcalar["id"].max() + 1)
            if not df_parcalar.empty
            and "id" in df_parcalar.columns
            and pd.notna(df_parcalar["id"]).any()
            else 1
        )

        yeni_veri = {
            "id": yeni_id,
            "bolge": tr_upper(e_bolge),
            "sistem_adi": tr_upper(e_sistem),
            "sistem_pn": tr_upper(e_s_pn),
            "sistem_sn": tr_upper(e_s_sn),
            "parca_adi": tr_upper(e_parca),
            "parca_pn": tr_upper(e_p_pn),
            "parca_sn": tr_upper(e_p_sn),
            "durum": e_durum,
            "onarim_tarih": e_tarih,
            "aciklama": tr_upper(e_aciklama),
        }

        try:
          response = requests.post(WEB_APP_URL, json=yeni_veri)
          if response.status_code == 200:
            # Başarılı bildirim ve 2.5 saniye sonra otomatik kaybolma
            st.toast("✅ Kayıt başarıyla tamamlandı!", icon="🎉")
            msg = st.success(
                "✅ Yeni kayıt başarıyla eklendi! Sayfa yenileniyor..."
            )
            time.sleep(2.5)
            msg.empty()
            verileri_getir.clear()
            st.rerun()
          else:
            st.error(f"Kayıt eklenemedi. Sunucu yanıtı: {response.status_code}")
        except Exception as ex:
          st.error(f"Bağlantı hatası: {ex}")

# 4. EXCEL DIŞA AKTAR SEKMESİ
with tab_yonetim:
  st.subheader("Veri Yönetimi")
  if not df_parcalar.empty:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
      df_parcalar.to_excel(writer, index=False, sheet_name="parcalar")
    excel_data = output.getvalue()

    st.download_button(
        label="📥 Tüm Verileri Excel Olarak İndir",
        data=excel_data,
        file_name=(
            f"sistem_takip_{datetime.date.today().strftime('%d_%m_%Y')}.xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )