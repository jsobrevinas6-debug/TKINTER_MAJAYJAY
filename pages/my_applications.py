import tkinter as tk
from tkinter import ttk
import threading

BG      = "#F7FAFC"
WHITE   = "#FFFFFF"
PURPLE  = "#667EEA"
PURPLE2 = "#764BA2"
BORDER  = "#E2E8F0"
DARK    = "#2D3748"
GRAY    = "#718096"
RED     = "#F56565"
GREEN   = "#48BB78"
ORANGE  = "#ED8936"
SHADOW  = "#CBD5E0"

STATUS_COLORS = {
    "pending":   ("#FFF8E1", "#D97706"),
    "approved":  ("#F0FFF4", "#276749"),
    "rejected":  ("#FFF5F5", "#C53030"),
    "cancelled": ("#F7FAFC", "#718096"),
}


class MyApplicationsPage(tk.Frame):
    def __init__(self, parent, user: dict):
        super().__init__(parent, bg=BG)
        self.pack(fill="both", expand=True)
        self.user = user
        self._build_ui()

    def _build_ui(self):
        # ── Top bar ────────────────────────────────────────────────────────────
        topbar = tk.Frame(self, bg=WHITE, height=64)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Frame(topbar, bg=BORDER, height=1).pack(side="bottom", fill="x")
        tk.Label(topbar, text="My Applications",
                 bg=WHITE, fg=DARK,
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=28, pady=16)
        refresh_btn = tk.Button(topbar, text="⟳  Refresh",
                                bg=PURPLE, fg=WHITE,
                                activebackground=PURPLE2,
                                relief="flat", bd=0,
                                font=("Segoe UI", 10, "bold"),
                                cursor="hand2", padx=16, pady=6,
                                command=self._load)
        refresh_btn.pack(side="right", padx=20, pady=16)
        refresh_btn.bind("<Enter>", lambda e: refresh_btn.config(bg=PURPLE2))
        refresh_btn.bind("<Leave>", lambda e: refresh_btn.config(bg=PURPLE))

        # ── Table area ─────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=32, pady=24)

        # Shadow card wrapping the treeview
        shadow = tk.Frame(body, bg=SHADOW)
        shadow.pack(fill="both", expand=True)
        card = tk.Frame(shadow, bg=WHITE)
        card.pack(fill="both", expand=True, padx=2, pady=2)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("App.Treeview",
                        background=WHITE,
                        foreground=DARK,
                        rowheight=40,
                        fieldbackground=WHITE,
                        font=("Segoe UI", 11),
                        borderwidth=0)
        style.configure("App.Treeview.Heading",
                        background=PURPLE,
                        foreground=WHITE,
                        font=("Segoe UI", 11, "bold"),
                        relief="flat",
                        padding=(0, 10))
        style.map("App.Treeview",
                  background=[("selected", "#EBF4FF")],
                  foreground=[("selected", DARK)])
        style.layout("App.Treeview", [
            ("App.Treeview.treearea", {"sticky": "nswe"})
        ])

        cols = ("Name", "School", "Course", "Year Level",
                "GWA", "Year Applied", "Status", "Date Applied")
        self.tree = ttk.Treeview(card, columns=cols, show="headings",
                                 selectmode="browse", style="App.Treeview")

        col_widths = {
            "Name": 160, "School": 180, "Course": 150,
            "Year Level": 90, "GWA": 70, "Year Applied": 100,
            "Status": 100, "Date Applied": 110,
        }
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center",
                             width=col_widths.get(col, 120),
                             minwidth=60)

        # Scrollbars
        vsb = ttk.Scrollbar(card, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)

        # Status bar
        self.status_var = tk.StringVar()
        tk.Label(body, textvariable=self.status_var,
                 bg=BG, fg=GRAY,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(8, 0))

        self._load()

    def _load(self):
        threading.Thread(target=self._do_load, daemon=True).start()

    def _do_load(self):
        try:
            from db import fetch_all
            uid = self.user.get("user_id") or self.user.get("id")
            rows = fetch_all(
                """SELECT first_name, last_name, school_name, course,
                          year_level, gwa, year_applied, status, submission_date
                   FROM applications
                   WHERE user_id = %s
                   ORDER BY submission_date DESC""",
                (uid,))
            self.after(0, self._populate, rows)
        except Exception as exc:
            self.after(0, self.status_var.set, f"Error loading data: {exc}")

    def _populate(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not rows:
            self.status_var.set("No applications found.")
            return

        for r in rows:
            name  = f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
            date  = str(r.get("submission_date", ""))[:10]
            status = r.get("status", "pending")

            # Tag per status for row coloring
            tag = status
            self.tree.tag_configure(
                tag,
                background=STATUS_COLORS.get(status, ("#FFFFFF", "#2D3748"))[0],
                foreground=STATUS_COLORS.get(status, ("#FFFFFF", "#2D3748"))[1])

            self.tree.insert("", "end", tags=(tag,), values=(
                name,
                r.get("school_name", ""),
                r.get("course", ""),
                r.get("year_level", ""),
                r.get("gwa", ""),
                r.get("year_applied", ""),
                status.capitalize(),
                date,
            ))

        self.status_var.set(f"{len(rows)} application(s) found.")
