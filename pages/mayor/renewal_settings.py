import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

try:
    from db import fetch_one, execute
except ImportError:
    fetch_one = execute = None

try:
    from pages.sidebar import Sidebar
except ImportError:
    from sidebar import Sidebar

# =============================================================================
#  PALETTE
# =============================================================================
BG      = "#F7FAFC"
WHITE   = "#FFFFFF"
PURPLE  = "#667EEA"
BORDER  = "#E2E8F0"
DARK    = "#2D3748"
GRAY    = "#718096"

C_OPEN_BG      = "#F0FFF4"
C_OPEN_BORDER  = "#9AE6B4"
C_OPEN_TEXT    = "#2F855A"
C_CLOSED_BG    = "#FFF5F5"
C_CLOSED_BORDER = "#FEB2B2"
C_CLOSED_TEXT  = "#C53030"

C_BTN_OPEN   = "#48BB78"
C_BTN_CLOSE  = "#F56565"
C_BTN_OPEN_H = "#276749"
C_BTN_CLOSE_H = "#C53030"

C_TITLE   = "#667EEA"
C_ITEM_BG = "#F7FAFC"
C_MINI_BG = "#F7FAFC"

SUCCESS_BG = "#D4EDDA"; SUCCESS_FG = "#155724"; SUCCESS_BR = "#48BB78"
ERROR_BG   = "#F8D7DA"; ERROR_FG   = "#721C24"; ERROR_BR   = "#F56565"

_STATE = {
    "is_open":    False,
    "updated_at": None,
    "counts":     {"total": 0, "pending": 0, "approved": 0, "rejected": 0},
}


class RenewalSettingsFrame(tk.Frame):
    def __init__(self, parent, name="", email="", app=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.name    = name
        self.email   = email
        self.app     = app
        self._is_open = _STATE["is_open"]
        self._updated = _STATE["updated_at"]
        self._counts  = dict(_STATE["counts"])
        self._flash   = None
        self._build()
        self._load_from_db()

    # =========================================================================
    #  LAYOUT
    # =========================================================================
    def _build(self):
        Sidebar(
            self, user_type="mayor", name=self.name,
            active_item="Renewal Settings",
            on_nav=self._on_nav,
            on_logout=self._logout,
        ).pack(side="left", fill="y")

        main = tk.Frame(self, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        self._main_canvas = tk.Canvas(main, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(main, orient="vertical", command=self._main_canvas.yview)
        self._main_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._main_canvas.pack(fill="both", expand=True)

        self._inner = tk.Frame(self._main_canvas, bg=BG)
        wid = self._main_canvas.create_window((0, 0), window=self._inner, anchor="nw")

        def _resize(e):
            bbox = self._main_canvas.bbox("all")
            if bbox:
                self._main_canvas.configure(scrollregion=bbox)
            self._main_canvas.itemconfig(wid, width=e.width)

        self._main_canvas.bind("<Configure>", _resize)

        def _on_mousewheel(e):
            if self._main_canvas.winfo_exists():
                self._main_canvas.yview_scroll(int(-e.delta / 120), "units")
        self._main_canvas.bind("<MouseWheel>", _on_mousewheel)
        self._inner.bind("<MouseWheel>", _on_mousewheel)
        self.bind("<Destroy>", lambda e: self._main_canvas.unbind_all("<MouseWheel>"))

        # Top bar
        topbar = tk.Frame(self._inner, bg=WHITE, height=64)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Frame(topbar, bg=BORDER, height=1).pack(side="bottom", fill="x")
        tk.Label(topbar, text="Renewal Settings",
                 bg=WHITE, fg=DARK,
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=28, pady=16)

        right = tk.Frame(topbar, bg=WHITE)
        right.pack(side="right", fill="y", padx=20)
        tk.Label(right, text="Welcome, ", bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 10)).pack(side="left")
        tk.Label(right, text=self.name or "Mayor", bg=WHITE, fg=DARK,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Label(right, text=" MAYOR ", bg=PURPLE, fg=WHITE,
                 font=("Segoe UI", 9, "bold"),
                 padx=10, pady=3).pack(side="left", padx=(12, 0))

        self._content_area = tk.Frame(self._inner, bg=BG)
        self._content_area.pack(fill="both", expand=True)

        self._render()

    # =========================================================================
    #  NAVIGATION
    # =========================================================================
    def _on_nav(self, label):
        if label == "Dashboard":
            if self.app: self.app.show_mayor_dashboard()
        elif label == "Scholar Records":
            if self.app: self.app.show_mayor_records()
        elif label == "Renewal Settings":
            pass  # already here

    def _logout(self):
        if messagebox.askyesno("Log Out", "Are you sure you want to log out?"):
            if self.app: self.app.logout()

    # =========================================================================
    #  DB LOAD
    # =========================================================================
    def _load_from_db(self):
        if fetch_one is None:
            return
        try:
            setting = fetch_one("SELECT is_open, updated_at FROM renewal_settings WHERE id=1")
            if setting:
                self._is_open = bool(setting.get("is_open", False))
                self._updated = setting.get("updated_at")

            counts_row = fetch_one(
                "SELECT COUNT(*) AS total, "
                "SUM(status='Pending')  AS pending, "
                "SUM(status='Approved') AS approved, "
                "SUM(status='Rejected') AS rejected "
                "FROM renew")
            if counts_row:
                self._counts = {
                    k: int(counts_row.get(k) or 0)
                    for k in ("total", "pending", "approved", "rejected")
                }
            self.after(0, self._render)
        except Exception as e:
            print(f"[RenewalSettings] DB load error: {e}")

    # =========================================================================
    #  RENDER
    # =========================================================================
    def _render(self):
        for w in self._content_area.winfo_children():
            w.destroy()
        self._main_canvas.yview_moveto(0)

        wrap = tk.Frame(self._content_area, bg=BG)
        wrap.pack(fill="both", expand=True, padx=28, pady=(20, 32))

        if self._flash:
            self._build_flash(wrap, *self._flash)
            self._flash = None

        self._build_hero(wrap)
        self._build_content_grid(wrap)

    def _build_flash(self, parent, kind, msg):
        bg = SUCCESS_BG if kind == "success" else ERROR_BG
        fg = SUCCESS_FG if kind == "success" else ERROR_FG
        br = SUCCESS_BR if kind == "success" else ERROR_BR
        row = tk.Frame(parent, bg=bg, highlightbackground=br, highlightthickness=1)
        row.pack(fill="x", pady=(0, 18))
        tk.Frame(row, bg=br, width=4).pack(side="left", fill="y")
        tk.Label(row, text=msg, bg=bg, fg=fg,
                 font=("Segoe UI", 10, "bold"),
                 anchor="w", padx=14, pady=10).pack(side="left")

    def _build_hero(self, parent):
        hero = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        hero.pack(fill="x", pady=(0, 22))
        inner = tk.Frame(hero, bg=WHITE)
        inner.pack(fill="both", padx=28, pady=28)

        left = tk.Frame(inner, bg=WHITE)
        left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="Renewal Settings",
                 bg=WHITE, fg=C_TITLE,
                 font=("Segoe UI", 22, "bold"), anchor="w").pack(fill="x", pady=(0, 8))
        tk.Label(left,
                 text="Use this page to control whether approved scholars can submit renewal applications.",
                 bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 11), anchor="w",
                 wraplength=540, justify="left").pack(fill="x")

        sp_bg  = C_OPEN_BG     if self._is_open else C_CLOSED_BG
        sp_brd = C_OPEN_BORDER if self._is_open else C_CLOSED_BORDER
        sp_fg  = C_OPEN_TEXT   if self._is_open else C_CLOSED_TEXT

        sp = tk.Frame(inner, bg=sp_bg,
                      highlightbackground=sp_brd, highlightthickness=1,
                      padx=24, pady=18)
        sp.pack(side="right", padx=(28, 0))
        tk.Label(sp, text="CURRENT STATUS", bg=sp_bg, fg=GRAY,
                 font=("Segoe UI", 9, "bold")).pack()
        tk.Label(sp, text="Open" if self._is_open else "Closed",
                 bg=sp_bg, fg=sp_fg,
                 font=("Segoe UI", 26, "bold")).pack(pady=(6, 0))
        note = f"Updated: {self._updated}" if self._updated else "Default setting"
        tk.Label(sp, text=note, bg=sp_bg, fg=GRAY,
                 font=("Segoe UI", 9)).pack(pady=(6, 0))

    def _build_content_grid(self, parent):
        grid = tk.Frame(parent, bg=BG)
        grid.pack(fill="both", expand=True)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, minsize=340, weight=0)
        self._build_what_card(grid)
        self._build_control_card(grid)

    def _build_what_card(self, grid):
        card = tk.Frame(grid, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 11))
        inner = tk.Frame(card, bg=WHITE)
        inner.pack(fill="both", padx=24, pady=24)

        tk.Label(inner, text="What This Changes",
                 bg=WHITE, fg=DARK,
                 font=("Segoe UI", 14, "bold"), anchor="w").pack(fill="x")
        tk.Label(inner,
                 text=("When renewals are open, eligible students with approved "
                       "applications can access the renewal form. When closed, "
                       "the form stays unavailable and students are asked to check back later."),
                 bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 10), wraplength=500,
                 justify="left", anchor="w").pack(fill="x", pady=(8, 18))

        for title, desc in [
            ("Open renewals",    "Students can submit updated documents and renewal details."),
            ("Closed renewals",  "Students cannot start a new renewal until the window is reopened."),
            ("Existing records", "Submitted renewals remain visible in scholar records either way."),
        ]:
            item = tk.Frame(inner, bg=C_ITEM_BG, highlightbackground=BORDER, highlightthickness=1)
            item.pack(fill="x", pady=(0, 10))
            tk.Label(item, text=title, bg=C_ITEM_BG, fg=DARK,
                     font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x", padx=14, pady=(10, 2))
            tk.Label(item, text=desc, bg=C_ITEM_BG, fg=GRAY,
                     font=("Segoe UI", 10), anchor="w",
                     wraplength=460, justify="left").pack(fill="x", padx=14, pady=(0, 10))

    def _build_control_card(self, grid):
        card = tk.Frame(grid, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        card.grid(row=0, column=1, sticky="nsew", padx=(11, 0))
        inner = tk.Frame(card, bg=WHITE)
        inner.pack(fill="both", padx=24, pady=24)

        tk.Label(inner, text="Control Panel",
                 bg=WHITE, fg=DARK,
                 font=("Segoe UI", 14, "bold"), anchor="w").pack(fill="x")
        tk.Label(inner, text="The action takes effect immediately after confirmation.",
                 bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 10), anchor="w",
                 wraplength=280, justify="left").pack(fill="x", pady=(8, 16))

        btn_bg   = C_BTN_CLOSE   if self._is_open else C_BTN_OPEN
        btn_h    = C_BTN_CLOSE_H if self._is_open else C_BTN_OPEN_H
        btn_text = "🔒  Close Renewal Window" if self._is_open else "🔓  Open Renewal Window"

        toggle = tk.Button(inner, text=btn_text,
                           bg=btn_bg, fg=WHITE,
                           font=("Segoe UI", 11, "bold"),
                           relief="flat", bd=0,
                           activebackground=btn_h, activeforeground=WHITE,
                           cursor="hand2", pady=12,
                           command=self._toggle)
        toggle.pack(fill="x", pady=(0, 20))
        toggle.bind("<Enter>", lambda e: toggle.config(bg=btn_h))
        toggle.bind("<Leave>", lambda e: toggle.config(bg=btn_bg))

        stats = tk.Frame(inner, bg=WHITE)
        stats.pack(fill="x")
        stats.columnconfigure(0, weight=1)
        stats.columnconfigure(1, weight=1)

        for (key, label), (row, col) in zip(
            [("total", "Total"), ("pending", "Pending"),
             ("approved", "Approved"), ("rejected", "Rejected")],
            [(0, 0), (0, 1), (1, 0), (1, 1)]
        ):
            cell = tk.Frame(stats, bg=C_MINI_BG, highlightbackground=BORDER, highlightthickness=1)
            cell.grid(row=row, column=col, sticky="nsew",
                      padx=(0 if col == 0 else 6, 0),
                      pady=(0 if row == 0 else 6, 0),
                      ipadx=10, ipady=8)
            tk.Label(cell, text=str(self._counts.get(key, 0)),
                     bg=C_MINI_BG, fg=DARK,
                     font=("Segoe UI", 20, "bold")).pack(pady=(10, 2))
            tk.Label(cell, text=label.upper(),
                     bg=C_MINI_BG, fg=GRAY,
                     font=("Segoe UI", 8, "bold")).pack(pady=(0, 8))

    # =========================================================================
    #  TOGGLE
    # =========================================================================
    def _toggle(self):
        new_status = not self._is_open
        if execute is not None:
            try:
                execute(
                    "INSERT INTO renewal_settings (id, is_open) VALUES (1, %s) "
                    "ON DUPLICATE KEY UPDATE is_open = NOT is_open",
                    (new_status,))
            except Exception as e:
                print(f"[RenewalSettings] DB toggle error: {e}")

        self._is_open = new_status
        self._updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _STATE["is_open"]    = new_status
        _STATE["updated_at"] = self._updated

        state_text = "OPEN ✅" if new_status else "CLOSED 🔒"
        self._flash = ("success", f"Renewal window is now {state_text}")
        self._render()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Renewal Settings — test")
    root.geometry("1100x760")
    try: root.state("zoomed")
    except Exception: pass
    RenewalSettingsFrame(root, name="Mayor Juan Santos",
                         email="mayor@example.com").pack(fill="both", expand=True)
    root.mainloop()
