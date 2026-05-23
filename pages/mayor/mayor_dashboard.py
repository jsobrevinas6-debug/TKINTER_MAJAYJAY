import tkinter as tk
from tkinter import ttk, messagebox
import threading
import math

try:
    from db import fetch_one, fetch_all, execute
except ImportError:
    fetch_one = fetch_all = execute = None

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

# ══════════════════════════════════════════════════════════════════════════════
# Palette
# ══════════════════════════════════════════════════════════════════════════════
BG           = "#F7FAFC"
WHITE        = "#FFFFFF"
PURPLE       = "#667EEA"
PURPLE2      = "#764BA2"
BORDER       = "#E2E8F0"
BORDER2      = "#F1F5F9"
DARK         = "#2D3748"
GRAY         = "#718096"
SIDEBAR_DARK = WHITE
SIDEBAR_LINE = BORDER
SIDEBAR_TEXT = DARK
NAV_ACTIVE   = "#6B70D6"
NAV_HOVER    = "#EEF2FF"
SHADOW       = "#CBD5E0"
GREEN        = "#48BB78"
GREEN2       = "#276749"
ORANGE       = "#ED8936"
RED          = "#F56565"
RED2         = "#C53030"
HEADER_BG    = "#F8FAFC"
MUTED2       = "#64748B"

# Records-specific
REC_APPROVED  = "#16A34A"
REC_PENDING   = "#D97706"
REC_REJECTED  = "#DC2626"
REC_ARCHIVE   = "#F6AD55"
REC_ARCHIVE_H = "#DD6B20"

SUCCESS_BG = "#D4EDDA"; SUCCESS_FG = "#155724"; SUCCESS_BR = "#48BB78"
ERROR_BG   = "#F8D7DA"; ERROR_FG   = "#721C24"; ERROR_BR   = "#F56565"

ROWS_PER_PAGE = 10

# ══════════════════════════════════════════════════════════════════════════════
# Sample data  (replace with DB queries)
# ══════════════════════════════════════════════════════════════════════════════
SAMPLE_APPS = [
    {"application_id": i, "user_id": i, "email": f"student{i}@mail.com",
     "first_name": f"First{i}", "middle_name": "M.", "last_name": f"Last{i}",
     "student_id": f"STU-{1000+i}", "contact_number": f"09{i:09d}",
     "address": f"{i} Sample St.", "municipality": "Calamba", "baranggay": f"Brgy {i}",
     "school_name": "University of the Philippines", "course": "BS Computer Science",
     "year_level": str((i % 4) + 1), "gwa": f"{1 + (i % 3) * 0.25:.2f}",
     # normalised to lowercase to match DB enum and _count comparisons
     "status": ["approved", "pending", "rejected"][i % 3],
     "scholarship_type": ["new", "renewal"][i % 2],
     "year_applied": "2024", "reason": "Financial need and academic excellence.",
     "school_id_path": "", "id_picture_path": "", "birth_certificate_path": "",
     "grades_path": "", "cor_path": "",
     "submission_date": f"2024-0{(i%9)+1}-{(i%28)+1:02d}",
     "archived": 0}
    for i in range(1, 36)
]

SAMPLE_RENEWALS = [
    {"renewal_id": i, "application_id": i, "user_id": i,
     "email": f"student{i}@mail.com",
     "first_name": f"First{i}", "middle_name": "M.", "last_name": f"Last{i}",
     "student_id": f"STU-{1000+i}", "contact_number": f"09{i:09d}",
     "address": f"{i} Sample St.", "municipality": "Calamba", "baranggay": f"Brgy {i}",
     "course": "BS Computer Science",
     "year_level": str((i % 4) + 1), "gwa": f"{1 + (i % 3) * 0.25:.2f}",
     "reason": "Continuing academic excellence.",
     "school_id_path": "", "id_picture_path": "", "birth_certificate_path": "",
     "grades_path": "", "cor_path": "",
     # normalised to lowercase so _count works consistently
     "status": ["approved", "pending", "rejected"][i % 3],
     "submission_date": f"2024-0{(i%9)+1}-{(i%28)+1:02d}",
     "archived": 0}
    for i in range(1, 21)
]


def _count(data, key, val):
    return sum(1 for r in data if str(r.get(key, "")).lower() == str(val).lower())


# ══════════════════════════════════════════════════════════════════════════════
# MayorDashboard
# ══════════════════════════════════════════════════════════════════════════════
class MayorDashboard(tk.Frame):
    def __init__(self, parent, name, email, app, **_):
        super().__init__(parent, bg=BG)
        self.name  = name
        self.email = email
        self.app   = app

        # ── Dashboard state ───────────────────────────────────────────────────
        self._stat_cards    = {}
        self._summary_cards = {}

        # ── Records state ─────────────────────────────────────────────────────
        self._rec_section       = "applications"
        self._rec_show_archived = False
        self._rec_status_filter = "all"
        self._rec_sort_col      = None
        self._rec_sort_asc      = True
        self._rec_current_page  = 1
        self._rec_flash         = None
        self._rec_apps          = [dict(r) for r in SAMPLE_APPS]
        self._rec_renewals      = [dict(r) for r in SAMPLE_RENEWALS]
        self._rec_search_var    = None
        self._rec_tree          = None
        self._rec_pag_frame     = None
        self._rec_cols          = None

        self._build()
        threading.Thread(target=self._load_all, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # Layout skeleton
    # ══════════════════════════════════════════════════════════════════════════
    def _build(self):
        self._sidebar = Sidebar(
            self, user_type="mayor", name=self.name,
            active_item="Dashboard",
            on_nav=self._on_nav,
            on_logout=self._logout,
        )
        self._sidebar.pack(side="left", fill="y")

        self._main = tk.Frame(self, bg=BG)
        self._main.pack(side="left", fill="both", expand=True)

        # ── Persistent top bar ────────────────────────────────────────────────
        topbar = tk.Frame(self._main, bg=WHITE, height=64)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Frame(topbar, bg=BORDER, height=1).pack(side="bottom", fill="x")
        self._topbar_title = tk.Label(topbar, text="Dashboard",
                                      bg=WHITE, fg=DARK,
                                      font=("Segoe UI", 16, "bold"))
        self._topbar_title.pack(side="left", padx=28, pady=16)

        # ── Swappable content area ────────────────────────────────────────────
        self._content_area = tk.Frame(self._main, bg=BG)
        self._content_area.pack(fill="both", expand=True)

        self._render_home()

    def _on_nav(self, label):
        if label == "Dashboard":
            self._show_home()
        elif label == "Scholar Records":
            self._open_records()
        elif label == "Renewal Settings":
            self._open_renewal_settings()
        elif label == "Profile Settings":
            # FIX: was not in the original on_nav — ensure it's wired here
            self._show_profile_settings()

    # ══════════════════════════════════════════════════════════════════════════
    # Content switching
    # ══════════════════════════════════════════════════════════════════════════
    def _clear_content(self):
        for w in self._content_area.winfo_children():
            w.destroy()

    def _show_home(self):
        self._topbar_title.config(text="Dashboard")
        self._clear_content()
        self._render_home()

    def _open_records(self):
        if hasattr(self, "app") and self.app:
            self.app.show_mayor_records()
        else:
            self._show_records()

    def _show_records(self):
        if hasattr(self, "app") and self.app:
            self.app.show_mayor_records()
            return
        self._topbar_title.config(text="Scholar Records")
        self._clear_content()
        self._rec_section       = "applications"
        self._rec_show_archived = False
        self._rec_status_filter = "all"
        self._rec_sort_col      = None
        self._rec_current_page  = 1
        self._rec_flash         = None
        self._rec_render()

    # ══════════════════════════════════════════════════════════════════════════
    # ── HOME VIEW ─────────────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════════════
    def _render_home(self):
        canvas = tk.Canvas(self._content_area, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self._content_area, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        # FIX: all content now packed into `inner` so padx=32/pady=24 applies.
        # Previously a dead `inner` frame was created but content was packed
        # into `body` directly (no padding at all).
        inner = tk.Frame(canvas, bg=BG)
        wid   = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(wid, width=e.width)
        canvas.bind("<Configure>", _resize)
        # FIX: added Linux scroll bindings
        canvas.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        content = tk.Frame(inner, bg=BG)
        content.pack(fill="both", expand=True, padx=32, pady=24)

        tk.Label(content, text=f"Welcome back, {self.name}! 🏛",
                 bg=BG, fg=DARK, font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(content,
                 text="Overview of scholarship applications and renewals.",
                 bg=BG, fg=GRAY, font=("Segoe UI", 11)).pack(anchor="w", pady=(4, 24))

        # ── New Applications ──────────────────────────────────────────────────
        self._section_lbl(content, "🆕  New Scholarship Applications")
        new_row = tk.Frame(content, bg=BG)
        new_row.pack(fill="x", pady=(0, 24))
        for key, label, icon, accent in [
            ("total_new",    "Total New",  "📋", PURPLE),
            ("approved_new", "Approved",   "✅", GREEN),
            ("pending_new",  "Pending",    "⏳", ORANGE),
            ("rejected_new", "Rejected",   "❌", RED),
        ]:
            card = self._stat_card(new_row, icon, "—", label, accent)
            card.pack(side="left", fill="both", expand=True, padx=(0, 12))
            self._stat_cards[key] = card

        # ── Renewals ──────────────────────────────────────────────────────────
        self._section_lbl(content, "🔄  Scholarship Renewals")
        renew_row = tk.Frame(content, bg=BG)
        renew_row.pack(fill="x", pady=(0, 24))
        for key, label, icon, accent in [
            ("total_renew",    "Total Renewals", "🔄", PURPLE),
            ("approved_renew", "Approved",       "✅", GREEN),
            ("pending_renew",  "Pending",        "⏳", ORANGE),
            ("rejected_renew", "Rejected",       "❌", RED),
        ]:
            card = self._stat_card(renew_row, icon, "—", label, accent)
            card.pack(side="left", fill="both", expand=True, padx=(0, 12))
            self._stat_cards[key] = card

        # ── Overall Summary ───────────────────────────────────────────────────
        self._section_lbl(content, "📊  Overall Summary")
        sum_shadow = tk.Frame(content, bg=SHADOW)
        sum_shadow.pack(fill="x", pady=(0, 24))
        sum_card = tk.Frame(sum_shadow, bg=WHITE, padx=24, pady=20)
        sum_card.pack(fill="x", padx=2, pady=2)
        sum_row = tk.Frame(sum_card, bg=WHITE)
        sum_row.pack(fill="x")
        for key, label, icon, accent in [
            ("total_all",    "Total Applications", "📋", PURPLE),
            ("approved_all", "Total Approved",     "✅", GREEN),
            ("pending_all",  "Total Pending",      "⏳", ORANGE),
            ("rejected_all", "Total Rejected",     "❌", RED),
        ]:
            card = self._stat_card(sum_row, icon, "—", label, accent)
            card.pack(side="left", fill="both", expand=True, padx=(0, 12))
            self._summary_cards[key] = card

        # ── Quick Actions ─────────────────────────────────────────────────────
        self._section_lbl(content, "⚡  Quick Actions")
        btn_row = tk.Frame(content, bg=BG)
        btn_row.pack(anchor="w")
        for text, cmd, color, hover in [
            ("📋  View Scholar Records", self._open_records, PURPLE, PURPLE2),
        ]:
            btn = tk.Button(btn_row, text=text,
                            bg=color, fg=WHITE,
                            activebackground=hover, activeforeground=WHITE,
                            relief="flat", bd=0,
                            font=("Segoe UI", 10, "bold"),
                            padx=18, pady=10, cursor="hand2",
                            command=cmd)
            btn.pack(side="left", padx=(0, 12))
            btn.bind("<Enter>", lambda e, b=btn, h=hover: b.config(bg=h))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))

    # ── Widget helpers ─────────────────────────────────────────────────────────
    def _section_lbl(self, parent, text, pack=True):
        lbl = tk.Label(parent, text=text, bg=BG, fg=DARK,
                       font=("Segoe UI", 13, "bold"), anchor="w")
        if pack:
            lbl.pack(fill="x", pady=(0, 10))
        return lbl

    def _stat_card(self, parent, icon, number, label, accent):
        shadow = tk.Frame(parent, bg=SHADOW)
        card   = tk.Frame(shadow, bg=WHITE, padx=16, pady=16)
        card.pack(padx=2, pady=2)
        tk.Label(card, text=icon, bg=WHITE, font=("Segoe UI", 18)).pack(anchor="w")
        num_lbl = tk.Label(card, text=number, bg=WHITE, fg=accent,
                           font=("Segoe UI", 28, "bold"))
        num_lbl.pack(anchor="w")
        tk.Label(card, text=label, bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 9)).pack(anchor="w")
        shadow._num_label = num_lbl
        return shadow

    # ══════════════════════════════════════════════════════════════════════════
    # Data loading (home)
    # ══════════════════════════════════════════════════════════════════════════
    def _load_all(self):
        try:
            # FIX: was querying dropped `application` table; corrected to `applications`
            apps     = fetch_all("SELECT status FROM applications") or []
            renewals = fetch_all("SELECT status FROM renew")        or []
            s = {
                "total_new":      len(apps),
                "approved_new":   _count(apps,     "status", "approved"),
                "pending_new":    _count(apps,     "status", "pending"),
                "rejected_new":   _count(apps,     "status", "rejected"),
                "total_renew":    len(renewals),
                "approved_renew": _count(renewals, "status", "approved"),
                "pending_renew":  _count(renewals, "status", "pending"),
                "rejected_renew": _count(renewals, "status", "rejected"),
            }
            s["total_all"]    = s["total_new"]    + s["total_renew"]
            s["approved_all"] = s["approved_new"] + s["approved_renew"]
            s["pending_all"]  = s["pending_new"]  + s["pending_renew"]
            s["rejected_all"] = s["rejected_new"] + s["rejected_renew"]
            self.after(0, self._update_home_ui, s)
        except Exception as e:
            self.after(0, lambda: print(f"[Mayor] load error: {e}"))

    def _update_home_ui(self, s):
        for key, card in self._stat_cards.items():
            card._num_label.config(text=str(s.get(key, 0)))
        for key, card in self._summary_cards.items():
            card._num_label.config(text=str(s.get(key, 0)))

    # ══════════════════════════════════════════════════════════════════════════
    # ── RECORDS VIEW ──────────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════════════
    def _rec_render(self):
        self._clear_content()

        wrap = tk.Frame(self._content_area, bg=BG)
        wrap.pack(fill="both", expand=True, padx=32, pady=(20, 32))

        if self._rec_flash:
            self._rec_alert(wrap, *self._rec_flash)
            self._rec_flash = None

        self._rec_build_stats(wrap)
        self._rec_build_section_tabs(wrap)
        if not self._rec_show_archived:
            self._rec_build_status_tabs(wrap)
        self._rec_build_records_card(wrap)

    # ── Flash alert ────────────────────────────────────────────────────────────
    def _rec_alert(self, parent, kind, msg):
        bg = SUCCESS_BG if kind == "success" else ERROR_BG
        fg = SUCCESS_FG if kind == "success" else ERROR_FG
        br = SUCCESS_BR if kind == "success" else ERROR_BR
        row = tk.Frame(parent, bg=bg, highlightbackground=BORDER, highlightthickness=1)
        row.pack(fill="x", pady=(0, 14))
        tk.Frame(row, bg=br, width=4).pack(side="left", fill="y")
        tk.Label(row, text=msg, bg=bg, fg=fg,
                 font=("Segoe UI", 10, "bold"), anchor="w",
                 padx=14, pady=10).pack(side="left")

    # ── Stat cards ─────────────────────────────────────────────────────────────
    def _rec_build_stats(self, parent):
        grid = tk.Frame(parent, bg=BG)
        grid.pack(fill="x", pady=(0, 20))

        total    = len(self._rec_apps) + len(self._rec_renewals)
        # FIX: both datasets now use lowercase so all counts are consistent
        approved = (_count(self._rec_apps,     "status", "approved") +
                    _count(self._rec_renewals, "status", "approved"))
        pending  = (_count(self._rec_apps,     "status", "pending") +
                    _count(self._rec_renewals, "status", "pending"))
        rejected = (_count(self._rec_apps,     "status", "rejected") +
                    _count(self._rec_renewals, "status", "rejected"))

        for col, (label, val, colour) in enumerate([
            ("Total",    str(total),    PURPLE),
            ("Approved", str(approved), REC_APPROVED),
            ("Pending",  str(pending),  REC_PENDING),
            ("Rejected", str(rejected), REC_REJECTED),
        ]):
            card = tk.Frame(grid, bg=WHITE,
                            highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=0, column=col, sticky="nsew",
                      padx=(0 if col == 0 else 10, 0), ipadx=10, ipady=12)
            grid.columnconfigure(col, weight=1)
            tk.Label(card, text=val,   bg=WHITE, fg=colour,
                     font=("Segoe UI", 26, "bold")).pack(pady=(12, 2))
            tk.Label(card, text=label, bg=WHITE, fg="#666666",
                     font=("Segoe UI", 10)).pack(pady=(0, 12))

    # ── Section tabs ───────────────────────────────────────────────────────────
    def _rec_build_section_tabs(self, parent):
        bar = tk.Frame(parent, bg=WHITE,
                       highlightbackground=BORDER, highlightthickness=1)
        bar.pack(fill="x", pady=(0, 12), ipady=4)
        inner = tk.Frame(bar, bg=WHITE)
        inner.pack(side="left", padx=14, pady=6)
        for label, sec, arch in [
            ("📋  Active Applications",   "applications", False),
            ("🔄  Renewal Applications",  "renewals",     False),
            ("🗄️  Archived Applications", "applications", True),
        ]:
            active = (sec == self._rec_section and arch == self._rec_show_archived)
            bg = PURPLE if active else WHITE
            fg = WHITE  if active else "#666666"
            lbl = tk.Label(inner, text=label, bg=bg, fg=fg,
                           font=("Segoe UI", 9, "bold"),
                           padx=14, pady=7, cursor="hand2",
                           relief="solid", bd=1)
            lbl.pack(side="left", padx=(0, 8))
            lbl.bind("<Button-1>",
                     lambda e, s=sec, a=arch: self._rec_switch_section(s, a))

    # ── Status filter tabs ─────────────────────────────────────────────────────
    def _rec_build_status_tabs(self, parent):
        bar = tk.Frame(parent, bg=WHITE,
                       highlightbackground=BORDER, highlightthickness=1)
        bar.pack(fill="x", pady=(0, 18), ipady=4)
        inner = tk.Frame(bar, bg=WHITE)
        inner.pack(side="left", padx=14, pady=6)
        for label, val in [("All","all"),("Approved","approved"),
                           ("Pending","pending"),("Rejected","rejected")]:
            active = (self._rec_status_filter == val)
            bg = PURPLE if active else WHITE
            fg = WHITE  if active else "#666666"
            lbl = tk.Label(inner, text=label, bg=bg, fg=fg,
                           font=("Segoe UI", 9, "bold"),
                           padx=14, pady=7, cursor="hand2",
                           relief="solid", bd=1)
            lbl.pack(side="left", padx=(0, 8))
            lbl.bind("<Button-1>", lambda e, v=val: self._rec_set_filter(v))

    # ── Records card (search + table + pagination) ─────────────────────────────
    def _rec_build_records_card(self, parent):
        card = tk.Frame(parent, bg=WHITE,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True)
        inner = tk.Frame(card, bg=WHITE)
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        hdr = tk.Frame(inner, bg=WHITE)
        hdr.pack(fill="x", pady=(0, 12))
        title = ("Renewal Applications" if self._rec_section == "renewals"
                 else "Scholarship Applications")
        tk.Label(hdr, text=title, bg=WHITE, fg=DARK,
                 font=("Segoe UI", 12, "bold")).pack(side="left")

        self._rec_search_var = tk.StringVar()
        self._rec_search_var.trace_add("write", lambda *_: self._rec_on_search())
        sw = tk.Frame(hdr, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        sw.pack(side="right")
        tk.Label(sw, text="🔍", bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 10)).pack(side="left", padx=(8, 0))
        tk.Entry(sw, textvariable=self._rec_search_var,
                 bg=WHITE, fg=DARK, relief="flat",
                 font=("Segoe UI", 10), width=22,
                 insertbackground=DARK).pack(side="left", ipady=6, padx=8)

        self._rec_build_tree(inner)

        tk.Frame(inner, bg=BORDER2, height=1).pack(fill="x")
        self._rec_pag_frame = tk.Frame(inner, bg=WHITE)
        self._rec_pag_frame.pack(fill="x", pady=(10, 0))

        self._rec_refresh_table()

    # ── Treeview ───────────────────────────────────────────────────────────────
    def _rec_build_tree(self, parent):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Rec.Treeview",
                        background=WHITE, foreground="#374151",
                        rowheight=36, fieldbackground=WHITE,
                        font=("Segoe UI", 10), borderwidth=0, relief="flat")
        style.configure("Rec.Treeview.Heading",
                        background=HEADER_BG, foreground=MUTED2,
                        font=("Segoe UI", 9, "bold"), relief="flat", borderwidth=0)
        style.map("Rec.Treeview",
                  background=[("selected", "#EEF0FF")],
                  foreground=[("selected", DARK)])
        style.map("Rec.Treeview.Heading",
                  background=[("active", HEADER_BG)])

        if self._rec_section == "renewals":
            cols = ("renewal_id","name","course","year_level","gwa","status","submitted")
            hdrs = ("Renewal ID","Name","Course","Year Level","GWA","Status","Submitted")
            widths = (90,165,155,85,70,90,110)
        else:
            cols = ("app_id","name","school","course","year_level","status","submitted")
            hdrs = ("App ID","Name","School","Course","Year Level","Status","Submitted")
            widths = (70,145,170,135,80,90,110)

        self._rec_cols = cols
        all_cols = (*cols, "actions")

        wrap = tk.Frame(parent, bg=WHITE)
        wrap.pack(fill="both", expand=True)

        xbar = ttk.Scrollbar(wrap, orient="horizontal")
        xbar.pack(side="bottom", fill="x")

        self._rec_tree = ttk.Treeview(wrap, columns=all_cols, show="headings",
                                      style="Rec.Treeview",
                                      xscrollcommand=xbar.set,
                                      selectmode="browse", height=13)
        xbar.config(command=self._rec_tree.xview)
        self._rec_tree.pack(fill="both", expand=True)

        for col, hdr, w in zip(cols, hdrs, widths):
            self._rec_tree.heading(col, text=hdr,
                                   command=lambda c=col: self._rec_on_sort(c))
            self._rec_tree.column(col, width=w, minwidth=55, anchor="w")

        self._rec_tree.heading("actions", text="Actions")
        self._rec_tree.column("actions", width=175, minwidth=120,
                              anchor="w", stretch=False)

        self._rec_tree.tag_configure("even", background=WHITE)
        self._rec_tree.tag_configure("odd",  background="#F8FAFC")
        self._rec_tree.bind("<Double-1>", self._rec_on_double_click)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")

    # ── Data helpers ───────────────────────────────────────────────────────────
    def _rec_source(self):
        if self._rec_section == "renewals":
            return [r for r in self._rec_renewals if r["archived"] == 0]
        if self._rec_show_archived:
            return [r for r in self._rec_apps if r["archived"] == 1]
        return [r for r in self._rec_apps if r["archived"] == 0]

    def _rec_filtered_rows(self):
        rows = self._rec_source()
        q = (self._rec_search_var.get().strip().lower()
             if self._rec_search_var else "")

        if not self._rec_show_archived and self._rec_section != "renewals":
            if self._rec_status_filter != "all":
                rows = [r for r in rows
                        if r.get("status", "").lower() == self._rec_status_filter]

        if q:
            rows = [r for r in rows
                    if q in " ".join(str(v) for v in r.values()).lower()]

        if self._rec_sort_col:
            db_key = {
                "app_id":"application_id","renewal_id":"renewal_id",
                "name":"first_name","school":"school_name",
                "course":"course","year_level":"year_level",
                "gwa":"gwa","status":"status","submitted":"submission_date",
            }.get(self._rec_sort_col, self._rec_sort_col)
            rows = sorted(rows,
                          key=lambda r: str(r.get(db_key,"")).lower(),
                          reverse=not self._rec_sort_asc)
        return rows

    @property
    def _rec_total_pages(self):
        return max(1, math.ceil(len(self._rec_filtered_rows()) / ROWS_PER_PAGE))

    def _rec_page_rows(self):
        rows  = self._rec_filtered_rows()
        start = (self._rec_current_page - 1) * ROWS_PER_PAGE
        return rows[start: start + ROWS_PER_PAGE]

    # ── Refresh table rows + headings ──────────────────────────────────────────
    def _rec_refresh_table(self):
        for iid in self._rec_tree.get_children():
            self._rec_tree.delete(iid)

        arch_lbl = "Unarchive" if self._rec_show_archived else "Archive"

        for i, r in enumerate(self._rec_page_rows()):
            tag  = "even" if i % 2 == 0 else "odd"
            name = " ".join(filter(None, [r.get("first_name"),
                                          r.get("middle_name"),
                                          r.get("last_name")]))
            status = r.get("status", "N/A")
            s_disp = f"[{status.upper()}]"

            if self._rec_section == "renewals":
                vals = (r["renewal_id"], name, r.get("course",""),
                        r.get("year_level",""), r.get("gwa",""),
                        s_disp, r.get("submission_date",""),
                        f"View  |  {arch_lbl}")
            else:
                vals = (r.get("application_id",""), name,
                        r.get("school_name",""), r.get("course",""),
                        r.get("year_level",""), s_disp,
                        r.get("submission_date",""),
                        f"View  |  {arch_lbl}")

            self._rec_tree.insert("", "end", iid=str(i),
                                  values=vals, tags=(tag,))

        # FIX: rstrip(" ▲▼") strips individual chars not the substring;
        # replaced with explicit replace() calls
        for col in (*self._rec_cols, "actions"):
            base = (self._rec_tree.heading(col)["text"]
                    .replace(" ▲", "").replace(" ▼", ""))
            if col == self._rec_sort_col:
                arrow = " ▲" if self._rec_sort_asc else " ▼"
                self._rec_tree.heading(col, text=base + arrow)
            else:
                self._rec_tree.heading(col, text=base)

        self._rec_build_pagination()

    # ── Pagination ─────────────────────────────────────────────────────────────
    def _rec_build_pagination(self):
        for w in self._rec_pag_frame.winfo_children():
            w.destroy()

        total = len(self._rec_filtered_rows())
        cp    = self._rec_current_page
        start = (cp-1)*ROWS_PER_PAGE + 1 if total else 0
        end   = min(cp*ROWS_PER_PAGE, total)
        tp    = self._rec_total_pages

        tk.Label(self._rec_pag_frame,
                 text=f"Showing {start} to {end} of {total} entries",
                 bg=WHITE, fg="#666666",
                 font=("Segoe UI", 9)).pack(side="left", pady=6)

        nav = tk.Frame(self._rec_pag_frame, bg=WHITE)
        nav.pack(side="right")

        def _nbtn(text, cmd, disabled=False):
            c = "#BBBBBB" if disabled else PURPLE
            b = tk.Label(nav, text=text, bg=WHITE, fg=c,
                         font=("Segoe UI", 9, "bold"),
                         padx=9, pady=4, relief="solid", bd=1,
                         cursor="" if disabled else "hand2")
            b.pack(side="left", padx=2)
            if not disabled:
                b.bind("<Button-1>", lambda e: cmd())

        _nbtn("Previous", lambda: self._rec_go_page(cp-1), cp <= 1)

        for p in range(max(1, cp-2), min(tp+1, cp+3)):
            bg = PURPLE if p == cp else WHITE
            fg = WHITE  if p == cp else PURPLE
            b  = tk.Label(nav, text=str(p), bg=bg, fg=fg,
                          font=("Segoe UI", 9, "bold"),
                          width=3, padx=4, pady=4,
                          relief="solid", bd=1,
                          cursor="hand2")
            b.pack(side="left", padx=2)
            if p != cp:
                b.bind("<Button-1>", lambda e, pg=p: self._rec_go_page(pg))

        _nbtn("Next", lambda: self._rec_go_page(cp+1), cp >= tp)

    # ── Events ─────────────────────────────────────────────────────────────────
    def _rec_go_page(self, page):
        self._rec_current_page = max(1, min(page, self._rec_total_pages))
        self._rec_refresh_table()

    def _rec_on_sort(self, col):
        if col == "actions":
            return
        if self._rec_sort_col == col:
            self._rec_sort_asc = not self._rec_sort_asc
        else:
            self._rec_sort_col = col
            self._rec_sort_asc = True
        self._rec_current_page = 1
        self._rec_refresh_table()

    def _rec_on_search(self):
        self._rec_current_page = 1
        self._rec_refresh_table()

    def _rec_switch_section(self, sec, archived):
        self._rec_section       = sec
        self._rec_show_archived = archived
        self._rec_status_filter = "all"
        self._rec_sort_col      = None
        self._rec_current_page  = 1
        self._rec_render()

    def _rec_set_filter(self, val):
        self._rec_status_filter = val
        self._rec_current_page  = 1
        self._rec_render()

    def _rec_on_double_click(self, event):
        iid = self._rec_tree.focus()
        if not iid:
            return
        idx  = int(iid)
        rows = self._rec_page_rows()
        if idx >= len(rows):
            return
        record = rows[idx]
        rtype  = "renewal" if self._rec_section == "renewals" else "application"
        self._rec_open_modal(record, rtype)

    # ── Detail modal ───────────────────────────────────────────────────────────
    def _rec_open_modal(self, record, rtype):
        dlg = tk.Toplevel(self)
        dlg.title("Record Details")
        dlg.configure(bg=WHITE)
        dlg.grab_set()
        dlg.resizable(True, True)

        self.update_idletasks()
        w, h = 680, 680
        px = self.winfo_x() + (self.winfo_width()  - w) // 2
        py = self.winfo_y() + (self.winfo_height() - h) // 2
        dlg.geometry(f"{w}x{h}+{px}+{py}")

        hdr = tk.Frame(dlg, bg=WHITE)
        hdr.pack(fill="x", padx=28, pady=(22, 0))
        full_name = " ".join(filter(None, [record.get("first_name"),
                                           record.get("middle_name"),
                                           record.get("last_name")]))
        tk.Label(hdr, text=f"Record Details — {full_name}",
                 bg=WHITE, fg=DARK,
                 font=("Segoe UI", 15, "bold")).pack(side="left")
        tk.Button(hdr, text="×", bg=WHITE, fg=GRAY,
                  font=("Segoe UI", 18), relief="flat", cursor="hand2",
                  command=dlg.destroy).pack(side="right")
        tk.Frame(dlg, bg=BORDER, height=1).pack(fill="x", pady=10)

        bo = tk.Frame(dlg, bg=WHITE)
        bo.pack(fill="both", expand=True)
        bc = tk.Canvas(bo, bg=WHITE, highlightthickness=0)
        bvb = ttk.Scrollbar(bo, orient="vertical", command=bc.yview)
        bc.configure(yscrollcommand=bvb.set)
        bvb.pack(side="right", fill="y")
        bc.pack(side="left", fill="both", expand=True)
        body = tk.Frame(bc, bg=WHITE)
        bwin = bc.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>",
                  lambda e: bc.configure(scrollregion=bc.bbox("all")))
        bc.bind("<Configure>",
                lambda e: bc.itemconfig(bwin, width=e.width))
        bc.bind("<MouseWheel>",
                lambda e: bc.yview_scroll(-1*(e.delta//120), "units"))
        bc.bind("<Button-4>", lambda e: bc.yview_scroll(-1, "units"))
        bc.bind("<Button-5>", lambda e: bc.yview_scroll(1, "units"))

        def _row(label, value):
            f = tk.Frame(body, bg=WHITE)
            f.pack(fill="x", padx=28, pady=(0, 10))
            tk.Label(f, text=label, bg=WHITE, fg=DARK,
                     font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
            tk.Label(f, text=value or "N/A", bg=WHITE, fg="#4A5568",
                     font=("Segoe UI", 10), anchor="w",
                     wraplength=580, justify="left").pack(fill="x", pady=(2, 0))

        id_label  = "Renewal ID" if rtype == "renewal" else "Application ID"
        record_id = record.get("renewal_id" if rtype == "renewal"
                               else "application_id", "?")
        status    = record.get("status", "N/A")
        sch_type  = (record.get("scholarship_type", "New").capitalize()
                     if rtype == "application" else "Renewal")
        loc = " / ".join(filter(None, [record.get("municipality"),
                                       record.get("baranggay")])) or "N/A"

        _row(id_label,                  f"#{record_id}")
        _row("Name",                    full_name)
        _row("Student ID",              record.get("student_id"))
        _row("Email",                   record.get("email"))
        _row("Contact Number",          record.get("contact_number"))
        _row("Address",                 record.get("address"))
        _row("Municipality / Barangay", loc)
        if rtype == "application":
            _row("School", record.get("school_name"))
        _row("Course",     record.get("course"))
        _row("Year Level", record.get("year_level"))
        _row("GWA",        record.get("gwa"))
        _row("Type",       sch_type)
        _row("Status",     status.capitalize())
        _row("Submitted",  record.get("submission_date"))

        f = tk.Frame(body, bg=WHITE)
        f.pack(fill="x", padx=28, pady=(0, 10))
        tk.Label(f, text="Reason", bg=WHITE, fg=DARK,
                 font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
        rb = tk.Frame(f, bg="#F7F7F7",
                      highlightbackground=BORDER, highlightthickness=1)
        rb.pack(fill="x", pady=(4, 0))
        tk.Label(rb, text=record.get("reason") or "N/A",
                 bg="#F7F7F7", fg="#4A5568",
                 font=("Segoe UI", 10), anchor="w",
                 wraplength=560, justify="left",
                 padx=12, pady=10).pack(fill="x")

        f2 = tk.Frame(body, bg=WHITE)
        f2.pack(fill="x", padx=28, pady=(0, 16))
        tk.Label(f2, text="Documents", bg=WHITE, fg=DARK,
                 font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
        tk.Label(f2,
                 text="(Document links appear here when connected to the database)",
                 bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 9, "italic"), anchor="w").pack(fill="x", pady=(4, 0))

        tk.Frame(dlg, bg=BORDER, height=1).pack(fill="x")
        acts = tk.Frame(dlg, bg=WHITE)
        acts.pack(fill="x", padx=28, pady=14)

        s = status.lower()

        def _abtn(text, bg, hov, cmd):
            b = tk.Button(acts, text=text, bg=bg, fg=WHITE,
                          font=("Segoe UI", 10, "bold"),
                          relief="flat", padx=12, pady=6,
                          cursor="hand2", activebackground=hov,
                          activeforeground=WHITE, command=cmd)
            b.pack(side="left", padx=(0, 8))

        if s != "approved":
            _abtn("✓ Approve", REC_APPROVED, "#15803D",
                  lambda: self._rec_do_action(record, rtype, "approve", dlg))
        if s != "rejected":
            _abtn("✕ Reject", REC_REJECTED, "#B91C1C",
                  lambda: self._rec_do_action(record, rtype, "reject", dlg))

        arch_label = "Unarchive" if self._rec_show_archived else "Archive"
        arch_act   = "unarchive" if self._rec_show_archived else "archive"
        _abtn(arch_label, REC_ARCHIVE, REC_ARCHIVE_H,
              lambda: self._rec_do_action(record, rtype, arch_act, dlg))

        tk.Button(acts, text="Close", bg=WHITE, fg=GRAY,
                  font=("Segoe UI", 10), relief="solid", bd=1,
                  padx=12, pady=5, cursor="hand2",
                  command=dlg.destroy).pack(side="right")

    # ── Approve / Reject / Archive / Unarchive ─────────────────────────────────
    def _rec_do_action(self, record, rtype, action, dlg=None):
        if dlg:
            dlg.destroy()
        id_key = "renewal_id" if rtype == "renewal" else "application_id"
        rid    = record[id_key]
        source = self._rec_renewals if rtype == "renewal" else self._rec_apps
        msgs   = {
            "approve":   f"{'Renewal' if rtype=='renewal' else 'Application'} approved.",
            "reject":    f"{'Renewal' if rtype=='renewal' else 'Application'} rejected.",
            "archive":   f"{'Renewal' if rtype=='renewal' else 'Application'} archived.",
            "unarchive": f"{'Renewal' if rtype=='renewal' else 'Application'} unarchived.",
        }
        for r in source:
            if r[id_key] == rid:
                if action == "approve":
                    # FIX: consistently lowercase for both apps and renewals
                    r["status"] = "approved"
                elif action == "reject":
                    r["status"] = "rejected"
                elif action == "archive":
                    r["archived"] = 1
                elif action == "unarchive":
                    r["archived"] = 0
                break
        self._rec_flash        = ("success", "✅ " + msgs[action])
        self._rec_current_page = 1
        self._rec_render()

    # ══════════════════════════════════════════════════════════════════════════
    # Navigation stubs
    # ══════════════════════════════════════════════════════════════════════════
    def _show_profile_settings(self):
        """
        FIX: Two bugs were here:
          1. embedded=True was missing → ProfileSettingsPage built its own
             topbar inside _content_area, causing a double-header and making
             the back button call app.show_mayor_dashboard() which replaced
             the whole window (sidebar included).
          2. ProfileSettingsPage without embedded=True creates a Scrollbar
             packed side='right' to itself, which visually pushed the sidebar
             out of view on some geometry managers.
        Solution: always pass embedded=True so the page reuses the mayor's
        existing topbar and sidebar, and only renders its form content.
        """
        self._topbar_title.config(text="Profile Settings")
        self._clear_content()
        try:
            from pages.profile_settings import ProfileSettingsPage
        except ImportError:
            from profile_settings import ProfileSettingsPage
        ProfileSettingsPage(
            self._content_area,
            name=self.name,
            email=self.email,
            user_type="mayor",
            app=self.app,
            embedded=True,          # ← THE KEY FIX
        ).pack(fill="both", expand=True)

    def _open_pending(self):
        if hasattr(self, "app") and self.app:
            self.app.show_mayor_pending()

    def _open_renewal_settings(self):
        if hasattr(self, "app") and self.app:
            self.app.show_mayor_renewal_settings()

    def _logout(self):
        if messagebox.askyesno("Log Out", "Are you sure you want to log out?"):
            if hasattr(self, "app") and self.app:
                self.app.logout()


# ══════════════════════════════════════════════════════════════════════════════
# Standalone entry point
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Mayor Panel")
    root.geometry("1280x800")
    root.state("zoomed")

    dashboard = MayorDashboard(root, name="Mayor Juan Santos",
                               email="mayor@example.com", app=None)
    dashboard.pack(fill="both", expand=True)
    root.mainloop()