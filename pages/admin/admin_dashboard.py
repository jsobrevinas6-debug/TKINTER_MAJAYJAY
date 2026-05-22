import tkinter as tk
import threading

try:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    from logo import get_logo
except Exception:
    get_logo = lambda size=60: None

BG = "#F7FAFC"
WHITE = "#FFFFFF"
PURPLE = "#667EEA"
PURPLE2 = "#764BA2"
BORDER = "#E2E8F0"
DARK = "#2D3748"
GRAY = "#718096"
SHADOW = "#CBD5E0"
GREEN = "#48BB78"
ORANGE = "#ED8936"
RED = "#F56565"
SIDEBAR_DARK = WHITE
SIDEBAR_LINE = BORDER
SIDEBAR_TEXT = DARK
NAV_ACTIVE = "#6B70D6"
NAV_HOVER = "#EEF2FF"

ADMIN_NAME = "Admin User"
ADMIN_EMAIL = "admin@example.com"


class AdminDashboard(tk.Frame):
    def __init__(self, parent, name="", email="", app=None, **_):
        super().__init__(parent, bg=BG)
        self.app = app
        self._name = name or ADMIN_NAME
        self._email = email or ADMIN_EMAIL
        self._users = []
        self._build()
        threading.Thread(target=self._do_load, daemon=True).start()

    def _build(self):
        sidebar = tk.Frame(self, bg=SIDEBAR_DARK, width=238)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        self._show_dashboard()

    def _build_sidebar(self, sidebar):
        header = tk.Canvas(sidebar, height=170, bg=SIDEBAR_DARK, highlightthickness=0)
        header.pack(fill="x")
        header.bind("<Configure>", lambda _event: self._draw_header(header))

        tk.Frame(sidebar, bg=SIDEBAR_LINE, height=1).pack(fill="x", padx=18)

        nav_items = [
            ("Dashboard", self._show_dashboard),
            ("Add Admin / Mayor", self._show_add_admin),
        ]

        self._nav_btns = {}
        nav_frame = tk.Frame(sidebar, bg=SIDEBAR_DARK)
        nav_frame.pack(fill="x", pady=(10, 0))

        for label, command in nav_items:
            btn = tk.Button(
                nav_frame,
                text=f"  {label}",
                anchor="w",
                bg=SIDEBAR_DARK,
                fg=SIDEBAR_TEXT,
                activebackground=NAV_HOVER,
                activeforeground=DARK,
                relief="flat",
                bd=0,
                font=("Segoe UI", 10),
                padx=18,
                pady=10,
                cursor="hand2",
            )
            btn.pack(fill="x", padx=10, pady=3)
            btn.bind(
                "<Enter>",
                lambda _event, b=btn: b.config(bg=NAV_HOVER)
                if b["bg"] != NAV_ACTIVE else None,
            )
            btn.bind(
                "<Leave>",
                lambda _event, b=btn: b.config(bg=SIDEBAR_DARK)
                if b["bg"] == NAV_HOVER else None,
            )
            btn.config(command=lambda c=command, b=btn: self._nav(c, b))
            self._nav_btns[label] = btn

        tk.Frame(sidebar, bg=SIDEBAR_DARK).pack(fill="both", expand=True)
        tk.Frame(sidebar, bg=SIDEBAR_LINE, height=1).pack(
            fill="x", padx=18, pady=(12, 6)
        )

        logout_btn = tk.Button(
            sidebar,
            text="  Log Out",
            anchor="w",
            bg=SIDEBAR_DARK,
            fg="#E53E3E",
            activebackground="#742A2A",
            activeforeground=WHITE,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10),
            padx=18,
            pady=10,
            cursor="hand2",
            command=self._logout,
        )
        logout_btn.pack(fill="x", padx=10, pady=(0, 14))
        logout_btn.bind("<Enter>", lambda _event: logout_btn.config(bg="#742A2A"))
        logout_btn.bind(
            "<Leave>",
            lambda _event: logout_btn.config(bg=SIDEBAR_DARK, fg="#E53E3E"),
        )

    def _draw_header(self, canvas):
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        steps = 44

        for i in range(steps):
            r1, g1, b1 = 0x66, 0x7E, 0xEA
            r2, g2, b2 = 0x76, 0x4B, 0xA2
            t = i / steps
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            canvas.create_rectangle(
                0, i * height // steps, width, (i + 1) * height // steps,
                fill=f"#{r:02x}{g:02x}{b:02x}", outline="",
            )

        cx, cy, radius = width // 2, 58, 30
        logo = get_logo(radius * 2)
        if logo:
            if not hasattr(self, "_logo_photo"):
                self._logo_photo = logo
            canvas.create_image(cx, cy, image=self._logo_photo)
        else:
            canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                fill=WHITE, outline="",
            )
            canvas.create_text(
                cx, cy, text="MJS", fill=PURPLE, font=("Segoe UI", 14, "bold")
            )
        canvas.create_text(
            cx, cy + radius + 18, text=self._name,
            fill=WHITE, font=("Segoe UI", 11, "bold"),
        )
        canvas.create_text(
            cx, cy + radius + 35, text="Admin Panel",
            fill="#DDE3FF", font=("Segoe UI", 8),
        )

    def _nav(self, page_fn, btn):
        self._set_active_nav(btn)
        page_fn()

    def _set_active_nav(self, active_btn):
        for btn in self._nav_btns.values():
            btn.config(bg=SIDEBAR_DARK, fg=SIDEBAR_TEXT)
        active_btn.config(bg=NAV_ACTIVE, fg=WHITE)

    def _set_active_by_text(self, text):
        for label, btn in self._nav_btns.items():
            if text in label:
                btn.config(bg=NAV_ACTIVE, fg=WHITE)
            else:
                btn.config(bg=SIDEBAR_DARK, fg=SIDEBAR_TEXT)

    def _clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def _show_dashboard(self):
        self._clear_content()
        self._set_active_by_text("Dashboard")

        topbar = tk.Frame(self.content, bg=WHITE, height=64)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Frame(topbar, bg=BORDER, height=1).pack(side="bottom", fill="x")
        tk.Label(
            topbar,
            text="Dashboard",
            bg=WHITE,
            fg=DARK,
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left", padx=28, pady=16)

        body = tk.Frame(self.content, bg=BG)
        body.pack(fill="both", expand=True, padx=32, pady=24)

        tk.Label(
            body,
            text=f"Welcome back, {self._name}!",
            bg=BG,
            fg=DARK,
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w")
        tk.Label(
            body,
            text="System overview and registered user statistics.",
            bg=BG,
            fg=GRAY,
            font=("Segoe UI", 11),
        ).pack(anchor="w", pady=(4, 24))

        total = len(self._users)
        mayors = sum(1 for u in self._users if u["role"] == "mayor")
        students = sum(1 for u in self._users if u["role"] == "student")
        admins = sum(1 for u in self._users if u["role"] == "admin")

        cards_row = tk.Frame(body, bg=BG)
        cards_row.pack(anchor="w")

        for label, value, accent in [
            ("Total Users", total, PURPLE),
            ("Students", students, GREEN),
            ("Mayors", mayors, ORANGE),
            ("Admins", admins, RED),
        ]:
            shadow = tk.Frame(cards_row, bg=SHADOW)
            shadow.pack(side="left", padx=(0, 20))
            card = tk.Frame(shadow, bg=WHITE, padx=28, pady=20)
            card.pack(padx=2, pady=2)
            tk.Label(
                card,
                text=str(value),
                bg=WHITE,
                fg=accent,
                font=("Segoe UI", 30, "bold"),
            ).pack(anchor="w")
            tk.Label(
                card, text=label, bg=WHITE, fg=GRAY, font=("Segoe UI", 11)
            ).pack(anchor="w")

        tk.Label(
            body,
            text="Quick Actions",
            bg=BG,
            fg=DARK,
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(32, 12))

        btn = tk.Button(
            body,
            text="Add Admin / Mayor",
            bg=PURPLE,
            fg=WHITE,
            activebackground=PURPLE2,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10, "bold"),
            padx=18,
            pady=10,
            cursor="hand2",
            command=lambda: self._nav(
                self._show_add_admin, self._nav_btns["Add Admin / Mayor"]
            ),
        )
        btn.pack(side="left")
        btn.bind("<Enter>", lambda _event: btn.config(bg=PURPLE2))
        btn.bind("<Leave>", lambda _event: btn.config(bg=PURPLE))

    def _show_add_admin(self):
        self._clear_content()
        self._set_active_by_text("Add")
        from pages.admin.add_admin import AddAdminPage

        AddAdminPage(
            self.content,
            app=self.app,
            on_success=lambda: threading.Thread(
                target=self._do_load, daemon=True
            ).start(),
        )

    def _do_load(self):
        try:
            from db import fetch_all

            rows = fetch_all(
                "SELECT user_id, first_name, middle_name, last_name, "
                "email, user_type FROM users ORDER BY user_id ASC"
            )
            users = [
                {
                    "id": r["user_id"],
                    "firstName": r.get("first_name", "") or "",
                    "middleName": r.get("middle_name", "") or "",
                    "lastName": r.get("last_name", "") or "",
                    "email": r.get("email", ""),
                    "role": r.get("user_type", "student"),
                }
                for r in (rows or [])
            ]
            self.after(0, self._on_loaded, users)
        except Exception as exc:
            print(f"[Admin] load error: {exc}")

    def _on_loaded(self, users):
        self._users = users
        if self.content.winfo_exists():
            self._show_dashboard()

    def _logout(self):
        if self.app:
            self.app.logout()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Admin Dashboard")
    root.state("zoomed")
    AdminDashboard(root).pack(fill="both", expand=True)
    root.mainloop()
