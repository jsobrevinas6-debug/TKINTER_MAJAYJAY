import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

try:
    from student_dashboard import supabase, BG, WHITE, PURPLE, PURPLE2, BORDER, TEXT_DARK, TEXT_GRAY
except ImportError:
    BG=WHITE=PURPLE=PURPLE2=BORDER=TEXT_DARK=TEXT_GRAY=""
    supabase = None

INPUT_BG = "#F7FAFC"
RED      = "#E53E3E"
GREEN    = "#48BB78"


class ApplicationsFrame(tk.Frame):
    def __init__(self, parent, name, email, dashboard, **_):
        super().__init__(parent, bg=BG)
        self.name      = name
        self.email     = email
        self.dashboard = dashboard
        self._apps     = []
        self._build()
        threading.Thread(target=self._fetch, daemon=True).start()

    # ── Build UI ───────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=PURPLE)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📋  My Applications",
                 bg=PURPLE, fg="white",
                 font=("Helvetica",16,"bold"),
                 pady=14, padx=24, anchor="w").pack(fill="x")

        # Refresh button
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=24, pady=(12,4))
        tk.Button(bar, text="🔄 Refresh",
                  bg=WHITE, fg=PURPLE,
                  relief="flat", bd=1,
                  font=("Helvetica",10),
                  cursor="hand2",
                  command=self._refresh).pack(side="right")

        # Scrollable list
        self._canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical",
                          command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(fill="both", expand=True)

        self._list_frame = tk.Frame(self._canvas, bg=BG)
        self._wid = self._canvas.create_window(
            (0,0), window=self._list_frame, anchor="nw")

        def _resize(e):
            self._canvas.configure(
                scrollregion=self._canvas.bbox("all"))
            self._canvas.itemconfig(self._wid, width=e.width)
        self._canvas.bind("<Configure>", _resize)
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(
                int(-1*(e.delta/120)),"units"))

        self._loading_lbl = tk.Label(
            self._list_frame, text="Loading applications…",
            bg=BG, fg=TEXT_GRAY,
            font=("Helvetica",12))
        self._loading_lbl.pack(pady=40)

    # ── Data ───────────────────────────────────────────────────────────────────
    def _refresh(self):
        for w in self._list_frame.winfo_children():
            w.destroy()
        self._loading_lbl = tk.Label(
            self._list_frame, text="Loading applications…",
            bg=BG, fg=TEXT_GRAY, font=("Helvetica",12))
        self._loading_lbl.pack(pady=40)
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            user = (supabase.table("users")
                    .select("user_id")
                    .eq("email",self.email).single().execute())
            uid = user.data["user_id"]

            apps = (supabase.table("application").select("*")
                    .eq("user_id",uid)
                    .order("submission_date",desc=True).execute())
            renewals = (supabase.table("renew").select("*")
                        .eq("user_id",uid)
                        .order("submission_date",desc=True).execute())

            combined = []
            for a in (apps.data or []):
                a["type"] = "Application"
                a["application_id"] = a.get("application_id")
                combined.append(a)
            for r in (renewals.data or []):
                r["type"] = "Renewal"
                r["application_id"] = r.get("renewal_id")
                combined.append(r)

            combined.sort(key=lambda x: x.get("submission_date",""),
                          reverse=True)
            self.after(0, self._render, combined)
        except Exception as exc:
            self.after(0, self._render_error, str(exc))

    def _render(self, apps):
        for w in self._list_frame.winfo_children():
            w.destroy()

        if not apps:
            self._render_empty()
            return

        for app in apps:
            self._app_card(self._list_frame, app)

    def _render_empty(self):
        tk.Label(self._list_frame,
                 text="📭 No applications yet.",
                 bg=BG, fg=TEXT_GRAY,
                 font=("Helvetica",14)).pack(pady=30)
        tk.Button(self._list_frame,
                  text="Apply for Scholarship",
                  bg=PURPLE, fg="white",
                  relief="flat", bd=0,
                  font=("Helvetica",11,"bold"),
                  padx=20, pady=8,
                  cursor="hand2",
                  command=self.dashboard._show_apply).pack()

    def _render_error(self, msg):
        tk.Label(self._list_frame,
                 text=f"Error loading data: {msg}",
                 bg=BG, fg=RED,
                 font=("Helvetica",11)).pack(pady=30)

    # ── Card ───────────────────────────────────────────────────────────────────
    def _app_card(self, parent, app):
        status = app.get("status","pending")
        if status == "approved":
            bar_color, badge_bg, badge_fg, badge_txt = \
                GREEN, "#D4EDDA", "#155724", "✓ Approved"
        elif status == "rejected":
            bar_color, badge_bg, badge_fg, badge_txt = \
                RED, "#F8D7DA", "#721C24", "✗ Rejected"
        else:
            bar_color, badge_bg, badge_fg, badge_txt = \
                "#FFA500","#FFF3CD","#856404","⏳ Pending"

        outer = tk.Frame(parent, bg=BG)
        outer.pack(fill="x", padx=24, pady=8)

        # Left color bar + white card
        bar = tk.Frame(outer, bg=bar_color, width=5)
        bar.pack(side="left", fill="y")

        card = tk.Frame(outer, bg=WHITE,
                        highlightbackground=BORDER,
                        highlightthickness=1)
        card.pack(side="left", fill="both", expand=True)

        top = tk.Frame(card, bg=WHITE)
        top.pack(fill="x", padx=16, pady=(12,4))

        # Name + type tag + date
        name_txt = (f"{app.get('first_name','')} "
                    f"{app.get('middle_name','')} "
                    f"{app.get('last_name','')}").strip()
        tk.Label(top, text=name_txt, bg=WHITE, fg=TEXT_DARK,
                 font=("Helvetica",13,"bold"),
                 anchor="w").pack(anchor="w")
        tk.Label(top, text=f"{app['type']}  •  ID #{app['application_id']}",
                 bg=WHITE, fg=TEXT_GRAY,
                 font=("Helvetica",9)).pack(anchor="w")
        tk.Label(top,
                 text=f"📅 Submitted: {app.get('submission_date','N/A')}",
                 bg=WHITE, fg="#666666",
                 font=("Helvetica",9)).pack(anchor="w")

        # Status badge
        badge = tk.Label(top, text=badge_txt,
                         bg=badge_bg, fg=badge_fg,
                         font=("Helvetica",9,"bold"),
                         padx=10, pady=4)
        badge.place(relx=1.0, rely=0.0, anchor="ne")

        # Details box
        details = tk.Frame(card, bg="#F8F9FA",
                           highlightbackground=BORDER,
                           highlightthickness=1)
        details.pack(fill="x", padx=16, pady=(4,8))

        for lbl, val in [
            ("Student ID", app.get("student_id","N/A")),
            ("Course",     app.get("course","N/A")),
            ("Year Level", app.get("year_level","N/A")),
            ("GWA",        str(app.get("gwa","N/A"))),
        ]:
            row = tk.Frame(details, bg="#F8F9FA")
            row.pack(fill="x", padx=12, pady=2)
            tk.Label(row, text=lbl, bg="#F8F9FA",
                     fg="#666666",
                     font=("Helvetica",9)).pack(side="left")
            tk.Label(row, text=val, bg="#F8F9FA",
                     fg=TEXT_DARK,
                     font=("Helvetica",9,"bold")).pack(side="right")

        # Edit button (only if pending)
        if status == "pending":
            tk.Button(card, text="✏ Edit Application",
                      bg=PURPLE, fg="white",
                      relief="flat", bd=0,
                      font=("Helvetica",10),
                      cursor="hand2",
                      padx=12, pady=6,
                      command=lambda a=app: self._edit_dialog(a)
                      ).pack(anchor="w", padx=16, pady=(0,12))

    # ── Edit dialog ────────────────────────────────────────────────────────────
    def _edit_dialog(self, app):
        dlg = tk.Toplevel(self)
        dlg.title("Edit Application")
        dlg.geometry("460x480")
        dlg.configure(bg=WHITE)
        dlg.grab_set()

        tk.Label(dlg, text="Edit Application",
                 bg=WHITE, fg=PURPLE,
                 font=("Helvetica",14,"bold"),
                 pady=12).pack()

        fields = [
            ("Student ID", app.get("student_id","")),
            ("Course",     app.get("course","")),
            ("Year Level", app.get("year_level","")),
            ("GWA",        str(app.get("gwa",""))),
        ]
        vars_ = {}
        for label, val in fields:
            tk.Label(dlg, text=label, bg=WHITE, fg=TEXT_DARK,
                     font=("Helvetica",10), anchor="w",
                     padx=20).pack(fill="x", pady=(8,0))
            var = tk.StringVar(value=val)
            vars_[label] = var
            tk.Entry(dlg, textvariable=var,
                     bg="#F7FAFC", fg=TEXT_DARK,
                     relief="flat", bd=0,
                     font=("Helvetica",11),
                     highlightthickness=1,
                     highlightbackground=BORDER,
                     highlightcolor=PURPLE).pack(
                fill="x", padx=20, ipady=7)

        btn_row = tk.Frame(dlg, bg=WHITE)
        btn_row.pack(fill="x", padx=20, pady=20)

        tk.Button(btn_row, text="Cancel",
                  bg=WHITE, fg=TEXT_GRAY,
                  relief="flat", bd=1,
                  font=("Helvetica",10),
                  cursor="hand2",
                  command=dlg.destroy).pack(side="left", padx=(0,8))

        def _save():
            try:
                update = {
                    "student_id": vars_["Student ID"].get().strip(),
                    "course":     vars_["Course"].get().strip(),
                    "year_level": vars_["Year Level"].get().strip(),
                    "gwa": float(vars_["GWA"].get().strip() or 0),
                }
                table = "renew" if app["type"]=="Renewal" else "application"
                id_col = "renewal_id" if app["type"]=="Renewal" else "application_id"
                (supabase.table(table).update(update)
                 .eq(id_col, app["application_id"]).execute())
                dlg.destroy()
                messagebox.showinfo("Saved","Application updated successfully.")
                self._refresh()
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

        tk.Button(btn_row, text="Save Changes",
                  bg=PURPLE, fg="white",
                  relief="flat", bd=0,
                  font=("Helvetica",10,"bold"),
                  cursor="hand2",
                  command=_save).pack(side="right")