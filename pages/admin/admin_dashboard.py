import tkinter as tk
from tkinter import ttk, messagebox
import threading
import math

try:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    from logo import get_logo
except Exception:
    get_logo = lambda size=60: None

try:
    from pages.sidebar import Sidebar
except ImportError:
    from sidebar import Sidebar

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


ROWS_PER_PAGE = 12


class AdminDashboard(tk.Frame):
    def __init__(self, parent, name="", email="", app=None, **_):
        super().__init__(parent, bg=BG)
        self.app    = app
        self._name  = name or ADMIN_NAME
        self._email = email or ADMIN_EMAIL
        self._users = []
        # table state
        self._search_var   = None
        self._sort_col     = None
        self._sort_asc     = True
        self._current_page = 1
        self._build()
        threading.Thread(target=self._do_load, daemon=True).start()

    def _build(self):
        Sidebar(
            self, user_type="admin", name=self._name,
            active_item="Dashboard",
            on_nav=self._on_nav,
            on_logout=self._logout,
        ).pack(side="left", fill="y")

        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)
        self._show_dashboard()

    def _on_nav(self, label):
        if label == "Dashboard":
            self._show_dashboard()
        elif label == "Add Admin":
            self._show_add_admin()
        elif label == "Profile Settings":
            self._show_profile_settings()

    def _clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def _show_dashboard(self):
        self._clear_content()
        self._current_page = 1

        # ── Top bar ───────────────────────────────────────────────────────────
        topbar = tk.Frame(self.content, bg=WHITE, height=64)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Frame(topbar, bg=BORDER, height=1).pack(side="bottom", fill="x")
        tk.Label(topbar, text="Dashboard",
                 bg=WHITE, fg=DARK,
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=28, pady=16)

        body = tk.Frame(self.content, bg=BG)
        body.pack(fill="both", expand=True, padx=32, pady=24)
        body.rowconfigure(7, weight=1)
        body.columnconfigure(0, weight=1)

        tk.Label(body, text=f"Welcome back, {self._name}!",
                 bg=BG, fg=DARK,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(body, text="System overview and registered user statistics.",
                 bg=BG, fg=GRAY,
                 font=("Segoe UI", 11)).pack(anchor="w", pady=(4, 24))

        # ── Stat cards ────────────────────────────────────────────────────────
        total    = len(self._users)
        students = sum(1 for u in self._users if u["role"] == "student")
        mayors   = sum(1 for u in self._users if u["role"] == "mayor")
        admins   = sum(1 for u in self._users if u["role"] == "admin")

        cards_row = tk.Frame(body, bg=BG)
        cards_row.pack(anchor="w", pady=(0, 28))
        for label, value, accent in [
            ("Total Users", total,    PURPLE),
            ("Students",    students, GREEN),
            ("Mayors",      mayors,   ORANGE),
            ("Admins",      admins,   RED),
        ]:
            shadow = tk.Frame(cards_row, bg=SHADOW)
            shadow.pack(side="left", padx=(0, 20))
            card = tk.Frame(shadow, bg=WHITE, padx=28, pady=20)
            card.pack(padx=2, pady=2)
            tk.Label(card, text=str(value), bg=WHITE, fg=accent,
                     font=("Segoe UI", 30, "bold")).pack(anchor="w")
            tk.Label(card, text=label, bg=WHITE, fg=GRAY,
                     font=("Segoe UI", 11)).pack(anchor="w")

        # ── Users table ───────────────────────────────────────────────────────
        tk.Label(body, text="Registered Users",
                 bg=BG, fg=DARK,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 10))

        card = tk.Frame(body, bg=WHITE,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True)
        card.pack_propagate(False)
        inner = tk.Frame(card, bg=WHITE)
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        # Search
        hdr = tk.Frame(inner, bg=WHITE)
        hdr.pack(fill="x", pady=(0, 10))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())
        sw = tk.Frame(hdr, bg=WHITE,
                      highlightbackground=BORDER, highlightthickness=1)
        sw.pack(side="right")
        tk.Label(sw, text="🔍", bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 10)).pack(side="left", padx=(8, 0))
        tk.Entry(sw, textvariable=self._search_var,
                 bg=WHITE, fg=DARK, relief="flat",
                 font=("Segoe UI", 10), width=24,
                 insertbackground=DARK).pack(side="left", ipady=6, padx=8)

        # Treeview
        self._build_user_table(inner)

        # Pagination
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=(8, 0))
        self._pag_frame = tk.Frame(inner, bg=WHITE)
        self._pag_frame.pack(fill="x", pady=(8, 0))

        self._refresh_table()

    def _build_user_table(self, parent):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Admin.Treeview",
                        background=WHITE, foreground=DARK,
                        rowheight=36, fieldbackground=WHITE,
                        font=("Segoe UI", 10), borderwidth=0, relief="flat")
        style.configure("Admin.Treeview.Heading",
                        background="#F8FAFC", foreground="#64748B",
                        font=("Segoe UI", 9, "bold"),
                        relief="flat", borderwidth=0)
        style.map("Admin.Treeview",
                  background=[("selected", "#EEF0FF")],
                  foreground=[("selected", DARK)])
        style.map("Admin.Treeview.Heading",
                  background=[("active", "#F8FAFC")])
        style.layout("Admin.Treeview",
                     [("Treeview.treearea", {"sticky": "nswe"})])

        cols   = ("user_id", "first_name", "middle_name", "last_name", "email", "role")
        labels = ("ID", "First Name", "Middle Name", "Last Name", "Email", "Role")
        widths = (55, 130, 120, 130, 220, 90)

        wrap = tk.Frame(parent, bg=WHITE)
        wrap.pack(fill="both", expand=True)

        xbar = ttk.Scrollbar(wrap, orient="horizontal")
        xbar.pack(side="bottom", fill="x")

        self._tree = ttk.Treeview(wrap, columns=cols, show="headings",
                                  style="Admin.Treeview",
                                  xscrollcommand=xbar.set,
                                  selectmode="browse")
        xbar.config(command=self._tree.xview)
        self._tree.pack(fill="both", expand=True)

        for col, lbl, w in zip(cols, labels, widths):
            self._tree.heading(col, text=lbl,
                               command=lambda c=col: self._on_sort(c))
            self._tree.column(col, width=w, minwidth=50, anchor="w")

        self._tree.tag_configure("even", background=WHITE)
        self._tree.tag_configure("odd",  background="#F8FAFC")

    # ── Table helpers ─────────────────────────────────────────────────────────
    def _filtered_users(self):
        q = (self._search_var.get().strip().lower()
             if self._search_var else "")
        rows = self._users
        if q:
            rows = [u for u in rows
                    if q in " ".join(str(v) for v in u.values()).lower()]
        if self._sort_col:
            rows = sorted(rows,
                          key=lambda u: str(u.get(self._sort_col, "")).lower(),
                          reverse=not self._sort_asc)
        return rows

    @property
    def _total_pages(self):
        return max(1, math.ceil(len(self._filtered_users()) / ROWS_PER_PAGE))

    def _refresh_table(self):
        if not hasattr(self, "_tree") or not self._tree.winfo_exists():
            return
        for iid in self._tree.get_children():
            self._tree.delete(iid)

        rows  = self._filtered_users()
        start = (self._current_page - 1) * ROWS_PER_PAGE
        page  = rows[start: start + ROWS_PER_PAGE]

        for i, u in enumerate(page):
            tag = "even" if i % 2 == 0 else "odd"
            self._tree.insert("", "end", tags=(tag,), values=(
                u.get("id", ""),
                u.get("firstName", ""),
                u.get("middleName", ""),
                u.get("lastName", ""),
                u.get("email", ""),
                u.get("role", "").capitalize(),
            ))

        # Sort arrows
        col_map = {
            "user_id": "id", "first_name": "firstName",
            "middle_name": "middleName", "last_name": "lastName",
            "email": "email", "role": "role"
        }
        for col in ("user_id", "first_name", "middle_name",
                    "last_name", "email", "role"):
            base = self._tree.heading(col)["text"].rstrip(" ▲▼")
            arrow = (" ▲" if self._sort_asc else " ▼") \
                    if self._sort_col == col_map.get(col) else ""
            self._tree.heading(col, text=base + arrow)

        self._build_pagination(rows)

    def _build_pagination(self, rows):
        if not hasattr(self, "_pag_frame") or not self._pag_frame.winfo_exists():
            return
        for w in self._pag_frame.winfo_children():
            w.destroy()

        total = len(rows)
        cp    = self._current_page
        start = (cp - 1) * ROWS_PER_PAGE + 1 if total else 0
        end   = min(cp * ROWS_PER_PAGE, total)
        tp    = self._total_pages

        tk.Label(self._pag_frame,
                 text=f"Showing {start} to {end} of {total} entries",
                 bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 9)).pack(side="left")

        nav = tk.Frame(self._pag_frame, bg=WHITE)
        nav.pack(side="right")

        def _nbtn(text, cmd, disabled=False):
            fg = "#BBBBBB" if disabled else PURPLE
            b  = tk.Label(nav, text=text, bg=WHITE, fg=fg,
                          font=("Segoe UI", 9, "bold"),
                          padx=9, pady=4, relief="solid", bd=1,
                          cursor="" if disabled else "hand2")
            b.pack(side="left", padx=2)
            if not disabled:
                b.bind("<Button-1>", lambda e: cmd())

        _nbtn("Previous", lambda: self._go_page(cp - 1), cp <= 1)
        for p in range(max(1, cp - 2), min(tp + 1, cp + 3)):
            bg = PURPLE if p == cp else WHITE
            fg = WHITE  if p == cp else PURPLE
            b  = tk.Label(nav, text=str(p), bg=bg, fg=fg,
                          font=("Segoe UI", 9, "bold"),
                          width=3, padx=4, pady=4,
                          relief="solid", bd=1, cursor="hand2")
            b.pack(side="left", padx=2)
            if p != cp:
                b.bind("<Button-1>", lambda e, pg=p: self._go_page(pg))
        _nbtn("Next", lambda: self._go_page(cp + 1), cp >= tp)

    def _on_search(self):
        self._current_page = 1
        self._refresh_table()

    def _on_sort(self, col):
        key_map = {
            "user_id": "id", "first_name": "firstName",
            "middle_name": "middleName", "last_name": "lastName",
            "email": "email", "role": "role"
        }
        key = key_map.get(col, col)
        if self._sort_col == key:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = key
            self._sort_asc = True
        self._current_page = 1
        self._refresh_table()

    def _go_page(self, page):
        self._current_page = max(1, min(page, self._total_pages))
        self._refresh_table()

    def _show_profile_settings(self):
        if self.app:
            self.app.show_profile_settings()

    def _show_add_admin(self):
        self._clear_content()
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
        self._current_page = 1
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
