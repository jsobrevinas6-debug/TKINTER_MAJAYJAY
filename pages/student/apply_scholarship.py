import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

try:
    from student_dashboard import supabase, BG, WHITE, PURPLE, PURPLE2, BORDER, TEXT_DARK, TEXT_GRAY
except ImportError:
    BG        = "#F7FAFC"
    WHITE     = "#FFFFFF"
    PURPLE    = "#667EEA"
    PURPLE2   = "#764BA2"
    BORDER    = "#E2E8F0"
    TEXT_DARK = "#2D3748"
    TEXT_GRAY = "#718096"
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
                           ('school_id','id_picture','birth_cert','grades','cor')}
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

        def _on_mousewheel(e):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        def _on_scroll_up(e):
            if canvas.winfo_exists():
                canvas.yview_scroll(-1, "units")
        def _on_scroll_down(e):
            if canvas.winfo_exists():
                canvas.yview_scroll(1, "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", _on_scroll_up)
        canvas.bind("<Button-5>", _on_scroll_down)
        self._inner.bind("<MouseWheel>", _on_mousewheel)
        self.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        pad = tk.Frame(self._inner, bg=BG)
        pad.pack(fill="x", padx=32, pady=20)

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
                 pady=0,padx=20).pack(pady=(0,12))

        # Existing application notice (hidden by default)
        self._notice = tk.Label(pad,
            text="⚠ You already have an existing application.",
            bg="#FFF3CD", fg="#856404",
            font=("Helvetica",10,"bold"),
            pady=10, padx=12, anchor="w")

        card = tk.Frame(pad, bg=WHITE,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", pady=(0, 20))
        self._card = card

        self._vars = {}

        self._section(card, "👤 Personal Information")
        self._field(card,"firstName","First Name *",        disabled=True)
        self._field(card,"middleName","Middle Name",        disabled=True, required=False)
        self._field(card,"surname","Last Name *",           disabled=True)
        self._field(card,"studentId","Student ID *")
        self._field(card,"contact","Contact Number *")

        self._section(card,"📍 Address")
        self._field(card,"municipality","Municipality", disabled=True)
        self._vars["municipality"].set("Majayjay")
        self._field(card,"houseStreet","House No. / Street *")
        self._dropdown(card,"barangay","Barangay *",BARANGAYS)

        self._section(card,"🎓 Academic Information")
        self._field(card,"schoolName","School Name *")
        self._field(card,"course","Course / Strand *")
        self._dropdown(card,"gradeLevel","Year Level *",GRADE_LEVELS)
        self._field(card,"gwa","GWA *")

        self._section(card,"📎 Upload Requirements")
        for doc_key, doc_label in [
            ("school_id",  "School ID *"),
            ("id_picture", "2x2 ID Picture *"),
            ("birth_cert", "Birth Certificate *"),
            ("grades",     "Copy of Grades *"),
            ("cor",        "COR (Certificate of Registration) *"),
        ]:
            self._doc_upload(card, doc_key, doc_label)

        self._section(card,"💭 Why do you deserve this scholarship? *")
        self._textarea(card,"reason")

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
                 anchor="w",padx=20,pady=14).pack(fill="x")

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
            from db import fetch_one
            user = fetch_one(
                "SELECT first_name, middle_name, last_name, user_id FROM users WHERE email=%s",
                (self.email,))
            if not user:
                return
            self.after(0, lambda: [
                self._vars["firstName"].set(user.get("first_name", "")),
                self._vars["middleName"].set(user.get("middle_name", "") or ""),
                self._vars["surname"].set(user.get("last_name", "")),
            ])
            app = fetch_one(
                "SELECT status FROM applications WHERE user_id=%s ORDER BY submission_date DESC LIMIT 1",
                (user["user_id"],))
            if app:
                self.after(0, self._show_blocked, app["status"])
        except Exception as e:
            print(f"[ApplyFrame] load error: {e}")

    def _show_blocked(self, status):
        status = str(status).lower()
        if status == "pending":
            icon, title, msg, color = (
                "⏳", "Application Pending",
                "You already have a pending application.\nPlease wait for the review to be completed.",
                "#D97706")
        elif status == "approved":
            icon, title, msg, color = (
                "✅", "Application Approved",
                "Your scholarship application has been approved!\nYou may now apply for renewal.",
                "#16A34A")
        elif status == "rejected":
            icon, title, msg, color = (
                "❌", "Application Rejected",
                "Your scholarship application was rejected.\nPlease contact the office for more information.",
                "#DC2626")
        else:
            return
        for w in self.winfo_children():
            w.destroy()
        box = tk.Frame(self, bg=BG)
        box.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(box, text=icon, bg=BG,
                 font=("Helvetica", 48)).pack(pady=(0, 12))
        tk.Label(box, text=title, bg=BG, fg=color,
                 font=("Helvetica", 18, "bold")).pack()
        tk.Label(box, text=msg, bg=BG, fg=TEXT_GRAY,
                 font=("Helvetica", 11),
                 justify="center").pack(pady=(8, 20))
        tk.Button(box, text="View My Applications",
                  bg=PURPLE, fg=WHITE,
                  relief="flat", bd=0,
                  font=("Helvetica", 11, "bold"),
                  padx=20, pady=8, cursor="hand2",
                  command=self.dashboard._show_applications).pack()

    def _show_existing_notice(self):
        pass

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
                    "houseStreet","schoolName","course","gwa"):
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
                        ("birth_cert","Birth Certificate"),("grades","Grades"),
                        ("cor","COR")]:
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
            from db import fetch_one, execute
            user = fetch_one("SELECT user_id FROM users WHERE email=%s",
                             (self.email,))
            if not user:
                self.after(0, self._on_error, "User not found.")
                return
            uid = user["user_id"]

            file_data = {}
            for key, path in self._files.items():
                with open(path, "rb") as f:
                    file_data[key] = f.read()

            from datetime import datetime
            execute("""
                INSERT INTO applications
                    (user_id, first_name, middle_name, last_name,
                     student_id, contact_number,
                     municipality, barangay, school_name,
                     course, year_level, gwa, year_applied,
                     essay,
                     doc_school_id, doc_id_picture, doc_birth_cert,
                     doc_grades, doc_cor,
                     status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending')
            """, (
                uid,
                self._vars["firstName"].get().strip(),
                self._vars["middleName"].get().strip() or None,
                self._vars["surname"].get().strip(),
                self._vars["studentId"].get().strip(),
                self._vars["contact"].get().strip(),
                self._vars["municipality"].get().strip(),
                self._vars["barangay"].get(),
                self._vars["schoolName"].get().strip(),
                self._vars["course"].get().strip(),
                self._vars["gradeLevel"].get(),
                float(self._vars["gwa"].get().strip()),
                datetime.now().year,
                reason,
                file_data["school_id"],
                file_data["id_picture"],
                file_data["birth_cert"],
                file_data["grades"],
                file_data["cor"],
            ))
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
