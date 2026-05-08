import tkinter as tk
from tkinter import messagebox
import threading

try:
    from db import fetch_one, fetch_all, execute
except ImportError:
    fetch_one = fetch_all = execute = None

# ── Palette ────────────────────────────────────────────────────────────────────
BG       = "#F5F5F5"
WHITE    = "#FFFFFF"
BLUE     = "#1565C0"
BLUE_L   = "#E3F2FD"
GREEN    = "#2E7D32"
GREEN_L  = "#E8F5E9"
ORANGE   = "#E65100"
ORANGE_L = "#FFF3E0"
RED      = "#C62828"
RED_L    = "#FFEBEE"
SIDEBAR  = "#1A237E"
BORDER   = "#E0E0E0"
TEXT     = "#212121"
GRAY     = "#757575"


class MayorDashboard(tk.Frame):
    def __init__(self, parent, name, email, app, **_):
        super().__init__(parent, bg=BG)
        self.name  = name
        self.email = email
        self.app   = app

        self._stats       = {}
        self._renewal_open = False
        self._loading     = True

        self._build()
        threading.Thread(target=self._load_all, daemon=True).start()

    # ── Build ──────────────────────────────────────────────────────────────────
    def _build(self):
        # Sidebar
        sidebar = tk.Frame(self, bg=SIDEBAR, width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        # Main content
        main = tk.Frame(self, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        canvas = tk.Canvas(main, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(main, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        self._inner = tk.Frame(canvas, bg=BG)
        wid = canvas.create_window((0, 0), window=self._inner, anchor="nw")

        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(wid, width=e.width)
        canvas.bind("<Configure>", _resize)
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._build_content()

    def _build_sidebar(self, s):
        tk.Label(s, text="🏛", bg=SIDEBAR, fg=WHITE,
                 font=("Helvetica", 28)).pack(pady=(24, 4))
        tk.Label(s, text="Mayor Panel",
                 bg=SIDEBAR, fg=WHITE,
                 font=("Helvetica", 11, "bold")).pack()
        tk.Label(s, text=self.name,
                 bg=SIDEBAR, fg="#9FA8DA",
                 font=("Helvetica", 9)).pack(pady=(2, 20))

        tk.Frame(s, bg="#3949AB", height=1).pack(fill="x", padx=12)

        nav = [
            ("🏠  Dashboard",       lambda: None),
            ("⏳  Pending Scholars", self._open_pending),
            ("📋  Scholar Records",  self._open_records),
        ]
        self._nav_btns = {}
        for label, cmd in nav:
            btn = tk.Button(s, text=label, anchor="w",
                            bg=SIDEBAR, fg=WHITE,
                            activebackground="#283593",
                            relief="flat", bd=0,
                            font=("Helvetica", 10),
                            padx=16, pady=10,
                            cursor="hand2", command=cmd)
            btn.pack(fill="x")
            self._nav_btns[label] = btn

        self._nav_btns["🏠  Dashboard"].config(bg="#283593")

        tk.Frame(s, bg=SIDEBAR).pack(fill="both", expand=True)
        tk.Frame(s, bg="#3949AB", height=1).pack(fill="x", padx=12)
        tk.Button(s, text="🚪  Logout", anchor="w",
                  bg=SIDEBAR, fg="#EF9A9A",
                  relief="flat", bd=0,
                  font=("Helvetica", 10),
                  padx=16, pady=10,
                  cursor="hand2",
                  command=self._logout).pack(fill="x", pady=(0, 12))

    def _build_content(self):
        p = self._inner
        pad = tk.Frame(p, bg=BG)
        pad.pack(fill="both", padx=28, pady=20)

        # Welcome banner
        banner = tk.Frame(pad, bg=WHITE,
                          highlightbackground=BORDER, highlightthickness=1)
        banner.pack(fill="x", pady=(0, 20))
        tk.Label(banner,
                 text=f"Welcome, {self.name}! 🏛",
                 bg=WHITE, fg=BLUE,
                 font=("Helvetica", 20, "bold"),
                 anchor="w", padx=24, pady=14).pack(fill="x")
        tk.Label(banner,
                 text="Overview of scholarship applications and renewals",
                 bg=WHITE, fg=GRAY,
                 font=("Helvetica", 11),
                 anchor="w", padx=24, pady=(0, 16)).pack(fill="x")

        # ── New Applications ───────────────────────────────────────────────────
        self._section_title(pad, "🆕 New Scholarship Applications")
        new_row = tk.Frame(pad, bg=BG)
        new_row.pack(fill="x", pady=(0, 20))
        self._stat_cards = {}
        for key, label, color in [
            ("total_new",    "TOTAL NEW",  BLUE),
            ("approved_new", "APPROVED",   GREEN),
            ("pending_new",  "PENDING",    ORANGE),
            ("rejected_new", "REJECTED",   RED),
        ]:
            card = self._stat_card(new_row, "—", label, color)
            card.pack(side="left", fill="both", expand=True, padx=6)
            self._stat_cards[key] = card

        # ── Renewal Toggle ─────────────────────────────────────────────────────
        renewal_hdr = tk.Frame(pad, bg=BG)
        renewal_hdr.pack(fill="x", pady=(0, 8))
        self._section_title(renewal_hdr, "🔄 Scholarship Renewals", pack=False).pack(side="left")

        # Status badge
        self._renewal_badge = tk.Label(renewal_hdr,
                                       text="● CLOSED",
                                       bg=BG, fg=RED,
                                       font=("Helvetica", 10, "bold"))
        self._renewal_badge.pack(side="left", padx=12)

        self._toggle_btn = tk.Button(renewal_hdr,
                                     text="🔓 Open Renewal",
                                     bg=GREEN, fg=WHITE,
                                     relief="flat", bd=0,
                                     font=("Helvetica", 10, "bold"),
                                     padx=14, pady=6,
                                     cursor="hand2",
                                     command=self._toggle_renewal)
        self._toggle_btn.pack(side="right")

        renew_row = tk.Frame(pad, bg=BG)
        renew_row.pack(fill="x", pady=(0, 20))
        for key, label, color in [
            ("total_renew",    "TOTAL RENEWALS", BLUE),
            ("approved_renew", "APPROVED",       GREEN),
            ("pending_renew",  "PENDING",        ORANGE),
            ("rejected_renew", "REJECTED",       RED),
        ]:
            card = self._stat_card(renew_row, "—", label, color)
            card.pack(side="left", fill="both", expand=True, padx=6)
            self._stat_cards[key] = card

        # ── Overall Summary ────────────────────────────────────────────────────
        summary_card = tk.Frame(pad, bg=WHITE,
                                highlightbackground=BORDER, highlightthickness=1)
        summary_card.pack(fill="x", pady=(0, 20))
        tk.Frame(summary_card, bg=BLUE, width=4).pack(side="left", fill="y")
        summary_inner = tk.Frame(summary_card, bg=WHITE)
        summary_inner.pack(fill="both", padx=20, pady=16)
        tk.Label(summary_inner, text="📊 Overall Summary",
                 bg=WHITE, fg=BLUE,
                 font=("Helvetica", 14, "bold")).pack(anchor="w", pady=(0, 12))

        sum_row = tk.Frame(summary_inner, bg=WHITE)
        sum_row.pack(fill="x")
        self._summary_cards = {}
        for key, label in [
            ("total_all",    "TOTAL APPLICATIONS"),
            ("approved_all", "TOTAL APPROVED"),
            ("pending_all",  "TOTAL PENDING"),
            ("rejected_all", "TOTAL REJECTED"),
        ]:
            card = self._summary_card(sum_row, "—", label)
            card.pack(side="left", fill="both", expand=True, padx=6)
            self._summary_cards[key] = card

        # Quick action buttons
        btn_row = tk.Frame(pad, bg=BG)
        btn_row.pack(fill="x", pady=(4, 0))
        tk.Button(btn_row, text="⏳  View Pending Scholars",
                  bg=ORANGE, fg=WHITE,
                  relief="flat", bd=0,
                  font=("Helvetica", 11, "bold"),
                  padx=20, pady=10,
                  cursor="hand2",
                  command=self._open_pending).pack(side="left", padx=(0, 12))
        tk.Button(btn_row, text="📋  View All Scholar Records",
                  bg=BLUE, fg=WHITE,
                  relief="flat", bd=0,
                  font=("Helvetica", 11, "bold"),
                  padx=20, pady=10,
                  cursor="hand2",
                  command=self._open_records).pack(side="left")

    # ── Widget helpers ─────────────────────────────────────────────────────────
    def _section_title(self, parent, text, pack=True):
        lbl = tk.Label(parent, text=text,
                       bg=BG, fg=TEXT,
                       font=("Helvetica", 13, "bold"),
                       anchor="w")
        if pack:
            lbl.pack(fill="x", pady=(0, 8))
        return lbl

    def _stat_card(self, parent, number, label, color):
        card = tk.Frame(parent, bg=WHITE,
                        highlightbackground=color,
                        highlightthickness=2)
        tk.Label(card, text=number,
                 bg=WHITE, fg=color,
                 font=("Helvetica", 28, "bold")).pack(pady=(16, 4))
        tk.Label(card, text=label,
                 bg=WHITE, fg=GRAY,
                 font=("Helvetica", 9, "bold")).pack(pady=(0, 16))
        card._num_label = card.winfo_children()[0]
        return card

    def _summary_card(self, parent, number, label):
        card = tk.Frame(parent, bg=BLUE_L)
        tk.Label(card, text=number,
                 bg=BLUE_L, fg=BLUE,
                 font=("Helvetica", 32, "bold")).pack(pady=(16, 4))
        tk.Label(card, text=label,
                 bg=BLUE_L, fg=GRAY,
                 font=("Helvetica", 9, "bold")).pack(pady=(0, 16))
        card._num_label = card.winfo_children()[0]
        return card

    # ── Data loading ───────────────────────────────────────────────────────────
    def _load_all(self):
        try:
            apps     = fetch_all("SELECT status FROM application") or []
            renewals = fetch_all("SELECT status FROM renew") or []
            setting  = fetch_one("SELECT is_open FROM renewal_settings WHERE id=1")

            s = {
                "total_new":     len(apps),
                "approved_new":  sum(1 for a in apps     if a["status"]=="approved"),
                "pending_new":   sum(1 for a in apps     if a["status"]=="pending"),
                "rejected_new":  sum(1 for a in apps     if a["status"]=="rejected"),
                "total_renew":   len(renewals),
                "approved_renew":sum(1 for r in renewals if str(r["status"]).lower()=="approved"),
                "pending_renew": sum(1 for r in renewals if str(r["status"]).lower()=="pending"),
                "rejected_renew":sum(1 for r in renewals if str(r["status"]).lower()=="rejected"),
            }
            s["total_all"]    = s["total_new"]     + s["total_renew"]
            s["approved_all"] = s["approved_new"]  + s["approved_renew"]
            s["pending_all"]  = s["pending_new"]   + s["pending_renew"]
            s["rejected_all"] = s["rejected_new"]  + s["rejected_renew"]

            is_open = bool(setting["is_open"]) if setting else False
            self.after(0, self._update_ui, s, is_open)
        except Exception as e:
            self.after(0, lambda: print(f"[Mayor] load error: {e}"))

    def _update_ui(self, s, is_open):
        for key, card in self._stat_cards.items():
            card._num_label.config(text=str(s.get(key, 0)))
        for key, card in self._summary_cards.items():
            card._num_label.config(text=str(s.get(key, 0)))
        self._renewal_open = is_open
        self._update_renewal_badge()

    def _update_renewal_badge(self):
        if self._renewal_open:
            self._renewal_badge.config(text="● OPEN",   fg=GREEN)
            self._toggle_btn.config(text="🔒 Close Renewal", bg=RED)
        else:
            self._renewal_badge.config(text="● CLOSED", fg=RED)
            self._toggle_btn.config(text="🔓 Open Renewal",  bg=GREEN)

    # ── Renewal toggle ─────────────────────────────────────────────────────────
    def _toggle_renewal(self):
        self._toggle_btn.config(state="disabled")
        threading.Thread(target=self._do_toggle, daemon=True).start()

    def _do_toggle(self):
        try:
            new_status = not self._renewal_open
            execute(
                "UPDATE renewal_settings SET is_open=%s WHERE id=1",
                (new_status,)
            )
            self.after(0, self._on_toggled, new_status)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, self._toggle_btn.config, {"state": "normal"})

    def _on_toggled(self, new_status):
        self._renewal_open = new_status
        self._update_renewal_badge()
        self._toggle_btn.config(state="normal")
        status_text = "OPEN ✅" if new_status else "CLOSED 🔒"
        messagebox.showinfo("Renewal Status",
                            f"Scholarship renewal is now {status_text}")

    # ── Navigation ─────────────────────────────────────────────────────────────
    def _open_pending(self):
        self.app.show_mayor_pending()

    def _open_records(self):
        self.app.show_mayor_records()

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.app.logout()