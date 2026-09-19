import csv
import datetime
import os
import sqlite3
DB_DOSYASI = "sistem_takip.db"


def tr_upper(text):
    """Türkçe karakterleri doğru şekilde büyük harfe dönüştürür."""
    if not text:
        return ""
    donusum = {
        "i": "İ",
        "ı": "I",
        "ğ": "Ğ",
        "ü": "Ü",
        "ş": "Ş",
        "ö": "Ö",
        "ç": "Ç",
    }
    for k, v in donusum.items():
        text = text.replace(k, v)
    return text.upper()


class SistemTakipApp:

    def __init__(self, root):
        self.root = root
        self.root.title(
            "Sistem ve Parça Bakım Takip Sistemi - Gelişmiş Sürüm (2026)"
        )
        self.root.geometry("1400x750")
        self.root.configure(bg="#f1f5f9")

        self.secili_kayit_id = None
        self.db_olustur()

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TCombobox",
            fieldbackground="#ffffff",
            background="#e2e8f0",
            foreground="#0f172a",
            padding=3,
        )
        style.configure(
            "Treeview",
            rowheight=24,
            font=("Segoe UI", 9, "bold"),
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#0f172a",
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#e2e8f0",
            foreground="#1e293b",
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", "#0284c7")],
            foreground=[("selected", "#ffffff")],
        )

        vcmd = (root.register(self.tiklandiginda_buyuk_harf_yap), "%P")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_takip = tk.Frame(self.notebook, bg="#f1f5f9")
        self.tab_notlar = tk.Frame(self.notebook, bg="#f1f5f9")
        self.tab_log = tk.Frame(self.notebook, bg="#f1f5f9")

        self.notebook.add(self.tab_takip, text="  📊 Sistem & Parça Takip  ")
        self.notebook.add(self.tab_notlar, text="  📝 Günlük İş Notları  ")
        self.notebook.add(
            self.tab_log, text="  📜 İşlem & Arıza Geçmişi (Log)  "
        )

        # ==================== 1. SEKME: TAKİP EKRANI ====================
        main_container = tk.Frame(self.tab_takip, bg="#f1f5f9")
        main_container.pack(fill="both", expand=True, padx=6, pady=6)

        stat_outer_frame = tk.LabelFrame(
            main_container,
            text=" 📈 GENEL DURUM ÖZETİ ",
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            padx=8,
            pady=4,
            relief="solid",
            bd=1,
            highlightbackground="#cbd5e1",
        )
        stat_outer_frame.pack(fill="x", padx=0, pady=(0, 4))

        stat_frame = tk.Frame(stat_outer_frame, bg="#ffffff")
        stat_frame.pack(fill="x", expand=True)

        self.lbl_stat_toplam = self.create_stat_badge(
            stat_frame, "Toplam", "0", "#2563eb", "#eff6ff"
        )
        self.lbl_stat_faal = self.create_stat_badge(
            stat_frame, "Faal", "0", "#16a34a", "#f0fdf4"
        )
        self.lbl_stat_yedek = self.create_stat_badge(
            stat_frame, "Yedek", "0", "#9333ea", "#faf5ff"
        )
        self.lbl_stat_onarimda = self.create_stat_badge(
            stat_frame, "Onarımda", "0", "#d97706", "#fefce8"
        )
        self.lbl_stat_kritik = self.create_stat_badge(
            stat_frame, "30 Gün+ Kritik", "0", "#dc2626", "#fef2f2"
        )
        self.lbl_stat_gayri = self.create_stat_badge(
            stat_frame, "Gayri Faal", "0", "#e11d48", "#fff1f2"
        )

        btn_kritik_uyari = tk.Button(
            stat_frame,
            text="🔔 Kritik Uyarılar",
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2,
            command=self.kritik_parcalari_goster_popip,
        )
        btn_kritik_uyari.pack(side="right", padx=(8, 0))

        top_split_frame = tk.Frame(main_container, bg="#f1f5f9")
        top_split_frame.pack(fill="x", padx=0, pady=(0, 4))

        form_frame = tk.LabelFrame(
            top_split_frame,
            text=" 🗂️ SİSTEM VE PARÇA YÖNETİM PANELİ ",
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#0f172a",
            padx=8,
            pady=6,
            relief="solid",
            bd=1,
            highlightbackground="#64748b",
        )
        form_frame.pack(side="left", fill="both", expand=True, padx=(0, 4))

        inner_box_container = tk.Frame(form_frame, bg="#ffffff")
        inner_box_container.pack(fill="both", expand=True)

        sistem_box = tk.LabelFrame(
            inner_box_container,
            text=" 🖥️ Sistem Bilgileri ",
            font=("Segoe UI", 8, "bold"),
            bg="#f0f9ff",
            fg="#0369a1",
            padx=8,
            pady=4,
            relief="solid",
            bd=1,
            highlightbackground="#38bdf8",
        )
        sistem_box.pack(
            side="left", fill="both", expand=True, padx=(0, 3), pady=2
        )

        parca_box = tk.LabelFrame(
            inner_box_container,
            text=" ⚙️ Parça & Durum Bilgileri ",
            font=("Segoe UI", 8, "bold"),
            bg="#f0fdf4",
            fg="#15803d",
            padx=8,
            pady=4,
            relief="solid",
            bd=1,
            highlightbackground="#4ade80",
        )
        parca_box.pack(
            side="right", fill="both", expand=True, padx=(3, 0), pady=2
        )

        kutu_genisligi = 16

        # Sistem Bilgileri
        tk.Label(
            sistem_box,
            text="Bölge:",
            font=("Segoe UI", 8, "bold"),
            bg="#f0f9ff",
            fg="#0f172a",
        ).grid(row=0, column=0, sticky="w", padx=3, pady=2)
        self.cmb_bolge = ttk.Combobox(
            sistem_box, width=kutu_genisligi, state="normal"
        )
        self.cmb_bolge.grid(row=0, column=1, padx=3, pady=2, sticky="w")
        self.cmb_bolge.bind(
            "<<ComboboxSelected>>", self.bolge_otomatik_doldur_event
        )

        tk.Label(
            sistem_box,
            text="Sistem Adı:",
            font=("Segoe UI", 8, "bold"),
            bg="#f0f9ff",
            fg="#0f172a",
        ).grid(row=1, column=0, sticky="w", padx=3, pady=2)
        self.ent_sistem = tk.Entry(
            sistem_box,
            width=kutu_genisligi + 2,
            font=("Segoe UI", 8),
            validate="key",
            validatecommand=vcmd,
            bg="#ffffff",
            fg="#0f172a",
            relief="solid",
            bd=1,
        )
        self.ent_sistem.grid(row=1, column=1, padx=3, pady=2, sticky="w")

        tk.Label(
            sistem_box,
            text="Sistem PN:",
            font=("Segoe UI", 8, "bold"),
            bg="#f0f9ff",
            fg="#0f172a",
        ).grid(row=2, column=0, sticky="w", padx=3, pady=2)
        self.ent_sistem_pn = tk.Entry(
            sistem_box,
            width=kutu_genisligi + 2,
            font=("Segoe UI", 8),
            validate="key",
            validatecommand=vcmd,
            bg="#ffffff",
            fg="#0f172a",
            relief="solid",
            bd=1,
        )
        self.ent_sistem_pn.grid(row=2, column=1, padx=3, pady=2, sticky="w")

        tk.Label(
            sistem_box,
            text="Sistem SN:",
            font=("Segoe UI", 8, "bold"),
            bg="#f0f9ff",
            fg="#0f172a",
        ).grid(row=3, column=0, sticky="w", padx=3, pady=2)
        self.ent_sistem_sn = tk.Entry(
            sistem_box,
            width=kutu_genisligi + 2,
            font=("Segoe UI", 8),
            validate="key",
            validatecommand=vcmd,
            bg="#ffffff",
            fg="#0f172a",
            relief="solid",
            bd=1,
        )
        self.ent_sistem_sn.grid(row=3, column=1, padx=3, pady=2, sticky="w")

        # Parça Bilgileri
        tk.Label(
            parca_box,
            text="Parça Adı:",
            font=("Segoe UI", 8, "bold"),
            bg="#f0fdf4",
            fg="#0f172a",
        ).grid(row=0, column=0, sticky="w", padx=3, pady=2)
        self.cmb_parca = ttk.Combobox(
            parca_box, width=kutu_genisligi, state="normal"
        )
        self.cmb_parca.grid(row=0, column=1, padx=3, pady=2, sticky="w")
        self.cmb_parca.bind(
            "<<ComboboxSelected>>", self.parca_otomatik_doldur_event
        )

        tk.Label(
            parca_box,
            text="Parça PN:",
            font=("Segoe UI", 8, "bold"),
            bg="#f0fdf4",
            fg="#0f172a",
        ).grid(row=1, column=0, sticky="w", padx=3, pady=2)
        self.ent_parca_pn = tk.Entry(
            parca_box,
            width=kutu_genisligi + 2,
            font=("Segoe UI", 8),
            validate="key",
            validatecommand=vcmd,
            bg="#ffffff",
            fg="#0f172a",
            relief="solid",
            bd=1,
        )
        self.ent_parca_pn.grid(row=1, column=1, padx=3, pady=2, sticky="w")

        tk.Label(
            parca_box,
            text="Parça SN:",
            font=("Segoe UI", 8, "bold"),
            bg="#f0fdf4",
            fg="#0f172a",
        ).grid(row=2, column=0, sticky="w", padx=3, pady=2)
        self.ent_parca_sn = tk.Entry(
            parca_box,
            width=kutu_genisligi + 2,
            font=("Segoe UI", 8),
            validate="key",
            validatecommand=vcmd,
            bg="#ffffff",
            fg="#0f172a",
            relief="solid",
            bd=1,
        )
        self.ent_parca_sn.grid(row=2, column=1, padx=3, pady=2, sticky="w")

        tk.Label(
            parca_box,
            text="Parça Durumu:",
            font=("Segoe UI", 8, "bold"),
            bg="#f0fdf4",
            fg="#0f172a",
        ).grid(row=3, column=0, sticky="w", padx=3, pady=2)
        self.cmb_durum = ttk.Combobox(
            parca_box,
            values=["FAAL", "YEDEK PARÇA", "ONARIMDA", "GAYRI FAAL"],
            width=kutu_genisligi,
            state="readonly",
        )
        self.cmb_durum.grid(row=3, column=1, padx=3, pady=2, sticky="w")
        self.cmb_durum.set("FAAL")
        self.cmb_durum.bind("<<ComboboxSelected>>", self.durum_degisti_kontrol)

        self.lbl_onarim_tarih = tk.Label(
            parca_box,
            text="Onarım Başl. T.:",
            font=("Segoe UI", 8, "bold"),
            bg="#f0fdf4",
            fg="#0f172a",
        )
        self.lbl_onarim_tarih.grid(row=4, column=0, sticky="w", padx=3, pady=2)
        self.ent_onarim_tarih = tk.Entry(
            parca_box,
            width=kutu_genisligi + 2,
            font=("Segoe UI", 8),
            bg="#ffffff",
            fg="#0f172a",
            relief="solid",
            bd=1,
        )
        self.ent_onarim_tarih.grid(row=4, column=1, padx=3, pady=2, sticky="w")

        tk.Label(
            parca_box,
            text="Açıklama:",
            font=("Segoe UI", 8, "bold"),
            bg="#f0fdf4",
            fg="#0f172a",
        ).grid(row=5, column=0, sticky="w", padx=3, pady=2)
        self.ent_not = tk.Entry(
            parca_box,
            width=kutu_genisligi + 2,
            font=("Segoe UI", 8),
            validate="key",
            validatecommand=vcmd,
            bg="#ffffff",
            fg="#0f172a",
            relief="solid",
            bd=1,
        )
        self.ent_not.grid(row=5, column=1, padx=3, pady=2, sticky="w")

        # İşlem Menüsü
        action_menu_frame = tk.LabelFrame(
            top_split_frame,
            text=" ⚙️ İşlem Menüsü ",
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#0f172a",
            padx=8,
            pady=4,
            relief="solid",
            bd=1,
            highlightbackground="#cbd5e1",
        )
        action_menu_frame.pack(side="right", fill="y", padx=(0, 0), ipadx=2)

        btn_kaydet = tk.Button(
            action_menu_frame,
            text="💾 Değişiklikleri Kaydet",
            bg="#0284c7",
            fg="white",
            activebackground="#0369a1",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            command=self.degisiklikleri_kaydet_tiklandi,
            width=18,
            pady=2,
        )
        btn_kaydet.pack(fill="x", pady=2)

        btn_ekle = tk.Button(
            action_menu_frame,
            text="➕ Yeni Kayıt Ekle",
            bg="#16a34a",
            fg="white",
            activebackground="#15803d",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            command=self.kayit_ekle,
            width=18,
            pady=2,
        )
        btn_ekle.pack(fill="x", pady=2)

        btn_guncelle = tk.Button(
            action_menu_frame,
            text="🔄 Durumu Güncelle",
            bg="#d97706",
            fg="white",
            activebackground="#b45309",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            command=self.durum_guncelle,
            width=18,
            pady=2,
        )
        btn_guncelle.pack(fill="x", pady=2)

        btn_disari_aktar = tk.Button(
            action_menu_frame,
            text="📊 Excel / CSV Aktar",
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            command=self.verileri_disa_aktar,
            width=18,
            pady=2,
        )
        btn_disari_aktar.pack(fill="x", pady=2)

        btn_rapor = tk.Button(
            action_menu_frame,
            text="📄 Servis Formu",
            bg="#7c3aed",
            fg="white",
            activebackground="#6d28d9",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            command=self.servis_formu_olustur,
            width=18,
            pady=2,
        )
        btn_rapor.pack(fill="x", pady=2)

        btn_sil = tk.Button(
            action_menu_frame,
            text="🗑️ Seçili Kaydı Sil",
            bg="#e11d48",
            fg="white",
            activebackground="#be123c",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            command=self.kayit_sil,
            width=18,
            pady=2,
        )
        btn_sil.pack(fill="x", pady=2)

        # Filtreleme Alanı
        filter_frame = tk.Frame(main_container, bg="#f1f5f9")
        filter_frame.pack(fill="x", padx=0, pady=(0, 4))

        tk.Label(
            filter_frame,
            text="🔍 Bölge:",
            font=("Segoe UI", 8, "bold"),
            bg="#f1f5f9",
            fg="#334155",
        ).pack(side="left", padx=(0, 2))
        self.cmb_filtre_bolge = ttk.Combobox(
            filter_frame, width=12, state="readonly"
        )
        self.cmb_filtre_bolge.pack(side="left", padx=(0, 8))
        self.cmb_filtre_bolge.bind(
            "<<ComboboxSelected>>", lambda e: self.listeyi_guncelle()
        )

        tk.Label(
            filter_frame,
            text="🔍 Parça:",
            font=("Segoe UI", 8, "bold"),
            bg="#f1f5f9",
            fg="#334155",
        ).pack(side="left", padx=(0, 2))
        self.cmb_filtre_parca = ttk.Combobox(
            filter_frame, width=12, state="readonly"
        )
        self.cmb_filtre_parca.pack(side="left", padx=(0, 8))
        self.cmb_filtre_parca.bind(
            "<<ComboboxSelected>>", lambda e: self.listeyi_guncelle()
        )

        tk.Label(
            filter_frame,
            text="🔍 Durum:",
            font=("Segoe UI", 8, "bold"),
            bg="#f1f5f9",
            fg="#334155",
        ).pack(side="left", padx=(0, 2))
        self.cmb_filtre_durum = ttk.Combobox(
            filter_frame,
            values=[
                "TÜMÜ",
                "FAAL",
                "YEDEK PARÇA",
                "ONARIMDA",
                "30 GÜN+ KRİTİK",
                "GAYRI FAAL",
            ],
            width=14,
            state="readonly",
        )
        self.cmb_filtre_durum.pack(side="left", padx=(0, 8))
        self.cmb_filtre_durum.set("TÜMÜ")
        self.cmb_filtre_durum.bind(
            "<<ComboboxSelected>>", lambda e: self.listeyi_guncelle()
        )

        tk.Label(
            filter_frame,
            text="🔎 Genel Ara:",
            font=("Segoe UI", 8, "bold"),
            bg="#f1f5f9",
            fg="#334155",
        ).pack(side="left", padx=(0, 2))
        self.ent_arama = tk.Entry(
            filter_frame,
            width=18,
            font=("Segoe UI", 8),
            bg="#ffffff",
            fg="#0f172a",
            relief="solid",
            bd=1,
        )
        self.ent_arama.pack(side="left", padx=(0, 4))
        self.ent_arama.bind("<KeyRelease>", lambda e: self.listeyi_guncelle())

        # Tablo Alanı
        table_frame = tk.Frame(
            main_container,
            bg="#ffffff",
            bd=1,
            relief="solid",
            highlightbackground="#cbd5e1",
        )
        table_frame.pack(fill="both", expand=True, padx=0, pady=0)

        columns = (
            "Sistem",
            "Parca",
            "ParcaPN",
            "ParcaSN",
            "Durum",
            "OnarimTarih",
            "SureDurum",
            "Aciklama",
        )
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="tree headings"
        )

        self.tree.heading("#0", text="  BÖLGE / SİSTEM PN / SİSTEM SN")
        self.tree.heading("Sistem", text="SİSTEM ADI")
        self.tree.heading("Parca", text="PARÇA ADI")
        self.tree.heading("ParcaPN", text="PARÇA PN")
        self.tree.heading("ParcaSN", text="PARÇA SN")
        self.tree.heading("Durum", text="DURUMU")
        self.tree.heading("OnarimTarih", text="ONARIM BAŞL.")
        self.tree.heading("SureDurum", text="SÜRE KONTROL")
        self.tree.heading("Aciklama", text="AÇIKLAMA")

        self.tree.column("#0", width=220, anchor="w")
        self.tree.column("Sistem", width=100, anchor="w")
        self.tree.column("Parca", width=100, anchor="w")
        self.tree.column("ParcaPN", width=90, anchor="w")
        self.tree.column("ParcaSN", width=100, anchor="w")
        self.tree.column("Durum", width=95, anchor="w")
        self.tree.column("OnarimTarih", width=95, anchor="w")
        self.tree.column("SureDurum", width=120, anchor="w")
        self.tree.column("Aciklama", width=140, anchor="w")

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.tablodan_satir_sec)

        self.tree.tag_configure(
            "FAAL", background="#dcfce7", foreground="#166534"
        )
        self.tree.tag_configure(
            "YEDEK PARÇA", background="#f3e8ff", foreground="#6b21a8"
        )
        self.tree.tag_configure(
            "ONARIMDA", background="#fef9c3", foreground="#854d0e"
        )
        self.tree.tag_configure(
            "KRITIK_ONARIM", background="#fee2e2", foreground="#991b1b"
        )
        self.tree.tag_configure(
            "GAYRI FAAL", background="#ffe4e6", foreground="#9f1239"
        )

        # ==================== 2. SEKME: GÜNLÜK İŞ NOTLARI ====================
        not_container = tk.Frame(self.tab_notlar, bg="#f1f5f9")
        not_container.pack(fill="both", expand=True, padx=8, pady=8)

        not_ust_frame = tk.Frame(not_container, bg="#f1f5f9")
        not_ust_frame.pack(fill="x", pady=(0, 6))

        tk.Label(
            not_ust_frame,
            text="Bölge Bazlı Günlük Yapılan İşler, Görevler ve Not Paneli",
            font=("Segoe UI", 10, "bold"),
            bg="#f1f5f9",
            fg="#0f172a",
        ).pack(side="left")

        btn_not_sil = tk.Button(
            not_ust_frame,
            text="🗑️ Seçili Notu Sil",
            bg="#e11d48",
            fg="white",
            activebackground="#be123c",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            command=self.gunluk_not_sil,
            padx=8,
            pady=2,
        )
        btn_not_sil.pack(side="right")

        not_form_frame = tk.LabelFrame(
            not_container,
            text=" ✍️ Bölgeye Göre Yeni Not veya İş Ekle ",
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#0f172a",
            padx=10,
            pady=8,
            relief="solid",
            bd=1,
            highlightbackground="#cbd5e1",
        )
        not_form_frame.pack(fill="x", pady=(0, 6))

        not_girdi_ic_frame = tk.Frame(not_form_frame, bg="#ffffff")
        not_girdi_ic_frame.pack(fill="x", expand=True)

        tk.Label(
            not_girdi_ic_frame,
            text="Tarih / Saat:",
            font=("Segoe UI", 8, "bold"),
            bg="#ffffff",
            fg="#0f172a",
        ).grid(row=0, column=0, sticky="w", padx=4, pady=2)
        self.ent_not_tarih = tk.Entry(
            not_girdi_ic_frame,
            width=18,
            font=("Segoe UI", 8),
            bg="#ffffff",
            fg="#0f172a",
            relief="solid",
            bd=1,
        )
        self.ent_not_tarih.grid(row=0, column=1, sticky="w", padx=4, pady=2)
        self.ent_not_tarih.insert(
            0, datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        )

        tk.Label(
            not_girdi_ic_frame,
            text="Bölge:",
            font=("Segoe UI", 8, "bold"),
            bg="#ffffff",
            fg="#0f172a",
        ).grid(row=0, column=2, sticky="w", padx=(15, 4), pady=2)
        self.cmb_not_bolge = ttk.Combobox(
            not_girdi_ic_frame, width=22, state="normal"
        )
        self.cmb_not_bolge.grid(row=0, column=3, sticky="w", padx=4, pady=2)

        btn_bolge_parcalari = tk.Button(
            not_girdi_ic_frame,
            text="🔍 Seçili Bölgenin Parçalarını Göster",
            bg="#0284c7",
            fg="white",
            activebackground="#0369a1",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            command=self.bolge_parcalarini_goster,
            padx=6,
            pady=1,
        )
        btn_bolge_parcalari.grid(
            row=0, column=4, sticky="w", padx=(10, 0), pady=2
        )

        tk.Label(
            not_girdi_ic_frame,
            text="İş / Not Detayı:",
            font=("Segoe UI", 8, "bold"),
            bg="#ffffff",
            fg="#0f172a",
        ).grid(row=1, column=0, sticky="nw", padx=4, pady=(6, 2))

        txt_frame = tk.Frame(not_girdi_ic_frame, bg="#ffffff")
        txt_frame.grid(
            row=1,
            column=1,
            columnspan=4,
            sticky="we",
            padx=4,
            pady=(6, 2),
        )

        self.txt_gunluk_detay = tk.Text(
            txt_frame,
            height=3,
            width=75,
            font=("Segoe UI", 8),
            bg="#ffffff",
            fg="#0f172a",
            relief="solid",
            bd=1,
            wrap="word",
        )
        self.txt_gunluk_detay.pack(side="left", fill="both", expand=True)

        txt_scrollbar = ttk.Scrollbar(
            txt_frame,
            orient="vertical",
            command=self.txt_gunluk_detay.yview,
        )
        self.txt_gunluk_detay.configure(yscrollcommand=txt_scrollbar.set)
        txt_scrollbar.pack(side="right", fill="y")

        self.txt_gunluk_detay.bind("<KeyRelease>", self.not_metni_buyut)

        btn_not_ekle = tk.Button(
            not_form_frame,
            text="➕ Notu Kaydet",
            bg="#16a34a",
            fg="white",
            activebackground="#15803d",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            command=self.gunluk_not_ekle,
            padx=12,
            pady=3,
        )
        btn_not_ekle.pack(anchor="e", pady=(4, 0))

        # --- Not Filtreleme Alanı ---
        not_filter_frame = tk.Frame(not_container, bg="#f1f5f9")
        not_filter_frame.pack(fill="x", pady=(0, 4))

        tk.Label(
            not_filter_frame,
            text="🔍 Bölgeye Göre Süz:",
            font=("Segoe UI", 8, "bold"),
            bg="#f1f5f9",
            fg="#334155",
        ).pack(side="left", padx=(0, 2))
        self.cmb_not_filtre_bolge = ttk.Combobox(
            not_filter_frame, width=15, state="readonly"
        )
        self.cmb_not_filtre_bolge.pack(side="left", padx=(0, 10))
        self.cmb_not_filtre_bolge.bind(
            "<<ComboboxSelected>>", lambda e: self.gunluk_notlari_yukle()
        )

        tk.Label(
            not_filter_frame,
            text="🔎 Not İçinde Ara:",
            font=("Segoe UI", 8, "bold"),
            bg="#f1f5f9",
            fg="#334155",
        ).pack(side="left", padx=(0, 2))
        self.ent_not_arama = tk.Entry(
            not_filter_frame,
            width=20,
            font=("Segoe UI", 8),
            bg="#ffffff",
            fg="#0f172a",
            relief="solid",
            bd=1,
        )
        self.ent_not_arama.pack(side="left", padx=(0, 4))
        self.ent_not_arama.bind(
            "<KeyRelease>", lambda e: self.gunluk_notlari_yukle()
        )

        not_table_frame = tk.Frame(
            not_container,
            bg="#ffffff",
            bd=1,
            relief="solid",
            highlightbackground="#cbd5e1",
        )
        not_table_frame.pack(fill="both", expand=True)

        not_columns = ("NotID", "NotTarih", "NotBolge", "NotDetay")

        style.configure(
            "NotTreeview.Treeview",
            rowheight=36,
            font=("Segoe UI", 9, "bold"),
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#0f172a",
        )

        self.tree_notlar = ttk.Treeview(
            not_table_frame,
            columns=not_columns,
            show="headings",
            style="NotTreeview.Treeview",
        )
        self.tree_notlar.heading("NotID", text="ID")
        self.tree_notlar.heading("NotTarih", text="TARİH / SAAT")
        self.tree_notlar.heading("NotBolge", text="BÖLGE")
        self.tree_notlar.heading("NotDetay", text="YAPILAN İŞ / AÇIKLAMA")

        self.tree_notlar.column(
            "NotID", width=50, anchor="center", stretch=False
        )
        self.tree_notlar.column(
            "NotTarih", width=140, anchor="center", stretch=False
        )
        self.tree_notlar.column(
            "NotBolge", width=180, anchor="w", stretch=False
        )
        self.tree_notlar.column(
            "NotDetay", width=1000, anchor="w", stretch=True
        )

        not_scrollbar_v = ttk.Scrollbar(
            not_table_frame, orient="vertical", command=self.tree_notlar.yview
        )
        not_scrollbar_h = ttk.Scrollbar(
            not_table_frame, orient="horizontal", command=self.tree_notlar.xview
        )

        self.tree_notlar.configure(
            yscrollcommand=not_scrollbar_v.set,
            xscrollcommand=not_scrollbar_h.set,
        )

        not_scrollbar_v.pack(side="right", fill="y")
        not_scrollbar_h.pack(side="bottom", fill="x")
        self.tree_notlar.pack(side="left", fill="both", expand=True)

        self.tree_notlar.bind("<Double-1>", self.not_detay_penceresi_ac)

        # ==================== 3. SEKME: LOG EKRANI ====================
        log_container = tk.Frame(self.tab_log, bg="#f1f5f9")
        log_container.pack(fill="both", expand=True, padx=8, pady=8)

        tk.Label(
            log_container,
            text="Sistem Üzerinde Gerçekleşen Tüm İşlem ve Hareket Geçmişi",
            font=("Segoe UI", 10, "bold"),
            bg="#f1f5f9",
            fg="#0f172a",
        ).pack(anchor="w", pady=(0, 6))

        log_table_frame = tk.Frame(
            log_container,
            bg="#ffffff",
            bd=1,
            relief="solid",
            highlightbackground="#cbd5e1",
        )
        log_table_frame.pack(fill="both", expand=True)

        log_columns = ("Zaman", "İşlemTuru", "Detay")

        style.configure(
            "LogTreeview.Treeview",
            rowheight=24,
            font=("Segoe UI", 9, "bold"),
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#0f172a",
        )

        self.tree_log = ttk.Treeview(
            log_table_frame,
            columns=log_columns,
            show="headings",
            style="LogTreeview.Treeview",
        )
        self.tree_log.heading("Zaman", text="İŞLEM TARİHİ / SAATİ")
        self.tree_log.heading("İşlemTuru", text="İŞLEM TÜRÜ")
        self.tree_log.heading("Detay", text="AÇIKLAMA / İŞLEM DETAYI")

        self.tree_log.column("Zaman", width=150, anchor="w")
        self.tree_log.column("İşlemTuru", width=130, anchor="w")
        self.tree_log.column("Detay", width=900, anchor="w")

        log_scrollbar = ttk.Scrollbar(
            log_table_frame, orient="vertical", command=self.tree_log.yview
        )
        self.tree_log.configure(yscroll=log_scrollbar.set)
        self.tree_log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Başlangıç Yüklemeleri
        self.bolge_listesini_guncelle()
        self.parca_listesini_guncelle()
        self.filtre_listesini_guncelle()
        self.listeyi_guncelle()
        self.gunluk_notlari_yukle()
        self.loglari_ekrana_yukle()
        self.durum_degisti_kontrol(None)

        self.root.after(500, self.acilis_kritik_kontrolu)

    # ==================== VERİTABANI İŞLEMLERİ ====================
    def db_olustur(self):
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
            conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror(
                "Veritabanı Hatası", f"Tablolar oluşturulamadı: {e}"
            )
        finally:
            conn.close()

    def log_ekle(self, islem_turu, detay):
        zaman = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO islem_loglari (zaman, islem_turu, detay) VALUES (?, ?, ?)",
                (zaman, islem_turu, detay),
            )
            conn.commit()
        except sqlite3.Error as e:
            print(f"Log yazma hatası: {e}")
        finally:
            conn.close()
        self.loglari_ekrana_yukle()

    # ==================== YARDIMCI VE UI ARAYÜZ METOTLARI ====================
    def create_stat_badge(
        self, parent, title, initial_val, color_fg, color_bg
    ):
        frame = tk.Frame(
            parent,
            bg=color_bg,
            highlightbackground=color_fg,
            highlightthickness=1,
            padx=10,
            pady=2,
        )
        frame.pack(side="left", padx=4, expand=True, fill="x")

        lbl_val = tk.Label(
            frame,
            text=initial_val,
            font=("Segoe UI", 12, "bold"),
            bg=color_bg,
            fg=color_fg,
        )
        lbl_val.pack()

        lbl_title = tk.Label(
            frame,
            text=title,
            font=("Segoe UI", 7, "bold"),
            bg=color_bg,
            fg="#475569",
        )
        lbl_title.pack()

        return lbl_val

    def tiklandiginda_buyuk_harf_yap(self, P):
        return tr_upper(P)

    def not_metni_buyut(self, event):
        metin = self.txt_gunluk_detay.get("1.0", tk.END)
        buyuk_metin = tr_upper(metin)
        if metin != buyuk_metin:
            cursor_pos = self.txt_gunluk_detay.index(tk.INSERT)
            self.txt_gunluk_detay.delete("1.0", tk.END)
            self.txt_gunluk_detay.insert("1.0", buyuk_metin.strip("\n"))
            self.txt_gunluk_detay.mark_set(tk.INSERT, cursor_pos)

    def durum_degisti_kontrol(self, event):
        durum = self.cmb_durum.get()
        if durum == "ONARIMDA":
            self.lbl_onarim_tarih.grid()
            self.ent_onarim_tarih.grid()
            if not self.ent_onarim_tarih.get().strip():
                self.ent_onarim_tarih.delete(0, tk.END)
                self.ent_onarim_tarih.insert(
                    0, datetime.datetime.now().strftime("%d.%m.%Y")
                )
        else:
            self.lbl_onarim_tarih.grid_remove()
            self.ent_onarim_tarih.grid_remove()

    def verileri_yukle(self):
        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, bolge, sistem_adi, sistem_pn, sistem_sn, parca_adi, parca_pn, parca_sn, durum, onarim_tarih, aciklama FROM parcalar"
            )
            rows = cursor.fetchall()
            return rows
        except sqlite3.Error as e:
            messagebox.showerror(
                "Veritabanı Hatası", f"Veriler yüklenemedi: {e}"
            )
            return []
        finally:
            conn.close()

    def bolge_listesini_guncelle(self):
        conn = sqlite3.connect(DB_DOSYASI)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT bolge FROM parcalar WHERE bolge != ''")
        bolgeler = [r[0] for r in cursor.fetchall()]
        conn.close()

        self.cmb_bolge["values"] = bolgeler
        self.cmb_not_bolge["values"] = bolgeler

    def parca_listesini_guncelle(self):
        conn = sqlite3.connect(DB_DOSYASI)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT parca_adi FROM parcalar WHERE parca_adi != ''"
        )
        parcalar = [r[0] for r in cursor.fetchall()]
        conn.close()

        self.cmb_parca["values"] = parcalar

    def filtre_listesini_guncelle(self):
        conn = sqlite3.connect(DB_DOSYASI)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT bolge FROM parcalar WHERE bolge != ''")
        bolgeler = ["TÜMÜ"] + [r[0] for r in cursor.fetchall()]

        cursor.execute(
            "SELECT DISTINCT parca_adi FROM parcalar WHERE parca_adi != ''"
        )
        parcalar = ["TÜMÜ"] + [r[0] for r in cursor.fetchall()]

        conn.close()

        self.cmb_filtre_bolge["values"] = bolgeler
        self.cmb_filtre_bolge.set("TÜMÜ")

        self.cmb_filtre_parca["values"] = parcalar
        self.cmb_filtre_parca.set("TÜMÜ")

        self.cmb_not_filtre_bolge["values"] = bolgeler
        self.cmb_not_filtre_bolge.set("TÜMÜ")

    # ==================== LİSTELEME VE İSTATİSTİK METOTLARI ====================
    def listeyi_guncelle(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        veriler = self.verileri_yukle()

        f_bolge = self.cmb_filtre_bolge.get()
        f_parca = self.cmb_filtre_parca.get()
        f_durum = self.cmb_filtre_durum.get()
        f_arama = tr_upper(self.ent_arama.get().strip())

        toplam = 0
        faal = 0
        yedek = 0
        onarimda = 0
        kritik = 0
        gayri = 0

        bugun = datetime.datetime.now().date()

        for row in veriler:
            (
                p_id,
                bolge,
                sistem_adi,
                sistem_pn,
                sistem_sn,
                parca_adi,
                parca_pn,
                parca_sn,
                durum,
                onarim_tarih,
                aciklama,
            ) = row

            # İstatistik Hesaplama
            toplam += 1
            if durum == "FAAL":
                faal += 1
            elif durum == "YEDEK PARÇA":
                yedek += 1
            elif durum == "ONARIMDA":
                onarimda += 1
            elif durum == "GAYRI FAAL":
                gayri += 1

            gecen_gun = 0
            is_kritik = False
            sure_durum_text = "-"

            if durum == "ONARIMDA" and onarim_tarih:
                try:
                    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
                        try:
                            bas_tarih = datetime.datetime.strptime(
                                onarim_tarih.strip(), fmt
                            ).date()
                            break
                        except ValueError:
                            pass
                    gecen_gun = (bugun - bas_tarih).days
                    sure_durum_text = f"{gecen_gun} GÜNDÜR ONARIMDA"
                    if gecen_gun >= 30:
                        kritik += 1
                        is_kritik = True
                except Exception:
                    sure_durum_text = "TARİH HATALI"

            # Filtreleme Mantığı
            if f_bolge != "TÜMÜ" and f_bolge != bolge:
                continue
            if f_parca != "TÜMÜ" and f_parca != parca_adi:
                continue

            if f_durum == "30 GÜN+ KRİTİK":
                if not is_kritik:
                    continue
            elif f_durum != "TÜMÜ" and f_durum != durum:
                continue

            if f_arama:
                birlesik = tr_upper(
                    f"{bolge} {sistem_adi} {sistem_pn} {sistem_sn} {parca_adi} {parca_pn} {parca_sn} {aciklama}"
                )
                if f_arama not in birlesik:
                    continue

            tag = durum
            if is_kritik:
                tag = "KRITIK_ONARIM"

            tree_text = f"📍 {bolge} | PN: {sistem_pn} | SN: {sistem_sn}"
            self.tree.insert(
                "",
                "end",
                iid=str(p_id),
                text=tree_text,
                values=(
                    sistem_adi,
                    parca_adi,
                    parca_pn,
                    parca_sn,
                    durum,
                    onarim_tarih if durum == "ONARIMDA" else "-",
                    sure_durum_text,
                    aciklama,
                ),
                tags=(tag,),
            )

        # Rozet İstatistikleri Güncelle
        self.lbl_stat_toplam.config(text=str(toplam))
        self.lbl_stat_faal.config(text=str(faal))
        self.lbl_stat_yedek.config(text=str(yedek))
        self.lbl_stat_onarimda.config(text=str(onarimda))
        self.lbl_stat_kritik.config(text=str(kritik))
        self.lbl_stat_gayri.config(text=str(gayri))

    def acilis_kritik_kontrolu(self):
        veriler = self.verileri_yukle()
        bugun = datetime.datetime.now().date()
        kritik_sayisi = 0

        for r in veriler:
            durum, onarim_tarih = r[8], r[9]
            if durum == "ONARIMDA" and onarim_tarih:
                try:
                    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
                        try:
                            bas_tarih = datetime.datetime.strptime(
                                onarim_tarih.strip(), fmt
                            ).date()
                            break
                        except ValueError:
                            pass
                    if (bugun - bas_tarih).days >= 30:
                        kritik_sayisi += 1
                except Exception:
                    pass

        if kritik_sayisi > 0:
            messagebox.showwarning(
                "🚨 Kritik Süre Uyarısı",
                f"Sistemde 30 günü aşan onarımda **{kritik_sayisi} adet** kritik parça bulunmaktadır!\n\nLütfen Onarımda olan parçaları inceleyiniz.",
            )

    def kritik_parcalari_goster_popip(self):
        self.cmb_filtre_durum.set("30 GÜN+ KRİTİK")
        self.listeyi_guncelle()

    # ==================== KAYIT İŞLEMLERİ (CRUD) ====================
    def tablodan_satir_sec(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        p_id = selected[0]
        self.secili_kayit_id = p_id

        conn = sqlite3.connect(DB_DOSYASI)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM parcalar WHERE id=?", (p_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            self.cmb_bolge.set(row[1])
            self.ent_sistem.delete(0, tk.END)
            self.ent_sistem.insert(0, row[2])
            self.ent_sistem_pn.delete(0, tk.END)
            self.ent_sistem_pn.insert(0, row[3])
            self.ent_sistem_sn.delete(0, tk.END)
            self.ent_sistem_sn.insert(0, row[4])

            self.cmb_parca.set(row[5])
            self.ent_parca_pn.delete(0, tk.END)
            self.ent_parca_pn.insert(0, row[6])
            self.ent_parca_sn.delete(0, tk.END)
            self.ent_parca_sn.insert(0, row[7])

            self.cmb_durum.set(row[8])
            self.ent_onarim_tarih.delete(0, tk.END)
            if row[9]:
                self.ent_onarim_tarih.insert(0, row[9])

            self.ent_not.delete(0, tk.END)
            if row[10]:
                self.ent_not.insert(0, row[10])

            self.durum_degisti_kontrol(None)

    def kayit_ekle(self):
        bolge = tr_upper(self.cmb_bolge.get().strip())
        sistem = tr_upper(self.ent_sistem.get().strip())
        sistem_pn = tr_upper(self.ent_sistem_pn.get().strip())
        sistem_sn = tr_upper(self.ent_sistem_sn.get().strip())
        parca = tr_upper(self.cmb_parca.get().strip())
        parca_pn = tr_upper(self.ent_parca_pn.get().strip())
        parca_sn = tr_upper(self.ent_parca_sn.get().strip())
        durum = self.cmb_durum.get().strip()
        onarim_tarih = (
            self.ent_onarim_tarih.get().strip() if durum == "ONARIMDA" else ""
        )
        aciklama = tr_upper(self.ent_not.get().strip())

        if not bolge or not sistem or not parca:
            messagebox.showwarning(
                "Eksik Bilgi", "Lütfen Bölge, Sistem Adı ve Parça Adı giriniz!"
            )
            return

        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO parcalar (bolge, sistem_adi, sistem_pn, sistem_sn, parca_adi, parca_pn, parca_sn, durum, onarim_tarih, aciklama)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    bolge,
                    sistem,
                    sistem_pn,
                    sistem_sn,
                    parca,
                    parca_pn,
                    parca_sn,
                    durum,
                    onarim_tarih,
                    aciklama,
                ),
            )
            conn.commit()
            messagebox.showinfo("Başarılı", "Yeni parça kaydı başarıyla eklendi.")
            self.log_ekle(
                "KAYIT EKLEME", f"{bolge} - {sistem} için {parca} eklendi."
            )
        except sqlite3.Error as e:
            messagebox.showerror("Hata", f"Kayıt eklenemedi: {e}")
        finally:
            conn.close()

        self.bolge_listesini_guncelle()
        self.parca_listesini_guncelle()
        self.filtre_listesini_guncelle()
        self.listeyi_guncelle()

    def degisiklikleri_kaydet_tiklandi(self):
        if not self.secili_kayit_id:
            messagebox.showwarning(
                "Uyarı", "Lütfen güncellemek istediğiniz kaydı tablodan seçin."
            )
            return

        bolge = tr_upper(self.cmb_bolge.get().strip())
        sistem = tr_upper(self.ent_sistem.get().strip())
        sistem_pn = tr_upper(self.ent_sistem_pn.get().strip())
        sistem_sn = tr_upper(self.ent_sistem_sn.get().strip())
        parca = tr_upper(self.cmb_parca.get().strip())
        parca_pn = tr_upper(self.ent_parca_pn.get().strip())
        parca_sn = tr_upper(self.ent_parca_sn.get().strip())
        durum = self.cmb_durum.get().strip()
        onarim_tarih = (
            self.ent_onarim_tarih.get().strip() if durum == "ONARIMDA" else ""
        )
        aciklama = tr_upper(self.ent_not.get().strip())

        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE parcalar
                SET bolge=?, sistem_adi=?, sistem_pn=?, sistem_sn=?, parca_adi=?, parca_pn=?, parca_sn=?, durum=?, onarim_tarih=?, aciklama=?
                WHERE id=?
            """,
                (
                    bolge,
                    sistem,
                    sistem_pn,
                    sistem_sn,
                    parca,
                    parca_pn,
                    parca_sn,
                    durum,
                    onarim_tarih,
                    aciklama,
                    self.secili_kayit_id,
                ),
            )
            conn.commit()
            messagebox.showinfo("Başarılı", "Kayıt başarıyla güncellendi.")
            self.log_ekle(
                "GÜNCELLEME",
                f"ID #{self.secili_kayit_id} - {parca} bilgileri güncellendi.",
            )
        except sqlite3.Error as e:
            messagebox.showerror("Hata", f"Güncelleme yapılamadı: {e}")
        finally:
            conn.close()

        self.listeyi_guncelle()

    def durum_guncelle(self):
        self.degisiklikleri_kaydet_tiklandi()

    def kayit_sil(self):
        if not self.secili_kayit_id:
            messagebox.showwarning("Uyarı", "Lütfen silinecek kaydı seçin.")
            return

        cevap = messagebox.askyesno(
            "Onay",
            f"ID #{self.secili_kayit_id} olan kaydı silmek istediğinize emin misiniz?",
        )
        if cevap:
            try:
                conn = sqlite3.connect(DB_DOSYASI)
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM parcalar WHERE id=?", (self.secili_kayit_id,)
                )
                conn.commit()
                messagebox.showinfo("Başarılı", "Kayıt silindi.")
                self.log_ekle(
                    "KAYIT SİLME", f"ID #{self.secili_kayit_id} kaydı silindi."
                )
                self.secili_kayit_id = None
            except sqlite3.Error as e:
                messagebox.showerror("Hata", f"Kayıt silinemedi: {e}")
            finally:
                conn.close()

            self.listeyi_guncelle()

    # ==================== DİĞER ETKİLEŞİM VE İÇERİK METOTLARI ====================
    def bolge_otomatik_doldur_event(self, event):
        bolge = self.cmb_bolge.get().strip()
        if not bolge:
            return
        conn = sqlite3.connect(DB_DOSYASI)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT sistem_adi, sistem_pn, sistem_sn FROM parcalar WHERE bolge=? LIMIT 1",
            (bolge,),
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            self.ent_sistem.delete(0, tk.END)
            self.ent_sistem.insert(0, row[0] or "")
            self.ent_sistem_pn.delete(0, tk.END)
            self.ent_sistem_pn.insert(0, row[1] or "")
            self.ent_sistem_sn.delete(0, tk.END)
            self.ent_sistem_sn.insert(0, row[2] or "")

    def parca_otomatik_doldur_event(self, event):
        parca = self.cmb_parca.get().strip()
        if not parca:
            return
        conn = sqlite3.connect(DB_DOSYASI)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT parca_pn FROM parcalar WHERE parca_adi=? LIMIT 1", (parca,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            self.ent_parca_pn.delete(0, tk.END)
            self.ent_parca_pn.insert(0, row[0] or "")

    # ==================== GÜNLÜK İŞ NOTLARI METOTLARI ====================
    def gunluk_not_ekle(self):
        tarih = self.ent_not_tarih.get().strip()
        bolge = tr_upper(self.cmb_not_bolge.get().strip())
        detay = tr_upper(self.txt_gunluk_detay.get("1.0", tk.END).strip())

        if not bolge or not detay:
            messagebox.showwarning("Eksik Bilgi", "Lütfen Bölge ve Not detayını giriniz!")
            return

        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO gunluk_notlar (tarih, bolge, detay) VALUES (?, ?, ?)",
                (tarih, bolge, detay),
            )
            conn.commit()
            messagebox.showinfo("Başarılı", "Günlük iş notu kaydedildi.")
            self.txt_gunluk_detay.delete("1.0", tk.END)
            self.log_ekle("GÜNLÜK NOT", f"{bolge} bölgesine yeni not eklendi.")
        except sqlite3.Error as e:
            messagebox.showerror("Hata", f"Not kaydedilemedi: {e}")
        finally:
            conn.close()

        self.gunluk_notlari_yukle()

    def gunluk_notlari_yukle(self):
        for item in self.tree_notlar.get_children():
            self.tree_notlar.delete(item)

        f_bolge = self.cmb_not_filtre_bolge.get()
        f_arama = tr_upper(self.ent_not_arama.get().strip())

        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, tarih, bolge, detay FROM gunluk_notlar ORDER BY id DESC"
            )
            rows = cursor.fetchall()

            for r in rows:
                n_id, tarih, bolge, detay = r
                if f_bolge != "TÜMÜ" and f_bolge != bolge:
                    continue
                if f_arama and f_arama not in tr_upper(
                    f"{bolge} {detay} {tarih}"
                ):
                    continue

                self.tree_notlar.insert(
                    "", "end", iid=str(n_id), values=(n_id, tarih, bolge, detay)
                )
        except sqlite3.Error as e:
            print(f"Not yükleme hatası: {e}")
        finally:
            conn.close()

    def gunluk_not_sil(self):
        selected = self.tree_notlar.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silinecek notu seçin.")
            return

        n_id = selected[0]
        if messagebox.askyesno("Onay", "Seçili günlük notu silmek istiyor musunuz?"):
            try:
                conn = sqlite3.connect(DB_DOSYASI)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM gunluk_notlar WHERE id=?", (n_id,))
                conn.commit()
                messagebox.showinfo("Başarılı", "Not silindi.")
            except sqlite3.Error as e:
                messagebox.showerror("Hata", f"Not silinemedi: {e}")
            finally:
                conn.close()

            self.gunluk_notlari_yukle()

    def not_detay_penceresi_ac(self, event):
        selected = self.tree_notlar.selection()
        if not selected:
            return

        item = self.tree_notlar.item(selected[0])
        vals = item["values"]

        top = tk.Toplevel(self.root)
        top.title(f"Not Detayı - ID #{vals[0]}")
        top.geometry("600x400")
        top.configure(bg="#f8fafc")

        tk.Label(
            top,
            text=f"📍 Bölge: {vals[2]} | 📅 Tarih: {vals[1]}",
            font=("Segoe UI", 10, "bold"),
            bg="#f8fafc",
            fg="#0f172a",
        ).pack(anchor="w", padx=10, pady=10)

        txt = tk.Text(
            top,
            wrap="word",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#0f172a",
            padx=8,
            pady=8,
        )
        txt.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        txt.insert("1.0", vals[3])
        txt.config(state="disabled")

    def bolge_parcalarini_goster(self):
        bolge = self.cmb_not_bolge.get().strip()
        if not bolge:
            messagebox.showwarning("Uyarı", "Lütfen bir bölge seçiniz.")
            return

        top = tk.Toplevel(self.root)
        top.title(f"{bolge} Bölgesindeki Tüm Parçalar")
        top.geometry("800x400")

        tree = ttk.Treeview(
            top,
            columns=("Sistem", "Parca", "PN", "SN", "Durum"),
            show="headings",
        )
        tree.heading("Sistem", text="SİSTEM ADI")
        tree.heading("Parca", text="PARÇA ADI")
        tree.heading("PN", text="PARÇA PN")
        tree.heading("SN", text="PARÇA SN")
        tree.heading("Durum", text="DURUMU")

        tree.pack(fill="both", expand=True)

        conn = sqlite3.connect(DB_DOSYASI)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT sistem_adi, parca_adi, parca_pn, parca_sn, durum FROM parcalar WHERE bolge=?",
            (bolge,),
        )
        rows = cursor.fetchall()
        conn.close()

        for r in rows:
            tree.insert("", "end", values=r)

    # ==================== LOG VE AKTARIM METOTLARI ====================
    def loglari_ekrana_yukle(self):
        for item in self.tree_log.get_children():
            self.tree_log.delete(item)

        try:
            conn = sqlite3.connect(DB_DOSYASI)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT zaman, islem_turu, detay FROM islem_loglari ORDER BY id DESC LIMIT 200"
            )
            rows = cursor.fetchall()

            for r in rows:
                self.tree_log.insert("", "end", values=r)
        except sqlite3.Error as e:
            print(f"Log okuma hatası: {e}")
        finally:
            conn.close()

    def verileri_disa_aktar(self):
        dosya_yolu = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Dosyası", "*.csv"), ("Tüm Dosyalar", "*.*")],
            title="Verileri Dışa Aktar",
        )
        if not dosya_yolu:
            return

        try:
            veriler = self.verileri_yukle()
            with open(
                dosya_yolu, mode="w", newline="", encoding="utf-8-sig"
            ) as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(
                    [
                        "ID",
                        "Bölge",
                        "Sistem Adı",
                        "Sistem PN",
                        "Sistem SN",
                        "Parça Adı",
                        "Parça PN",
                        "Parça SN",
                        "Durumu",
                        "Onarım Tarihi",
                        "Açıklama",
                    ]
                )
                for row in veriler:
                    writer.writerow(row)

            messagebox.showinfo("Başarılı", "Veriler başarıyla aktarıldı.")
            self.log_ekle("DISARI AKTAR", f"Veriler {dosya_yolu} dosyasına aktarıldı.")
        except Exception as e:
            messagebox.showerror("Hata", f"Aktarım hatası: {e}")

    def servis_formu_olustur(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Uyarı", "Lütfen servis formu oluşturulacak parçayı seçin."
            )
            return

        p_id = selected[0]
        conn = sqlite3.connect(DB_DOSYASI)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM parcalar WHERE id=?", (p_id,))
        r = cursor.fetchone()
        conn.close()

        if not r:
            return

        dosya_yolu = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Metin Belgesi", "*.txt")],
            title="Servis Formu Kaydet",
            initialfile=f"Servis_Formu_{r[5]}_{r[7]}.txt",
        )
        if not dosya_yolu:
            return

        tarih_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        form_metni = f"""
====================================================================
                   TEKNİK SERVİS & PARÇA DEĞİŞİM FORMU
====================================================================
Tarih/Saat : {tarih_str}
Form No    : SRV-{r[0]}-{datetime.datetime.now().strftime('%Y%m%d')}

1. SİSTEM BİLGİLERİ
--------------------------------------------------------------------
Bölge      : {r[1]}
Sistem Adı : {r[2]}
Sistem PN  : {r[3]}
Sistem SN  : {r[4]}

2. PARÇA VE DURUM BİLGİLERİ
--------------------------------------------------------------------
Parça Adı  : {r[5]}
Parça PN   : {r[6]}
Parça SN   : {r[7]}
Mevcut Durum: {r[8]}
Onarım Başl.: {r[9] if r[9] else 'N/A'}

3. AÇIKLAMA VE NOTLAR
--------------------------------------------------------------------
{r[10] if r[10] else 'Açıklama belirtilmedi.'}

====================================================================
Teslim Eden (İmza)                       Teslim Alan (İmza)
====================================================================
        """
        try:
            with open(dosya_yolu, "w", encoding="utf-8") as f:
                f.write(form_metni)
            messagebox.showinfo("Başarılı", "Servis Formu başarıyla oluşturuldu.")
            self.log_ekle(
                "SERVIS FORMU", f"ID #{r[0]} için Servis Formu yazdırıldı."
            )
        except Exception as e:
            messagebox.showerror("Hata", f"Form oluşturulamadı: {e}")
import streamlit as st

st.title("Sistem ve Parça Takip Uygulaması")
st.write("Uygulama başarıyla çalışıyor!")