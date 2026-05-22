# =============================================================================
#  pages/mayor/records.py
#  Usage:  RecordsFrame(parent, name="...", email="...", app=app_controller)
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import math
import io
from PIL import Image, ImageTk

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

# =============================================================================
#  PALETTE  (matches mayor_dashboard.py)
# =============================================================================
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
ORANGE       = "#ED8936"
RED          = "#F56565"
HEADER_BG    = "#F8FAFC"
MUTED2       = "#64748B"

REC_APPROVED  = "#16A34A"
REC_PENDING   = "#D97706"
REC_REJECTED  = "#DC2626"
REC_ARCHIVE   = "#F6AD55"
REC_ARCHIVE_H = "#DD6B20"

SUCCESS_BG = "#D4EDDA"; SUCCESS_FG = "#155724"; SUCCESS_BR = "#48BB78"
ERROR_BG   = "#F8D7DA"; ERROR_FG   = "#721C24"; ERROR_BR   = "#F56565"

ROWS_PER_PAGE = 10

# =============================================================================
#  DB LOADERS
# =============================================================================
def _load_apps():
    if fetch_all is None:
        return []
    rows = fetch_all("""
        SELECT a.application_id, a.user_id,
               a.first_name, a.middle_name, a.last_name,
               a.student_id, a.contact_number,
               a.municipality, a.barangay AS baranggay,
               a.school_name, a.course, a.year_level,
               a.gwa, a.year_applied, a.essay AS reason,
               a.status, a.submission_date,
               u.email
        FROM applications a
        LEFT JOIN users u ON u.user_id = a.user_id
        ORDER BY a.submission_date DESC
    """) or []
    for r in rows:
        r.setdefault("archived", 0)
        r.setdefault("scholarship_type", "new")
        if r.get("submission_date"):
            r["submission_date"] = str(r["submission_date"])
        if r.get("gwa") is not None:
            r["gwa"] = str(r["gwa"])
    return rows

def _load_renewals():
    if fetch_all is None:
        return []
    rows = fetch_all("""
        SELECT r.renewal_id, r.application_id, r.user_id,
               r.status, r.submission_date,
               a.first_name, a.middle_name, a.last_name,
               a.student_id, a.contact_number,
               a.municipality, a.barangay AS baranggay,
               a.school_name, a.course, a.year_level,
               a.gwa, a.essay AS reason,
               u.email
        FROM renewals r
        LEFT JOIN applications a ON a.application_id = r.application_id
        LEFT JOIN users u ON u.user_id = r.user_id
        ORDER BY r.submission_date DESC
    """) or []
    for r in rows:
        r.setdefault("archived", 0)
        if r.get("submission_date"):
            r["submission_date"] = str(r["submission_date"])
        if r.get("gwa") is not None:
            r["gwa"] = str(r["gwa"])
    return rows

def _count(data, key, val):
    return sum(1 for r in data
               if str(r.get(key,"")).lower() == str(val).lower())


# =============================================================================
#  RECORDS FRAME
# =============================================================================
class RecordsFrame(tk.Frame):
    """
    Full-page Scholar Records screen.
    Matches the sidebar style of MayorDashboard.

    app.py usage:
        RecordsFrame(parent, name=name, email=email, app=self)
    """

    def __init__(self, parent, name="", email="", app=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.name  = name
        self.email = email
        self.app   = app

        # ── Records state ─────────────────────────────────────────────────────
        self._section       = "applications"
        self._show_archived = False
        self._status_filter = "all"
        self._sort_col      = None
        self._sort_asc      = True
        self._current_page  = 1
        self._flash         = None
        self._search_var    = None
        self._tree          = None
        self._pag_frame     = None
        self._cols          = None

        # ── Data ──────────────────────────────────────────────────────────────
        self._apps     = _load_apps()
        self._renewals = _load_renewals()

        self._build()

    # =========================================================================
    #  LAYOUT SKELETON
    # =========================================================================
    def _build(self):
        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = tk.Frame(self, bg=SIDEBAR_DARK, width=238)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        # ── Main area ─────────────────────────────────────────────────────────
        main = tk.Frame(self, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        self._main_canvas = tk.Canvas(main, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(main, orient="vertical",
                          command=self._main_canvas.yview)
        self._main_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._main_canvas.pack(fill="both", expand=True)

        self._inner = tk.Frame(self._main_canvas, bg=BG)
        wid = self._main_canvas.create_window(
            (0,0), window=self._inner, anchor="nw")

        def _resize(e):
            bbox = self._main_canvas.bbox("all")
            if bbox:
                self._main_canvas.configure(scrollregion=bbox)
            self._main_canvas.itemconfig(wid, width=e.width)

        self._main_canvas.bind("<Configure>", _resize)
        self._main_canvas.bind_all(
            "<MouseWheel>",
            lambda e: self._main_canvas.yview_scroll(
                int(-e.delta/120), "units"))

        # ── Top bar ───────────────────────────────────────────────────────────
        topbar = tk.Frame(self._inner, bg=WHITE, height=64)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Frame(topbar, bg=BORDER, height=1).pack(side="bottom", fill="x")

        tk.Label(topbar, text="Scholar Records",
                 bg=WHITE, fg=DARK,
                 font=("Segoe UI", 16, "bold")).pack(
                     side="left", padx=28, pady=16)

        # Welcome + badge (top-right)
        right = tk.Frame(topbar, bg=WHITE)
        right.pack(side="right", fill="y", padx=20)
        tk.Label(right, text="Welcome, ", bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 10)).pack(side="left")
        tk.Label(right, text=self.name or "Mayor", bg=WHITE, fg=DARK,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Label(right, text=" MAYOR ", bg=PURPLE, fg=WHITE,
                 font=("Segoe UI", 9, "bold"),
                 padx=10, pady=3).pack(side="left", padx=(12,0))

        # ── Content area ──────────────────────────────────────────────────────
        self._content_area = tk.Frame(self._inner, bg=BG)
        self._content_area.pack(fill="both", expand=True)

        self._render()

    # =========================================================================
    #  SIDEBAR  (identical style to MayorDashboard)
    # =========================================================================
    def _build_sidebar(self, s):
        # Gradient header
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
            is_active = (label == "Scholar Records")
            btn = tk.Button(
                nav_frame, text=f"  {label}", anchor="w",
                bg=NAV_ACTIVE if is_active else SIDEBAR_DARK,
                fg=WHITE      if is_active else SIDEBAR_TEXT,
                activebackground=NAV_HOVER, activeforeground=DARK,
                relief="flat", bd=0,
                font=("Segoe UI", 10),
                padx=18, pady=10, cursor="hand2")
            btn.pack(fill="x", padx=10, pady=3)
            if not is_active:
                btn.bind("<Enter>",
                         lambda e, b=btn: b.config(bg=NAV_HOVER)
                         if b["bg"] != NAV_ACTIVE else None)
                btn.bind("<Leave>",
                         lambda e, b=btn: b.config(bg=SIDEBAR_DARK)
                         if b["bg"] == NAV_HOVER else None)
            self._nav_btns[label] = btn
            btn.config(command=lambda c=cmd, b=btn: self._nav(c, b))

        tk.Frame(nav_frame, bg=SIDEBAR_LINE, height=1).pack(
            fill="x", padx=10, pady=(8, 8))

        ren_btn = tk.Button(
            nav_frame, text="  Renewal Settings", anchor="w",
            bg=SIDEBAR_DARK, fg=SIDEBAR_TEXT,
            activebackground=NAV_HOVER, activeforeground=DARK,
            relief="flat", bd=0,
            font=("Segoe UI", 10),
            padx=18, pady=10, cursor="hand2",
            command=lambda: self._nav(self._go_renewal, ren_btn))
        ren_btn.pack(fill="x", padx=10, pady=3)
        ren_btn.bind("<Enter>",
                     lambda e: ren_btn.config(bg=NAV_HOVER)
                     if ren_btn["bg"] != NAV_ACTIVE else None)
        ren_btn.bind("<Leave>",
                     lambda e: ren_btn.config(bg=SIDEBAR_DARK)
                     if ren_btn["bg"] == NAV_HOVER else None)
        self._nav_btns["Renewal Settings"] = ren_btn

        # Spacer + logout
        tk.Frame(s, bg=SIDEBAR_DARK).pack(fill="both", expand=True)
        tk.Frame(s, bg=SIDEBAR_LINE, height=1).pack(
            fill="x", padx=18, pady=(12, 6))

        lo = tk.Button(s, text="  Log Out", anchor="w",
                       bg=SIDEBAR_DARK, fg="#E53E3E",
                       activebackground="#742A2A", activeforeground=WHITE,
                       relief="flat", bd=0,
                       font=("Segoe UI", 10),
                       padx=18, pady=10, cursor="hand2",
                       command=self._logout)
        lo.pack(fill="x", padx=10, pady=(0,14))
        lo.bind("<Enter>", lambda e: lo.config(bg="#742A2A", fg=WHITE))
        lo.bind("<Leave>", lambda e: lo.config(bg=SIDEBAR_DARK, fg="#E53E3E"))

    def _draw_sidebar_header(self, c):
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        steps = 44
        for i in range(steps):
            t = i / steps
            r = int(0x66 + (0x76-0x66)*t)
            g = int(0x7E + (0x4B-0x7E)*t)
            b = int(0xEA + (0xA2-0xEA)*t)
            c.create_rectangle(0, i*h//steps, w, (i+1)*h//steps,
                                fill=f"#{r:02x}{g:02x}{b:02x}", outline="")
        cx, cy, r = w//2, 58, 30
        logo = get_logo(r * 2)
        if logo:
            if not hasattr(self, "_logo_photo"):
                self._logo_photo = logo
            c.create_image(cx, cy, image=self._logo_photo)
        else:
            c.create_oval(cx-r, cy-r, cx+r, cy+r, fill=WHITE, outline="")
            c.create_text(cx, cy, text="MJS",
                          fill=PURPLE, font=("Segoe UI", 14, "bold"))
        c.create_text(cx, cy+r+18,
                      text=self.name or "Mayor", fill=WHITE,
                      font=("Segoe UI", 11, "bold"))
        c.create_text(cx, cy+r+35, text="Mayor Panel",
                      fill="#DDE3FF", font=("Segoe UI", 8))

    def _nav(self, page_fn, btn):
        for b in self._nav_btns.values():
            b.config(bg=SIDEBAR_DARK, fg=SIDEBAR_TEXT)
        btn.config(bg=NAV_ACTIVE, fg=WHITE)
        page_fn()

    # ── Sidebar navigation ────────────────────────────────────────────────────
    def _go_dashboard(self):
        if self.app:
            self.app.show_mayor_dashboard()

    def _go_records(self):
        pass   # already here

    def _go_renewal(self):
        if self.app:
            self.app.show_mayor_renewal_settings()

    def _logout(self):
        if messagebox.askyesno("Log Out", "Are you sure you want to log out?"):
            if self.app:
                self.app.logout()

    # =========================================================================
    #  FULL RE-RENDER
    # =========================================================================
    def _render(self):
        for w in self._content_area.winfo_children():
            w.destroy()
        self._main_canvas.yview_moveto(0)

        wrap = tk.Frame(self._content_area, bg=BG)
        wrap.pack(fill="both", expand=True, padx=28, pady=(20,32))

        if self._flash:
            self._build_flash(wrap, *self._flash)
            self._flash = None

        self._build_stat_cards(wrap)
        self._build_section_tabs(wrap)
        if not self._show_archived:
            self._build_filter_tabs(wrap)
        self._build_records_card(wrap)

    # ── Flash banner ──────────────────────────────────────────────────────────
    def _build_flash(self, parent, kind, msg):
        bg = SUCCESS_BG if kind == "success" else ERROR_BG
        fg = SUCCESS_FG if kind == "success" else ERROR_FG
        br = SUCCESS_BR if kind == "success" else ERROR_BR
        row = tk.Frame(parent, bg=bg,
                       highlightbackground=br, highlightthickness=1)
        row.pack(fill="x", pady=(0,14))
        tk.Frame(row, bg=br, width=4).pack(side="left", fill="y")
        tk.Label(row, text=msg, bg=bg, fg=fg,
                 font=("Segoe UI", 10, "bold"),
                 anchor="w", padx=14, pady=10).pack(side="left")

    # =========================================================================
    #  STAT CARDS
    # =========================================================================
    def _build_stat_cards(self, parent):
        grid = tk.Frame(parent, bg=BG)
        grid.pack(fill="x", pady=(0,18))

        total    = len(self._apps) + len(self._renewals)
        approved = (_count(self._apps,    "status","approved") +
                    _count(self._renewals,"status","Approved"))
        pending  = (_count(self._apps,    "status","pending") +
                    _count(self._renewals,"status","Pending"))
        rejected = (_count(self._apps,    "status","rejected") +
                    _count(self._renewals,"status","Rejected"))

        for col, (label, val, colour) in enumerate([
            ("Total",    total,    PURPLE),
            ("Approved", approved, REC_APPROVED),
            ("Pending",  pending,  REC_PENDING),
            ("Rejected", rejected, REC_REJECTED),
        ]):
            card = tk.Frame(grid, bg=WHITE,
                            highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=0, column=col, sticky="nsew",
                      padx=(0 if col==0 else 12, 0), ipadx=12, ipady=14)
            grid.columnconfigure(col, weight=1)
            tk.Label(card, text=str(val), bg=WHITE, fg=colour,
                     font=("Segoe UI", 28, "bold")).pack(pady=(14,2))
            tk.Label(card, text=label, bg=WHITE, fg=GRAY,
                     font=("Segoe UI", 10)).pack(pady=(0,14))

    # =========================================================================
    #  SECTION TABS
    # =========================================================================
    def _build_section_tabs(self, parent):
        bar = tk.Frame(parent, bg=WHITE,
                       highlightbackground=BORDER, highlightthickness=1)
        bar.pack(fill="x", pady=(0,10))
        inner = tk.Frame(bar, bg=WHITE)
        inner.pack(side="left", padx=14, pady=8)

        for label, sec, arch in [
            ("Active Applications",   "applications", False),
            ("Renewal Applications",  "renewals",     False),
            ("Archived Applications", "applications", True),
        ]:
            active = (sec == self._section and arch == self._show_archived)
            bg = PURPLE if active else WHITE
            fg = WHITE  if active else "#666666"
            lbl = tk.Label(inner, text=label, bg=bg, fg=fg,
                           font=("Segoe UI", 9, "bold"),
                           padx=16, pady=8, cursor="hand2",
                           relief="solid", bd=1)
            lbl.pack(side="left", padx=(0,8))
            lbl.bind("<Button-1>",
                     lambda e, s=sec, a=arch: self._switch_section(s, a))
            if not active:
                lbl.bind("<Enter>",
                         lambda e, l=lbl: l.config(bg=NAV_HOVER))
                lbl.bind("<Leave>",
                         lambda e, l=lbl: l.config(bg=WHITE))

    # =========================================================================
    #  FILTER TABS
    # =========================================================================
    def _build_filter_tabs(self, parent):
        bar = tk.Frame(parent, bg=WHITE,
                       highlightbackground=BORDER, highlightthickness=1)
        bar.pack(fill="x", pady=(0,16))
        inner = tk.Frame(bar, bg=WHITE)
        inner.pack(side="left", padx=14, pady=8)

        for label, val in [("All","all"),("Approved","approved"),
                           ("Pending","pending"),("Rejected","rejected")]:
            active = (self._status_filter == val)
            bg = PURPLE if active else WHITE
            fg = WHITE  if active else "#666666"
            lbl = tk.Label(inner, text=label, bg=bg, fg=fg,
                           font=("Segoe UI", 9, "bold"),
                           padx=16, pady=8, cursor="hand2",
                           relief="solid", bd=1)
            lbl.pack(side="left", padx=(0,8))
            lbl.bind("<Button-1>", lambda e, v=val: self._set_filter(v))
            if not active:
                lbl.bind("<Enter>",
                         lambda e, l=lbl: l.config(bg=NAV_HOVER))
                lbl.bind("<Leave>",
                         lambda e, l=lbl: l.config(bg=WHITE))

    # =========================================================================
    #  RECORDS CARD
    # =========================================================================
    def _build_records_card(self, parent):
        card = tk.Frame(parent, bg=WHITE,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True)
        inner = tk.Frame(card, bg=WHITE)
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        # Header row
        hdr = tk.Frame(inner, bg=WHITE)
        hdr.pack(fill="x", pady=(0,12))
        title = ("Renewal Applications" if self._section == "renewals"
                 else "Scholarship Applications")
        tk.Label(hdr, text=title, bg=WHITE, fg=DARK,
                 font=("Segoe UI", 13, "bold")).pack(side="left")

        # Search box
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())
        sw = tk.Frame(hdr, bg=WHITE,
                      highlightbackground=BORDER, highlightthickness=1)
        sw.pack(side="right")
        tk.Label(sw, text="🔍", bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 10)).pack(side="left", padx=(10,0))
        tk.Entry(sw, textvariable=self._search_var,
                 bg=WHITE, fg=DARK, relief="flat",
                 font=("Segoe UI", 10), width=22,
                 insertbackground=DARK
                 ).pack(side="left", ipady=6, padx=(4,10))

        # Table
        self._build_treeview(inner)

        # Separator + pagination
        tk.Frame(inner, bg=BORDER2, height=1).pack(fill="x")
        self._pag_frame = tk.Frame(inner, bg=WHITE)
        self._pag_frame.pack(fill="x", pady=(10,0))

        self._refresh_table()

    # =========================================================================
    #  TREEVIEW
    # =========================================================================
    def _build_treeview(self, parent):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Rec.Treeview",
                        background=WHITE, foreground=DARK,
                        rowheight=40, fieldbackground=WHITE,
                        font=("Segoe UI", 10), borderwidth=0, relief="flat")
        style.configure("Rec.Treeview.Heading",
                        background=HEADER_BG, foreground=MUTED2,
                        font=("Segoe UI", 8, "bold"),
                        relief="flat", borderwidth=0, padding=(8,10))
        style.map("Rec.Treeview",
                  background=[("selected","#EEF0FF")],
                  foreground=[("selected", DARK)])
        style.map("Rec.Treeview.Heading",
                  background=[("active", HEADER_BG)])
        style.layout("Rec.Treeview",
                     [("Treeview.treearea", {"sticky":"nswe"})])

        if self._section == "renewals":
            cols   = ("renewal_id","name","course","year_level",
                      "gwa","status","submitted")
            labels = ("RENEWAL ID","NAME","COURSE","YEAR LEVEL",
                      "GWA","STATUS","SUBMITTED")
            widths = (90,175,165,90,65,100,130)
        else:
            cols   = ("app_id","name","school","course",
                      "year_level","status","submitted")
            labels = ("APP ID","NAME","SCHOOL","COURSE",
                      "YEAR LEVEL","STATUS","SUBMITTED")
            widths = (70,165,115,155,80,100,140)

        self._cols = cols
        all_cols   = (*cols, "actions")

        wrap = tk.Frame(parent, bg=WHITE)
        wrap.pack(fill="both", expand=True)

        xbar = ttk.Scrollbar(wrap, orient="horizontal")
        xbar.pack(side="bottom", fill="x")

        self._tree = ttk.Treeview(wrap, columns=all_cols,
                                  show="headings", style="Rec.Treeview",
                                  xscrollcommand=xbar.set,
                                  selectmode="browse", height=14)
        xbar.config(command=self._tree.xview)
        self._tree.pack(fill="both", expand=True)

        for col, lbl, w in zip(cols, labels, widths):
            self._tree.heading(col, text=lbl,
                               command=lambda c=col: self._on_sort(c))
            self._tree.column(col, width=w, minwidth=50,
                              anchor="w", stretch=False)

        self._tree.heading("actions", text="ACTIONS")
        self._tree.column("actions", width=170, minwidth=140,
                          anchor="center", stretch=False)

        self._tree.tag_configure("even",     background=WHITE)
        self._tree.tag_configure("odd",      background="#F8FAFC")

        self._tree.bind("<Double-1>",        self._on_double_click)
        self._tree.bind("<ButtonRelease-1>", self._on_tree_click)
        self._tree.bind("<Configure>",       lambda e: self._draw_action_btns())
        self._tree.bind("<<TreeviewSelect>>", lambda e: self._draw_action_btns())
        self._overlay_frame = tk.Frame(wrap, bg=WHITE)
        self._overlay_frame.place(x=0, y=0)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")

    # =========================================================================
    #  DATA HELPERS
    # =========================================================================
    def _source(self):
        if self._section == "renewals":
            return [r for r in self._renewals if r["archived"] == 0]
        if self._show_archived:
            return [r for r in self._apps if r["archived"] == 1]
        return [r for r in self._apps if r["archived"] == 0]

    def _filtered_rows(self):
        rows = self._source()
        q = (self._search_var.get().strip().lower()
             if self._search_var else "")

        if not self._show_archived and self._section != "renewals":
            if self._status_filter != "all":
                rows = [r for r in rows
                        if r.get("status","").lower() == self._status_filter]
        if q:
            rows = [r for r in rows
                    if q in " ".join(str(v) for v in r.values()).lower()]
        if self._sort_col:
            db_key = {
                "app_id":"application_id","renewal_id":"renewal_id",
                "name":"first_name","school":"school_name",
                "course":"course","year_level":"year_level",
                "gwa":"gwa","status":"status",
                "submitted":"submission_date",
            }.get(self._sort_col, self._sort_col)
            rows = sorted(rows,
                          key=lambda r: str(r.get(db_key,"")).lower(),
                          reverse=not self._sort_asc)
        return rows

    @property
    def _total_pages(self):
        return max(1, math.ceil(len(self._filtered_rows()) / ROWS_PER_PAGE))

    def _page_rows(self):
        rows  = self._filtered_rows()
        start = (self._current_page - 1) * ROWS_PER_PAGE
        return rows[start: start + ROWS_PER_PAGE]

    # =========================================================================
    #  REFRESH TABLE
    # =========================================================================
    def _refresh_table(self):
        for iid in self._tree.get_children():
            self._tree.delete(iid)

        arch_lbl = "Unarchive" if self._show_archived else "Archive"

        for i, r in enumerate(self._page_rows()):
            name   = " ".join(filter(None,[r.get("first_name"),
                                           r.get("middle_name"),
                                           r.get("last_name")]))
            status = r.get("status","N/A")
            s_disp = f"  {status.upper()}  "

            if self._section == "renewals":
                vals = (r["renewal_id"], name,
                        r.get("course",""), r.get("year_level",""),
                        r.get("gwa",""), s_disp,
                        r.get("submission_date",""),
                        f"View   {arch_lbl}")
            else:
                vals = (r.get("application_id",""), name,
                        r.get("school_name",""), r.get("course",""),
                        r.get("year_level",""), s_disp,
                        r.get("submission_date",""),
                        f"View   {arch_lbl}")

            row_tag = "even" if i % 2 == 0 else "odd"
            self._tree.insert("", "end", iid=str(i),
                              values=vals, tags=(row_tag,))

        # Sort arrows
        for col in (*self._cols, "actions"):
            base   = self._tree.heading(col)["text"].rstrip(" ▲▼")
            suffix = (" ▲" if self._sort_asc else " ▼") \
                     if col == self._sort_col else ""
            self._tree.heading(col, text=base + suffix)

        self._build_pagination()
        self._tree.after(10, self._draw_action_btns)

    # ── Overlay action buttons ────────────────────────────────────────────────
    def _draw_action_btns(self):
        if not self._overlay_frame.winfo_exists():
            return
        for w in self._overlay_frame.winfo_children():
            w.destroy()

        arch_lbl = "Unarchive" if self._show_archived else "Archive"
        rows     = self._page_rows()

        for i, r in enumerate(rows):
            iid  = str(i)
            bbox = self._tree.bbox(iid, "actions")
            if not bbox:
                continue
            x, y, w, h = bbox
            rtype  = "renewal" if self._section == "renewals" else "application"

            # ── View button (purple gradient look) ────────────────────────────
            view_btn = tk.Button(
                self._overlay_frame,
                text="View",
                bg=PURPLE, fg=WHITE,
                font=("Segoe UI", 8, "bold"),
                relief="flat", bd=0,
                padx=10, pady=3,
                cursor="hand2",
                activebackground=PURPLE2, activeforeground=WHITE,
                command=lambda rec=r, rt=rtype: self._open_modal(rec, rt))
            view_btn.place(x=x + 6, y=y + (h - 24) // 2, width=60, height=24)

            # ── Archive/Unarchive button (orange) ─────────────────────────────
            arch_btn = tk.Button(
                self._overlay_frame,
                text=arch_lbl,
                bg=REC_ARCHIVE, fg=WHITE,
                font=("Segoe UI", 8, "bold"),
                relief="flat", bd=0,
                padx=10, pady=3,
                cursor="hand2",
                activebackground=REC_ARCHIVE_H, activeforeground=WHITE,
                command=lambda rec=r, rt=rtype: self._do_action(
                    rec, rt, "unarchive" if self._show_archived else "archive"))
            arch_btn.place(x=x + 74, y=y + (h - 24) // 2, width=84, height=24)

    # ── Action column click ───────────────────────────────────────────────────
    def _on_tree_click(self, event):
        col = self._tree.identify_column(event.x)
        iid = self._tree.identify_row(event.y)
        if not iid:
            return
        actions_col = f"#{len(self._cols)+1}"
        if col != actions_col:
            return
        idx  = int(iid)
        rows = self._page_rows()
        if idx >= len(rows):
            return
        record = rows[idx]
        rtype  = "renewal" if self._section == "renewals" else "application"
        bbox   = self._tree.bbox(iid, "actions")
        if not bbox:
            return
        rel_x = event.x - bbox[0]
        if rel_x < bbox[2] * 0.42:
            self._open_modal(record, rtype)
        else:
            self._do_action(record, rtype,
                            "unarchive" if self._show_archived else "archive")

    def _on_double_click(self, event):
        iid = self._tree.focus()
        if not iid:
            return
        idx  = int(iid)
        rows = self._page_rows()
        if idx >= len(rows):
            return
        rtype = "renewal" if self._section == "renewals" else "application"
        self._open_modal(rows[idx], rtype)

    # =========================================================================
    #  PAGINATION
    # =========================================================================
    def _build_pagination(self):
        for w in self._pag_frame.winfo_children():
            w.destroy()

        total = len(self._filtered_rows())
        cp    = self._current_page
        start = (cp-1)*ROWS_PER_PAGE + 1 if total else 0
        end   = min(cp*ROWS_PER_PAGE, total)
        tp    = self._total_pages

        tk.Label(self._pag_frame,
                 text=f"Showing {start} to {end} of {total} entries",
                 bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 9)).pack(side="left", pady=6)

        nav = tk.Frame(self._pag_frame, bg=WHITE)
        nav.pack(side="right")

        def _nbtn(text, cmd=None, active=False, disabled=False):
            bg  = PURPLE    if active  else ("#E5E7EB" if disabled else WHITE)
            fg  = WHITE     if active  else (GRAY if disabled else PURPLE)
            b   = tk.Label(nav, text=text, bg=bg, fg=fg,
                           font=("Segoe UI", 9, "bold"),
                           padx=10, pady=5,
                           relief="solid", bd=1,
                           cursor="" if disabled else "hand2")
            b.pack(side="left", padx=2)
            if not disabled and cmd:
                b.bind("<Button-1>", lambda e: cmd())
                if not active:
                    b.bind("<Enter>",
                           lambda e, btn=b: btn.config(bg=NAV_HOVER))
                    b.bind("<Leave>",
                           lambda e, btn=b, orig=bg: btn.config(bg=orig))

        _nbtn("Previous", lambda: self._go_page(cp-1), disabled=(cp<=1))
        for p in range(max(1,cp-2), min(tp+1,cp+3)):
            _nbtn(str(p),
                  (lambda pg=p: self._go_page(pg)) if p!=cp else None,
                  active=(p==cp))
        _nbtn("Next", lambda: self._go_page(cp+1), disabled=(cp>=tp))

    # =========================================================================
    #  DETAIL MODAL
    # =========================================================================
    def _open_modal(self, record, rtype):
        root = self.winfo_toplevel()
        dlg  = tk.Toplevel(root)
        dlg.title("Record Details")
        dlg.configure(bg=WHITE)
        dlg.grab_set()
        dlg.resizable(True, True)

        root.update_idletasks()
        w, h = 700, 700
        px = root.winfo_x() + (root.winfo_width()  - w)//2
        py = root.winfo_y() + (root.winfo_height() - h)//2
        dlg.geometry(f"{w}x{h}+{px}+{py}")

        # Header
        hdr = tk.Frame(dlg, bg=WHITE)
        hdr.pack(fill="x", padx=28, pady=(22,0))
        full_name = " ".join(filter(None,[record.get("first_name"),
                                          record.get("middle_name"),
                                          record.get("last_name")]))
        tk.Label(hdr, text=f"Record Details — {full_name}",
                 bg=WHITE, fg=DARK,
                 font=("Segoe UI", 15, "bold")).pack(side="left")
        tk.Button(hdr, text="×", bg=WHITE, fg=GRAY,
                  font=("Segoe UI", 18), relief="flat", bd=0,
                  cursor="hand2", command=dlg.destroy).pack(side="right")
        tk.Frame(dlg, bg=BORDER, height=1).pack(fill="x", pady=10)

        # Scrollable body
        bo  = tk.Frame(dlg, bg=WHITE)
        bo.pack(fill="both", expand=True)
        bc  = tk.Canvas(bo, bg=WHITE, highlightthickness=0)
        bvb = ttk.Scrollbar(bo, orient="vertical", command=bc.yview)
        bc.configure(yscrollcommand=bvb.set)
        bvb.pack(side="right", fill="y")
        bc.pack(side="left", fill="both", expand=True)
        body = tk.Frame(bc, bg=WHITE)
        bwin = bc.create_window((0,0), window=body, anchor="nw")
        body.bind("<Configure>",
                  lambda e: bc.configure(scrollregion=bc.bbox("all")))
        bc.bind("<Configure>",
                lambda e: bc.itemconfig(bwin, width=e.width))

        def _field(label, value):
            f = tk.Frame(body, bg=WHITE)
            f.pack(fill="x", padx=28, pady=(0,10))
            tk.Label(f, text=label, bg=WHITE, fg=GRAY,
                     font=("Segoe UI", 8, "bold"),
                     anchor="w").pack(fill="x")
            tk.Label(f, text=value or "—", bg=WHITE, fg=DARK,
                     font=("Segoe UI", 10), anchor="w",
                     wraplength=600, justify="left").pack(fill="x", pady=(1,0))
            tk.Frame(f, bg=BORDER, height=1).pack(fill="x", pady=(6,0))

        id_label  = "Renewal ID" if rtype=="renewal" else "Application ID"
        record_id = record.get("renewal_id" if rtype=="renewal"
                               else "application_id","?")
        status    = record.get("status","N/A")
        sch_type  = (record.get("scholarship_type","New").capitalize()
                     if rtype=="application" else "Renewal")
        loc = " / ".join(filter(None,[record.get("municipality"),
                                      record.get("baranggay")])) or "—"

        _field(id_label,              f"#{record_id}")
        _field("Full Name",           full_name)
        _field("Student ID",          record.get("student_id"))
        _field("Email Address",       record.get("email"))
        _field("Contact Number",      record.get("contact_number"))
        _field("Address",             record.get("address"))
        _field("Municipality / Brgy", loc)
        if rtype == "application":
            _field("School",          record.get("school_name"))
        _field("Course",              record.get("course"))
        _field("Year Level",          record.get("year_level"))
        _field("GWA",                 record.get("gwa"))
        _field("Application Type",    sch_type)
        # Status with colour
        sf = tk.Frame(body, bg=WHITE)
        sf.pack(fill="x", padx=28, pady=(0,10))
        tk.Label(sf, text="Status", bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x")
        s_lower = status.lower()
        s_color = REC_APPROVED if "approved" in s_lower else \
                  REC_PENDING  if "pending"  in s_lower else \
                  REC_REJECTED if "rejected" in s_lower else DARK
        tk.Label(sf, text=status or "—", bg=WHITE, fg=s_color,
                 font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x", pady=(1,0))
        tk.Frame(sf, bg=BORDER, height=1).pack(fill="x", pady=(6,0))
        _field("Submission Date",     record.get("submission_date"))

        # Reason box
        f = tk.Frame(body, bg=WHITE)
        f.pack(fill="x", padx=28, pady=(0,10))
        tk.Label(f, text="Reason", bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x")
        rb = tk.Frame(f, bg="#F7F7F7",
                      highlightbackground=BORDER, highlightthickness=1)
        rb.pack(fill="x", pady=(4,0))
        tk.Label(rb, text=record.get("reason") or "—",
                 bg="#F7F7F7", fg=DARK,
                 font=("Segoe UI", 10), anchor="w",
                 wraplength=560, justify="left",
                 padx=12, pady=10).pack(fill="x")
        tk.Frame(body, bg=WHITE, height=16).pack()

        # Action buttons
        tk.Frame(dlg, bg=BORDER, height=1).pack(fill="x")
        acts = tk.Frame(dlg, bg=WHITE)
        acts.pack(fill="x", padx=28, pady=14)

        s = status.lower()

        def _abtn(text, bg, hov, cmd):
            b = tk.Button(acts, text=text, bg=bg, fg=WHITE,
                          font=("Segoe UI", 10, "bold"),
                          relief="flat", padx=14, pady=7,
                          cursor="hand2",
                          activebackground=hov, activeforeground=WHITE,
                          command=cmd)
            b.pack(side="left", padx=(0,8))

        if s != "approved":
            _abtn("✓  Approve", REC_APPROVED, "#15803D",
                  lambda: self._do_action(record, rtype, "approve", dlg))
        if s != "rejected":
            _abtn("✕  Reject", REC_REJECTED, "#B91C1C",
                  lambda: self._do_action(record, rtype, "reject", dlg))

        arch_label = "Unarchive" if self._show_archived else "Archive"
        arch_act   = "unarchive" if self._show_archived else "archive"
        _abtn(f"🗄  {arch_label}", REC_ARCHIVE, REC_ARCHIVE_H,
              lambda: self._do_action(record, rtype, arch_act, dlg))

        _abtn("📄  Documents", PURPLE2, "#5a3780",
              lambda: self._open_docs_viewer(record, rtype))

        tk.Button(acts, text="Close", bg="#E5E7EB", fg=DARK,
                  font=("Segoe UI", 10), relief="flat",
                  padx=14, pady=6, cursor="hand2",
                  activebackground="#D1D5DB",
                  command=dlg.destroy).pack(side="right")

    # =========================================================================
    #  DOCUMENTS VIEWER
    # =========================================================================
    def _open_docs_viewer(self, record, rtype):
        """Open a window showing all attached documents for the application."""
        # Fetch blobs from DB
        if fetch_one is None:
            messagebox.showerror("Error", "Database not connected.")
            return

        if rtype == "renewal":
            app_id = record.get("application_id")
        else:
            app_id = record.get("application_id")

        row = fetch_one("""
            SELECT doc_school_id, doc_id_picture, doc_birth_cert,
                   doc_grades, doc_cor
            FROM applications WHERE application_id = %s
        """, (app_id,))

        doc_labels = [
            ("School ID",        row.get("doc_school_id")   if row else None),
            ("ID Picture",       row.get("doc_id_picture")  if row else None),
            ("Birth Certificate",row.get("doc_birth_cert")  if row else None),
            ("Grades",           row.get("doc_grades")      if row else None),
            ("Certificate of Registration", row.get("doc_cor") if row else None),
        ]

        root = self.winfo_toplevel()
        dlg  = tk.Toplevel(root)
        full_name = " ".join(filter(None, [record.get("first_name"),
                                           record.get("middle_name"),
                                           record.get("last_name")]))
        dlg.title(f"Documents — {full_name}")
        dlg.configure(bg=WHITE)
        dlg.grab_set()
        dlg.resizable(True, True)
        root.update_idletasks()
        w, h = 780, 600
        px = root.winfo_x() + (root.winfo_width()  - w) // 2
        py = root.winfo_y() + (root.winfo_height() - h) // 2
        dlg.geometry(f"{w}x{h}+{px}+{py}")

        # Header
        hdr = tk.Frame(dlg, bg=WHITE)
        hdr.pack(fill="x", padx=24, pady=(18, 0))
        tk.Label(hdr, text=f"Attached Documents — {full_name}",
                 bg=WHITE, fg=DARK,
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        tk.Button(hdr, text="×", bg=WHITE, fg=GRAY,
                  font=("Segoe UI", 18), relief="flat", bd=0,
                  cursor="hand2", command=dlg.destroy).pack(side="right")
        tk.Frame(dlg, bg=BORDER, height=1).pack(fill="x", pady=10)

        # Scrollable grid
        outer = tk.Frame(dlg, bg=WHITE)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=WHITE, highlightthickness=0)
        vsb    = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        grid_frame = tk.Frame(canvas, bg=WHITE)
        win_id = canvas.create_window((0, 0), window=grid_frame, anchor="nw")
        grid_frame.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

        self._doc_images = []   # keep references alive

        col, row_idx = 0, 0
        for label, blob in doc_labels:
            cell = tk.Frame(grid_frame, bg=WHITE,
                            highlightbackground=BORDER, highlightthickness=1)
            cell.grid(row=row_idx, column=col, padx=14, pady=14, sticky="nsew")
            grid_frame.columnconfigure(col, weight=1)

            tk.Label(cell, text=label, bg=WHITE, fg=DARK,
                     font=("Segoe UI", 9, "bold"),
                     anchor="w", padx=10, pady=6).pack(fill="x")
            tk.Frame(cell, bg=BORDER, height=1).pack(fill="x")

            if blob:
                try:
                    img  = Image.open(io.BytesIO(blob))
                    img.thumbnail((320, 240))
                    photo = ImageTk.PhotoImage(img)
                    self._doc_images.append(photo)
                    thumb = tk.Label(cell, image=photo, bg=WHITE,
                                     cursor="hand2")
                    thumb.pack(padx=10, pady=10)
                    # Click to view full size
                    thumb.bind("<Button-1>",
                               lambda e, b=blob, lbl=label:
                               self._view_full_image(b, lbl))
                    tk.Label(cell, text="Click to view full size",
                             bg=WHITE, fg=GRAY,
                             font=("Segoe UI", 8)).pack(pady=(0, 8))
                except Exception:
                    # Not an image — show download-style label
                    tk.Label(cell, text="📎 File attached (not an image)",
                             bg=WHITE, fg=PURPLE,
                             font=("Segoe UI", 9),
                             padx=10, pady=20).pack()
            else:
                tk.Label(cell, text="No document uploaded",
                         bg=WHITE, fg=GRAY,
                         font=("Segoe UI", 9, "italic"),
                         padx=10, pady=20).pack()

            col += 1
            if col >= 2:
                col = 0
                row_idx += 1

        # Close button
        tk.Frame(dlg, bg=BORDER, height=1).pack(fill="x")
        tk.Button(dlg, text="Close", bg="#E5E7EB", fg=DARK,
                  font=("Segoe UI", 10), relief="flat",
                  padx=14, pady=7, cursor="hand2",
                  activebackground="#D1D5DB",
                  command=dlg.destroy).pack(anchor="e", padx=24, pady=12)

    def _view_full_image(self, blob, title):
        """Open a full-size image in a new window."""
        try:
            img   = Image.open(io.BytesIO(blob))
            root  = self.winfo_toplevel()
            win   = tk.Toplevel(root)
            win.title(title)
            win.configure(bg=WHITE)
            win.resizable(True, True)
            root.update_idletasks()
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            max_w, max_h = int(sw * 0.85), int(sh * 0.85)
            img.thumbnail((max_w, max_h))
            photo = ImageTk.PhotoImage(img)
            self._doc_images.append(photo)
            tk.Label(win, image=photo, bg=WHITE).pack(padx=10, pady=10)
            tk.Button(win, text="Close", bg="#E5E7EB", fg=DARK,
                      font=("Segoe UI", 10), relief="flat",
                      padx=14, pady=6, cursor="hand2",
                      command=win.destroy).pack(pady=(0, 10))
        except Exception as ex:
            messagebox.showerror("Error", f"Cannot display image:\n{ex}")

    # =========================================================================
    #  ACTIONS
    # =========================================================================
    def _do_action(self, record, rtype, action, dlg=None):
        if dlg:
            dlg.destroy()
        id_key = "renewal_id" if rtype == "renewal" else "application_id"
        rid    = record[id_key]
        msgs   = {
            "approve":   "Application approved successfully.",
            "reject":    "Application rejected.",
            "archive":   "Record archived.",
            "unarchive": "Record restored from archive.",
        }
        # ── Persist to DB ─────────────────────────────────────────────────────
        if execute:
            if action == "approve" and rtype == "renewal":
                execute("UPDATE renewals SET status='approved' WHERE renewal_id=%s", (rid,))
            elif action == "reject" and rtype == "renewal":
                execute("UPDATE renewals SET status='rejected' WHERE renewal_id=%s", (rid,))
            elif action == "approve":
                execute("UPDATE applications SET status='approved' WHERE application_id=%s", (rid,))
            elif action == "reject":
                execute("UPDATE applications SET status='rejected' WHERE application_id=%s", (rid,))
        # ── Reload from DB ────────────────────────────────────────────────────
        self._apps     = _load_apps()
        self._renewals = _load_renewals()
        self._flash        = ("success", "✅  " + msgs[action])
        self._current_page = 1
        self._render()

    # =========================================================================
    #  EVENTS
    # =========================================================================
    def _on_search(self):
        self._current_page = 1
        self._refresh_table()

    def _on_sort(self, col):
        if col == "actions": return
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self._current_page = 1
        self._refresh_table()

    def _switch_section(self, sec, archived):
        self._section       = sec
        self._show_archived = archived
        self._status_filter = "all"
        self._sort_col      = None
        self._current_page  = 1
        self._render()

    def _set_filter(self, val):
        self._status_filter = val
        self._current_page  = 1
        self._render()

    def _go_page(self, page):
        self._current_page = max(1, min(page, self._total_pages))
        self._refresh_table()


# =============================================================================
#  STANDALONE TEST
# =============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Scholar Records — test")
    root.geometry("1350x820")
    try: root.state("zoomed")
    except Exception: pass
    RecordsFrame(root, name="Mayor Juan Santos",
                 email="mayor@example.com").pack(fill="both", expand=True)
    root.mainloop()