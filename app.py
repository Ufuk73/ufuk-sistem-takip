import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import datetime
import csv
import os

DB_DOSYASI = "sistem_takip.db"

def tr_upper(text):
    """Türkçe karakter uyumlu büyük harf dönüşümü yapar."""
    if not text:
        return ""
    harf_haritasi = {'i': 'İ', 'ı': 'I', 'ç': 'Ç', 'ğ': 'Ğ', 'ö': 'Ö', 'ş': 'Ş', 'ü': 'Ü'}
    return "".join(harf_haritasi.get(c, c.upper()) for c in text)


class SistemTakipApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kurumsal Sistem ve Parça Takip Sistemi v2.0")
        self.root.geometry("1280x768")
        self.root.minsize(1024, 650)
        
        # Tema ve Stil Tanımlamaları
        self.setup_styles()
        
        self.secili_kayit_id = None
        self.veritabani_olustur()

        # Ana Ekran Düzeni
        self.create_main_layout()
        
        # İlk Yüklemeler
        self.bolge_listesini_guncelle()
        self.parca_listesini_guncelle()
        self.filtre_listesini_guncelle()
        self.listeyi_guncelle()
        self.gunluk_notlari_yukle()
        self.loglari_ekrana_yukle()
        self.acilis_kritik_kontrolu()

    def setup_styles(self):
        """Modern ttk stillerini ve renk paletini ayarlar."""
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Renk paleti (Modern Kurumsal Gri/Mavi Tonları)
        self.bg_color = "#f8fafc"
        self.card_bg = "#ffffff"
        self.primary_color = "#0284c7" # Sky Blue
        self.danger_color = "#ef4444"  # Red
        self.success_color = "#10b981" # Emerald
        self.warning_color = "#f59e0b" # Amber
        self.text_color = "#1e293b"    # Slate 800

        self.root.configure(bg=self.bg_color)
        
        # Stil Ayarları
        self.style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        self.style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[14, 8])
        self.style.configure("Treeview", font=("Segoe UI", 9), rowheight=25, background="#ffffff", fieldbackground="#ffffff")
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#e2e8f0", foreground="#334155")
        
    def veritabani_olustur(self):
        """SQLite veritabanını ve tabloları oluşturur, performans için indeks tanımlar."""
        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parcalar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bolge TEXT,
                    sistem_adi TEXT,
                    sistem_pn TEXT,
                    sistem_sn TEXT,
                    parca_adi TEXT,
                    parca_pn TEXT,
                    parca_sn TEXT,
                    durum TEXT,
                    onarim_tarih TEXT,
                    aciklama TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gunluk_notlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tarih TEXT,
                    bolge TEXT,
                    detay TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS islem_loglari (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zaman TEXT,
                    islem_turu TEXT,
                    detay TEXT
                )
            """)

            # Performans için indexler
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_parcalar_bolge ON parcalar(bolge)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_parcalar_durum ON parcalar(durum)")
            
            conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Veritabanı oluşturulurken bir hata oluştu:\n{e}")
        finally:
            if conn:
                conn.close()

    def log_yaz(self, islem_turu, detay):
        """Sistem üzerinde yapılan işlemleri güvenli şekilde veritabanına kaydeder."""
        conn = None
        try:
            zaman = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO islem_loglari (zaman, islem_turu, detay) VALUES (?, ?, ?)",
                (zaman, islem_turu, detay),
            )
            conn.commit()
        except sqlite3.Error as e:
            print(f"Log yazılamadı: {e}")
        finally:
            if conn:
                conn.close()
        self.loglari_ekrana_yukle()

    def loglari_ekrana_yukle(self):
        """Log sekmesindeki tabloyu günceller."""
        for row in self.tree_log.get_children():
            self.tree_log.delete(row)
        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute("SELECT zaman, islem_turu, detay FROM islem_loglari ORDER BY id DESC LIMIT 200")
            for row in cursor.fetchall():
                self.tree_log.insert("", "end", values=row)
        except sqlite3.Error as e:
            print(f"Loglar yüklenemedi: {e}")
        finally:
            if conn:
                conn.close()

    def create_main_layout(self):
        """Uygulamanın ana sekme yapısını ve üst panelini kurar."""
        # Üst Özet Bandı (Dashboard Header)
        top_frame = tk.Frame(self.root, bg="#ffffff", bd=1, relief="solid")
        top_frame.pack(side="top", fill="x", padx=10, pady=8)

        lbl_header_title = tk.Label(top_frame, text="📊 OPERASYONELDURUM ÖZETİ", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#475569")
        lbl_header_title.pack(side="left", padx=10, pady=6)

        badges_container = tk.Frame(top_frame, bg="#ffffff")
        badges_container.pack(side="right", padx=6, pady=4)

        self.lbl_stat_toplam = self.create_stat_badge(badges_container, "TOPLAM", "0", "#0284c7", "#f0f9ff")
        self.lbl_stat_faal = self.create_stat_badge(badges_container, "FAAL", "0", "#10b981", "#ecfdf5")
        self.lbl_stat_yedek = self.create_stat_badge(badges_container, "YEDEK", "0", "#6366f1", "#eef2ff")
        self.lbl_stat_onarimda = self.create_stat_badge(badges_container, "ONARIMDA", "0", "#f59e0b", "#fffbeb")
        self.lbl_stat_kritik = self.create_stat_badge(badges_container, "KRİTİK (30G+)", "0", "#ef4444", "#fef2f2")
        self.lbl_stat_gayri = self.create_stat_badge(badges_container, "GAYRİ FAAL", "0", "#64748b", "#f1f5f9")

        # Notebook (Sekmeler)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_takip = ttk.Frame(self.notebook)
        self.tab_notlar = ttk.Frame(self.notebook)
        self.tab_loglar = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_takip, text=" ⚙️ Sistem & Parça Takibi ")
        self.notebook.add(self.tab_notlar, text=" 📝 Bölge Günlük Notları ")
        self.notebook.add(self.tab_loglar, text=" 🛡️ İşlem Logları ")

        self.build_takip_sekmesi()
        self.build_notlar_sekmesi()
        self.build_loglar_sekmesi()

    def create_stat_badge(self, parent, title, value, color, bg_color):
        """Üst durum özet paneli için modern istatistik rozeti oluşturur."""
        frame = tk.Frame(parent, bg=bg_color, bd=1, relief="solid", highlightbackground=color, padx=8, pady=3)
        frame.pack(side="left", padx=3, fill="y")

        lbl_title = tk.Label(frame, text=title, font=("Segoe UI", 7, "bold"), bg=bg_color, fg=color)
        lbl_title.pack(anchor="w")

        lbl_val = tk.Label(frame, text=value, font=("Segoe UI", 10, "bold"), bg=bg_color, fg=color)
        lbl_val.pack(anchor="w")
        return lbl_val

    def build_takip_sekmesi(self):
        """Ana takip sekmesinin arayüz bileşenlerini kurar."""
        # Sol Panel: Form Giriş Alanları
        left_frame = tk.LabelFrame(self.tab_takip, text=" Kayıt ve Düzenleme Paneli ", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155", padx=10, pady=10)
        left_frame.pack(side="left", fill="y", padx=(0, 8), pady=8)

        fields = [
            ("Bölge:", "cmb_bolge", ttk.Combobox, {}),
            ("Sistem Adı:", "ent_sistem", tk.Entry, {}),
            ("Sistem P/N:", "ent_sistem_pn", tk.Entry, {}),
            ("Sistem S/N:", "ent_sistem_sn", tk.Entry, {}),
            ("Parça Adı:", "cmb_parca", ttk.Combobox, {}),
            ("Parça P/N:", "ent_parca_pn", tk.Entry, {}),
            ("Parça S/N:", "ent_parca_sn", tk.Entry, {}),
            ("Durumu:", "cmb_durum", ttk.Combobox, {"values": ["FAAL", "YEDEK PARÇA", "ONARIMDA", "GAYRI FAAL"]}),
            ("Onarım Başl. Tarih:", "ent_onarim_tarih", tk.Entry, {}),
            ("Açıklama / Not:", "ent_not", tk.Entry, {})
        ]

        self.form_widgets = {}
        for idx, (label_text, attr_name, widget_class, kwargs) in enumerate(fields):
            lbl = tk.Label(left_frame, text=label_text, font=("Segoe UI", 8, "bold"), bg="#ffffff", fg="#475569")
            lbl.grid(row=idx*2, column=0, sticky="w", pady=(4, 1))
            
            if widget_class == ttk.Combobox:
                widget = ttk.Combobox(left_frame, font=("Segoe UI", 9), **kwargs)
                if attr_name == "cmb_durum":
                    widget.bind("<<ComboboxSelected>>", self.durum_degisti_kontrol)
            else:
                widget = tk.Entry(left_frame, font=("Segoe UI", 9), bg="#f8fafc", relief="solid", bd=1)
                
            widget.grid(row=idx*2+1, column=0, sticky="ew", pady=(0, 4), ipady=2)
            setattr(self, attr_name, widget)
            self.form_widgets[attr_name] = widget

        # Varsayılan durum ataması
        self.cmb_durum.set("FAAL")
        self.lbl_onarim_tarih = left_frame.grid_slaves(row=16, column=0)[0] if len(left_frame.grid_slaves(row=16, column=0)) > 0 else None

        # Butonlar Kutusu
        btn_frame = tk.Frame(left_frame, bg="#ffffff")
        btn_frame.grid(row=20, column=0, sticky="ew", pady=10)

        tk.Button(btn_frame, text="➕ Yeni Ekle", bg="#0284c7", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", command=self.kayit_ekle).pack(fill="x", pady=2, ipady=3)
        tk.Button(btn_frame, text="💾 Değişiklikleri Kaydet", bg="#10b981", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", command=self.degisiklikleri_kaydet_tiklandi).pack(fill="x", pady=2, ipady=3)
        tk.Button(btn_frame, text="🗑️ Kaydı Sil", bg="#ef4444", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", command=self.kayit_sil).pack(fill="x", pady=2, ipady=3)
        tk.Button(btn_frame, text="🧹 Formu Temizle", bg="#64748b", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", command=self.formu_temizle).pack(fill="x", pady=2, ipady=3)

        # Sağ Panel: Filtreleme ve Ağaç Yapısı
        right_frame = tk.Frame(self.tab_takip, bg=self.bg_color)
        right_frame.pack(side="right", fill="both", expand=True, pady=8)

        # Filtre Alanı
        filter_box = tk.LabelFrame(right_frame, text=" Filtreleme ve Arama ", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155", padx=8, pady=8)
        filter_box.pack(fill="x", padx=(0, 0), pady=(0, 6))

        tk.Label(filter_box, text="Bölge:", font=("Segoe UI", 8, "bold"), bg="#ffffff").pack(side="left", padx=(0, 2))
        self.cmb_filtre_bolge = ttk.Combobox(filter_box, font=("Segoe UI", 8), width=14, state="readonly")
        self.cmb_filtre_bolge.pack(side="left", padx=(0, 10))
        self.cmb_filtre_bolge.bind("<<ComboboxSelected>>", lambda e: self.listeyi_guncelle())

        tk.Label(filter_box, text="Parça:", font=("Segoe UI", 8, "bold"), bg="#ffffff").pack(side="left", padx=(0, 2))
        self.cmb_filtre_parca = ttk.Combobox(filter_box, font=("Segoe UI", 8), width=14, state="readonly")
        self.cmb_filtre_parca.pack(side="left", padx=(0, 10))
        self.cmb_filtre_parca.bind("<<ComboboxSelected>>", lambda e: self.listeyi_guncelle())

        tk.Label(filter_box, text="Durum:", font=("Segoe UI", 8, "bold"), bg="#ffffff").pack(side="left", padx=(0, 2))
        self.cmb_filtre_durum = ttk.Combobox(filter_box, font=("Segoe UI", 8), width=14, state="readonly", values=["TÜMÜ", "FAAL", "YEDEK PARÇA", "ONARIMDA", "30 GÜN+ KRİTİK", "GAYRI FAAL"])
        self.cmb_filtre_durum.set("TÜMÜ")
        self.cmb_filtre_durum.pack(side="left", padx=(0, 10))
        self.cmb_filtre_durum.bind("<<ComboboxSelected>>", lambda e: self.listeyi_guncelle())

        tk.Label(filter_box, text="Arama:", font=("Segoe UI", 8, "bold"), bg="#ffffff").pack(side="left", padx=(0, 2))
        self.ent_arama = tk.Entry(filter_box, font=("Segoe UI", 8), relief="solid", bd=1, width=15)
        self.ent_arama.pack(side="left", padx=(0, 10), ipady=2)
        self.ent_arama.bind("<KeyRelease>", lambda e: self.listeyi_guncelle())

        tk.Button(filter_box, text="🔄 Yenile", bg="#0ea5e9", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", command=self.listeyi_guncelle).pack(side="left", padx=4)
        tk.Button(filter_box, text="📤 CSV Dışa Aktar", bg="#475569", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", command=self.verileri_disa_aktar).pack(side="left", padx=4)
        tk.Button(filter_box, text="📥 Veri İçe Aktar", bg="#10b981", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", command=self.verileri_ice_aktar).pack(side="left", padx=4)

        # Ağaç Tablosu (Treeview)
        tree_container = tk.Frame(right_frame, bg="#ffffff", bd=1, relief="solid")
        tree_container.pack(fill="both", expand=True)

        columns = ("sistem", "parca", "parca_pn", "parca_sn", "durum", "onarim", "sure_kontrol", "aciklama")
        self.tree = ttk.Treeview(tree_container, columns=columns, selectmode="browse")
        
        self.tree.heading("#0", text="BÖLGE / HİYARARŞİ")
        self.tree.heading("sistem", text="SİSTEM ADI")
        self.tree.heading("parca", text="PARÇA ADI")
        self.tree.heading("parca_pn", text="PARÇA P/N")
        self.tree.heading("parca_sn", text="PARÇA S/N")
        self.tree.heading("durum", text="DURUMU")
        self.tree.heading("onarim", text="ONARIM TARİHİ")
        self.tree.heading("sure_kontrol", text="SÜRE / KONTROL")
        self.tree.heading("aciklama", text="AÇIKLAMA")

        self.tree.column("#0", width=220, stretch=True)
        self.tree.column("sistem", width=140, stretch=True)
        self.tree.column("parca", width=130, stretch=True)
        self.tree.column("parca_pn", width=90, stretch=True)
        self.tree.column("parca_sn", width=90, stretch=True)
        self.tree.column("durum", width=100, stretch=True)
        self.tree.column("onarim", width=90, stretch=True)
        self.tree.column("sure_kontrol", width=120, stretch=True)
        self.tree.column("aciklama", width=150, stretch=True)

        tree_scrollbar_y = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        tree_scrollbar_x = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scrollbar_y.set, xscrollcommand=tree_scrollbar_x.set)

        self.tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar_y.pack(side="right", fill="y")
        tree_scrollbar_x.pack(side="bottom", fill="x", side_to_bottom=True if hasattr(ttk, 'S') else None)

        # Tablo renk etiketleri
        self.tree.tag_configure("FAAL", foreground="#065f46")
        self.tree.tag_configure("YEDEK PARÇA", foreground="#3730a3")
        self.tree.tag_configure("ONARIMDA", foreground="#b45309")
        self.tree.tag_configure("KRITIK_ONARIM", foreground="#991b1b", font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("GAYRI FAAL", foreground="#475569")

        self.tree.bind("<<TreeviewSelect>>", self.tablodan_satir_sec)
        
        # Sağ Tık Menüsü (Context Menu)
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="📝 Servis Formu Oluştur", command=self.servis_formu_olustur)
        self.context_menu.add_command(label="⚡ Durumu 'FAAL' Yap", command=lambda: self.hizli_durum_degis("FAAL"))
        self.context_menu.add_command(label="⚡ Durumu 'ONARIMDA' Yap", command=lambda: self.hizli_durum_degis("ONARIMDA"))
        
        self.tree.bind("<Button-3>", self.sag_tik_menu_goster)

    def build_notlar_sekmesi(self):
        """Bölge günlük notları sekmesini oluşturur."""
        frame = self.tab_notlar
        
        top_form = tk.LabelFrame(frame, text=" Yeni Günlük Not Ekle ", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155", padx=10, pady=10)
        top_form.pack(fill="x", padx=10, pady=10)

        tk.Label(top_form, text="Tarih:", font=("Segoe UI", 8, "bold"), bg="#ffffff").grid(row=0, column=0, sticky="w", padx=4)
        self.ent_not_tarih = tk.Entry(top_form, font=("Segoe UI", 9), relief="solid", bd=1, width=15)
        self.ent_not_tarih.grid(row=0, column=1, sticky="w", padx=4, ipady=2)
        self.ent_not_tarih.insert(0, datetime.datetime.now().strftime("%d.%m.%Y"))

        tk.Label(top_form, text="Bölge:", font=("Segoe UI", 8, "bold"), bg="#ffffff").grid(row=0, column=2, sticky="w", padx=4)
        self.cmb_not_bolge = ttk.Combobox(top_form, font=("Segoe UI", 9), width=20)
        self.cmb_not_bolge.grid(row=0, column=3, sticky="w", padx=4)

        tk.Button(top_form, text="🔎 Bölge Parçalarını Gör", bg="#0284c7", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", command=self.bolge_parcalarini_goster).grid(row=0, column=4, padx=10)
        tk.Button(top_form, text="🚨 Kritik Onarımlar (30G+)", bg="#ef4444", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", command=self.kritik_parcalari_goster_popip).grid(row=0, column=5, padx=5)

        tk.Label(top_form, text="Not Detayı:", font=("Segoe UI", 8, "bold"), bg="#ffffff").grid(row=1, column=0, sticky="nw", padx=4, pady=8)
        self.txt_gunluk_detay = tk.Text(top_form, font=("Segoe UI", 9), height=4, width=60, relief="solid", bd=1)
        self.txt_gunluk_detay.grid(row=1, column=1, columnspan=4, sticky="ew", padx=4, pady=8)

        tk.Button(top_form, text="💾 Notu Kaydet", bg="#10b981", fg="white", font=("Segoe UI", 9, "bold"), relief="flat", command=self.gunluk_not_ekle).grid(row=1, column=5, sticky="ne", padx=5, pady=8, ipady=10)

        # Alt Bölüm: Not Listesi
        list_frame = tk.LabelFrame(frame, text=" Kayıtlı Günlük Notlar ", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155", padx=10, pady=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        filter_sub = tk.Frame(list_frame, bg="#ffffff")
        filter_sub.pack(fill="x", pady=(0, 8))

        tk.Label(filter_sub, text="Bölge Filtre:", font=("Segoe UI", 8, "bold"), bg="#ffffff").pack(side="left", padx=(0, 4))
        self.cmb_not_filtre_bolge = ttk.Combobox(filter_sub, font=("Segoe UI", 8), width=15, state="readonly")
        self.cmb_not_filtre_bolge.pack(side="left", padx=(0, 15))
        self.cmb_not_filtre_bolge.bind("<<ComboboxSelected>>", lambda e: self.gunluk_notlari_yukle())

        tk.Label(filter_sub, text="Arama:", font=("Segoe UI", 8, "bold"), bg="#ffffff").pack(side="left", padx=(0, 4))
        self.ent_not_arama = tk.Entry(filter_sub, font=("Segoe UI", 8), relief="solid", bd=1, width=20)
        self.ent_not_arama.pack(side="left", padx=(0, 10), ipady=2)
        self.ent_not_arama.bind("<KeyRelease>", lambda e: self.gunluk_notlari_yukle())

        tk.Button(filter_sub, text="🗑️ Seçili Notu Sil", bg="#ef4444", fg="white", font=("Segoe UI", 8, "bold"), relief="flat", command=self.gunluk_not_sil).pack(side="right")

        not_tree_container = tk.Frame(list_frame, bg="#ffffff", bd=1, relief="solid")
        not_tree_container.pack(fill="both", expand=True)

        not_columns = ("id", "tarih", "bolge", "detay")
        self.tree_notlar = ttk.Treeview(not_tree_container, columns=not_columns, show="headings", selectmode="browse")
        self.tree_notlar.heading("id", text="ID")
        self.tree_notlar.heading("tarih", text="TARİH")
        self.tree_notlar.heading("bolge", text="BÖLGE")
        self.tree_notlar.heading("detay", text="NOT DETAYI")

        self.tree_notlar.column("id", width=50, stretch=False)
        self.tree_notlar.column("tarih", width=90, stretch=False)
        self.tree_notlar.column("bolge", width=150, stretch=False)
        self.tree_notlar.column("detay", width=600, stretch=True)

        not_scrollbar = ttk.Scrollbar(not_tree_container, orient="vertical", command=self.tree_notlar.yview)
        self.tree_notlar.configure(yscrollcommand=not_scrollbar.set)

        self.tree_notlar.pack(side="left", fill="both", expand=True)
        not_scrollbar.pack(side="right", fill="y")
        self.tree_notlar.bind("<Double-1>", self.not_detay_penceresi_ac)

    def build_loglar_sekmesi(self):
        """Sistem işlem logları sekmesini oluşturur."""
        frame = self.tab_loglar
        
        container = tk.Frame(frame, bg="#ffffff", bd=1, relief="solid")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        log_columns = ("zaman", "islem_turu", "detay")
        self.tree_log = ttk.Treeview(container, columns=log_columns, show="headings")
        self.tree_log.heading("zaman", text="ZAMAN")
        self.tree_log.heading("islem_turu", text="İŞLEM TÜRÜ")
        self.tree_log.heading("detay", text="DETAYLI AÇIKLAMA")

        self.tree_log.column("zaman", width=140, stretch=False)
        self.tree_log.column("islem_turu", width=130, stretch=False)
        self.tree_log.column("detay", width=700, stretch=True)

        log_scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree_log.yview)
        self.tree_log.configure(yscrollcommand=log_scrollbar.set)

        self.tree_log.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")

    def bolge_listesini_guncelle(self):
        """Bölge combobox listelerini veritabanındaki kayıtlarla doldurur."""
        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT bolge FROM parcalar WHERE bolge IS NOT NULL AND bolge != '' ORDER BY bolge")
            bolgeler = [row[0] for row in cursor.fetchall()]
            self.cmb_bolge['values'] = bolgeler
            self.cmb_not_bolge['values'] = bolgeler
        except sqlite3.Error as e:
            print(f"Bölge listesi alınamadı: {e}")
        finally:
            if conn:
                conn.close()

    def parca_listesini_guncelle(self):
        """Parça adı combobox listesini günceller."""
        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT parca_adi FROM parcalar WHERE parca_adi IS NOT NULL AND parca_adi != '' ORDER BY parca_adi")
            parcalar = [row[0] for row in cursor.fetchall()]
            self.cmb_parca['values'] = parcalar
        except sqlite3.Error as e:
            print(f"Parça listesi alınamadı: {e}")
        finally:
            if conn:
                conn.close()

    def filtre_listesini_guncelle(self):
        """Filtreleme alanlarındaki seçenekleri yeniler."""
        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT bolge FROM parcalar WHERE bolge IS NOT NULL AND bolge != '' ORDER BY bolge")
            bolgeler = ["TÜMÜ"] + [row[0] for row in cursor.fetchall()]
            self.cmb_filtre_bolge['values'] = bolgeler
            if not self.cmb_filtre_bolge.get():
                self.cmb_filtre_bolge.set("TÜMÜ")

            cursor.execute("SELECT DISTINCT parca_adi FROM parcalar WHERE parca_adi IS NOT NULL AND parca_adi != '' ORDER BY parca_adi")
            parcalar = ["TÜMÜ"] + [row[0] for row in cursor.fetchall()]
            self.cmb_filtre_parca['values'] = parcalar
            if not self.cmb_filtre_parca.get():
                self.cmb_filtre_parca.set("TÜMÜ")

            cursor.execute("SELECT DISTINCT bolge FROM parcalar WHERE bolge IS NOT NULL AND bolge != '' ORDER BY bolge")
            not_bolgeler = ["TÜMÜ"] + [row[0] for row in cursor.fetchall()]
            self.cmb_not_filtre_bolge['values'] = not_bolgeler
            if not self.cmb_not_filtre_bolge.get():
                self.cmb_not_filtre_bolge.set("TÜMÜ")
        except sqlite3.Error as e:
            print(f"Filtre listeleri güncellenemedi: {e}")
        finally:
            if conn:
                conn.close()

    def durum_degisti_kontrol(self, event):
        """Parça durumu 'ONARIMDA' seçildiğinde onarım tarih alanını otomatik ayarlar."""
        durum = self.cmb_durum.get()
        if durum == "ONARIMDA":
            if not self.ent_onarim_tarih.get():
                self.ent_onarim_tarih.delete(0, tk.END)
                self.ent_onarim_tarih.insert(0, datetime.datetime.now().strftime("%d.%m.%Y"))
        else:
            self.ent_onarim_tarih.delete(0, tk.END)

    def listeyi_guncelle(self):
        """Ana takip tablosunu hiyerarşik yapı ve filtrelerle günceller."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        f_bolge = self.cmb_filtre_bolge.get()
        f_parca = self.cmb_filtre_parca.get()
        f_durum = self.cmb_filtre_durum.get()
        f_arama = tr_upper(self.ent_arama.get())

        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute("SELECT id, bolge, sistem_adi, sistem_pn, sistem_sn, parca_adi, parca_pn, parca_sn, durum, onarim_tarih, aciklama FROM parcalar")
            kayitlar = cursor.fetchall()

            toplam = len(kayitlar)
            faal = 0
            yedek = 0
            onarimda = 0
            kritik = 0
            gayri = 0

            bolge_dict = {}
            bugun = datetime.date.today()

            for k in kayitlar:
                kid, bolge, s_adi, s_pn, s_sn, p_adi, p_pn, p_sn, durum, o_tarih, aciklama = k

                if durum == "FAAL":
                    faal += 1
                elif durum == "YEDEK PARÇA":
                    yedek += 1
                elif durum == "ONARIMDA":
                    onarimda += 1
                    if o_tarih:
                        try:
                            baslangic = datetime.datetime.strptime(o_tarih.strip(), "%d.%m.%Y").date()
                            if (bugun - baslangic).days >= 30:
                                kritik += 1
                        except ValueError:
                            pass
                elif durum == "GAYRI FAAL":
                    gayri += 1

                sure_durum_str = "-"
                tag = durum
                if durum == "ONARIMDA" and o_tarih:
                    try:
                        baslangic = datetime.datetime.strptime(o_tarih.strip(), "%d.%m.%Y").date()
                        gecen_gun = (bugun - baslangic).days
                        sure_durum_str = f"{gecen_gun} gündür onarımda"
                        if gecen_gun >= 30:
                            tag = "KRITIK_ONARIM"
                    except ValueError:
                        sure_durum_str = "Tarih Format Hatası"

                if f_bolge and f_bolge != "TÜMÜ" and bolge != f_bolge:
                    continue
                if f_parca and f_parca != "TÜMÜ" and p_adi != f_parca:
                    continue
                if f_durum and f_durum != "TÜMÜ":
                    if f_durum == "30 GÜN+ KRİTİK":
                        if tag != "KRITIK_ONARIM":
                            continue
                    elif durum != f_durum:
                        continue
                if f_arama:
                    toplu = tr_upper(f"{bolge} {s_adi} {s_pn} {s_sn} {p_adi} {p_pn} {p_sn} {durum} {aciklama}")
                    if f_arama not in toplu:
                        continue

                b_key = bolge if bolge else "BELİRTİLMEMİŞ BÖLGE"
                s_key = f"{s_adi} (PN: {s_pn or '-'} / SN: {s_sn or '-'})"

                if b_key not in bolge_dict:
                    bolge_dict[b_key] = {}
                if s_key not in bolge_dict[b_key]:
                    bolge_dict[b_key][s_key] = []
                
                bolge_dict[b_key][s_key].append((kid, p_adi, p_pn, p_sn, durum, o_tarih, sure_durum_str, aciklama, tag))

            for b_name, sistemler in bolge_dict.items():
                parent_b = self.tree.insert("", "end", text=f"📍 {b_name}", values=("", "", "", "", "", "", "", ""))
                for s_name, parcalar in sistemler.items():
                    parent_s = self.tree.insert(parent_b, "end", text=f"   🖥️ {s_name}", values=("", "", "", "", "", "", "", ""))
                    for p in parcalar:
                        kid, p_adi, p_pn, p_sn, durum, o_tarih, sure_str, aciklama, p_tag = p
                        self.tree.insert(
                            parent_s,
                            "end",
                            text=f"      ⚙️ {p_adi}",
                            values=(s_name.split(" (")[0], p_adi, p_pn or "-", p_sn or "-", durum, o_tarih if o_tarih else "-", sure_str, aciklama),
                            tags=(p_tag,)
                        )

            # İstatistikleri güncelle
            self.lbl_stat_toplam.config(text=str(toplam))
            self.lbl_stat_faal.config(text=str(faal))
            self.lbl_stat_yedek.config(text=str(yedek))
            self.lbl_stat_onarimda.config(text=str(onarimda))
            self.lbl_stat_kritik.config(text=str(kritik))
            self.lbl_stat_gayri.config(text=str(gayri))

        except sqlite3.Error as e:
            messagebox.showerror("Hata", f"Veriler listelenirken hata oluştu:\n{e}")
        finally:
            if conn:
                conn.close()

    def kayit_ekle(self):
        """Yeni kayıt ekler."""
        bolge = tr_upper(self.cmb_bolge.get().strip())
        sistem = tr_upper(self.ent_sistem.get().strip())
        sistem_pn = tr_upper(self.ent_sistem_pn.get().strip())
        sistem_sn = tr_upper(self.ent_sistem_sn.get().strip())
        parca = tr_upper(self.cmb_parca.get().strip())
        parca_pn = tr_upper(self.ent_parca_pn.get().strip())
        parca_sn = tr_upper(self.ent_parca_sn.get().strip())
        durum = self.cmb_durum.get().strip()
        onarim_tarih = self.ent_onarim_tarih.get().strip()
        aciklama = tr_upper(self.ent_not.get().strip())

        if not bolge or not sistem or not parca:
            messagebox.showwarning("Eksik Bilgi", "Lütfen en az Bölge, Sistem Adı ve Parça Adı alanlarını doldurun!")
            return

        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO parcalar (bolge, sistem_adi, sistem_pn, sistem_sn, parca_adi, parca_pn, parca_sn, durum, onarim_tarih, aciklama)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (bolge, sistem, sistem_pn, sistem_sn, parca, parca_pn, parca_sn, durum, onarim_tarih, aciklama))
            conn.commit()
            
            self.log_yaz("YENİ KAYIT", f"{bolge} bölgesine {sistem} / {parca} eklendi.")
            messagebox.showinfo("Başarılı", "Kayıt başarıyla eklendi.")
            
            self.bolge_listesini_guncelle()
            self.parca_listesini_guncelle()
            self.filtre_listesini_guncelle()
            self.listeyi_guncelle()
        except sqlite3.Error as e:
            messagebox.showerror("Hata", f"Kayıt eklenirken hata oluştu:\n{e}")
        finally:
            if conn:
                conn.close()

    def tablodan_satir_sec(self, event):
        """Tablodan seçilen satırın verilerini forma yükler."""
        selected = self.tree.selection()
        if not selected:
            return
        
        values = self.tree.item(selected[0], "values")
        if not values or len(values) < 8 or values[0] == "":
            return

        sistem_adi = values[0]
        parca_adi = values[1]
        parca_pn = values[2] if values[2] != "-" else ""
        parca_sn = values[3] if values[3] != "-" else ""

        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, bolge, sistem_adi, sistem_pn, sistem_sn, parca_adi, parca_pn, parca_sn, durum, onarim_tarih, aciklama 
                FROM parcalar WHERE sistem_adi = ? AND parca_adi = ? AND (parca_pn = ? OR parca_pn IS NULL) AND (parca_sn = ? OR parca_sn IS NULL)
            """, (sistem_adi, parca_adi, parca_pn, parca_sn))
            row = cursor.fetchone()
            if row:
                self.secili_kayit_id = row[0]
                self.cmb_bolge.set(row[1])
                self.ent_sistem.delete(0, tk.END)
                self.ent_sistem.insert(0, row[2])
                self.ent_sistem_pn.delete(0, tk.END)
                self.ent_sistem_pn.insert(0, row[3] if row[3] else "")
                self.ent_sistem_sn.delete(0, tk.END)
                self.ent_sistem_sn.insert(0, row[4] if row[4] else "")
                self.cmb_parca.set(row[5])
                self.ent_parca_pn.delete(0, tk.END)
                self.ent_parca_pn.insert(0, row[6] if row[6] else "")
                self.ent_parca_sn.delete(0, tk.END)
                self.ent_parca_sn.insert(0, row[7] if row[7] else "")
                self.cmb_durum.set(row[8])
                self.ent_onarim_tarih.delete(0, tk.END)
                if row[9]:
                    self.ent_onarim_tarih.insert(0, row[9])
                self.ent_not.delete(0, tk.END)
                self.ent_not.insert(0, row[10] if row[10] else "")
        except sqlite3.Error as e:
            print(f"Satır seçilemedi: {e}")
        finally:
            if conn:
                conn.close()

    def degisiklikleri_kaydet_tiklandi(self):
        """Seçili kaydı günceller."""
        if not self.secili_kayit_id:
            messagebox.showwarning("Seçim Yapılmadı", "Lütfen tablodan güncellemek istediğiniz bir kayıt seçin!")
            return

        bolge = tr_upper(self.cmb_bolge.get().strip())
        sistem = tr_upper(self.ent_sistem.get().strip())
        sistem_pn = tr_upper(self.ent_sistem_pn.get().strip())
        sistem_sn = tr_upper(self.ent_sistem_sn.get().strip())
        parca = tr_upper(self.cmb_parca.get().strip())
        parca_pn = tr_upper(self.ent_parca_pn.get().strip())
        parca_sn = tr_upper(self.ent_parca_sn.get().strip())
        durum = self.cmb_durum.get().strip()
        onarim_tarih = self.ent_onarim_tarih.get().strip()
        aciklama = tr_upper(self.ent_not.get().strip())

        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE parcalar SET bolge=?, sistem_adi=?, sistem_pn=?, sistem_sn=?, parca_adi=?, parca_pn=?, parca_sn=?, durum=?, onarim_tarih=?, aciklama=?
                WHERE id=?
            """, (bolge, sistem, sistem_pn, sistem_sn, parca, parca_pn, parca_sn, durum, onarim_tarih, aciklama, self.secili_kayit_id))
            conn.commit()

            self.log_yaz("GÜNCELLEME", f"Kayıt ID {self.secili_kayit_id} güncellendi.")
            messagebox.showinfo("Başarılı", "Değişiklikler kaydedildi.")
            self.listeyi_guncelle()
        except sqlite3.Error as e:
            messagebox.showerror("Hata", f"Güncelleme sırasında hata oluştu:\n{e}")
        finally:
            if conn:
                conn.close()

    def hizli_durum_degis(self, yeni_durum):
        """Sağ tık menüsünden hızlı durum güncellenmesini sağlar."""
        if not self.secili_kayit_id:
            messagebox.showwarning("Uyarı", "Lütfen bir kayıt seçin.")
            return
        
        self.cmb_durum.set(yeni_durum)
        self.durum_degisti_kontrol(None)
        self.degisiklikleri_kaydet_tiklandi()

    def kayit_sil(self):
        """Seçili kaydı siler."""
        if not self.secili_kayit_id:
            messagebox.showwarning("Seçim Yapılmadı", "Lütfen silinecek bir kayıt seçin!")
            return

        if messagebox.askyesno("Onay", "Seçili kaydı silmek istediğinize emin misiniz?"):
            conn = None
            try:
                conn = sqlite3.connect(DB_DOSYASI)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM parcalar WHERE id=?", (self.secili_kayit_id,))
                conn.commit()

                self.log_yaz("SİLME", f"Kayıt ID {self.secili_kayit_id} silindi.")
                messagebox.showinfo("Başarılı", "Kayıt silindi.")
                
                self.secili_kayit_id = None
                self.formu_temizle()
                self.listeyi_guncelle()
                self.filtre_listesini_guncelle()
            except sqlite3.Error as e:
                messagebox.showerror("Hata", f"Silme işlemi başarısız:\n{e}")
            finally:
                if conn:
                    conn.close()

    def formu_temizle(self):
        """Giriş formunu sıfırlar."""
        self.secili_kayit_id = None
        for widget in self.form_widgets.values():
            if isinstance(widget, ttk.Combobox):
                widget.set("")
            elif isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)
        self.cmb_durum.set("FAAL")

    def sag_tik_menu_goster(self, event):
        """Sağ tık menüsünü açar."""
        try:
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
                self.tablodan_satir_sec(None)
                self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def gunluk_not_ekle(self):
        """Günlük not kaydeder."""
        tarih = self.ent_not_tarih.get().strip()
        bolge = tr_upper(self.cmb_not_bolge.get().strip())
        detay = tr_upper(self.txt_gunluk_detay.get("1.0", tk.END).strip())

        if not bolge or not detay:
            messagebox.showwarning("Eksik Bilgi", "Lütfen Bölge ve Not Detayı alanlarını doldurun!")
            return

        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO gunluk_notlar (tarih, bolge, detay) VALUES (?, ?, ?)", (tarih, bolge, detay))
            conn.commit()

            self.log_yaz("NOT EKLE", f"{bolge} bölgesi için günlük not eklendi.")
            messagebox.showinfo("Başarılı", "Not kaydedildi.")
            self.txt_gunluk_detay.delete("1.0", tk.END)
            self.gunluk_notlari_yukle()
        except sqlite3.Error as e:
            messagebox.showerror("Hata", f"Not eklenemedi:\n{e}")
        finally:
            if conn:
                conn.close()

    def gunluk_notlari_yukle(self):
        """Günlük notları listeler."""
        for row in self.tree_notlar.get_children():
            self.tree_notlar.delete(row)

        f_bolge = self.cmb_not_filtre_bolge.get()
        f_arama = tr_upper(self.ent_not_arama.get())

        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute("SELECT id, tarih, bolge, detay FROM gunluk_notlar ORDER BY id DESC")
            for row in cursor.fetchall():
                nid, ntarih, nbolge, ndetay = row
                if f_bolge and f_bolge != "TÜMÜ" and nbolge != f_bolge:
                    continue
                if f_arama and f_arama not in tr_upper(ndetay):
                    continue
                self.tree_notlar.insert("", "end", values=(nid, ntarih, nbolge, ndetay))
        except sqlite3.Error as e:
            print(f"Notlar yüklenemedi: {e}")
        finally:
            if conn:
                conn.close()

    def gunluk_not_sil(self):
        """Seçilen günlük notu siler."""
        selected = self.tree_notlar.selection()
        if not selected:
            messagebox.showwarning("Seçim Yapılmadı", "Lütfen silinecek bir not seçin!")
            return

        nid = self.tree_notlar.item(selected[0], "values")[0]
        if messagebox.askyesno("Onay", "Seçili notu silmek istiyor musunuz?"):
            conn = None
            try:
                conn = sqlite3.connect(DB_DOSYASI)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM gunluk_notlar WHERE id=?", (nid,))
                conn.commit()
                self.log_yaz("NOT SİL", f"Not ID {nid} silindi.")
                self.gunluk_notlari_yukle()
            except sqlite3.Error as e:
                messagebox.showerror("Hata", f"Not silinemedi:\n{e}")
            finally:
                if conn:
                    conn.close()

    def not_detay_penceresi_ac(self, event):
        """Çift tıklandığında not detayını büyük pencerede açar."""
        selected = self.tree_notlar.selection()
        if not selected:
            return
        values = self.tree_notlar.item(selected[0], "values")
        
        top = tk.Toplevel(self.root)
        top.title(f"Günlük Not Detayı - ID: {values[0]}")
        top.geometry("500x320")
        top.configure(bg="#f8fafc")

        tk.Label(top, text=f"Tarih: {values[1]} | Bölge: {values[2]}", font=("Segoe UI", 9, "bold"), bg="#f8fafc", fg="#334155").pack(anchor="w", padx=12, pady=10)

        txt = tk.Text(top, font=("Segoe UI", 10), wrap="word", bg="#ffffff", fg="#1e293b", padx=10, pady=10, relief="solid", bd=1)
        txt.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        txt.insert("1.0", values[3])
        txt.config(state="disabled")

    def bolge_parcalarini_goster(self):
        """Seçilen bölgenin parçalarını popup pencerede gösterir."""
        bolge = self.cmb_not_bolge.get().strip()
        if not bolge:
            messagebox.showwarning("Uyarı", "Lütfen bir bölge seçin!")
            return

        top = tk.Toplevel(self.root)
        top.title(f"Bölge Parça Envanteri - {bolge}")
        top.geometry("750x400")

        columns = ("Sistem", "Parca", "Durum", "Aciklama")
        tree = ttk.Treeview(top, columns=columns, show="headings")
        tree.heading("Sistem", text="SİSTEM")
        tree.heading("Parca", text="PARÇA")
        tree.heading("Durum", text="DURUM")
        tree.heading("Aciklama", text="AÇIKLAMA")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute("SELECT sistem_adi, parca_adi, durum, aciklama FROM parcalar WHERE bolge = ?", (bolge,))
            for row in cursor.fetchall():
                tree.insert("", "end", values=row)
        except sqlite3.Error as e:
            print(f"Bölge parçaları alınamadı: {e}")
        finally:
            if conn:
                conn.close()

    def kritik_parcalari_goster_popip(self):
        """30 günü aşan onarımları listeler."""
        top = tk.Toplevel(self.root)
        top.title("Kritik Onarımdaki Parçalar (30 Gün ve Üzeri)")
        top.geometry("850x400")

        columns = ("Bolge", "Sistem", "Parca", "Tarih", "Sure")
        tree = ttk.Treeview(top, columns=columns, show="headings")
        tree.heading("Bolge", text="BÖLGE")
        tree.heading("Sistem", text="SİSTEM")
        tree.heading("Parca", text="PARÇA")
        tree.heading("Tarih", text="ONARIM BAŞL.")
        tree.heading("Sure", text="GEÇEN SÜRE")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute("SELECT bolge, sistem_adi, parca_adi, onarim_tarih FROM parcalar WHERE durum = 'ONARIMDA'")
            bugun = datetime.date.today()
            for row in cursor.fetchall():
                bolge, sistem, parca, o_tarih = row
                if o_tarih:
                    try:
                        baslangic = datetime.datetime.strptime(o_tarih.strip(), "%d.%m.%Y").date()
                        gecen = (bugun - baslangic).days
                        if gecen >= 30:
                            tree.insert("", "end", values=(bolge, sistem, parca, o_tarih, f"{gecen} gün"))
                    except ValueError:
                        pass
        except sqlite3.Error as e:
            print(f"Kritik parçalar alınamadı: {e}")
        finally:
            if conn:
                conn.close()

    def acilis_kritik_kontrolu(self):
        """Açılışta 30 günü geçen onarımlar varsa uyarı gösterir."""
        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute("SELECT bolge, sistem_adi, parca_adi, onarim_tarih FROM parcalar WHERE durum = 'ONARIMDA'")
            bugun = datetime.date.today()
            kritikler = 0
            for row in cursor.fetchall():
                _, _, _, o_tarih = row
                if o_tarih:
                    try:
                        baslangic = datetime.datetime.strptime(o_tarih.strip(), "%d.%m.%Y").date()
                        if (bugun - baslangic).days >= 30:
                            kritikler += 1
                    except ValueError:
                        pass
            if kritiklar > 0:
                root.after(500, lambda: messagebox.showwarning("Kritik Uyarı", f"Dikkat! 30 günü aşmış {kritikler} adet onarımda parça bulunmaktadır."))
        except Exception:
            pass
        finally:
            if conn:
                conn.close()

    def verileri_disa_aktar(self):
        """Verileri CSV dosyasına aktarır."""
        dosya = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Dosyası", "*.csv"), ("Tüm Dosyalar", "*.*")])
        if not dosya:
            return

        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute("SELECT bolge, sistem_adi, sistem_pn, sistem_sn, parca_adi, parca_pn, parca_sn, durum, onarim_tarih, aciklama FROM parcalar")
            rows = cursor.fetchall()

            with open(dosya, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Bölge", "Sistem Adı", "Sistem PN", "Sistem SN", "Parça Adı", "Parça PN", "Parça SN", "Durum", "Onarım Tarihi", "Açıklama"])
                writer.writerows(rows)

            messagebox.showinfo("Başarılı", "Veriler CSV formatında dışa aktarıldı.")
            self.log_yaz("DIŞARI AKTAR", f"Veriler dışa aktarıldı: {os.path.basename(dosya)}")
        except Exception as e:
            messagebox.showerror("Hata", f"Dışa aktarılamadı:\n{e}")
        finally:
            if conn:
                conn.close()

    def verileri_ice_aktar(self):
        """CSV dosyasından toplu veri içe aktarır."""
        dosya = filedialog.askopenfilename(filetypes=[("CSV Dosyası", "*.csv"), ("Tüm Dosyalar", "*.*")])
        if not dosya:
            return

        conn = None
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            eklenen = 0
            with open(dosya, mode="r", encoding="utf-8-sig") as f:
                reader = csv.reader(f, delimiter=";")
                next(reader, None) # Başlık atla
                for row in reader:
                    if len(row) >= 10:
                        cursor.execute("""
                            INSERT INTO parcalar (bolge, sistem_adi, sistem_pn, sistem_sn, parca_adi, parca_pn, parca_sn, durum, onarim_tarih, aciklama)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))
                        eklenen += 1
            conn.commit()
            messagebox.showinfo("Başarılı", f"Toplam {eklenen} kayıt başarıyla içe aktarıldı.")
            self.log_yaz("İÇE AKTAR", f"{eklenen} adet kayıt dışarıdan alındı.")
            self.bolge_listesini_guncelle()
            self.parca_listesini_guncelle()
            self.filtre_listesini_guncelle()
            self.listeyi_guncelle()
        except Exception as e:
            messagebox.showerror("Hata", f"İçe aktarma sırasında hata oluştu:\n{e}")
        finally:
            if conn:
                conn.close()

    def servis_formu_olustur(self):
        """Seçili parça için servis tutanağı metin belgesi üretir."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Seçim Yapılmadı", "Lütfen bir kayıt seçin!")
            return

        values = self.tree.item(selected[0], "values")
        if not values or len(values) < 8 or values[0] == "":
            messagebox.showwarning("Uyarı", "Lütfen ana parça satırlarından birini seçin!")
            return

        dosya = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Metin Belgesi", "*.txt")])
        if not dosya:
            return

        try:
            with open(dosya, mode="w", encoding="utf-8") as f:
                f.write("========================================\n")
                f.write("       KURUMSAL SERVİS TUTANAĞI         \n")
                f.write("========================================\n")
                f.write(f"Düzenleme Tarihi : {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
                f.write(f"Sistem Adı       : {values[0]}\n")
                f.write(f"Parça Adı        : {values[1]}\n")
                f.write(f"Parça P/N        : {values[2]}\n")
                f.write(f"Parça S/N        : {values[3]}\n")
                f.write(f"Durumu           : {values[4]}\n")
                f.write(f"Onarım Başlangıç : {values[5]}\n")
                f.write(f"Süre/Kontrol     : {values[6]}\n")
                f.write(f"Açıklama         : {values[7]}\n")
                f.write("========================================\n")
                f.write("Teknisyen İmza / Kaşe:\n\n\n")

            messagebox.showinfo("Başarılı", "Servis formu oluşturuldu.")
            self.log_yaz("SERVİS FORMU", f"Servis formu kaydedildi: {os.path.basename(dosya)}")
        except Exception as e:
            messagebox.showerror("Hata", f"Servis formu oluşturulamadı:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SistemTakipApp(root)
    root.mainloop()