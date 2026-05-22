import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import threading

try:
    from db import fetch_one, fetch_all, execute
except ImportError:
    fetch_one = fetch_all = execute = None

BG           = "#F7FAFC"
WHITE        = "#FFFFFF"
PURPLE       = "#667EEA"
PURPLE2      = "#764BA2"
BORDER       = "#E2E8F0"
DARK         = "#2D3748"
GRAY         = "#718096"
SIDEBAR_DARK = WHITE
SIDEBAR_LINE = BORDER
SIDEBAR_TEXT = DARK
NAV_ACTIVE   = "#6B70D6"
NAV_HOVER    = "#EEF2FF"
GREEN        = "#48BB78"
GREEN2       = "#15803D"
RED          = "#E53935"
RED2         = "#C62828"
CARD_BG      = "#F7F8FC"


class RenewalSettingsFrame(tk.Frame):
    def __init__(self, parent, name="", email="", app=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.name       = name
        self.email      = email
        self.app        = app
        self.is_open    = True
        self.total      = 0
        self.pending    = 0
        self.approved   = 0
        self.rejected   = 0
        self.updated_at = ""
        self._build()
        threading.Thread(target=self._load_data, daemon=True).start()

    # =========================================================================
    # LAYOUT
    # =========================================================================
    def _build(self):
        sidebar = tk.Frame(self, bg=SIDEBAR_DARK, width=238)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        main = tk.Frame(self, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        # Top bar
        topbar = tk.Frame(main, bg=WHITE, height=64)
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

        # Scrollable body
        canvas = tk.Canvas(main, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(main, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        inner = tk.Frame(canvas, bg=BG)
        wid = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _resize(e):
            bbox = canvas.bbox("all")
            if bbox:
                canvas.configure(scrollregion=bbox)
            canvas.itemconfig(wid, width=e.width)

        canvas.bind("<Configure>", _resize)
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

        self._build_body(inner)

    # =========================================================================
    # SIDEBAR
    # =========================================================================
    def _build_sidebar(self, s):
        hdr = tk.Canvas(s, height=170, bg=SIDEBAR_DARK, highlightthickness=0)
        hdr.pack(fill="x")
        hdr.bind("<Configure>", lambda e: self._draw_sidebar_header(hdr))

        tk.Frame(s, bg=SIDEBAR_LINE, height=1).pack(fill="x", padx=18)

        self._nav_btns = {}
        nav_frame = tk.Frame(s, bg=SIDEBAR_DARK)
        nav_frame.pack(fill="x", pady=(10, 0))

        for label, cmd in [
            ("Dashboard",       self._go_dashboard),
            ("Scholar Records", self._go_records),
        ]:
            btn = tk.Button(
                nav_frame, text=f"  {label}", anchor="w",
                bg=SIDEBAR_DARK, fg=SIDEBAR_TEXT,
                activebackground=NAV_HOVER, activeforeground=DARK,
                relief="flat", bd=0,
                font=("Segoe UI", 10),
                padx=18, pady=10, cursor="hand2")
            btn.pack(fill="x", padx=10, pady=3)
            btn.bind("<Enter>",
                     lambda e, b=btn: b.config(bg=NAV_HOVER)
                     if b["bg"] != NAV_ACTIVE else None)
            btn.bind("<Leave>",
                     lambda e, b=btn: b.config(bg=SIDEBAR_DARK)
                     if b["bg"] == NAV_HOVER else None)
            btn.config(command=lambda c=cmd, b=btn: self._nav(c, b))
            self._nav_btns[label] = btn

        tk.Frame(nav_frame, bg=SIDEBAR_LINE, height=1).pack(
            fill="x", padx=10, pady=(8, 8))

        ren_btn = tk.Button(
            nav_frame, text="  Renewal Settings", anchor="w",
            bg=NAV_ACTIVE, fg=WHITE,
            activebackground=NAV_HOVER, activeforeground=DARK,
            relief="flat", bd=0,
            font=("Segoe UI", 10),
            padx=18, pady=10, cursor="hand2")
        ren_btn.pack(fill="x", padx=10, pady=3)
        self._nav_btns["Renewal Settings"] = ren_btn

        tk.Frame(s, bg=SIDEBAR_DARK).pack(fill="both", expand=True)
        tk.Frame(s, bg=SIDEBAR_LINE, height=1).pack(fill="x", padx=18, pady=(12, 6))

        lo = tk.Button(s, text="  Log Out", anchor="w",
                       bg=SIDEBAR_DARK, fg="#E53E3E",
                       activebackground="#742A2A", activeforeground=WHITE,
                       relief="flat", bd=0,
                       font=("Segoe UI", 10),
                       padx=18, pady=10, cursor="hand2",
                       command=self._logout)
        lo.pack(fill="x", padx=10, pady=(0, 14))
        lo.bind("<Enter>", lambda e: lo.config(bg="#742A2A", fg=WHITE))
        lo.bind("<Leave>", lambda e: lo.config(bg=SIDEBAR_DARK, fg="#E53E3E"))

    def _draw_sidebar_header(self, c):
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        steps = 44
        for i in range(steps):
            t = i / steps
            r = int(0x66 + (0x76 - 0x66) * t)
            g = int(0x7E + (0x4B - 0x7E) * t)
            b = int(0xEA + (0xA2 - 0xEA) * t)
            c.create_rectangle(0, i * h // steps, w, (i + 1) * h // steps,
                                fill=f"#{r:02x}{g:02x}{b:02x}", outline="")
        cx, cy, r = w // 2, 58, 30
        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=WHITE, outline="")
        c.create_text(cx, cy, text="MJS", fill=PURPLE,
                      font=("Segoe UI", 14, "bold"))
        c.create_text(cx, cy + r + 18, text=self.name or "Mayor",
                      fill=WHITE, font=("Segoe UI", 11, "bold"))
        c.create_text(cx, cy + r + 35, text="Mayor Panel",
                      fill="#DDE3FF", font=("Segoe UI", 8))

    def _nav(self, page_fn, btn):
        for b in self._nav_btns.values():
            b.config(bg=SIDEBAR_DARK, fg=SIDEBAR_TEXT)
        btn.config(bg=NAV_ACTIVE, fg=WHITE)
        page_fn()

    def _go_dashboard(self):
        if self.app:
            self.app.show_mayor_dashboard()

    def _go_records(self):
        if self.app:
            self.app.show_mayor_records()

    def _logout(self):
        if messagebox.askyesno("Log Out", "Are you sure you want to log out?"):
            if self.app:
                self.app.logout()

    # =========================================================================
    # BODY
    # =========================================================================
    def _build_body(self, parent):
        body = tk.Frame(parent, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=24)

        # ── Hero card ─────────────────────────────────────────────────────────
        hero = tk.Frame(body, bg=WHITE,
                        highlightbackground=BORDER, highlightthickness=1)
        hero.pack(fill="x", pady=(0, 20))

        left_hero = tk.Frame(hero, bg=WHITE)
        left_hero.pack(side="left", fill="both", expand=True, padx=30, pady=28)

        tk.Label(left_hero, text="Manage Renewal Availability",
                 bg=WHITE, fg=PURPLE,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(left_hero,
                 text="Use this page to control whether approved scholars can submit renewal applications.",
                 bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 11),
                 wraplength=520, justify="left").pack(anchor="w", pady=(8, 0))

        # Status panel
        self._status_panel = tk.Frame(hero, bg="#ECFFF3",
                                      highlightbackground=BORDER,
                                      highlightthickness=1)
        self._status_panel.pack(side="right", padx=30, pady=28, ipadx=20, ipady=10)

        tk.Label(self._status_panel, text="Current Status",
                 bg="#ECFFF3", fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(pady=(14, 4))
        self._status_value = tk.Label(self._status_panel, text="OPEN",
                                      bg="#ECFFF3", fg="#16A34A",
                                      font=("Segoe UI", 28, "bold"))
        self._status_value.pack()
        self._status_updated = tk.Label(self._status_panel,
                                        text=f"Updated: {self.updated_at}",
                                        bg="#ECFFF3", fg=GRAY,
                                        font=("Segoe UI", 9))
        self._status_updated.pack(pady=(4, 14))

        # ── Two-column grid ───────────────────────────────────────────────────
        grid = tk.Frame(body, bg=BG)
        grid.pack(fill="both", expand=True)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        # Left card — What This Changes
        left_card = tk.Frame(grid, bg=WHITE,
                             highlightbackground=BORDER, highlightthickness=1)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        tk.Label(left_card, text="What This Changes",
                 bg=WHITE, fg=DARK,
                 font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=24, pady=(22, 6))
        tk.Label(left_card,
                 text="When renewals are open, eligible students can submit updated documents.",
                 bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 10),
                 wraplength=380, justify="left").pack(anchor="w", padx=24)

        for title, text in [
            ("Open Renewals",    "Students can submit renewal forms."),
            ("Closed Renewals",  "Students cannot submit applications."),
            ("Existing Records", "Submitted records remain visible."),
        ]:
            box = tk.Frame(left_card, bg=CARD_BG,
                           highlightbackground=BORDER, highlightthickness=1)
            box.pack(fill="x", padx=24, pady=8)
            tk.Label(box, text=title, bg=CARD_BG, fg=DARK,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 2))
            tk.Label(box, text=text, bg=CARD_BG, fg=GRAY,
                     font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=(0, 12))

        tk.Frame(left_card, bg=BG, height=16).pack()

        # Right card — Control Panel
        right_card = tk.Frame(grid, bg=WHITE,
                              highlightbackground=BORDER, highlightthickness=1)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        tk.Label(right_card, text="Control Panel",
                 bg=WHITE, fg=DARK,
                 font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=24, pady=(22, 6))
        tk.Label(right_card,
                 text="The action takes effect immediately after confirmation.",
                 bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 10)).pack(anchor="w", padx=24)

        self._toggle_btn = tk.Button(
            right_card, text="Close Renewal Window",
            bg=RED, fg=WHITE,
            activebackground=RED2, activeforeground=WHITE,
            relief="flat", bd=0,
            font=("Segoe UI", 12, "bold"),
            padx=20, pady=14, cursor="hand2",
            command=self._toggle_renewal)
        self._toggle_btn.pack(fill="x", padx=24, pady=20)

        # Mini stats
        stats_frame = tk.Frame(right_card, bg=WHITE)
        stats_frame.pack(fill="both", expand=True, padx=16, pady=(0, 20))
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)

        self._stat_labels = []
        for idx, (label, val) in enumerate([
            ("Total",    self.total),
            ("Pending",  self.pending),
            ("Approved", self.approved),
            ("Rejected", self.rejected),
        ]):
            r, c = divmod(idx, 2)
            box = tk.Frame(stats_frame, bg=CARD_BG,
                           highlightbackground=BORDER, highlightthickness=1)
            box.grid(row=r, column=c, sticky="nsew", padx=8, pady=8)
            stats_frame.rowconfigure(r, weight=1)
            num_lbl = tk.Label(box, text=str(val), bg=CARD_BG, fg=PURPLE,
                               font=("Segoe UI", 28, "bold"))
            num_lbl.pack(pady=(18, 4))
            self._stat_labels.append(num_lbl)
            tk.Label(box, text=label.upper(), bg=CARD_BG, fg=GRAY,
                     font=("Segoe UI", 9)).pack(pady=(0, 18))

    # =========================================================================
    # DB LOAD
    # =========================================================================
    def _load_data(self):
        try:
            setting = fetch_one("SELECT is_open, updated_at FROM renewal_settings WHERE id=1") if fetch_one else None
            apps    = fetch_all("SELECT status FROM applications") if fetch_all else []
            renews  = fetch_all("SELECT status FROM renewals")     if fetch_all else []
            all_rows = list(apps or []) + list(renews or [])
            data = {
                "is_open":    bool(setting["is_open"]) if setting else False,
                "updated_at": str(setting["updated_at"]) if setting and setting["updated_at"] else "",
                "total":      len(all_rows),
                "pending":    sum(1 for r in all_rows if str(r.get("status","")).lower() == "pending"),
                "approved":   sum(1 for r in all_rows if str(r.get("status","")).lower() == "approved"),
                "rejected":   sum(1 for r in all_rows if str(r.get("status","")).lower() == "rejected"),
            }
            self.after(0, self._apply_data, data)
        except Exception as e:
            print(f"[RenewalSettings] load error: {e}")

    def _apply_data(self, data):
        self.is_open    = data["is_open"]
        self.total      = data["total"]
        self.pending    = data["pending"]
        self.approved   = data["approved"]
        self.rejected   = data["rejected"]
        self.updated_at = data["updated_at"]
        # refresh stat labels
        for lbl, val in zip(self._stat_labels,
                            [self.total, self.pending, self.approved, self.rejected]):
            lbl.config(text=str(val))
        self._update_ui()

    # =========================================================================
    # TOGGLE
    # =========================================================================
    def _toggle_renewal(self):
        self._toggle_btn.config(state="disabled")
        threading.Thread(target=self._do_toggle, daemon=True).start()

    def _do_toggle(self):
        try:
            new_val = 0 if self.is_open else 1
            if execute:
                execute("UPDATE renewal_settings SET is_open=%s WHERE id=1", (new_val,))
            self.after(0, self._load_data)
            self.after(0, lambda: self._toggle_btn.config(state="normal"))
            self.after(0, lambda: messagebox.showinfo("Success", "Renewal availability updated successfully."))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: self._toggle_btn.config(state="normal"))

    def _update_ui(self):
        if self.is_open:
            panel_bg = "#ECFFF3"
            val_text = "OPEN"
            val_fg   = "#16A34A"
            btn_text = "Close Renewal Window"
            btn_bg   = RED
            btn_hov  = RED2
        else:
            panel_bg = "#FFF1F1"
            val_text = "CLOSED"
            val_fg   = "#DC2626"
            btn_text = "Open Renewal Window"
            btn_bg   = GREEN
            btn_hov  = GREEN2

        self._status_panel.config(bg=panel_bg)
        for w in self._status_panel.winfo_children():
            w.config(bg=panel_bg)
        self._status_value.config(text=val_text, fg=val_fg)
        self._status_updated.config(text=f"Updated: {self.updated_at}")
        self._toggle_btn.config(text=btn_text, bg=btn_bg,
                                activebackground=btn_hov)


# =============================================================================
# STANDALONE
# =============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Renewal Settings — Mayor Panel")
    root.geometry("1280x800")
    try:
        root.state("zoomed")
    except Exception:
        pass
    RenewalSettingsFrame(root, name="Mayor Juan Santos",
                         email="mayor@example.com").pack(fill="both", expand=True)
    root.mainloop()
