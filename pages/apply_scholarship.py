import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

try:
    from student_dashboard import supabase, BG, WHITE, PURPLE, PURPLE2, BORDER, TEXT_DARK, TEXT_GRAY
except ImportError:
    BG=WHITE=PURPLE=PURPLE2=BORDER=TEXT_DARK=TEXT_GRAY=""
    supabase = None

INPUT_BG  = "#F7FAFC"
DISABLED  = "#EDF2F7"
RED       = "#E53E3E"
GREEN     = "#48BB78"

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


class ApplyFrame(tk.Frame):
    def __init__(self, parent, name, email, dashboard, **_):
        super().__init__(parent, bg=BG)
        self.name       = name
        self.email      = email
        self.dashboard  = dashboard
        self._files     = {k: None for k in
                           ('school_id','id_picture','birth_cert','grades')}
        self._file_labels = {}
        self._submitting = False
        self._has_existing = False
        self._build()
        threading.Thread(target=self._load_and_check, daemon=True).start()

    # ── Build UI ───────────────────────────────────────────────────────────────
    def _build(self):
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        self._inner = tk.Frame(canvas, bg=BG)
        wid = canvas.create_window((0,0), window=self._inner, anchor="nw")

        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(wid, width=e.width)
        canvas.bind("<Configure>", _resize)
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

        pad = tk.Frame(self._inner, bg=BG)
        pad.pack(fill="both", padx=32, pady=20)

        # Header
        hdr = tk.Frame(pad, bg=WHITE,
                       highlightbackground=BORDER, highlightthickness=1)
        hdr.pack(fill="x", pady=(0,20))
        tk.Label(hdr, text="Scholarship Application Form",
                 bg=WHITE, fg=PURPLE,
                 font=("Helvetica",18,"bold"),
                 pady=12).pack()
        tk.Label(hdr, text="Complete the form honestly. Fields marked with * are required.",
                 bg=WHITE, fg=TEXT_GRAY,
                 font=("Helvetica",10),
                 pady=(0),padx=20).pack(pady=(0,12))

        # Existing application notice (hidden by default)
        self._notice = tk.Label(pad,
            text="⚠ You already have an existing application.",
            bg="#FFF3CD", fg="#856404",
            font=("Helvetica",10,"bold"),
            pady=10, padx=12, anchor="w")

        card = tk.Frame(pad, bg=WHITE,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x")
        self._card = card

        self._vars = {}

        self._section(card, "👤 Personal Information")
        self._field(card,"firstName","First Name *",        disabled=True)
        self._field(card,"middleName","Middle Name",        disabled=True, required=False)
        self._field(card,"surname","Last Name *",           disabled=True)
        self._field(card,"studentId","Student ID *")
        self._field(card,"contact","Contact Number *")

        self._section(card,"📍 Address")
        self._field(card,"houseStreet","House No. / Street *")
        self._dropdown(card,"barangay","Barangay *",BARANGAYS)

        self._section(card,"🎓 Academic Information")
        self._field(card,"course","Course / Strand *")
        self._dropdown(card,"gradeLevel","Year Level *",GRADE_LEVELS)
        self._field(card,"gwa","GWA *")

        self._section(card,"💭 Why do you deserve this scholarship? *")
        self._textarea(card,"reason")

        self._section(card,"📎 Upload Requirements")
        for doc_key, doc_label in [
            ("school_id",  "School ID *"),
            ("id_picture", "2x2 ID Picture *"),
            ("birth_cert", "Birth Certificate *"),
            ("grades",     "Copy of Grades *"),
        ]:
            self._doc_upload(card, doc_key, doc_label)

        # Error / submit
        self._err_var = tk.StringVar()
        tk.Label(card, textvariable=self._err_var,
                 bg=WHITE, fg=RED,
                 font=("Helvetica",10),
                 wraplength=600, justify="left").pack(fill="x",padx=20,pady=(4,0))

        self._submit_btn = tk.Button(
            card, text="📝 Submit Application",
            bg=PURPLE, fg=WHITE,
            activebackground=PURPLE2,
            relief="flat", bd=0,
            font=("Helvetica",12,"bold"),
            height=2, cursor="hand2",
            command=self._submit)
        self._submit_btn.pack(fill="x", padx=20, pady=(10,20))

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _section(self, parent, text):
        tk.Label(parent, text=text, bg=WHITE, fg=TEXT_DARK,
                 font=("Helvetica",12,"bold"),
                 anchor="w",padx=20,pady=(14,0)).pack(fill="x")

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
                     insertbackground=PURPLE,
                     relief="flat", bd=0,
                     font=("Helvetica",11),
                     highlightthickness=1,
                     highlightbackground=BORDER,
                     highlightcolor=PURPLE)
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
        return cb

    def _textarea(self, parent, key):
        var = tk.StringVar()
        self._vars[key] = var
        txt = tk.Text(parent, height=4,
                      bg=INPUT_BG, fg=TEXT_DARK,
                      font=("Helvetica",11),
                      relief="flat", bd=0,
                      highlightthickness=1,
                      highlightbackground=BORDER,
                      highlightcolor=PURPLE,
                      wrap="word")
        txt.pack(fill="x", padx=20, pady=(4,2))
        # Bind Text widget to StringVar manually
        self._reason_widget = txt

    def _doc_upload(self, parent, key, label):
        row = tk.Frame(parent, bg=WHITE)
        row.pack(fill="x", padx=20, pady=4)
        tk.Label(row, text=label, bg=WHITE, fg=TEXT_DARK,
                 font=("Helvetica",10,"bold"),
                 anchor="w").pack(anchor="w")
        btn_row = tk.Frame(row, bg=WHITE)
        btn_row.pack(fill="x",pady=(4,0))
        btn = tk.Button(btn_row, text="📁 Choose File",
                        bg=INPUT_BG, fg=PURPLE,
                        relief="flat", bd=1,
                        font=("Helvetica",10),
                        cursor="hand2",
                        command=lambda k=key: self._pick_file(k))
        btn.pack(side="left")
        lbl = tk.Label(btn_row, text="No file chosen",
                       bg=WHITE, fg=TEXT_GRAY,
                       font=("Helvetica",9))
        lbl.pack(side="left", padx=8)
        self._file_labels[key] = lbl

    # ── Data loading ───────────────────────────────────────────────────────────
    def _load_and_check(self):
        try:
            user = (supabase.table("users")
                    .select("first_name,middle_name,last_name,user_id")
                    .eq("email", self.email).single().execute())
            d = user.data
            self.after(0, lambda: [
                self._vars["firstName"].set(d.get("first_name","")),
                self._vars["middleName"].set(d.get("middle_name","")),
                self._vars["surname"].set(d.get("last_name","")),
            ])
            uid = d.get("user_id")
            apps = (supabase.table("application")
                    .select("application_id")
                    .eq("user_id", uid).execute())
            if apps.data:
                self.after(0, self._show_existing_notice)
        except Exception:
            pass

    def _show_existing_notice(self):
        self._has_existing = True
        self._notice.pack(fill="x", padx=32, pady=(0,8), before=self._card)

    # ── File picking ───────────────────────────────────────────────────────────
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
        # Validate
        errors = []
        for key in ("firstName","surname","studentId","contact",
                    "houseStreet","course","gwa"):
            if not self._vars.get(key,"").get().strip():
                errors.append(f"'{key}' is required.")
        if not self._vars.get("barangay","").get():
            errors.append("Please select your barangay.")
        if not self._vars.get("gradeLevel","").get():
            errors.append("Please select your year level.")
        reason = self._reason_widget.get("1.0","end").strip()
        if not reason:
            errors.append("Please provide your reason.")
        for k, lbl in [("school_id","School ID"),("id_picture","ID Picture"),
                        ("birth_cert","Birth Certificate"),("grades","Grades")]:
            if not self._files[k]:
                errors.append(f"Please upload {lbl}.")
        if errors:
            return self._err_var.set(errors[0])

        self._submit_btn.config(state="disabled", text="Submitting…",
                                bg="#A0AEC0")
        threading.Thread(target=self._do_submit,
                         args=(reason,), daemon=True).start()

    def _do_submit(self, reason):
        try:
            user = (supabase.table("users")
                    .select("user_id")
                    .eq("email",self.email).single().execute())
            uid = user.data["user_id"]

            # Upload files
            file_urls = {}
            cols = {"school_id":"school_id_path","id_picture":"id_picture_path",
                    "birth_cert":"birth_certificate_path","grades":"grades_path"}
            for key, path in self._files.items():
                ext = os.path.splitext(path)[1]
                storage_path = f"{uid}/{key}{ext}"
                with open(path,"rb") as f:
                    supabase.storage.from_("scholarship_bucket").upload(
                        storage_path, f.read(),
                        {"content-type": "image/jpeg","x-upsert":"true"})
                url = (supabase.storage.from_("scholarship_bucket")
                       .get_public_url(storage_path))
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
                "year_level":   self._vars["gradeLevel"].get(),
                "gwa":          float(self._vars["gwa"].get().strip()),
                "reason":       reason,
                "status":       "pending",
                **file_urls,
            }
            supabase.table("application").insert(data).execute()
            self.after(0, self._on_submitted)
        except Exception as exc:
            self.after(0, self._on_error, str(exc))

    def _on_submitted(self):
        self._submit_btn.config(state="normal",
                                text="📝 Submit Application", bg=PURPLE)
        messagebox.showinfo("Submitted!",
                            "Your application has been submitted successfully!")
        self.dashboard._show_applications()

    def _on_error(self, msg):
        self._submit_btn.config(state="normal",
                                text="📝 Submit Application", bg=PURPLE)
        self._err_var.set(f"Error: {msg}")