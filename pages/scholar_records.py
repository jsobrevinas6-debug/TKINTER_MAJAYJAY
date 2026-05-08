import tkinter as tk
from tkinter import ttk, messagebox
import threading

try:
    from db import fetch_all, execute
except ImportError:
    fetch_all = execute = None

BG     = "#F5F7FA"
WHITE  = "#FFFFFF"
INDIGO = "#4F46E5"
GREEN  = "#16A34A"
RED    = "#DC2626"
ORANGE = "#EA580C"
BORDER = "#E2E8F0"
TEXT   = "#1E293B"
GRAY   = "#64748B"


class ScholarRecordsFrame(tk.Frame):
    def __init__(self, parent, name, email, app, **_):
        super().__init__(parent, bg=BG)
        self.name   = name
        self.email  = email
        self.app    = app
        self._tab   = "Active"
        self._data  = []
        self._page  = 1
        self._per   = 12
        self._build()
        threading.Thread(target=self._fetch, daemon=True).start()

    # ── Build ──────────────────────────────────────────────────────────────────
    def _build(self):
        # Top bar
        top = tk.Frame(self, bg=WHITE,
                       highlightbackground=BORDER, highlightthickness=1)
        top.pack(fill="x")
        tk.Button(top, text="← Back",
                  bg=WHITE, fg=INDIGO,
                  relief="flat", bd=0,
                  font=("Helvetica", 11),
                  cursor="hand2",
                  command=self.app.show_mayor_dashboard).pack(side="left",
                                                               padx=16, pady=10)
        tk.Label(top, text="📋 Scholar Records",
                 bg=WHITE, fg=INDIGO,
                 font=("Helvetica", 15, "bold")).pack(side="left")
        tk.Button(top, text="🔄 Refresh",
                  bg=BG, fg=INDIGO,
                  relief="flat", bd=1,
                  font=("Helvetica", 10),
                  cursor="hand2",
                  command=self._refresh).pack(side="right", padx=16, pady=10)

        # Tab bar
        tab_bar = tk.Frame(self, bg=WHITE,
                           highlightbackground=BORDER, highlightthickness=1)
        tab_bar.pack(fill="x")
        self._tab_btns = {}
        for tab in ("Active", "Renewals", "Archived"):
            btn = tk.Button(tab_bar, text=tab,
                            bg=WHITE, fg=GRAY,
                            relief="flat", bd=0,
                            font=("Helvetica", 11),
                            padx=20, pady=10,
                            cursor="hand2",
                            command=lambda t=tab: self._switch_tab(t))
            btn.pack(side="left")
            self._tab_btns[tab] = btn
        self._switch_tab("Active", fetch=False)

        # Search + filter bar
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=16, pady=10)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply())
        tk.Entry(bar, textvariable=self._search_var,
                 bg=WHITE, fg=TEXT,
                 font=("Helvetica", 11),
                 relief="flat",
                 highlightthickness=1,
                 highlightbackground=BORDER,
                 highlightcolor=INDIGO,
                 width=30).pack(side="left", ipady=7, padx=(0, 10))

        self._status_var = tk.StringVar(value="All")
        ttk.Combobox(bar, textvariable=self._status_var,
                     values=["All","Pending","Approved","Rejected"],
                     state="readonly",
                     font=("Helvetica", 10),
                     width=14).pack(side="left")
        self._status_var.trace_add("write", lambda *_: self._apply())

        # Table frame
        tbl_frame = tk.Frame(self, bg=WHITE,
                             highlightbackground=BORDER, highlightthickness=1)
        tbl_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        cols = ("ID","Name","Student ID","Course","Year","GWA","Type","Status","Date","Actions")
        self._tree = ttk.Treeview(tbl_frame, columns=cols,
                                  show="headings", selectmode="browse")
        widths = [60, 160, 100, 180, 80, 60, 100, 90, 100, 80]
        for col, w in zip(cols, widths):
            self._tree.heading(col, text=col,
                               command=lambda c=col: self._sort(c))
            self._tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(tbl_frame, orient="vertical",
                            command=self._tree.yview)
        hsb = ttk.Scrollbar(tbl_frame, orient="horizontal",
                            command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set,
                             xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self._tree.pack(fill="both", expand=True)
        self._tree.bind("<Double-1>", self._on_row_click)

        # Status row tags
        self._tree.tag_configure("approved", foreground=GREEN)
        self._tree.tag_configure("rejected", foreground=RED)
        self._tree.tag_configure("pending",  foreground=ORANGE)

        # Pagination
        pg = tk.Frame(self, bg=BG)
        pg.pack(fill="x", padx=16, pady=(0, 10))
        self._prev_btn = tk.Button(pg, text="← Prev",
                                   bg=WHITE, fg=INDIGO,
                                   relief="flat", bd=1,
                                   font=("Helvetica", 10),
                                   cursor="hand2",
                                   command=self._prev_page)
        self._prev_btn.pack(side="left", padx=(0, 8))
        self._page_lbl = tk.Label(pg, text="Page 1",
                                  bg=BG, fg=TEXT,
                                  font=("Helvetica", 10))
        self._page_lbl.pack(side="left")
        self._next_btn = tk.Button(pg, text="Next →",
                                   bg=WHITE, fg=INDIGO,
                                   relief="flat", bd=1,
                                   font=("Helvetica", 10),
                                   cursor="hand2",
                                   command=self._next_page)
        self._next_btn.pack(side="left", padx=8)
        self._count_lbl = tk.Label(pg, text="",
                                   bg=BG, fg=GRAY,
                                   font=("Helvetica", 10))
        self._count_lbl.pack(side="right")

        self._loading_lbl = tk.Label(self, text="Loading records…",
                                     bg=BG, fg=GRAY,
                                     font=("Helvetica", 12))
        self._loading_lbl.pack()

    # ── Tab switching ──────────────────────────────────────────────────────────
    def _switch_tab(self, tab, fetch=True):
        self._tab = tab
        for t, btn in self._tab_btns.items():
            btn.config(bg=INDIGO if t==tab else WHITE,
                       fg=WHITE   if t==tab else GRAY,
                       font=("Helvetica", 11, "bold" if t==tab else "normal"))
        self._page = 1
        if fetch:
            threading.Thread(target=self._fetch, daemon=True).start()

    # ── Data ───────────────────────────────────────────────────────────────────
    def _refresh(self):
        self._loading_lbl.config(text="Refreshing…")
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            if self._tab == "Active":
                apps = fetch_all(
                    "SELECT *,'Application' as type FROM application WHERE archived=0 ORDER BY submission_date DESC"
                ) or []
                data = apps

            elif self._tab == "Renewals":
                rens = fetch_all(
                    "SELECT *,'Renewal' as type FROM renew WHERE archived=0 ORDER BY submission_date DESC"
                ) or []
                data = rens

            else:  # Archived
                apps = fetch_all(
                    "SELECT *,'Application' as type FROM application WHERE archived=1 ORDER BY submission_date DESC"
                ) or []
                rens = fetch_all(
                    "SELECT *,'Renewal' as type FROM renew WHERE archived=1 ORDER BY submission_date DESC"
                ) or []
                data = apps + rens

            self.after(0, self._on_data, data)
        except Exception as e:
            self.after(0, lambda: self._loading_lbl.config(
                text=f"Error: {e}", fg=RED))

    def _on_data(self, data):
        self._data = data
        self._loading_lbl.config(text="")
        self._apply()

    # ── Filter + render ────────────────────────────────────────────────────────
    def _apply(self):
        q      = self._search_var.get().lower()
        status = self._status_var.get()

        filtered = [
            r for r in self._data
            if (status == "All" or
                str(r.get("status","")).lower() == status.lower()) and
               (not q or
                q in str(r.get("first_name","")).lower() or
                q in str(r.get("last_name","")).lower() or
                q in str(r.get("student_id","")).lower() or
                q in str(r.get("course","")).lower())
        ]

        total = len(filtered)
        pages = max(1, (total + self._per - 1) // self._per)
        self._page = min(self._page, pages)

        start = (self._page - 1) * self._per
        page_data = filtered[start:start + self._per]

        # Clear tree
        for row in self._tree.get_children():
            self._tree.delete(row)

        for r in page_data:
            name = f"{r.get('first_name','')} {r.get('last_name','')}".strip()
            rid  = f"#{r.get('application_id') or r.get('renewal_id','')}"
            status_val = str(r.get("status","pending")).capitalize()
            tag = status_val.lower()
            self._tree.insert("", "end",
                              values=(rid, name,
                                      r.get("student_id","N/A"),
                                      r.get("course","N/A"),
                                      r.get("year_level","N/A"),
                                      r.get("gwa","N/A"),
                                      r.get("type","N/A"),
                                      status_val,
                                      str(r.get("submission_date",""))[:10],
                                      "View"),
                              tags=(tag,),
                              iid=str(id(r)))
            # store full record for detail lookup
            self._tree.set(str(id(r)), "ID", rid)
            self._tree._records = getattr(self._tree, "_records", {})
            self._tree._records[str(id(r))] = r

        self._page_lbl.config(text=f"Page {self._page} of {pages}")
        self._count_lbl.config(text=f"{total} record(s)")
        self._prev_btn.config(state="normal" if self._page > 1 else "disabled")
        self._next_btn.config(state="normal" if self._page < pages else "disabled")

    # ── Sort ───────────────────────────────────────────────────────────────────
    def _sort(self, col):
        key_map = {
            "Name": lambda r: f"{r.get('first_name','')} {r.get('last_name','')}",
            "Student ID": lambda r: str(r.get("student_id","")),
            "Course":     lambda r: str(r.get("course","")),
            "Status":     lambda r: str(r.get("status","")),
            "Date":       lambda r: str(r.get("submission_date","")),
        }
        fn = key_map.get(col)
        if fn:
            self._data.sort(key=fn)
            self._apply()

    # ── Pagination ─────────────────────────────────────────────────────────────
    def _prev_page(self):
        if self._page > 1:
            self._page -= 1
            self._apply()

    def _next_page(self):
        self._page += 1
        self._apply()

    # ── Row click → detail ─────────────────────────────────────────────────────
    def _on_row_click(self, event):
        sel = self._tree.selection()
        if not sel:
            return
        iid = sel[0]
        rec = getattr(self._tree, "_records", {}).get(iid)
        if rec:
            self._show_detail(rec)

    def _show_detail(self, app):
        dlg = tk.Toplevel(self)
        dlg.title("Scholar Record Detail")
        dlg.geometry("540x620")
        dlg.configure(bg=WHITE)
        dlg.grab_set()

        status_val = str(app.get("status","")).lower()
        hdr_color  = GREEN if status_val=="approved" else \
                     RED   if status_val=="rejected"  else ORANGE

        hdr = tk.Frame(dlg, bg=hdr_color)
        hdr.pack(fill="x")
        name = f"{app.get('first_name','')} {app.get('last_name','')}".strip()
        tk.Label(hdr, text=name, bg=hdr_color, fg=WHITE,
                 font=("Helvetica", 14, "bold"),
                 padx=16, pady=12, anchor="w").pack(fill="x")
        tk.Label(hdr,
                 text=f"{app.get('type','N/A')} • Status: {status_val.capitalize()}",
                 bg=hdr_color, fg="white",
                 font=("Helvetica", 10),
                 padx=16, pady=(0, 10), anchor="w").pack(fill="x")

        # Body
        canvas = tk.Canvas(dlg, bg=WHITE, highlightthickness=0)
        sb     = tk.Scrollbar(dlg, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        body = tk.Frame(canvas, bg=WHITE)
        wid  = canvas.create_window((0,0), window=body, anchor="nw")
        canvas.bind("<Configure>", lambda e: (
            canvas.configure(scrollregion=canvas.bbox("all")),
            canvas.itemconfig(wid, width=e.width)))

        fields = [
            ("Student ID",  "student_id"),
            ("Course",      "course"),
            ("Year Level",  "year_level"),
            ("GWA",         "gwa"),
            ("Contact",     "contact_number"),
            ("Address",     "address"),
            ("Submitted",   "submission_date"),
        ]
        for label, key in fields:
            val = str(app.get(key,"N/A"))
            if key == "submission_date":
                val = val[:10]
            row = tk.Frame(body, bg=WHITE)
            row.pack(fill="x", padx=16, pady=4)
            tk.Label(row, text=f"{label}:", bg=WHITE, fg=GRAY,
                     font=("Helvetica", 10, "bold"),
                     width=14, anchor="w").pack(side="left")
            tk.Label(row, text=val, bg=WHITE, fg=TEXT,
                     font=("Helvetica", 10),
                     anchor="w").pack(side="left")

        if app.get("reason"):
            tk.Label(body, text="💭 Reason:", bg=WHITE, fg=GRAY,
                     font=("Helvetica", 10, "bold"),
                     padx=16, anchor="w").pack(fill="x", pady=(8,2))
            tk.Label(body, text=app["reason"],
                     bg="#F8F9FA", fg=TEXT,
                     font=("Helvetica", 10),
                     wraplength=470, justify="left",
                     padx=16, pady=10, anchor="w").pack(fill="x", padx=16)

        # Actions
        btn_row = tk.Frame(dlg, bg=WHITE)
        btn_row.pack(fill="x", padx=16, pady=12)
        tk.Button(btn_row, text="Close",
                  bg=WHITE, fg=GRAY,
                  relief="flat", bd=1,
                  cursor="hand2",
                  command=dlg.destroy).pack(side="right", padx=(8,0))

        if status_val == "pending":
            tk.Button(btn_row, text="✓ Approve",
                      bg=GREEN, fg=WHITE,
                      relief="flat", bd=0,
                      font=("Helvetica", 10,"bold"),
                      padx=12, pady=6,
                      cursor="hand2",
                      command=lambda: (dlg.destroy(),
                                       self._update_status(app,"approved"))
                      ).pack(side="right", padx=(8,0))
            tk.Button(btn_row, text="✗ Reject",
                      bg=RED, fg=WHITE,
                      relief="flat", bd=0,
                      font=("Helvetica", 10,"bold"),
                      padx=12, pady=6,
                      cursor="hand2",
                      command=lambda: (dlg.destroy(),
                                       self._update_status(app,"rejected"))
                      ).pack(side="right", padx=(8,0))

        if not app.get("archived"):
            tk.Button(btn_row, text="📦 Archive",
                      bg=ORANGE, fg=WHITE,
                      relief="flat", bd=0,
                      font=("Helvetica", 10,"bold"),
                      padx=12, pady=6,
                      cursor="hand2",
                      command=lambda: (dlg.destroy(),
                                       self._archive(app))
                      ).pack(side="left")

    def _update_status(self, app, status):
        def _do():
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
                self.after(0, lambda: (
                    messagebox.showinfo("Updated", f"Status updated to {status}."),
                    threading.Thread(target=self._fetch, daemon=True).start()
                ))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=_do, daemon=True).start()

    def _archive(self, app):
        if not messagebox.askyesno("Archive",
            f"Archive {app['type']} #{app.get('application_id') or app.get('renewal_id')}?"):
            return
        def _do():
            try:
                if app["type"] == "Application":
                    execute(
                        "UPDATE application SET archived=1 WHERE application_id=%s",
                        (app["application_id"],)
                    )
                else:
                    execute(
                        "UPDATE renew SET archived=1 WHERE renewal_id=%s",
                        (app["renewal_id"],)
                    )
                self.after(0, lambda: (
                    messagebox.showinfo("Archived","Record archived successfully."),
                    threading.Thread(target=self._fetch, daemon=True).start()
                ))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=_do, daemon=True).start()