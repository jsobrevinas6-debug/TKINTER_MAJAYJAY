import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

try:
    from student_dashboard import supabase, BG, WHITE, PURPLE, PURPLE2, BORDER, TEXT_DARK, TEXT_GRAY
except ImportError:
    BG=WHITE=PURPLE=PURPLE2=BORDER=TEXT_DARK=TEXT_GRAY=""
    supabase = None

INPUT_BG = "#F7FAFC"
DISABLED = "#EDF2F7"
VIOLET   = "#9B59B6"
RED      = "#E53E3E"
GREEN    = "#48BB78"

GRADE_LEVELS = ['Grade 11','Grade 12','1st Year','2nd Year','3rd Year','4th Year']
BARANGAYS = [
    'Amonoy','Bakia','Balanac','Balayong','Banilad','Banti','Bitaoy',
    'Botocan','Bukal','Burgos','Burol','Coralao','Gagalot','Ibabang Banga',
    'Ibabang Bayucain','Ilayang Banga','Ilayang Bayucain','Isabang','Malinao',
    'May-it','Munting Kawayan','Olla','Oobi','Origuel (Poblacion)','Panalaban',
    'Pangil','Panglan','Piit','Pook','Rizal','San Francisco (Poblacion)',
    'San Isidro','San Miguel (Poblacion)','San Roque','Santa Catalina','Suba',
    'Talortor','Tanawan','Taytay','Villa Nogales',
]


class RenewFrame(tk.Frame):
    def __init__(self, parent, name, email, dashboard, **_):
        super().__init__(parent, bg=BG)
        self.name       = name
        self.email      = email
        self.dashboard  = dashboard
        self._files     = {k: None for k in
                           ('school_id','id_picture','birth_cert','grades','cor')}
        self._file_labels = {}
        self._vars      = {}
        self._build()
        threading.Thread(target=self._load_data, daemon=True).start()

    # ── Build UI ───────────────────────────────────────────────────────────────
    def _build(self):
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG)
        wid = canvas.create_window((0,0), window=inner, anchor="nw")

        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(wid, width=e.width)
        canvas.bind("<Configure>", _resize)
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

        pad = tk.Frame(inner, bg=BG)
        pad.pack(fill="both", padx=32, pady=20)

        # Header
        hdr = tk.Frame(pad, bg=WHITE,
                       highlightbackground=BORDER, highlightthickness=1)
        hdr.pack(fill="x", pady=(0,16))
        tk.Label(hdr, text="🔄 Scholarship Renewal Form",
                 bg=WHITE, fg=VIOLET,
                 font=("Helvetica",18,"bold"), pady=12).pack()
        tk.Label(hdr,
                 text="All fields marked with * are mandatory.",
                 bg=WHITE, fg=TEXT_GRAY,
                 font=("Helvetica",10), pady=(0,)).pack(pady=(0,12))

        # Info box
        info = tk.Frame(pad, bg="#E8F5E9",
                        highlightbackground=GREEN, highlightthickness=1)
        info.pack(fill="x", pady=(0,16))
        tk.Label(info,
                 text="ℹ  Make sure all documents are ready (max 5MB each). Supported: JPG, PNG, PDF.",
                 bg="#E8F5E9", fg="#2E7D32",
                 font=("Helvetica",9,"bold"),
                 pady=8, padx=12, anchor="w").pack(fill="x")

        card = tk.Frame(pad, bg=WHITE,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x")

        self._section(card,"👤 Personal Information")
        self._field(card,"firstName","First Name *",   disabled=True)
        self._field(card,"middleName","Middle Name",   disabled=True, required=False)
        self._field(card,"surname","Last Name *",      disabled=True)
        self._field(card,"studentId","Student ID *")
        self._field(card,"contact","Contact Number *")

        self._section(card,"📍 Address")
        self._field(card,"houseStreet","House No. / Street *")
        self._dropdown(card,"barangay","Barangay *", BARANGAYS)
        self._field(card,"municipality","Municipality",disabled=True)
        self._vars["municipality"].set("Majayjay")

        self._section(card,"🎓 Academic Information")
        self._field(card,"course","Course / Program *")
        self._dropdown(card,"yearLevel","Year Level *", GRADE_LEVELS)
        self._field(card,"gwa","GWA *")

        self._section(card,"📎 Required Documents")
        for key, lbl in [
            ("school_id",  "School ID *"),
            ("id_picture", "2x2 ID Picture *"),
            ("birth_cert", "Birth Certificate *"),
            ("grades",     "Copy of Grades *"),
            ("cor",        "COR (Certificate of Registration) *"),
        ]:
            self._doc_upload(card, key, lbl)

        self._section(card,"💭 Reason for Renewal *")
        self._reason = tk.Text(card, height=5,
                               bg=INPUT_BG, fg=TEXT_DARK,
                               font=("Helvetica",11),
                               relief="flat", bd=0,
                               highlightthickness=1,
                               highlightbackground=BORDER,
                               highlightcolor=VIOLET,
                               wrap="word")
        self._reason.pack(fill="x", padx=20, pady=(4,8))

        # Warning box
        warn = tk.Frame(card, bg="#FFF3CD",
                        highlightbackground="#FFA500", highlightthickness=1)
        warn.pack(fill="x", padx=20, pady=(4,12))
        tk.Label(warn,
                 text=("⚠ Important Reminders\n"
                       "• Double-check all information before submitting\n"
                       "• Ensure your GWA is accurate\n"
                       "• Your renewal will be reviewed by the admin\n"
                       "• You will be notified of the decision"),
                 bg="#FFF3CD", fg="#856404",
                 font=("Helvetica",9),
                 justify="left", padx=10, pady=8, anchor="w").pack(fill="x")

        self._err_var = tk.StringVar()
        tk.Label(card, textvariable=self._err_var,
                 bg=WHITE, fg=RED,
                 font=("Helvetica",10),
                 wraplength=600).pack(fill="x",padx=20)

        self._submit_btn = tk.Button(
            card, text="🔄 Submit Renewal",
            bg=VIOLET, fg=WHITE,
            activebackground=PURPLE2,
            relief="flat", bd=0,
            font=("Helvetica",12,"bold"),
            height=2, cursor="hand2",
            command=self._submit)
        self._submit_btn.pack(fill="x", padx=20, pady=(10,20))

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _section(self, parent, text):
        tk.Label(parent, text=text, bg=WHITE, fg=VIOLET,
                 font=("Helvetica",12,"bold"),
                 anchor="w", padx=20, pady=(12,0)).pack(fill="x")

    def _field(self, parent, key, label, disabled=False, required=True):
        tk.Label(parent, text=label, bg=WHITE, fg=TEXT_DARK,
                 font=("Helvetica",10), anchor="w",
                 padx=20).pack(fill="x",pady=(8,2))
        var = tk.StringVar()
        self._vars[key] = var
        state = "disabled" if disabled else "normal"
        bg    = DISABLED   if disabled else INPUT_BG
        e = tk.Entry(parent, textvariable=var, state=state,
                     bg=bg, fg=TEXT_DARK,
                     disabledbackground=DISABLED,
                     disabledforeground="#A0AEC0",
                     insertbackground=VIOLET,
                     relief="flat", bd=0,
                     font=("Helvetica",11),
                     highlightthickness=1,
                     highlightbackground=BORDER,
                     highlightcolor=VIOLET)
        e.pack(fill="x", padx=20, ipady=7, pady=(0,2))
        return e

    def _dropdown(self, parent, key, label, options):
        tk.Label(parent, text=label, bg=WHITE, fg=TEXT_DARK,
                 font=("Helvetica",10), anchor="w",
                 padx=20).pack(fill="x",pady=(8,2))
        var = tk.StringVar()
        self._vars[key] = var
        cb = ttk.Combobox(parent, textvariable=var,
                          values=options, state="readonly",
                          font=("Helvetica",11))
        cb.pack(fill="x", padx=20, pady=(0,2))

    def _doc_upload(self, parent, key, label):
        row = tk.Frame(parent, bg=WHITE)
        row.pack(fill="x", padx=20, pady=4)
        tk.Label(row, text=label, bg=WHITE, fg=TEXT_DARK,
                 font=("Helvetica",10,"bold"), anchor="w").pack(anchor="w")
        btn_row = tk.Frame(row, bg=WHITE)
        btn_row.pack(fill="x", pady=(4,0))
        tk.Button(btn_row, text="📁 Choose File",
                  bg=INPUT_BG, fg=VIOLET,
                  relief="flat", bd=1,
                  font=("Helvetica",10), cursor="hand2",
                  command=lambda k=key: self._pick_file(k)).pack(side="left")
        lbl = tk.Label(btn_row, text="No file chosen",
                       bg=WHITE, fg=TEXT_GRAY, font=("Helvetica",9))
        lbl.pack(side="left", padx=8)
        self._file_labels[key] = lbl

    # ── Data loading ───────────────────────────────────────────────────────────
    def _load_data(self):
        try:
            user = (supabase.table("users")
                    .select("user_id,first_name,middle_name,last_name")
                    .eq("email",self.email).single().execute())
            d    = user.data
            uid  = d["user_id"]

            app = (supabase.table("application")
                   .select("*")
                   .eq("user_id",uid).eq("status","approved")
                   .maybe_single().execute())

            def _fill():
                self._vars["firstName"].set(d.get("first_name",""))
                self._vars["middleName"].set(d.get("middle_name",""))
                self._vars["surname"].set(d.get("last_name",""))
                if app.data:
                    self._vars["houseStreet"].set(app.data.get("address",""))
                    self._vars["barangay"].set(app.data.get("baranggay",""))
            self.after(0, _fill)
        except Exception:
            pass

    def _pick_file(self, key):
        path = filedialog.askopenfilename(
            filetypes=[("Images & PDF","*.jpg *.jpeg *.png *.pdf")])
        if path:
            self._files[key] = path
            self._file_labels[key].config(
                text=os.path.basename(path), fg="#2D3748")

    # ── Submit ─────────────────────────────────────────────────────────────────
    def _submit(self):
        self._err_var.set("")
        errors = []
        for key in ("studentId","contact","houseStreet","course","gwa"):
            if not self._vars.get(key, tk.StringVar()).get().strip():
                errors.append(f"'{key}' is required.")
        if not self._vars.get("yearLevel","").get():
            errors.append("Please select your year level.")
        reason = self._reason.get("1.0","end").strip()
        if not reason or len(reason) < 50:
            errors.append("Reason must be at least 50 characters.")
        for k, lbl in [("school_id","School ID"),("id_picture","ID Picture"),
                        ("birth_cert","Birth Certificate"),
                        ("grades","Grades"),("cor","COR")]:
            if not self._files[k]:
                errors.append(f"Please upload {lbl}.")
        if errors:
            return self._err_var.set(errors[0])

        self._submit_btn.config(state="disabled",
                                text="Submitting…", bg="#A0AEC0")
        threading.Thread(target=self._do_submit,
                         args=(reason,), daemon=True).start()

    def _do_submit(self, reason):
        try:
            user = (supabase.table("users")
                    .select("user_id")
                    .eq("email",self.email).single().execute())
            uid = user.data["user_id"]

            file_urls = {}
            cols = {"school_id":"school_id_path","id_picture":"id_picture_path",
                    "birth_cert":"birth_certificate_path",
                    "grades":"grades_path","cor":"cor_path"}
            for key, path in self._files.items():
                ext = os.path.splitext(path)[1]
                sp  = f"{uid}/renew_{key}{ext}"
                with open(path,"rb") as f:
                    supabase.storage.from_("scholarship_bucket").upload(
                        sp, f.read(),
                        {"content-type":"image/jpeg","x-upsert":"true"})
                url = (supabase.storage.from_("scholarship_bucket")
                       .get_public_url(sp))
                file_urls[cols[key]] = url

            data = {
                "user_id":      uid,
                "first_name":   self._vars["firstName"].get().strip(),
                "middle_name":  self._vars["middleName"].get().strip() or None,
                "last_name":    self._vars["surname"].get().strip(),
                "student_id":   self._vars["studentId"].get().strip(),
                "contact":      self._vars["contact"].get().strip(),
                "address":      self._vars["houseStreet"].get().strip(),
                "baranggay":    self._vars["barangay"].get(),
                "course":       self._vars["course"].get().strip(),
                "year_level":   self._vars["yearLevel"].get(),
                "gwa":          float(self._vars["gwa"].get().strip()),
                "reason":       reason,
                "status":       "pending",
                **file_urls,
            }
            supabase.table("renew").insert(data).execute()
            self.after(0, self._on_submitted)
        except Exception as exc:
            self.after(0, self._on_error, str(exc))

    def _on_submitted(self):
        self._submit_btn.config(state="normal",
                                text="🔄 Submit Renewal", bg=VIOLET)
        messagebox.showinfo("Submitted!",
                            "Your renewal has been submitted successfully!")
        self.dashboard._show_applications()

    def _on_error(self, msg):
        self._submit_btn.config(state="normal",
                                text="🔄 Submit Renewal", bg=VIOLET)
        self._err_var.set(f"Error: {msg}")