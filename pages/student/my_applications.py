import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

from db import fetch_one, fetch_all, execute

BG        = "#F7FAFC"
WHITE     = "#FFFFFF"
PURPLE    = "#667EEA"
PURPLE2   = "#764BA2"
BORDER    = "#E2E8F0"
TEXT_DARK = "#2D3748"
TEXT_GRAY = "#718096"
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


class ApplicationsFrame(tk.Frame):
    def __init__(self, parent, name, email, dashboard, **_):
        super().__init__(parent, bg=BG)
        self.name      = name
        self.email     = email
        self.dashboard = dashboard
        self._build()
        threading.Thread(target=self._fetch, daemon=True).start()

    # =========================================================================
    # BUILD UI
    # =========================================================================
    def _build(self):
        hdr = tk.Frame(self, bg=PURPLE)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📋  My Applications",
                 bg=PURPLE, fg=WHITE,
                 font=("Helvetica", 16, "bold"),
                 pady=14, padx=24, anchor="w").pack(fill="x")

        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=24, pady=(12, 4))
        tk.Button(bar, text="🔄 Refresh",
                  bg=WHITE, fg=PURPLE,
                  relief="flat", bd=1,
                  font=("Helvetica", 10),
                  cursor="hand2",
                  command=self._refresh).pack(side="right")

        self._canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(fill="both", expand=True)

        self._list_frame = tk.Frame(self._canvas, bg=BG)
        self._wid = self._canvas.create_window((0, 0), window=self._list_frame, anchor="nw")

        def _resize(e):
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
            self._canvas.itemconfig(self._wid, width=e.width)
        self._canvas.bind("<Configure>", _resize)
        self._canvas.bind("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self._canvas.bind("<Button-4>", lambda e: self._canvas.yview_scroll(-1, "units"))
        self._canvas.bind("<Button-5>", lambda e: self._canvas.yview_scroll(1, "units"))

        tk.Label(self._list_frame, text="Loading applications…",
                 bg=BG, fg=TEXT_GRAY, font=("Helvetica", 12)).pack(pady=40)

    # =========================================================================
    # DATA
    # =========================================================================
    def _refresh(self):
        for w in self._list_frame.winfo_children():
            w.destroy()
        tk.Label(self._list_frame, text="Loading applications…",
                 bg=BG, fg=TEXT_GRAY, font=("Helvetica", 12)).pack(pady=40)
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            user = fetch_one("SELECT user_id FROM users WHERE email=%s", (self.email,))
            if not user:
                raise ValueError("No user record found.")
            uid = user["user_id"]

            apps = fetch_all("""
                SELECT application_id, first_name, middle_name, last_name,
                       student_id, contact_number, municipality, barangay,
                       school_name, course, year_level, gwa,
                       status, submission_date
                FROM applications
                WHERE user_id=%s
                ORDER BY submission_date DESC
            """, (uid,)) or []

            renewals = fetch_all("""
                SELECT r.renewal_id, r.status, r.submission_date,
                       a.first_name, a.middle_name, a.last_name,
                       a.student_id, a.course, a.year_level, a.gwa
                FROM renewals r
                LEFT JOIN applications a ON a.application_id = r.application_id
                WHERE r.user_id=%s
                ORDER BY r.submission_date DESC
            """, (uid,)) or []

            combined = []
            for a in apps:
                a["type"] = "Application"
                if a.get("submission_date"):
                    a["submission_date"] = str(a["submission_date"])
                if a.get("gwa") is not None:
                    a["gwa"] = str(a["gwa"])
                combined.append(a)
            for r in renewals:
                r["type"] = "Renewal"
                r["application_id"] = r.get("renewal_id")
                if r.get("submission_date"):
                    r["submission_date"] = str(r["submission_date"])
                if r.get("gwa") is not None:
                    r["gwa"] = str(r["gwa"])
                combined.append(r)

            combined.sort(key=lambda x: x.get("submission_date", ""), reverse=True)
            self.after(0, self._render, combined)
        except Exception as exc:
            self.after(0, self._render_error, str(exc))

    # =========================================================================
    # RENDER
    # =========================================================================
    def _render(self, apps):
        if not self.winfo_exists() or not self._list_frame.winfo_exists():
            return
        for w in self._list_frame.winfo_children():
            w.destroy()
        if not apps:
            self._render_empty()
            return
        for app in apps:
            self._app_card(self._list_frame, app)

    def _render_empty(self):
        if not self.winfo_exists() or not self._list_frame.winfo_exists():
            return
        tk.Label(self._list_frame, text="📭 No applications yet.",
                 bg=BG, fg=TEXT_GRAY, font=("Helvetica", 14)).pack(pady=30)
        tk.Button(self._list_frame, text="Apply for Scholarship",
                  bg=PURPLE, fg=WHITE, relief="flat", bd=0,
                  font=("Helvetica", 11, "bold"),
                  padx=20, pady=8, cursor="hand2",
                  command=self.dashboard._show_apply).pack()

    def _render_error(self, msg):
        if not self.winfo_exists() or not self._list_frame.winfo_exists():
            return
        tk.Label(self._list_frame, text=f"Error loading data: {msg}",
                 bg=BG, fg=RED, font=("Helvetica", 11)).pack(pady=30)

    # =========================================================================
    # CARD
    # =========================================================================
    def _app_card(self, parent, app):
        status = str(app.get("status", "pending")).lower()
        if status == "approved":
            bar_color, badge_bg, badge_fg, badge_txt = \
                GREEN, "#D4EDDA", "#155724", "✓ Approved"
        elif status == "rejected":
            bar_color, badge_bg, badge_fg, badge_txt = \
                RED, "#F8D7DA", "#721C24", "✗ Rejected"
        else:
            bar_color, badge_bg, badge_fg, badge_txt = \
                "#FFA500", "#FFF3CD", "#856404", "⏳ Pending"

        outer = tk.Frame(parent, bg=BG)
        outer.pack(fill="x", padx=24, pady=8)
        tk.Frame(outer, bg=bar_color, width=5).pack(side="left", fill="y")

        card = tk.Frame(outer, bg=WHITE,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(side="left", fill="both", expand=True)

        top = tk.Frame(card, bg=WHITE)
        top.pack(fill="x", padx=16, pady=(12, 4))

        name_txt = " ".join(filter(None, [
            app.get("first_name", ""), app.get("middle_name", ""), app.get("last_name", "")]))
        tk.Label(top, text=name_txt, bg=WHITE, fg=TEXT_DARK,
                 font=("Helvetica", 13, "bold"), anchor="w").pack(anchor="w")
        tk.Label(top, text=f"{app['type']}  •  ID #{app['application_id']}",
                 bg=WHITE, fg=TEXT_GRAY, font=("Helvetica", 9)).pack(anchor="w")
        tk.Label(top, text=f"📅 Submitted: {app.get('submission_date', 'N/A')}",
                 bg=WHITE, fg="#666666", font=("Helvetica", 9)).pack(anchor="w")
        tk.Label(top, text=badge_txt, bg=badge_bg, fg=badge_fg,
                 font=("Helvetica", 9, "bold"),
                 padx=10, pady=4).place(relx=1.0, rely=0.0, anchor="ne")

        details = tk.Frame(card, bg="#F8F9FA",
                           highlightbackground=BORDER, highlightthickness=1)
        details.pack(fill="x", padx=16, pady=(4, 8))
        for lbl, val in [
            ("Student ID", app.get("student_id", "N/A")),
            ("School",     app.get("school_name", "N/A")),
            ("Course",     app.get("course", "N/A")),
            ("Year Level", app.get("year_level", "N/A")),
            ("GWA",        str(app.get("gwa", "N/A"))),
        ]:
            row = tk.Frame(details, bg="#F8F9FA")
            row.pack(fill="x", padx=12, pady=2)
            tk.Label(row, text=lbl, bg="#F8F9FA", fg="#666666",
                     font=("Helvetica", 9)).pack(side="left")
            tk.Label(row, text=val, bg="#F8F9FA", fg=TEXT_DARK,
                     font=("Helvetica", 9, "bold")).pack(side="right")

        # Only show Edit button for pending applications
        if status == "pending" and app["type"] == "Application":
            tk.Button(card, text="✏ Edit Application",
                      bg=PURPLE, fg=WHITE, relief="flat", bd=0,
                      font=("Helvetica", 10), cursor="hand2",
                      padx=12, pady=6,
                      command=lambda a=app: self._edit_dialog(a)
                      ).pack(anchor="w", padx=16, pady=(0, 12))
        elif status in ("approved", "rejected"):
            tk.Label(card,
                     text="🔒 Editing is not available for this application.",
                     bg=WHITE, fg=TEXT_GRAY,
                     font=("Helvetica", 9, "italic"),
                     anchor="w").pack(anchor="w", padx=16, pady=(0, 12))

    # =========================================================================
    # EDIT DIALOG
    # =========================================================================
    def _edit_dialog(self, app):
        dlg = tk.Toplevel(self)
        dlg.title("Edit Application")
        dlg.configure(bg=WHITE)
        dlg.grab_set()
        dlg.resizable(True, True)

        root = self.winfo_toplevel()
        root.update_idletasks()
        w, h = 560, 720
        px = root.winfo_x() + (root.winfo_width()  - w) // 2
        py = root.winfo_y() + (root.winfo_height() - h) // 2
        dlg.geometry(f"{w}x{h}+{px}+{py}")

        # ── Scrollable body ───────────────────────────────────────────────────
        canvas = tk.Canvas(dlg, bg=WHITE, highlightthickness=0)
        sb = tk.Scrollbar(dlg, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        body = tk.Frame(canvas, bg=WHITE)
        wid  = canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))
        canvas.bind("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-e.delta/120), "units"))
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        tk.Label(body, text="Edit Application",
                 bg=WHITE, fg=PURPLE,
                 font=("Helvetica", 14, "bold"),
                 pady=12).pack()
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=20)

        vars_  = {}
        files_ = {k: None for k in ('school_id','id_picture','birth_cert','grades','cor')}
        flbls_ = {}

        def _lbl(text):
            tk.Label(body, text=text, bg=WHITE, fg=PURPLE,
                     font=("Helvetica", 11, "bold"),
                     anchor="w", padx=20, pady=8).pack(fill="x")

        def _field(key, label, val="", disabled=False):
            tk.Label(body, text=label, bg=WHITE, fg=TEXT_DARK,
                     font=("Helvetica", 10), anchor="w",
                     padx=20).pack(fill="x", pady=(6, 2))
            var = tk.StringVar(value=val)
            vars_[key] = var
            bg    = DISABLED if disabled else INPUT_BG
            state = "disabled" if disabled else "normal"
            tk.Entry(body, textvariable=var, state=state,
                     bg=bg, fg=TEXT_DARK,
                     disabledbackground=DISABLED,
                     disabledforeground="#A0AEC0",
                     relief="flat", bd=0,
                     font=("Helvetica", 11),
                     highlightthickness=1,
                     highlightbackground=BORDER,
                     highlightcolor=PURPLE
                     ).pack(fill="x", padx=20, ipady=7, pady=(0, 2))

        def _dropdown(key, label, options, val=""):
            tk.Label(body, text=label, bg=WHITE, fg=TEXT_DARK,
                     font=("Helvetica", 10), anchor="w",
                     padx=20).pack(fill="x", pady=(6, 2))
            var = tk.StringVar(value=val)
            vars_[key] = var
            cb = ttk.Combobox(body, textvariable=var,
                              values=options, state="readonly",
                              font=("Helvetica", 11))
            cb.pack(fill="x", padx=20, pady=(0, 2))

        def _doc(key, label):
            row = tk.Frame(body, bg=WHITE)
            row.pack(fill="x", padx=20, pady=4)
            tk.Label(row, text=label, bg=WHITE, fg=TEXT_DARK,
                     font=("Helvetica", 10, "bold"), anchor="w").pack(anchor="w")
            btn_row = tk.Frame(row, bg=WHITE)
            btn_row.pack(fill="x", pady=(4, 0))
            tk.Button(btn_row, text="📁 Choose File",
                      bg=INPUT_BG, fg=PURPLE,
                      relief="flat", bd=1,
                      font=("Helvetica", 10), cursor="hand2",
                      command=lambda k=key: _pick(k)).pack(side="left")
            lbl = tk.Label(btn_row, text="No new file chosen",
                           bg=WHITE, fg=TEXT_GRAY, font=("Helvetica", 9))
            lbl.pack(side="left", padx=8)
            flbls_[key] = lbl

        def _pick(key):
            path = filedialog.askopenfilename(
                filetypes=[("Images & PDF", "*.jpg *.jpeg *.png *.pdf")])
            if path:
                files_[key] = path
                flbls_[key].config(text=os.path.basename(path), fg=TEXT_DARK)

        # Personal Information
        _lbl("👤 Personal Information")
        _field("firstName",  "First Name",    app.get("first_name", ""),  disabled=True)
        _field("middleName", "Middle Name",   app.get("middle_name", ""), disabled=True)
        _field("surname",    "Last Name",     app.get("last_name", ""),   disabled=True)
        _field("studentId",  "Student ID *",  app.get("student_id", ""))
        _field("contact",    "Contact Number *", app.get("contact_number", ""))

        # Address
        _lbl("📍 Address")
        _field("municipality", "Municipality", app.get("municipality", "Majayjay"), disabled=True)
        _field("houseStreet",  "House No. / Street *", "")
        _dropdown("barangay", "Barangay *", BARANGAYS, app.get("barangay", ""))

        # Academic
        _lbl("🎓 Academic Information")
        _field("schoolName", "School Name *", app.get("school_name", ""))
        _field("course",     "Course *",      app.get("course", ""))
        _dropdown("yearLevel", "Year Level *", GRADE_LEVELS, app.get("year_level", ""))
        _field("gwa", "GWA *", str(app.get("gwa", "")))

        # Documents
        _lbl("📎 Documents (leave blank to keep existing)")
        for k, l in [
            ("school_id",  "School ID"),
            ("id_picture", "2x2 ID Picture"),
            ("birth_cert", "Birth Certificate"),
            ("grades",     "Copy of Grades"),
            ("cor",        "COR"),
        ]:
            _doc(k, l)

        # Error label
        err_var = tk.StringVar()
        tk.Label(body, textvariable=err_var,
                 bg=WHITE, fg=RED,
                 font=("Helvetica", 9),
                 wraplength=500).pack(fill="x", padx=20)

        # Buttons
        btn_row = tk.Frame(body, bg=WHITE)
        btn_row.pack(fill="x", padx=20, pady=(12, 20))

        tk.Button(btn_row, text="Cancel",
                  bg=WHITE, fg=TEXT_GRAY,
                  relief="flat", bd=1,
                  font=("Helvetica", 10),
                  cursor="hand2",
                  command=dlg.destroy).pack(side="left", padx=(0, 8))

        def _save():
            err_var.set("")
            for key, label in [("studentId","Student ID"),("contact","Contact"),
                                ("schoolName","School Name"),("course","Course"),("gwa","GWA")]:
                if not vars_[key].get().strip():
                    err_var.set(f"{label} is required.")
                    return
            try:
                gwa = float(vars_["gwa"].get().strip())
            except ValueError:
                err_var.set("GWA must be a number.")
                return

            # Build file updates
            doc_cols = {
                "school_id":  "doc_school_id",
                "id_picture": "doc_id_picture",
                "birth_cert": "doc_birth_cert",
                "grades":     "doc_grades",
                "cor":        "doc_cor",
            }
            set_parts = [
                "student_id=%s", "contact_number=%s",
                "barangay=%s", "school_name=%s",
                "course=%s", "year_level=%s", "gwa=%s",
            ]
            params = [
                vars_["studentId"].get().strip(),
                vars_["contact"].get().strip(),
                vars_["barangay"].get(),
                vars_["schoolName"].get().strip(),
                vars_["course"].get().strip(),
                vars_["yearLevel"].get(),
                gwa,
            ]
            for key, col in doc_cols.items():
                if files_[key]:
                    with open(files_[key], "rb") as f:
                        set_parts.append(f"{col}=%s")
                        params.append(f.read())

            params.append(app["application_id"])
            try:
                execute(
                    f"UPDATE applications SET {', '.join(set_parts)} WHERE application_id=%s",
                    tuple(params))
                dlg.destroy()
                messagebox.showinfo("Saved", "Application updated successfully.")
                self._refresh()
            except Exception as exc:
                err_var.set(f"Error: {exc}")

        tk.Button(btn_row, text="💾 Save Changes",
                  bg=PURPLE, fg=WHITE,
                  relief="flat", bd=0,
                  font=("Helvetica", 10, "bold"),
                  cursor="hand2",
                  command=_save).pack(side="right")
