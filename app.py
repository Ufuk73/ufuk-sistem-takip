from io import BytesIO
import re
import datetime
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Sayfa Yapılandırması en başta olmalı
st.set_page_config(
    page_title="Sistem ve Parça Takip Sistemi",
    page_icon="⚙️",
    layout="wide"
)

try:
    # Google Sheets Bağlantısı
    conn = st.connection("gsheets", type=GSheetsConnection)

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

    # Verileri Google Sheets'ten Çekme Fonksiyonu
    @st.cache_data(ttl=0)
    def verileri_getir():
        try:
            df = conn.read(worksheet="parcalar", ttl=0)
            if df.empty or "id" not in df.columns:
                return pd.DataFrame(columns=[
                    "id", "bolge", "sistem_adi", "sistem_pn", "sistem_sn", 
                    "parca_adi", "parca_pn", "parca_sn", "durum", "onarim_tarih", "aciklama"
                ])
            return df
        except Exception:
            return pd.DataFrame(columns=[
                "id", "bolge", "sistem_adi", "sistem_pn", "sistem_sn", 
                "parca_adi", "parca_pn", "parca_sn", "durum", "onarim_tarih", "aciklama"
            ])

    df_parcalar = verileri_getir()

    # --- ANA BAŞLIK VE İSTATİSTİKLER ---
    st.title("⚙️ Sistem ve Parça Takip Sistemi (Bulut & Mobil)")

    # İstatistik Hesaplama
    toplam = len(df_parcalar)
    faal = len(df_parcalar[df_parcalar["durum"] == "FAAL"]) if not df_parcalar.empty and "durum" in df_parcalar.columns else 0
    yedek = len(df_parcalar[df_parcalar["durum"] == "YEDEK PARÇA"]) if not df_parcalar.empty and "durum" in df_parcalar.columns else 0
    onarimda = len(df_parcalar[df_parcalar["durum"] == "ONARIMDA"]) if not df_parcalar.empty and "durum" in df_parcalar.columns else 0
    gayri = len(df_parcalar[df_parcalar["durum"] == "GAYRI FAAL"]) if not df_parcalar.empty and "durum" in df_parcalar.columns else 0

    # Kritik onarım hesaplama (30 gün+)
    kritik = 0
    if not df_parcalar.empty and "onarim_tarih" in df_parcalar.columns and "durum" in df_parcalar.columns:
        bugun = datetime.date.today()
        for _, row in df_parcalar[df_parcalar["durum"] == "ONARIMDA"].iterrows():
            o_tarih = row["onarim_tarih"]
            if o_tarih and pd.notna(o_tarih):
                try:
                    baslangic = datetime.datetime.strptime(str(o_tarih).strip(), "%d.%m.%Y").date()
                    if (bugun - baslangic).days >= 30:
                        kritik += 1
                except ValueError:
                    pass

    # Üst Metrikler (Rozetler)
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Toplam", toplam)
    col2.metric("Faal", faal)
    col3.metric("Yedek", yedek)
    col4.metric("Onarımda", onarimda)
    col5.metric("Kritik (30 Gün+)", kritik, delta_color="inverse" if kritik > 0 else "off")
    col6.metric("Gayri Faal", gayri)

    st.markdown("---")

    # --- SEKMELER ---
    tab_takip, tab_ekle, tab_yonetim = st.tabs([
        "📋 Sistem Takip & Filtreleme", 
        "➕ Yeni Kayıt Ekle", 
        "⚙️ Dışa/İçe Aktar"
    ])

    # 1. SEKME: TAKİP & FİLTRELEME
    with tab_takip:
        st.subheader("Sistem Parça Listesi ve Filtreleme")
        
        if not df_parcalar.empty:
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            
            bolgeler = ["TÜMÜ"] + list(df_parcalar["bolge"].dropna().unique()) if "bolge" in df_parcalar.columns else ["TÜMÜ"]
            parcalar = ["TÜMÜ"] + list(df_parcalar["parca_adi"].dropna().unique()) if "parca_adi" in df_parcalar.columns else ["TÜMÜ"]
            durumlar = ["TÜMÜ", "FAAL", "YEDEK PARÇA", "ONARIMDA", "GAYRI FAAL", "30 GÜN+ KRİTİK"]
            
            f_bolge = col_f1.selectbox("Bölge Seç", bolgeler)
            f_parca = col_f2.selectbox("Parça Adı Seç", parcalar)
            f_durum = col_f3.selectbox("Durum Seç", durumlar)
            f_arama = col_f4.text_input("Hızlı Arama (Sistem/Parça/SN)")
            
            # Filtreleme Uygula
            filt_df = df_parcalar.copy()
            if f_bolge != "TÜMÜ" and "bolge" in filt_df.columns:
                filt_df = filt_df[filt_df["bolge"] == f_bolge]
            if f_parca != "TÜMÜ" and "parca_adi" in filt_df.columns:
                filt_df = filt_df[filt_df["parca_adi"] == f_parca]
            if f_durum != "TÜMÜ" and f_durum != "30 GÜN+ KRİTİK" and "durum" in filt_df.columns:
                filt_df = filt_df[filt_df["durum"] == f_durum]
            elif f_durum == "30 GÜN+ KRİTİK" and "durum" in filt_df.columns and "onarim_tarih" in filt_df.columns:
                kritik_idler = []
                bugun = datetime.date.today()
                for _, r in filt_df[filt_df["durum"] == "ONARIMDA"].iterrows():
                    if pd.notna(r["onarim_tarih"]):
                        try:
                            b_t = datetime.datetime.strptime(str(r["onarim_tarih"]).strip(), "%d.%m.%Y").date()
                            if (bugun - b_t).days >= 30:
                                kritik_idler.append(r["id"])
                        except ValueError:
                            pass
                filt_df = filt_df[filt_df["id"].isin(kritik_idler)]
                
            if f_arama:
                a_upper = tr_upper(f_arama)
                filt_df = filt_df[filt_df.apply(lambda row: row.astype(str).str.upper().str.contains(a_upper).any(), axis=1)]
                
            st.dataframe(filt_df, use_container_width=True, hide_index=True)
            
            # Seçili Kayıt Düzenleme / Silme Bölümü
            st.markdown("### Kayıt Düzenle veya Sil")
            secili_id = st.selectbox("İşlem Yapılacak Kayıt ID Seç", [None] + list(filt_df["id"].values))
            
            if secili_id is not None:
                kayit_secim = df_parcalar[df_parcalar["id"] == secili_id]
                if not kayit_secim.empty:
                    kayit = kayit_secim.iloc[0]
                    with st.form("guncelle_form"):
                        g_bolge = st.text_input("Bölge", value=kayit.get("bolge", "") if pd.notna(kayit.get("bolge", "")) else "")
                        g_sistem = st.text_input("Sistem Adı", value=kayit.get("sistem_adi", "") if pd.notna(kayit.get("sistem_adi", "")) else "")
                        g_s_pn = st.text_input("Sistem PN", value=kayit.get("sistem_pn", "") if pd.notna(kayit.get("sistem_pn", "")) else "")
                        g_s_sn = st.text_input("Sistem SN", value=kayit.get("sistem_sn", "") if pd.notna(kayit.get("sistem_sn", "")) else "")
                        g_parca = st.text_input("Parça Adı", value=kayit.get("parca_adi", "") if pd.notna(kayit.get("parca_adi", "")) else "")
                        g_p_pn = st.text_input("Parça PN", value=kayit.get("parca_pn", "") if pd.notna(kayit.get("parca_pn", "")) else "")
                        g_p_sn = st.text_input("Parça SN", value=kayit.get("parca_sn", "") if pd.notna(kayit.get("parca_sn", "")) else "")
                        
                        mevcut_durum = kayit.get("durum", "FAAL")
                        durum_secenekleri = ["FAAL", "YEDEK PARÇA", "ONARIMDA", "GAYRI FAAL"]
                        durum_index = durum_secenekleri.index(mevcut_durum) if mevcut_durum in durum_secenekleri else 0
                        g_durum = st.selectbox("Durum", durum_secenekleri, index=durum_index)
                        
                        g_tarih = st.text_input("Onarım Tarihi (GG.AA.YYYY)", value=kayit.get("onarim_tarih", "") if pd.notna(kayit.get("onarim_tarih", "")) else "")
                        g_aciklama = st.text_area("Açıklama / Not", value=kayit.get("aciklama", "") if pd.notna(kayit.get("aciklama", "")) else "")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        guncelle_basildi = col_btn1.form_submit_button("Değişiklikleri Kaydet")
                        sil_basildi = col_btn2.form_submit_button("Kayıt Sil", type="primary")
                        
                        if guncelle_basildi:
                            df_parcalar.loc[df_parcalar["id"] == secili_id, ["bolge", "sistem_adi", "sistem_pn", "sistem_sn", "parca_adi", "parca_pn", "parca_sn", "durum", "onarim_tarih", "aciklama"]] = [
                                tr_upper(g_bolge), tr_upper(g_sistem), tr_upper(g_s_pn), tr_upper(g_s_sn), 
                                tr_upper(g_parca), tr_upper(g_p_pn), tr_upper(g_p_sn), g_durum, g_tarih, tr_upper(g_aciklama)
                            ]
                            conn.update(worksheet="parcalar", data=df_parcalar)
                            st.success("Kayıt başarıyla güncellendi!")
                            st.rerun()
                            
                        if sil_basildi:
                            df_parcalar = df_parcalar[df_parcalar["id"] != secili_id]
                            conn.update(worksheet="parcalar", data=df_parcalar)
                            st.success("Kayıt silindi!")
                            st.rerun()
        else:
            st.info("Henüz kayıt bulunmuyor.")

    # 2. SEKME: YENİ KAYIT EKLE
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
            e_durum = st.selectbox("Durum", ["FAAL", "YEDEK PARÇA", "ONARIMDA", "GAYRI FAAL"])
            e_tarih = st.text_input("Onarım Başlangıç Tarihi (GG.AA.YYYY)", value=datetime.datetime.now().strftime("%d.%m.%Y"))
            e_aciklama = st.text_area("Açıklama")
            
            submit_yeni = st.form_submit_button("Sisteme Kaydet")
            if submit_yeni:
                if not e_bolge or not e_sistem or not e_parca:
                    st.warning("Lütfen Bölge, Sistem Adı ve Parça Adı alanlarını doldurun!")
                else:
                    yeni_id = int(df_parcalar["id"].max() + 1) if not df_parcalar.empty and "id" in df_parcalar.columns and pd.notna(df_parcalar["id"]).any() else 1
                    
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
                        "aciklama": tr_upper(e_aciklama)
                    }
                    
                    updated_df = pd.concat([df_parcalar, pd.DataFrame([yeni_veri])], ignore_index=True)
                    conn.update(worksheet="parcalar", data=updated_df)
                    st.success("Yeni parça başarıyla buluta eklendi ve asla silinmeyecek!")
                    st.rerun()

    # 3. SEKME: DIŞA / İÇE AKTAR
    with tab_yonetim:
        st.subheader("Veri Yönetimi (Dışa / İçe Aktar)")
        
        if not df_parcalar.empty:
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_parcalar.to_excel(writer, index=False, sheet_name="parcalar")
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Tüm Verileri Excel Olarak İndir",
                data=excel_data,
                file_name=f"sistem_takip_{datetime.date.today().strftime('%d_%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        st.markdown("---")
        st.markdown("### Toplu Veri İçe Aktar (Excel / CSV)")
        yuklenen_dosya = st.file_uploader("Dosya Seçin", type=["xlsx", "csv"])
        if yuklenen_dosya is not None:
            try:
                if yuklenen_dosya.name.endswith('.csv'):
                    df_yuklenen = pd.read_csv(yuklenen_dosya, sep=";")
                else:
                    df_yuklenen = pd.read_excel(yuklenen_dosya)
                    
                if st.button("Google Sheets'e Toplu Aktarımı Başlat"):
                    updated_df = pd.concat([df_parcalar, df_yuklenen], ignore_index=True)
                    conn.update(worksheet="parcalar", data=updated_df)
                    st.success("Veriler başarıyla buluta aktarıldı!")
                    st.rerun()
            except Exception as e:
                st.error(f"Dosya okuma hatası: {e}")

except Exception as e:
    st.error("Uygulama çalışırken bir hata oluştu:")
    st.code(traceback.format_exc())