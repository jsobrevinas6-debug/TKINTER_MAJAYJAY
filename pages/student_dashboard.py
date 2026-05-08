import tkinter as tk

BG         = "#F7FAFC"
WHITE      = "#FFFFFF"
PURPLE     = "#667EEA"
PURPLE2    = "#764BA2"
SIDEBAR_BG = "#2D3748"
SIDEBAR_H  = "#3D4F63"
TEXT_DARK  = "#2D3748"
TEXT_LIGHT = "#EDF2F7"
TEXT_GRAY  = "#718096"
BORDER     = "#E2E8F0"
RED        = "#F56565"
SHADOW     = "#CBD5E0"
DIVIDER    = "#4A5568"


class StudentDashboard(tk.Frame):
    def __init__(self, parent, name: str, email: str, app):
        super().__init__(parent, bg=BG)
        self.app   = app
        self.name  = name
        self.email = email
        self.user  = {"name": name, "email": email, "user_type": "student"}
        self._load_user()
        self._build_ui()

    def _load_user(self):
        try:
            from db import fetch_one
            row = fetch_one("SELECT * FROM users WHERE email = %s", (self.email,))
            if row:
                self.user = row
        except Exception:
            pass

    def _build_ui(self):
        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=230)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Gradient header in sidebar
        hdr = tk.Canvas(sidebar, height=160, bg=SIDEBAR_BG,
                        highlightthickness=0)
        hdr.pack(fill="x")
        hdr.bind("<Configure>", lambda e: self._draw_sidebar_header(hdr))
        self._sidebar_hdr = hdr

        tk.Frame(sidebar, bg=DIVIDER, height=1).pack(fill="x", padx=16)

        # Nav items
        nav_items = [
            ("🏠   Home",               self._show_home),
            ("📋   Apply Scholarship",  self._open_apply),
            ("📁   My Applications",    self._open_applications),
            ("🔄   Renewal",            self._open_renewal),
            ("👤   My Profile",         self._open_profile),
        ]
        self._nav_buttons = []
        nav_frame = tk.Frame(sidebar, bg=SIDEBAR_BG)
        nav_frame.pack(fill="x", pady=(8, 0))

        for label, cmd in nav_items:
            btn = tk.Button(nav_frame, text=label, anchor="w",
                            bg=SIDEBAR_BG, fg=TEXT_LIGHT,
                            activebackground=PURPLE, activeforeground=WHITE,
                            relief="flat", bd=0, cursor="hand2",
                            font=("Segoe UI", 11), padx=20, pady=8)
            btn.pack(fill="x", padx=8, pady=1)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=SIDEBAR_H)
                     if b["bg"] != PURPLE else None)
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=SIDEBAR_BG)
                     if b["bg"] == SIDEBAR_H else None)
            self._nav_buttons.append(btn)
            btn.config(command=lambda c=cmd, b=btn: self._nav(c, b))

        tk.Frame(sidebar, bg=DIVIDER, height=1).pack(fill="x", padx=16, pady=(12, 4))

        # Logout
        logout_btn = tk.Button(sidebar, text="🚪   Log Out", anchor="w",
                               bg=SIDEBAR_BG, fg=RED,
                               activebackground="#742A2A", activeforeground=WHITE,
                               relief="flat", bd=0, cursor="hand2",
                               font=("Segoe UI", 11), padx=20, pady=8,
                               command=self._logout)
        logout_btn.pack(fill="x", padx=8, pady=1)
        logout_btn.bind("<Enter>", lambda e: logout_btn.config(bg="#742A2A", fg=WHITE))
        logout_btn.bind("<Leave>", lambda e: logout_btn.config(bg=SIDEBAR_BG, fg=RED))

        # ── Content area ──────────────────────────────────────────────────────
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        self._nav(self._show_home, self._nav_buttons[0])

    # ── Sidebar gradient header ────────────────────────────────────────────────
    def _draw_sidebar_header(self, c):
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        steps = 40
        for i in range(steps):
            r1, g1, b1 = 0x66, 0x7E, 0xEA
            r2, g2, b2 = 0x76, 0x4B, 0xA2
            t = i / steps
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            c.create_rectangle(0, i * h // steps,
                                w, (i + 1) * h // steps,
                                fill=f"#{r:02x}{g:02x}{b:02x}", outline="")
        # Logo circle
        cx, cy, r = w // 2, 54, 30
        c.create_oval(cx - r, cy - r, cx + r, cy + r,
                      fill=WHITE, outline="")
        c.create_text(cx, cy, text="MJS",
                      fill=PURPLE, font=("Segoe UI", 14, "bold"))
        # Name & email
        display = self.name if self.name else "Student"
        c.create_text(cx, cy + r + 16, text=display,
                      fill=WHITE, font=("Segoe UI", 11, "bold"))
        c.create_text(cx, cy + r + 32, text=self.email,
                      fill="#D6BCFA", font=("Segoe UI", 8))

    # ── Navigation ────────────────────────────────────────────────────────────
    def _nav(self, page_fn, btn):
        for b in self._nav_buttons:
            b.config(bg=SIDEBAR_BG, fg=TEXT_LIGHT)
        if btn:
            btn.config(bg=PURPLE, fg=WHITE)
        page_fn()

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    # ── Pages ─────────────────────────────────────────────────────────────────
    def _show_home(self):
        self._clear_content()

        # Top bar
        topbar = tk.Frame(self.content, bg=WHITE, height=64)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Frame(topbar, bg=BORDER, height=1).pack(side="bottom", fill="x")
        tk.Label(topbar, text="Dashboard",
                 bg=WHITE, fg=TEXT_DARK,
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=28, pady=16)

        # Body
        body = tk.Frame(self.content, bg=BG)
        body.pack(fill="both", expand=True, padx=32, pady=28)

        tk.Label(body, text=f"Welcome back, {self.name}! 👋",
                 bg=BG, fg=TEXT_DARK,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(body,
                 text="Here's a summary of your scholarship activity.",
                 bg=BG, fg=TEXT_GRAY,
                 font=("Segoe UI", 11)).pack(anchor="w", pady=(4, 24))

        # Stat cards row
        cards_row = tk.Frame(body, bg=BG)
        cards_row.pack(anchor="w")

        stats = [
            ("📋", "Applications", self._count("applications"), PURPLE),
            ("🔄", "Renewals",     self._count("renewals"),     PURPLE2),
        ]
        for icon, label, value, accent in stats:
            shadow = tk.Frame(cards_row, bg=SHADOW)
            shadow.pack(side="left", padx=(0, 20))
            card = tk.Frame(shadow, bg=WHITE, padx=28, pady=20)
            card.pack(padx=2, pady=2)
            tk.Label(card, text=icon,
                     bg=WHITE, font=("Segoe UI", 22)).pack(anchor="w")
            tk.Label(card, text=str(value),
                     bg=WHITE, fg=accent,
                     font=("Segoe UI", 30, "bold")).pack(anchor="w")
            tk.Label(card, text=label,
                     bg=WHITE, fg=TEXT_GRAY,
                     font=("Segoe UI", 11)).pack(anchor="w")

        # Quick actions
        tk.Label(body, text="Quick Actions",
                 bg=BG, fg=TEXT_DARK,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(32, 12))

        actions_row = tk.Frame(body, bg=BG)
        actions_row.pack(anchor="w")

        quick = [
            ("📋  Apply for Scholarship", self._open_apply),
            ("📁  View My Applications",  self._open_applications),
            ("🔄  Submit Renewal",        self._open_renewal),
        ]
        for text, cmd in quick:
            btn = tk.Button(actions_row, text=text,
                            bg=PURPLE, fg=WHITE,
                            activebackground=PURPLE2, activeforeground=WHITE,
                            relief="flat", bd=0, cursor="hand2",
                            font=("Segoe UI", 10, "bold"),
                            padx=18, pady=10, command=cmd)
            btn.pack(side="left", padx=(0, 12))
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=PURPLE2))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=PURPLE))

    def _count(self, table: str) -> int:
        uid = self.user.get("user_id") or self.user.get("id")
        if not uid:
            return 0
        try:
            from db import fetch_one
            row = fetch_one(
                f"SELECT COUNT(*) AS cnt FROM {table} WHERE user_id = %s", (uid,))
            return row["cnt"] if row else 0
        except Exception:
            return 0

    def _open_apply(self):
        self._clear_content()
        from pages.apply_scholarship import ApplyScholarshipPage
        ApplyScholarshipPage(self.content, self.user)

    def _open_applications(self):
        self._clear_content()
        from pages.my_applications import MyApplicationsPage
        MyApplicationsPage(self.content, self.user)

    def _open_renewal(self):
        self._clear_content()
        from pages.renewal_scholarship import RenewalScholarshipPage
        RenewalScholarshipPage(self.content, self.user)

    def _open_profile(self):
        self._clear_content()
        from pages.student_profile import StudentProfilePage
        StudentProfilePage(self.content, self.user)

    def _logout(self):
        self.app.logout()
