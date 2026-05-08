import tkinter as tk
from tkinter import ttk, filedialog
import threading
import os
from datetime import datetime

BG       = "#F7FAFC"
WHITE    = "#FFFFFF"
PURPLE   = "#667EEA"
PURPLE2  = "#764BA2"
BORDER   = "#E2E8F0"
DARK     = "#2D3748"
GRAY     = "#718096"
MED      = "#4A5568"
INPUT_BG = "#F7FAFC"
RED      = "#F56565"
GREEN    = "#48BB78"
SHADOW   = "#CBD5E0"
DIVIDER  = "#E2E8F0"

MUNICIPALITIES = [
    "Majayjay",
    "Liliw",
    "Magdalena",
    "Luisiana",
    "Cavinti",
    "Kalayaan",
    "Pagsanjan",
    "Pangil",
    "Pakil",
    "Siniloan",
    "Famy",
    "Santa Maria",
    "Nagcarlan",
    "Rizal",
    "San Pablo City",
]

BARANGAYS = [
    "Barangay 1 (Poblacion)",
    "Barangay 2 (Poblacion)",
    "Barangay 3 (Poblacion)",
    "Barangay 4 (Poblacion)",
    "Barangay 5 (Poblacion)",
    "Barangay 6 (Poblacion)",
    "Barangay 7 (Poblacion)",
    "Barangay 8 (Poblacion)",
    "Anulin",
    "Bakia",
    "Bukal",
    "Bunga",
    "Buo",
    "Burlungan",
    "Cigaras",
    "Halayhayin",
    "Humalin",
    "Ibabang Palina",
    "Ibabang Sungi",
    "Ibabang Taykin",
    "Ilayang Palina",
    "Ilayang Sungi",
    "Ilayang Taykin",
    "Isabang",
    "Malinao",
    "Manaol",
    "Munting Kawayan",
    "Olla",
    "Palayan",
    "Pansol",
    "Patimbao",
    "Pook",
    "Talortor",
    "Tawagan",
    "Taytay",
    "Tipacan",
]

YEAR_LEVELS = ["1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year"]
CURRENT_YEAR = datetime.now().year
YEAR_OPTIONS = [str(y) for y in range(CURRENT_YEAR, CURRENT_YEAR - 6, -1)]


class ApplyScholarshipPage(tk.Frame):
    def __init__(self, parent, user: dict):
        super().__init__(parent, bg=BG)
        self.pack(fill="both", expand=True)
        self.user = user
        self._vars = {}
        self._build_ui()
        # Check on load — lock form if already applied
        threading.Thread(target=self._check_existing, daemon=True).start()

    def _build_ui(self):
        # ── Top bar ────────────────────────────────────────────────────────────
        topbar = tk.Frame(self, bg=WHITE, height=64)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Frame(topbar, bg=BORDER, height=1).pack(side="bottom", fill="x")
        tk.Label(topbar, text="Apply for Scholarship",
                 bg=WHITE, fg=DARK,
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=28, pady=16)

        # ── Scrollable body ────────────────────────────────────────────────────
        scroll_canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        scroll_canvas.pack(fill="both", expand=True)

        inner = tk.Frame(scroll_canvas, bg=BG)
        wid   = scroll_canvas.create_window((0, 0), window=inner, anchor="n")

        def _update_scroll(e=None):
            bbox = scroll_canvas.bbox("all")
            if bbox:
                scroll_canvas.configure(scrollregion=bbox)
        inner.bind("<Configure>", _update_scroll)
        scroll_canvas.bind("<Configure>",
                           lambda e: scroll_canvas.itemconfig(wid, width=e.width))
        scroll_canvas.bind("<MouseWheel>",
                           lambda e: scroll_canvas.yview_scroll(
                               int(-1 * (e.delta / 120)), "units"))
        inner.bind("<MouseWheel>",
                   lambda e: scroll_canvas.yview_scroll(
                       int(-1 * (e.delta / 120)), "units"))

        # ── Card ───────────────────────────────────────────────────────────────
        center = tk.Frame(inner, bg=BG)
        center.pack(pady=(24, 32), padx=32, fill="x")

        shadow = tk.Frame(center, bg=SHADOW)
        shadow.pack(fill="x")
        card = tk.Frame(shadow, bg=WHITE, padx=36, pady=32)
        card.pack(fill="x", padx=2, pady=2)

        # ── Section: Personal Information ──────────────────────────────────────
        self._section(card, "👤  Personal Information")

        row1 = tk.Frame(card, bg=WHITE)
        row1.pack(fill="x")
        self._field_col(row1, "First Name *",   "first_name",  side="left")
        tk.Frame(row1, bg=WHITE, width=16).pack(side="left")
        self._field_col(row1, "Middle Name",    "middle_name", side="left")
        tk.Frame(row1, bg=WHITE, width=16).pack(side="left")
        self._field_col(row1, "Last Name *",    "last_name",   side="left")

        row2 = tk.Frame(card, bg=WHITE)
        row2.pack(fill="x", pady=(0, 0))
        self._field_col(row2, "Student ID *",     "student_id",      side="left")
        tk.Frame(row2, bg=WHITE, width=16).pack(side="left")
        self._field_col(row2, "Contact Number *", "contact_number",  side="left")

        # ── Section: Address ───────────────────────────────────────────────────
        self._section(card, "📍  Address")

        row3 = tk.Frame(card, bg=WHITE)
        row3.pack(fill="x")
        self._dropdown_col(row3, "Municipality *", "municipality",
                           MUNICIPALITIES, side="left")
        tk.Frame(row3, bg=WHITE, width=16).pack(side="left")
        self._dropdown_col(row3, "Barangay *", "barangay",
                           BARANGAYS, side="left")

        # ── Section: Academic Information ──────────────────────────────────────
        self._section(card, "🎓  Academic Information")

        self._flabel(card, "School Name *")
        self._input(card, "school_name")

        row4 = tk.Frame(card, bg=WHITE)
        row4.pack(fill="x")
        self._field_col(row4, "Course / Program *", "course", side="left")
        tk.Frame(row4, bg=WHITE, width=16).pack(side="left")

        # Year Level dropdown
        yr_col = tk.Frame(row4, bg=WHITE)
        yr_col.pack(side="left", fill="x", expand=True)
        self._flabel(yr_col, "Year Level *")
        self._vars["year_level"] = tk.StringVar(value="Select year level")
        self._dropdown_widget(yr_col, self._vars["year_level"], YEAR_LEVELS)

        row5 = tk.Frame(card, bg=WHITE)
        row5.pack(fill="x")
        self._field_col(row5, "GWA *", "gwa", side="left",
                        placeholder="e.g. 1.75")
        tk.Frame(row5, bg=WHITE, width=16).pack(side="left")

        # Year Applied dropdown
        ya_col = tk.Frame(row5, bg=WHITE)
        ya_col.pack(side="left", fill="x", expand=True)
        self._flabel(ya_col, "Year Applied *")
        self._vars["year_applied"] = tk.StringVar(value=str(CURRENT_YEAR))
        self._dropdown_widget(ya_col, self._vars["year_applied"], YEAR_OPTIONS)

        # ── Section: Documents ─────────────────────────────────────────────────
        self._section(card, "📎  Upload Documents")

        tk.Label(card, text="Accepted formats: JPG, PNG, PDF  •  Max 5MB each",
                 bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 8))

        self._doc_paths = {}
        docs = [
            ("school_id",   "School ID",                    "🪪"),
            ("id_picture",  "ID Picture",                   "🖼️"),
            ("birth_cert",  "Birth Certificate",            "📄"),
            ("grades",      "Grades",                       "📊"),
            ("cor",         "Certificate of Registration (COR)", "📋"),
        ]
        self._doc_rows = {}
        for key, label, icon in docs:
            self._doc_upload_row(card, key, label, icon)

        # ── Section: Essay ─────────────────────────────────────────────────────
        self._section(card, "✍️  Essay")

        self._flabel(card, "Why should you be selected?  *")
        essay_wrap = tk.Frame(card, bg=WHITE, highlightthickness=1,
                              highlightbackground=BORDER,
                              highlightcolor=PURPLE)
        essay_wrap.pack(fill="x", pady=(0, 4))
        self.essay_text = tk.Text(essay_wrap, height=6,
                                  bg=INPUT_BG, fg=DARK,
                                  font=("Segoe UI", 11),
                                  relief="flat", bd=0,
                                  insertbackground=PURPLE,
                                  wrap="word")
        self.essay_text.pack(fill="x", padx=12, pady=10)
        self.essay_text.bind("<FocusIn>",
            lambda e: essay_wrap.config(highlightbackground=PURPLE))
        self.essay_text.bind("<FocusOut>",
            lambda e: essay_wrap.config(highlightbackground=BORDER))

        # ── Error / success message ────────────────────────────────────────────
        self.msg_var = tk.StringVar()
        self.msg_label = tk.Label(card, textvariable=self.msg_var,
                                  bg=WHITE, fg=RED,
                                  font=("Segoe UI", 9),
                                  wraplength=600, justify="left")
        self.msg_label.pack(fill="x", pady=(8, 0))

        # ── Divider ────────────────────────────────────────────────────────────
        div = tk.Frame(card, bg=WHITE)
        div.pack(fill="x", pady=(16, 16))
        tk.Frame(div, bg=BORDER, height=1).place(relx=0, rely=0.5,
                                                  relwidth=0.38, anchor="w")
        tk.Label(div, text="  Submit Application  ",
                 bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 9)).pack()
        tk.Frame(div, bg=BORDER, height=1).place(relx=1, rely=0.5,
                                                  relwidth=0.38, anchor="e")

        # ── Submit button ──────────────────────────────────────────────────────
        self.submit_btn = tk.Button(card, text="Submit Application →",
                                    bg=PURPLE, fg=WHITE,
                                    activebackground=PURPLE2,
                                    activeforeground=WHITE,
                                    relief="flat", bd=0,
                                    font=("Segoe UI", 12, "bold"),
                                    cursor="hand2",
                                    command=self._submit)
        self.submit_btn.pack(fill="x", ipady=11)
        self.submit_btn.bind("<Enter>",
            lambda e: self.submit_btn.config(bg=PURPLE2))
        self.submit_btn.bind("<Leave>",
            lambda e: self.submit_btn.config(
                bg="#A0AEC0" if self.submit_btn["state"] == "disabled"
                else PURPLE))

    # ── Widget helpers ─────────────────────────────────────────────────────────
    def _section(self, parent, text):
        tk.Frame(parent, bg=DIVIDER, height=1).pack(fill="x", pady=(20, 0))
        tk.Label(parent, text=text, bg=WHITE, fg=PURPLE,
                 font=("Segoe UI", 12, "bold"),
                 anchor="w").pack(fill="x", pady=(10, 4))

    def _flabel(self, parent, text):
        tk.Label(parent, text=text, bg=WHITE, fg=DARK,
                 font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill="x", pady=(10, 4))

    def _input(self, parent, key, placeholder=""):
        wrap = tk.Frame(parent, bg=WHITE, highlightthickness=1,
                        highlightbackground=BORDER, highlightcolor=PURPLE)
        wrap.pack(fill="x", pady=(0, 4))
        self._vars[key] = tk.StringVar()
        e = tk.Entry(wrap, textvariable=self._vars[key],
                     bg=INPUT_BG, fg=DARK,
                     insertbackground=PURPLE,
                     relief="flat", bd=0,
                     font=("Segoe UI", 11))
        e.pack(fill="x", ipady=10, padx=12)
        e.bind("<FocusIn>",
               lambda ev, w=wrap: w.config(highlightbackground=PURPLE))
        e.bind("<FocusOut>",
               lambda ev, w=wrap: w.config(highlightbackground=BORDER))
        return e

    def _field_col(self, parent, label, key, side="left", placeholder=""):
        col = tk.Frame(parent, bg=WHITE)
        col.pack(side=side, fill="x", expand=True)
        self._flabel(col, label)
        wrap = tk.Frame(col, bg=WHITE, highlightthickness=1,
                        highlightbackground=BORDER, highlightcolor=PURPLE)
        wrap.pack(fill="x", pady=(0, 4))
        self._vars[key] = tk.StringVar()
        e = tk.Entry(wrap, textvariable=self._vars[key],
                     bg=INPUT_BG, fg=DARK,
                     insertbackground=PURPLE,
                     relief="flat", bd=0,
                     font=("Segoe UI", 11))
        e.pack(fill="x", ipady=10, padx=12)
        e.bind("<FocusIn>",
               lambda ev, w=wrap: w.config(highlightbackground=PURPLE))
        e.bind("<FocusOut>",
               lambda ev, w=wrap: w.config(highlightbackground=BORDER))
        return e

    def _dropdown_widget(self, parent, var, options):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("App.TCombobox",
                        fieldbackground=INPUT_BG,
                        background=INPUT_BG,
                        foreground=DARK,
                        bordercolor=BORDER,
                        arrowcolor=PURPLE,
                        padding=(10, 8))
        style.map("App.TCombobox",
                  fieldbackground=[("readonly", INPUT_BG)],
                  bordercolor=[("focus", PURPLE)])
        cb = ttk.Combobox(parent, textvariable=var,
                          values=options, state="readonly",
                          style="App.TCombobox",
                          font=("Segoe UI", 11))
        cb.pack(fill="x", pady=(0, 4), ipady=2)
        return cb

    def _dropdown_col(self, parent, label, key, options, side="left"):
        col = tk.Frame(parent, bg=WHITE)
        col.pack(side=side, fill="x", expand=True)
        self._flabel(col, label)
        self._vars[key] = tk.StringVar(value=f"Select {label.rstrip(' *').lower()}")
        self._dropdown_widget(col, self._vars[key], options)

    # ── Submit ─────────────────────────────────────────────────────────────────
    def _submit(self):
        self.msg_var.set("")

        # Collect
        first   = self._vars["first_name"].get().strip()
        middle  = self._vars["middle_name"].get().strip()
        last    = self._vars["last_name"].get().strip()
        sid     = self._vars["student_id"].get().strip()
        contact = self._vars["contact_number"].get().strip()
        muni    = self._vars["municipality"].get().strip()
        brgy    = self._vars["barangay"].get().strip()
        school  = self._vars["school_name"].get().strip()
        course  = self._vars["course"].get().strip()
        yr_lvl  = self._vars["year_level"].get().strip()
        gwa     = self._vars["gwa"].get().strip()
        yr_app  = self._vars["year_applied"].get().strip()
        essay   = self.essay_text.get("1.0", "end").strip()

        # Validate
        if not first:
            return self._show_msg("Please enter your first name.")
        if not last:
            return self._show_msg("Please enter your last name.")
        if not sid:
            return self._show_msg("Please enter your student ID.")
        if not contact:
            return self._show_msg("Please enter your contact number.")
        if muni.startswith("Select"):
            return self._show_msg("Please select a municipality.")
        if brgy.startswith("Select"):
            return self._show_msg("Please select a barangay.")
        if not school:
            return self._show_msg("Please enter your school name.")
        if not course:
            return self._show_msg("Please enter your course/program.")
        if yr_lvl.startswith("Select"):
            return self._show_msg("Please select your year level.")
        if not gwa:
            return self._show_msg("Please enter your GWA.")
        try:
            gwa_val = float(gwa)
            if not (1.0 <= gwa_val <= 5.0):
                raise ValueError
        except ValueError:
            return self._show_msg("GWA must be a number between 1.0 and 5.0.")
        if not essay:
            return self._show_msg("Please answer the essay question.")

        # Validate documents
        doc_labels = {
            "school_id":  "School ID",
            "id_picture": "ID Picture",
            "birth_cert": "Birth Certificate",
            "grades":     "Grades",
            "cor":        "Certificate of Registration (COR)",
        }
        for key, lbl in doc_labels.items():
            path = self._doc_paths.get(key, "")
            if not path:
                return self._show_msg(f"Please upload your {lbl}.")
            if not os.path.isfile(path):
                return self._show_msg(f"{lbl}: file no longer found. Please re-upload.")
            if os.path.getsize(path) > 5 * 1024 * 1024:
                return self._show_msg(f"{lbl} exceeds the 5MB limit.")

        self._set_loading(True)
        threading.Thread(target=self._do_submit,
                         args=(first, middle, last, sid, contact,
                               muni, brgy, school, course, yr_lvl,
                               gwa_val, yr_app, essay),
                         daemon=True).start()

    def _doc_upload_row(self, parent, key, label, icon):
        row = tk.Frame(parent, bg=WHITE, highlightthickness=1,
                       highlightbackground=BORDER)
        row.pack(fill="x", pady=(0, 8))

        # Left: icon + label
        left = tk.Frame(row, bg=WHITE)
        left.pack(side="left", fill="y", padx=(12, 0), pady=10)
        tk.Label(left, text=icon, bg=WHITE,
                 font=("Segoe UI", 16)).pack(side="left", padx=(0, 8))
        info = tk.Frame(left, bg=WHITE)
        info.pack(side="left")
        tk.Label(info, text=label, bg=WHITE, fg=DARK,
                 font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(anchor="w")
        name_lbl = tk.Label(info, text="No file chosen",
                            bg=WHITE, fg=GRAY,
                            font=("Segoe UI", 9), anchor="w")
        name_lbl.pack(anchor="w")

        # Right: Browse + Clear buttons
        right = tk.Frame(row, bg=WHITE)
        right.pack(side="right", padx=12, pady=10)

        clear_btn = tk.Button(right, text="✕",
                              bg=WHITE, fg=RED,
                              relief="flat", bd=0,
                              font=("Segoe UI", 10, "bold"),
                              cursor="hand2")
        clear_btn.pack(side="right", padx=(6, 0))

        browse_btn = tk.Button(right, text="Browse",
                               bg=PURPLE, fg=WHITE,
                               activebackground=PURPLE2,
                               activeforeground=WHITE,
                               relief="flat", bd=0,
                               font=("Segoe UI", 9, "bold"),
                               cursor="hand2",
                               padx=14, pady=4)
        browse_btn.pack(side="right")
        browse_btn.bind("<Enter>", lambda e: browse_btn.config(bg=PURPLE2))
        browse_btn.bind("<Leave>", lambda e: browse_btn.config(bg=PURPLE))

        def _browse(k=key, lbl=name_lbl, r=row):
            path = filedialog.askopenfilename(
                title=f"Select {label}",
                filetypes=[("Images & PDF", "*.jpg *.jpeg *.png *.pdf"),
                           ("All files", "*.*")])
            if path:
                self._doc_paths[k] = path
                fname = os.path.basename(path)
                display = fname if len(fname) <= 40 else fname[:37] + "…"
                lbl.config(text=display, fg=PURPLE)
                r.config(highlightbackground=GREEN)

        def _clear(k=key, lbl=name_lbl, r=row):
            self._doc_paths.pop(k, None)
            lbl.config(text="No file chosen", fg=GRAY)
            r.config(highlightbackground=BORDER)

        browse_btn.config(command=_browse)
        clear_btn.config(command=_clear)
        self._doc_rows[key] = (row, name_lbl)

    def _do_submit(self, first, middle, last, sid, contact,
                   muni, brgy, school, course, yr_lvl,
                   gwa_val, yr_app, essay):
        try:
            from db import execute, fetch_one
            uid = self.user.get("user_id") or self.user.get("id")

            # Block if ANY application exists — student must use renewal instead
            existing = fetch_one(
                "SELECT application_id, status FROM applications "
                "WHERE user_id = %s", (uid,))
            if existing:
                status = existing.get("status", "existing")
                if status == "pending":
                    msg = ("You already have a pending application. "
                           "Please wait for it to be reviewed.")
                elif status == "approved":
                    msg = ("You already have an approved scholarship. "
                           "Please use Renewal Scholarship instead.")
                else:
                    msg = ("You already submitted an application. "
                           "Please use Renewal Scholarship to re-apply.")
                self.after(0, self._show_msg, msg)
                self.after(0, self._set_loading, False)
                return

            # Read document bytes
            def _read(key):
                path = self._doc_paths.get(key, "")
                if path and os.path.isfile(path):
                    with open(path, "rb") as f:
                        return f.read()
                return None

            execute(
                """INSERT INTO applications
                   (user_id, first_name, middle_name, last_name,
                    student_id, contact_number,
                    municipality, barangay,
                    school_name, course, year_level,
                    gwa, year_applied, essay,
                    doc_school_id, doc_id_picture, doc_birth_cert,
                    doc_grades, doc_cor,
                    status)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                           %s,%s,%s,%s,%s,'pending')""",
                (uid, first, middle or None, last,
                 sid, contact, muni, brgy,
                 school, course, yr_lvl, gwa_val, yr_app, essay,
                 _read("school_id"), _read("id_picture"), _read("birth_cert"),
                 _read("grades"),    _read("cor")))

            self.after(0, self._on_success)
        except Exception as exc:
            self.after(0, self._show_msg, f"Error: {exc}")
            self.after(0, self._set_loading, False)

    def _check_existing(self):
        """Called on page load — locks the form if student already has an application."""
        try:
            from db import fetch_one
            uid = self.user.get("user_id") or self.user.get("id")
            existing = fetch_one(
                "SELECT status FROM applications WHERE user_id = %s", (uid,))
            if existing:
                status = existing.get("status", "existing")
                if status == "pending":
                    msg = "⏳ You have a pending application. Please wait for the review."
                elif status == "approved":
                    msg = "✅ You have an approved scholarship. Use Renewal Scholarship to re-apply."
                else:
                    msg = "ℹ️ You already submitted an application. Use Renewal Scholarship to re-apply."
                self.after(0, self._lock_form, msg)
        except Exception:
            pass

    def _lock_form(self, msg: str):
        """Disable the submit button and show a notice banner."""
        self.submit_btn.config(
            state="disabled",
            bg="#A0AEC0",
            text="Application Already Submitted")
        self._show_msg(msg, "#718096")

    def _on_success(self):
        self._set_loading(False)
        self._show_msg("✅ Application submitted successfully!", GREEN)
        # Clear all fields
        for key, var in self._vars.items():
            if key == "year_applied":
                continue
            if key in ("municipality", "barangay", "year_level"):
                var.set(f"Select {key.replace('_', ' ')}")
            else:
                var.set("")
        self.essay_text.delete("1.0", "end")
        # Reset document rows
        self._doc_paths.clear()
        for key, (row, lbl) in self._doc_rows.items():
            lbl.config(text="No file chosen", fg=GRAY)
            row.config(highlightbackground=BORDER)
        # Lock the form — student cannot apply again
        self.after(1500, lambda: self._lock_form(
            "✅ Application submitted! Use Renewal Scholarship if you need to re-apply."))

    def _set_loading(self, loading: bool):
        self.submit_btn.config(
            text="Submitting…" if loading else "Submit Application →",
            state="disabled" if loading else "normal",
            bg="#A0AEC0" if loading else PURPLE)

    def _show_msg(self, msg: str, color: str = RED):
        self.msg_var.set(msg)
        self.msg_label.config(fg=color)
