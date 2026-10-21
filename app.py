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
                "CREATE TABLE IF NOT EXISTS parcalar (id INTEGER PRIMARY KEY AUTOINCREMENT)"
            )
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS islem_loglari (id INTEGER PRIMARY KEY AUTOINCREMENT, zaman TEXT, islem_turu TEXT, detay TEXT)"
            )
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS gunluk_notlar (id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, bolge TEXT, detay TEXT)"
            )
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS parca_gecmis (id INTEGER PRIMARY KEY AUTOINCREMENT, parca_sn TEXT, tarih TEXT, islem TEXT, aciklama TEXT)"
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
                    "INSERT INTO islem_loglari (zaman, islem_turu, detay) VALUES (?, ?, ?)",
                    (zaman, islem_turu, detay),
                )
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
            "<div style='text-align: right; padding-top: 10px;'><span class='autosave-badge'>🟢 Otomatik Excel Yedekleme Aktif</span></div>",
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
                            f"• **Bölge: {row.get('bolge', 'Bölge Yok')}** ({row.get('parca_adi', 'Parça')} - SN: {row.get('parca_sn', '-')}) -> {gecen_gun} gündür onarımda!"
                        )
                except ValueError:
                    pass

    if kritik > 0:
        st.error(
            f"⚠️ **DİKKAT:** 30 Günü Aşan Onarımda Bekleyen **{kritik}** Adet Parça Bulunuyor!"
        )
        with st.expander("Kritik Parçaları Listele", expanded=False):
            for k_bilgi in kritik_liste:
                st.markdown(k_bilgi)

    # Metrikleri Çerçeveli Sütunlar Halinde Yerleştirme
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">Toplam</div><div class="metric-value">{toplam}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">Faal</div><div class="metric-value" style="color: #2ecc71;">{faal}</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">Yedek</div><div class="metric-value" style="color: #3498db;">{yedek}</div></div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">Onarımda</div><div class="metric-value" style="color: #f1c40f;">{onarimda}</div></div>',
            unsafe_allow_html=True,
        )
    with c5:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">Kritik (30+)</div><div class="metric-value" style="color: #e74c3c;">{kritik}</div></div>',
            unsafe_allow_html=True,
        )
    with c6:
        st.markdown(
            f'<div class="metric-card"><div class="metric-title">Gayri Faal</div><div class="metric-value" style="color: #95a5a6;">{gayri}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        "<hr style='margin:15px 0 10px 0; border-color: #333333;'>",
        unsafe_allow_html=True,
    )

    tab_takip, tab_ekle, tab_notlar, tab_loglar, tab_gecmis, tab_yonetim = st.tabs([
        "📋 Kart Görünümü",
        "➕ Yeni Kayıt",
        "📝 Günlük Notlar",
        "📜 Loglar",
        "🔍 Parça Geçmişi",
        "⚙️ Yönetim",
    ])

    # Dialog ile Düzenleme Fonksiyonu
    @st.dialog("Kayıt Düzenle", width="large")
    def duzenle_dialog(r_id):
        with sqlite3.connect(DB_DOSYASI) as conn:
            df_tekil = pd.read_sql_query(
                "SELECT * FROM parcalar WHERE id = ?", conn, params=(r_id,)
            )

        if not df_tekil.empty:
            row = df_tekil.iloc[0]
            with st.form(key=f"dialog_form_{r_id}"):
                e_bolge = st.text_input(
                    "Bölge",
                    value=(
                        row.get("bolge", "") if pd.notna(row.get("bolge", "")) else ""
                    ),
                )
                e_sistem = st.text_input(
                    "Sistem Adı",
                    value=(
                        row.get("sistem_adi", "")
                        if pd.notna(row.get("sistem_adi", ""))
                        else ""
                    ),
                )

                col_d1, col_d2 = st.columns(2)
                e_s_pn = col_d1.text_input(
                    "Sistem PN",
                    value=(
                        row.get("sistem_pn", "")
                        if pd.notna(row.get("sistem_pn", ""))
                        else ""
                    ),
                )
                e_s_sn = col_d2.text_input(
                    "Sistem SN",
                    value=(
                        row.get("sistem_sn", "")
                        if pd.notna(row.get("sistem_sn", ""))
                        else ""
                    ),
                )

                e_parca = st.text_input(
                    "Parça Adı",
                    value=(
                        row.get("parca_adi", "")
                        if pd.notna(row.get("parca_adi", ""))
                        else ""
                    ),
                )

                col_d3, col_d4 = st.columns(2)
                e_p_pn = col_d3.text_input(
                    "Parça PN",
                    value=(
                        row.get("parca_pn", "")
                        if pd.notna(row.get("parca_pn", ""))
                        else ""
                    ),
                )
                e_p_sn = col_d4.text_input(
                    "Parça SN",
                    value=(
                        row.get("parca_sn", "")
                        if pd.notna(row.get("parca_sn", ""))
                        else ""
                    ),
                )

                mevcut_d = row.get("durum", "FAAL")
                d_list = ["FAAL", "YEDEK PARÇA", "ONARIMDA", "SEVK 🚚", "GAYRI FAAL"]
                d_idx = d_list.index(mevcut_d) if mevcut_d in d_list else 0
                e_durum = st.selectbox("Durum", d_list, index=d_idx)

                varsayilan_tarih = str_to_date(row.get("onarim_tarih"))
                e_tarih_obj = st.date_input(
                    "Onarım Tarihi", value=varsayilan_tarih, format="DD.MM.YYYY"
                )
                e_tarih_str = e_tarih_obj.strftime("%d.%m.%Y")

                e_aciklama = st.text_area(
                    "Açıklama / Not",
                    value=(
                        row.get("aciklama", "")
                        if pd.notna(row.get("aciklama", ""))
                        else ""
                    ),
                )

                if st.form_submit_button("Güncellemeyi Kaydet", type="primary"):
                    with sqlite3.connect(DB_DOSYASI) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            UPDATE parcalar SET bolge=?, sistem_adi=?, sistem_pn=?, sistem_sn=?, parca_adi=?, parca_pn=?, parca_sn=?, durum=?, onarim_tarih=?, aciklama=?
                            WHERE id=?
                            """,
                            (
                                tr_upper(e_bolge),
                                tr_upper(e_sistem),
                                tr_upper(e_s_pn),
                                tr_upper(
