import tkinter as tk
from tkinter import messagebox, ttk
import threading

try:
    from db import fetch_all, execute
except ImportError:
    fetch_all = execute = None

BG      = "#EDE4FF"
WHITE   = "#FFFFFF"
PURPLE  = "#5B4AC7"
PURPLE2 = "#7A5AF5"
GREEN   = "#48BB78"
RED     = "#E53E3E"
ORANGE  = "#FFA500"
BORDER  = "#E0E0E0"
TEXT    = "#2D3748"
GRAY    = "#718096"


class PendingScholarsFrame(tk.Frame):
    def __init__(self, parent, name, email, app, **_):
        super().__init__(parent, bg=BG)
        self.name  = name
        self.email = email
        self.app   = app
        self._apps = []
        self._filter = "All"
        self._search = ""
        self._build()
        threading.Thread(target=self._fetch, daemon=True).start()

    # ── Build UI ───────────────────────────────────────────────────────────────
    def _build(self):
        # Top bar
        top = tk.Frame(self, bg=WHITE,
                       highlightbackground=BORDER, highlightthickness=1)
        top.pack(fill="x")
        tk.Button(top, text="← Back",
                  bg=WHITE, fg=PURPLE,
                  relief="flat", bd=0,
                  font=("Helvetica", 11),
                  cursor="hand2",
                  command=self.app.show_mayor_dashboard).pack(side="left", padx=16, pady=10)
        tk.Label(top, text="⏳ Pending Applications",
                 bg=WHITE, fg=PURPLE,
                 font=("Helvetica", 15, "bold")).pack(side="left")
        tk.Button(top, text="⬆ Sort by Priority",
                  bg=BG, fg=PURPLE,
                  relief="flat", bd=1,
                  font=("Helvetica", 10),
                  cursor="hand2",
                  command=self._sort_priority).pack(side="right", padx=16, pady=10)

        # Stats banner
        self._banner = tk.Frame(self, bg=ORANGE)
        self._banner.pack(fill="x", padx=20, pady=12)
        tk.Label(self._banner, text="⏳ Pending Review",
                 bg=ORANGE, fg=WHITE,
                 font=("Helvetica", 14, "bold"),
                 padx=16, pady=8, anchor="w").pack(fill="x")
        tk.Label(self._banner,
                 text="Applications awaiting your review",
                 bg=ORANGE, fg="#FFF9C4",
                 font=("Helvetica", 9),
                 padx=16, anchor="w").pack(fill="x")

        self._stat_row = tk.Frame(self._banner, bg=ORANGE)
        self._stat_row.pack(fill="x", padx=16, pady=(8, 12))
        self._stat_labels = {}
        for key, label in [("total","Total"),("new","New"),
                            ("renewal","Renewal"),("high","High Priority")]:
            f = tk.Frame(self._stat_row, bg=ORANGE)
            f.pack(side="left", expand=True)
            n = tk.Label(f, text="0", bg=ORANGE, fg=WHITE,
                         font=("Helvetica", 22, "bold"))
            n.pack()
            tk.Label(f, text=label, bg=ORANGE, fg="#FFF9C4",
                     font=("Helvetica", 9)).pack()
            self._stat_labels[key] = n

        # Search + Filter
        sf = tk.Frame(self, bg=BG)
        sf.pack(fill="x", padx=20, pady=(0, 8))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter())
        search_e = tk.Entry(sf, textvariable=self._search_var,
                            bg=WHITE, fg=TEXT,
                            font=("Helvetica", 11),
                            relief="flat",
                            highlightthickness=1,
                            highlightbackground=BORDER,
                            highlightcolor=PURPLE)
        search_e.insert(0, "🔍 Search name, student ID, course…")
        search_e.bind("<FocusIn>",  lambda e: search_e.delete(0, "end")
                      if search_e.get().startswith("🔍") else None)
        search_e.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))

        self._filter_var = tk.StringVar(value="All")
        for val in ("All", "New Application", "Renewal"):
            tk.Radiobutton(sf, text=val,
                           variable=self._filter_var,
                           value=val,
                           bg=BG, fg=TEXT,
                           activebackground=BG,
                           selectcolor=PURPLE,
                           font=("Helvetica", 10),
                           command=self._apply_filter).pack(side="left", padx=4)

        # Scrollable list
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        self._list = tk.Frame(canvas, bg=BG)
        wid = canvas.create_window((0, 0), window=self._list, anchor="nw")

        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(wid, width=e.width)
        canvas.bind("<Configure>", _resize)
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._loading_lbl = tk.Label(self._list,
                                     text="Loading pending applications…",
                                     bg=BG, fg=GRAY,
                                     font=("Helvetica", 12))
        self._loading_lbl.pack(pady=40)

    # ── Data ───────────────────────────────────────────────────────────────────
    def _fetch(self):
        try:
            apps = fetch_all(
                """SELECT a.*, 'Application' as type
                   FROM application a
                   WHERE a.status='pending' AND a.archived=0
                   ORDER BY a.submission_date DESC"""
            ) or []
            renewals = fetch_all(
                """SELECT r.*, 'Renewal' as type
                   FROM renew r
                   WHERE r.status='Pending' AND r.archived=0
                   ORDER BY r.submission_date DESC"""
            ) or []
            combined = apps + renewals
            self.after(0, self._render, combined)
        except Exception as e:
            self.after(0, lambda: self._loading_lbl.config(
                text=f"Error: {e}", fg=RED))

    def _render(self, apps):
        self._apps = apps
        self._update_stats()
        self._apply_filter()

    def _update_stats(self):
        total   = len(self._apps)
        new_cnt = sum(1 for a in self._apps if a["type"] == "Application")
        ren_cnt = sum(1 for a in self._apps if a["type"] == "Renewal")
        self._stat_labels["total"].config(text=str(total))
        self._stat_labels["new"].config(text=str(new_cnt))
        self._stat_labels["renewal"].config(text=str(ren_cnt))
        self._stat_labels["high"].config(text=str(new_cnt))  # treat New as High

    def _apply_filter(self):
        for w in self._list.winfo_children():
            w.destroy()

        ftype  = self._filter_var.get()
        query  = self._search_var.get().lower()
        if query.startswith("🔍"):
            query = ""

        filtered = [
            a for a in self._apps
            if (ftype == "All" or a["type"] == ftype) and
               (not query or
                query in str(a.get("first_name","")).lower() or
                query in str(a.get("last_name","")).lower() or
                query in str(a.get("student_id","")).lower() or
                query in str(a.get("course","")).lower())
        ]

        if not filtered:
            tk.Label(self._list, text="No pending applications found.",
                     bg=BG, fg=GRAY,
                     font=("Helvetica", 12)).pack(pady=30)
            return

        for app in filtered:
            self._make_card(app)

    def _sort_priority(self):
        self._apps.sort(key=lambda a: 0 if a["type"]=="Application" else 1)
        self._apply_filter()

    # ── Card ───────────────────────────────────────────────────────────────────
    def _make_card(self, app):
        is_new = app["type"] == "Application"
        color  = PURPLE if is_new else "#4CAF50"
        badge  = "🆕 New Application" if is_new else "🔄 Renewal"

        outer = tk.Frame(self._list, bg=BG)
        outer.pack(fill="x", padx=20, pady=6)

        bar = tk.Frame(outer, bg=color, width=5)
        bar.pack(side="left", fill="y")

        card = tk.Frame(outer, bg=WHITE,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(side="left", fill="both", expand=True)

        top = tk.Frame(card, bg=WHITE)
        top.pack(fill="x", padx=16, pady=(12, 4))

        name = f"{app.get('first_name','')} {app.get('last_name','')}".strip()
        tk.Label(top, text=name, bg=WHITE, fg=TEXT,
                 font=("Helvetica", 13, "bold"),
                 anchor="w").pack(anchor="w")

        tk.Label(top,
                 text=f"{app.get('course','N/A')} • {app.get('year_level','N/A')} • GWA: {app.get('gwa','N/A')}",
                 bg=WHITE, fg=GRAY,
                 font=("Helvetica", 9)).pack(anchor="w")

        tk.Label(top,
                 text=f"📅 {str(app.get('submission_date','N/A'))[:10]}",
                 bg=WHITE, fg=GRAY,
                 font=("Helvetica", 9)).pack(anchor="w")

        # Badge
        tk.Label(card, text=badge,
                 bg=color, fg=WHITE,
                 font=("Helvetica", 9, "bold"),
                 padx=10, pady=4).place(relx=1.0, y=12, anchor="ne")

        # Buttons
        btn_row = tk.Frame(card, bg=WHITE)
        btn_row.pack(fill="x", padx=16, pady=(4, 12))

        tk.Button(btn_row, text="👁 View Details",
                  bg=PURPLE2, fg=WHITE,
                  relief="flat", bd=0,
                  font=("Helvetica", 10),
                  padx=10, pady=5,
                  cursor="hand2",
                  command=lambda a=app: self._view_detail(a)).pack(side="left", padx=(0, 8))

        tk.Button(btn_row, text="✓ Approve",
                  bg=GREEN, fg=WHITE,
                  relief="flat", bd=0,
                  font=("Helvetica", 10),
                  padx=10, pady=5,
                  cursor="hand2",
                  command=lambda a=app: self._approve(a)).pack(side="left", padx=(0, 8))

        tk.Button(btn_row, text="✗ Reject",
                  bg=RED, fg=WHITE,
                  relief="flat", bd=0,
                  font=("Helvetica", 10),
                  padx=10, pady=5,
                  cursor="hand2",
                  command=lambda a=app: self._reject_dialog(a)).pack(side="left")

    # ── Detail dialog ──────────────────────────────────────────────────────────
    def _view_detail(self, app):
        dlg = tk.Toplevel(self)
        dlg.title("Application Detail")
        dlg.geometry("520x600")
        dlg.configure(bg=WHITE)
        dlg.grab_set()

        # Header
        hdr = tk.Frame(dlg, bg=PURPLE)
        hdr.pack(fill="x")
        name = f"{app.get('first_name','')} {app.get('last_name','')}".strip()
        tk.Label(hdr, text=name, bg=PURPLE, fg=WHITE,
                 font=("Helvetica", 14, "bold"),
                 padx=16, pady=12, anchor="w").pack(fill="x")

        # Scrollable body
        canvas = tk.Canvas(dlg, bg=WHITE, highlightthickness=0)
        sb = tk.Scrollbar(dlg, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        body = tk.Frame(canvas, bg=WHITE)
        wid  = canvas.create_window((0,0), window=body, anchor="nw")
        canvas.bind("<Configure>", lambda e: (
            canvas.configure(scrollregion=canvas.bbox("all")),
            canvas.itemconfig(wid, width=e.width)))

        for label, val in [
            ("Student ID",  app.get("student_id","N/A")),
            ("Course",      app.get("course","N/A")),
            ("Year Level",  app.get("year_level","N/A")),
            ("GWA",         str(app.get("gwa","N/A"))),
            ("Contact",     app.get("contact_number","N/A")),
            ("Address",     app.get("address","N/A")),
            ("Type",        app.get("type","N/A")),
            ("Submitted",   str(app.get("submission_date","N/A"))[:10]),
        ]:
            row = tk.Frame(body, bg=WHITE)
            row.pack(fill="x", padx=16, pady=4)
            tk.Label(row, text=f"{label}:", bg=WHITE, fg=GRAY,
                     font=("Helvetica", 10, "bold"), width=14,
                     anchor="w").pack(side="left")
            tk.Label(row, text=str(val), bg=WHITE, fg=TEXT,
                     font=("Helvetica", 10),
                     anchor="w").pack(side="left")

        if app.get("reason"):
            tk.Label(body, text="💭 Reason:", bg=WHITE, fg=GRAY,
                     font=("Helvetica", 10, "bold"),
                     anchor="w", padx=16).pack(fill="x", pady=(8, 2))
            tk.Label(body, text=app["reason"],
                     bg="#F7F7F7", fg=TEXT,
                     font=("Helvetica", 10),
                     wraplength=460, justify="left",
                     padx=16, pady=10, anchor="w").pack(fill="x", padx=16)

        # Action buttons
        btn_row = tk.Frame(dlg, bg=WHITE)
        btn_row.pack(fill="x", padx=16, pady=12)
        tk.Button(btn_row, text="Close",
                  bg=WHITE, fg=GRAY,
                  relief="flat", bd=1,
                  font=("Helvetica", 10),
                  cursor="hand2",
                  command=dlg.destroy).pack(side="right", padx=(8, 0))
        if str(app.get("status","")).lower() == "pending":
            tk.Button(btn_row, text="✓ Approve",
                      bg=GREEN, fg=WHITE,
                      relief="flat", bd=0,
                      font=("Helvetica", 10, "bold"),
                      padx=12, pady=6,
                      cursor="hand2",
                      command=lambda: (dlg.destroy(),
                                       self._approve(app))).pack(side="right", padx=(8,0))

    # ── Approve / Reject ───────────────────────────────────────────────────────
    def _approve(self, app):
        if not messagebox.askyesno("Approve",
            f"Approve scholarship for {app.get('first_name','')} {app.get('last_name','')}?"):
            return
        threading.Thread(target=self._do_status,
                         args=(app, "approved"), daemon=True).start()

    def _reject_dialog(self, app):
        dlg = tk.Toplevel(self)
        dlg.title("Reject Application")
        dlg.geometry("400x280")
        dlg.configure(bg=WHITE)
        dlg.grab_set()

        tk.Label(dlg, text="✗ Reject Application",
                 bg=WHITE, fg=RED,
                 font=("Helvetica", 13, "bold"),
                 padx=16, pady=12, anchor="w").pack(fill="x")
        tk.Label(dlg,
                 text=f"Reject application for {app.get('first_name','')} {app.get('last_name','')}?",
                 bg=WHITE, fg=TEXT,
                 font=("Helvetica", 10),
                 padx=16, anchor="w").pack(fill="x")

        tk.Label(dlg, text="Reason for Rejection:",
                 bg=WHITE, fg=TEXT,
                 font=("Helvetica", 10, "bold"),
                 padx=16, anchor="w").pack(fill="x", pady=(12, 2))

        reason_txt = tk.Text(dlg, height=5, bg="#F7FAFC", fg=TEXT,
                             font=("Helvetica", 10),
                             relief="flat", highlightthickness=1,
                             highlightbackground=BORDER,
                             highlightcolor=RED)
        reason_txt.pack(fill="x", padx=16)

        btn_row = tk.Frame(dlg, bg=WHITE)
        btn_row.pack(fill="x", padx=16, pady=12)
        tk.Button(btn_row, text="Cancel",
                  bg=WHITE, fg=GRAY, relief="flat", bd=1,
                  cursor="hand2", command=dlg.destroy).pack(side="right", padx=(8,0))

        def _do():
            reason = reason_txt.get("1.0","end").strip()
            if not reason:
                messagebox.showwarning("Required",
                                       "Please provide a reason for rejection.")
                return
            dlg.destroy()
            threading.Thread(target=self._do_status,
                             args=(app, "rejected"), daemon=True).start()

        tk.Button(btn_row, text="✗ Reject",
                  bg=RED, fg=WHITE,
                  relief="flat", bd=0,
                  font=("Helvetica", 10, "bold"),
                  padx=12, pady=6,
                  cursor="hand2",
                  command=_do).pack(side="right")

    def _do_status(self, app, status):
        try:
            if app["type"] == "Application":
                execute(
                    "UPDATE application SET status=%s WHERE application_id=%s",
                    (status, app["application_id"])
                )
            else:
                execute(
                    "UPDATE renew SET status=%s WHERE renewal_id=%s",
                    (status.capitalize(), app["renewal_id"])
                )
            self.after(0, self._on_updated, app, status)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))

    def _on_updated(self, app, status):
        name = f"{app.get('first_name','')} {app.get('last_name','')}".strip()
        color = GREEN if status == "approved" else RED
        messagebox.showinfo("Updated", f"{name} has been {status}!")
        threading.Thread(target=self._fetch, daemon=True).start()