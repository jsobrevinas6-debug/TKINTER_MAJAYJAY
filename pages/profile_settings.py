import tkinter as tk
from tkinter import messagebox
import threading

try:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    from db import fetch_one, execute, verify_password, hash_password
except Exception:
    fetch_one = execute = verify_password = hash_password = None

BG          = "#F7FAFC"
WHITE       = "#FFFFFF"
PURPLE      = "#667EEA"
PURPLE2     = "#764BA2"
BORDER      = "#E2E8F0"
DARK        = "#2D3748"
GRAY        = "#718096"
GREEN       = "#48BB78"
DISABLED_BG = "#EDF2F7"
INPUT_BG    = "#FFFFFF"


class ProfileSettingsPage(tk.Frame):
    """Unified profile settings page for student, mayor, and admin.

    FIX — embedded mode (mayor / admin called from within their dashboard):
        When embedded=True the page skips building its own topbar and does NOT
        pack its own side='right' Scrollbar directly onto the root window.
        Previously, the missing embedded=True flag in mayor_dashboard caused:
          • A duplicate topbar appearing inside _content_area.
          • A Scrollbar packed side='right' to the ProfileSettingsPage frame,
            which on some geometry managers pushed the sidebar off-screen.
          • The '← Back' button calling app.show_mayor_dashboard(), which
            replaced the entire root window content (sidebar gone).
        All three issues are resolved by passing embedded=True from the
        mayor dashboard's _show_profile_settings method.
    """

    def __init__(self, parent, name="", email="", user_type="student", app=None,
                 dashboard=None, embedded=False, **_):
        super().__init__(parent, bg=BG)
        self.app       = app
        self.dashboard = dashboard
        self._email    = email
        self._name     = name
        self._utype    = user_type
        self._embedded = embedded
        self._editing  = False
        self._entries  = {}
        self._pw_vars  = {}
        self._build()
        threading.Thread(target=self._load_user, daemon=True).start()

    # ── Top-level layout ───────────────────────────────────────────────────────
    def _build(self):
        if not self._embedded:
            # Standalone mode: own topbar + back button + scrollable canvas
            topbar = tk.Frame(self, bg=WHITE, height=64)
            topbar.pack(fill="x")
            topbar.pack_propagate(False)
            tk.Frame(topbar, bg=BORDER, height=1).pack(side="bottom", fill="x")

            if self.app and self._utype in ("mayor", "admin"):
                tk.Button(topbar, text="← Back",
                          bg=WHITE, fg=PURPLE,
                          relief="flat", bd=0,
                          font=("Segoe UI", 10, "bold"),
                          cursor="hand2",
                          command=self._go_back).pack(side="left",
                                                      padx=(16, 0), pady=16)
            tk.Label(topbar, text="Profile Settings", bg=WHITE, fg=DARK,
                     font=("Segoe UI", 16, "bold")).pack(side="left",
                                                         padx=12, pady=16)

        # Both modes get a scrollable canvas — embedded just skips the topbar
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        self._inner = tk.Frame(canvas, bg=BG)
        wid = canvas.create_window((0, 0), window=self._inner, anchor="nw")

        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(wid, width=e.width)

        canvas.bind("<Configure>", _resize)
        canvas.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        self._build_form()

    # ── Form ───────────────────────────────────────────────────────────────────
    def _build_form(self):
        pad = 24 if self._embedded else 48
        wrap = tk.Frame(self._inner, bg=BG)
        wrap.pack(fill="both", padx=pad, pady=24)

        self._build_avatar_card(wrap)
        self._build_personal_card(wrap)
        if self._utype == "student":
            self._build_academic_card(wrap)
            self._build_status_card(wrap)
        self._build_password_card(wrap)

    # ── Avatar header card ─────────────────────────────────────────────────────
    def _build_avatar_card(self, wrap):
        hdr = tk.Frame(wrap, bg=WHITE,
                       highlightbackground=BORDER, highlightthickness=1)
        hdr.pack(fill="x", pady=(0, 20))

        row = tk.Frame(hdr, bg=WHITE)
        row.pack(fill="x", padx=24, pady=18)

        self._avatar_canvas = tk.Canvas(row, width=64, height=64,
                                        bg=WHITE, highlightthickness=0)
        self._avatar_canvas.pack(side="left")
        self._draw_avatar()

        info = tk.Frame(row, bg=WHITE)
        info.pack(side="left", padx=16)
        self._name_label = tk.Label(info, text=self._name or "—",
                                    bg=WHITE, fg=DARK,
                                    font=("Segoe UI", 14, "bold"))
        self._name_label.pack(anchor="w")
        tk.Label(info, text=self._email, bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 10)).pack(anchor="w")
        tk.Label(info, text=self._utype.capitalize(), bg=WHITE, fg=PURPLE,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(3, 0))

    def _draw_avatar(self, initial=None):
        c = self._avatar_canvas
        c.delete("all")
        ch = initial or (self._name[0].upper() if self._name else
                         self._email[0].upper() if self._email else "?")
        c.create_oval(2, 2, 62, 62, fill=PURPLE, outline="")
        c.create_text(32, 32, text=ch, fill=WHITE,
                      font=("Segoe UI", 22, "bold"))

    # ── Personal info card ─────────────────────────────────────────────────────
    def _build_personal_card(self, wrap):
        card = tk.Frame(wrap, bg=WHITE,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", pady=(0, 16))

        ch = tk.Frame(card, bg=WHITE)
        ch.pack(fill="x", padx=24, pady=(16, 0))
        tk.Label(ch, text="Personal Information", bg=WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(side="left")
        self._edit_btn = tk.Button(
            ch, text="✏  Edit", bg=PURPLE, fg=WHITE,
            activebackground=PURPLE2, activeforeground=WHITE,
            relief="flat", bd=0, font=("Segoe UI", 9, "bold"),
            padx=12, pady=4, cursor="hand2", command=self._toggle_edit)
        self._edit_btn.pack(side="right")

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(10, 0))

        ff = tk.Frame(card, bg=WHITE)
        ff.pack(fill="x", padx=24, pady=14)
        ff.columnconfigure(0, weight=1)
        ff.columnconfigure(1, weight=1)

        for label, key, row, col in [
            ("First Name",  "first_name",  0, 0),
            ("Last Name",   "last_name",   0, 1),
            ("Middle Name", "middle_name", 1, 0),
            ("Email",       "email",       1, 1),
        ]:
            self._field(ff, label, key, row, col, editable=(key != "email"))

        self._save_btn = tk.Button(
            card, text="💾  Save Changes", bg=PURPLE, fg=WHITE,
            activebackground=PURPLE2, activeforeground=WHITE,
            relief="flat", bd=0, font=("Segoe UI", 10, "bold"),
            padx=18, pady=8, cursor="hand2", command=self._save_profile)

        self._info_card = card

    # ── Academic card (student only) ───────────────────────────────────────────
    def _build_academic_card(self, wrap):
        card = tk.Frame(wrap, bg=WHITE,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", pady=(0, 16))

        tk.Label(card, text="Academic Information", bg=WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=24,
                                                     pady=(16, 0))
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(10, 0))

        ff = tk.Frame(card, bg=WHITE)
        ff.pack(fill="x", padx=24, pady=14)
        ff.columnconfigure(0, weight=1)
        ff.columnconfigure(1, weight=1)

        for label, key, row, col, editable in [
            ("Student ID",   "student_id", 0, 0, False),
            ("Course",       "course",     0, 1, True),
            ("Phone Number", "phone",      1, 0, True),
            ("Address",      "address",    1, 1, True),
        ]:
            self._field(ff, label, key, row, col, editable=editable)

    # ── Scholarship status card (student only) ─────────────────────────────────
    def _build_status_card(self, wrap):
        card = tk.Frame(wrap, bg=WHITE,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", pady=(0, 16))

        tk.Label(card, text="Scholarship Status", bg=WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=24,
                                                     pady=(16, 0))
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(10, 0))

        inner = tk.Frame(card, bg="#F0FFF4",
                         highlightbackground=GREEN, highlightthickness=1)
        inner.pack(fill="x", padx=24, pady=14)
        tk.Label(inner, text="✅  Active Scholar", bg="#F0FFF4", fg=GREEN,
                 font=("Segoe UI", 12, "bold"),
                 padx=16, pady=8, anchor="w").pack(fill="x")
        tk.Label(inner, text="Mayor's Scholarship Program",
                 bg="#F0FFF4", fg=GRAY,
                 font=("Segoe UI", 10), padx=16,
                 anchor="w").pack(fill="x", pady=(0, 10))

    # ── Change password card ───────────────────────────────────────────────────
    def _build_password_card(self, wrap):
        card = tk.Frame(wrap, bg=WHITE,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x")

        tk.Label(card, text="Change Password", bg=WHITE, fg=DARK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=24,
                                                     pady=(16, 0))
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(10, 0))

        ff = tk.Frame(card, bg=WHITE)
        ff.pack(fill="x", padx=24, pady=14)
        ff.columnconfigure(0, weight=1)
        ff.columnconfigure(1, weight=1)

        for i, (label, key) in enumerate([
            ("Current Password", "current"),
            ("New Password",     "new"),
            ("Confirm Password", "confirm"),
        ]):
            f = tk.Frame(ff, bg=WHITE)
            f.grid(row=i // 2, column=i % 2, sticky="ew",
                   padx=(0, 14 if i % 2 == 0 else 0), pady=(0, 12))
            tk.Label(f, text=label, bg=WHITE, fg=GRAY,
                     font=("Segoe UI", 9)).pack(anchor="w")
            var = tk.StringVar()
            tk.Entry(f, textvariable=var, show="•",
                     bg=INPUT_BG, fg=DARK, insertbackground=PURPLE,
                     relief="flat", bd=0, font=("Segoe UI", 11),
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=PURPLE).pack(fill="x", ipady=7, pady=(4, 0))
            self._pw_vars[key] = var

        tk.Button(card, text="🔒  Update Password",
                  bg=DARK, fg=WHITE,
                  activebackground="#1A202C", activeforeground=WHITE,
                  relief="flat", bd=0, font=("Segoe UI", 10, "bold"),
                  padx=16, pady=8, cursor="hand2",
                  command=self._change_password).pack(anchor="w", padx=24,
                                                      pady=(0, 18))

    # ── Shared field builder ───────────────────────────────────────────────────
    def _field(self, parent, label, key, row, col, editable=True):
        f = tk.Frame(parent, bg=WHITE)
        f.grid(row=row, column=col, sticky="ew",
               padx=(0, 14 if col == 0 else 0), pady=(0, 12))
        tk.Label(f, text=label, bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 9)).pack(anchor="w")
        var = tk.StringVar()
        e = tk.Entry(f, textvariable=var,
                     state="disabled",
                     bg=DISABLED_BG, fg=DARK,
                     disabledbackground=DISABLED_BG,
                     disabledforeground=DARK,
                     insertbackground=PURPLE,
                     relief="flat", bd=0, font=("Segoe UI", 11),
                     highlightthickness=1,
                     highlightbackground=BORDER,
                     highlightcolor=PURPLE)
        e.pack(fill="x", ipady=7, pady=(4, 0))
        self._entries[key] = (e, var, editable)

    def _go_back(self):
        """Only reachable in non-embedded (standalone) mode."""
        if not self.app:
            return
        if self._utype == "mayor":
            self.app.show_mayor_dashboard()
        elif self._utype == "admin":
            self.app.show_admin_dashboard()

    # ── Load from DB ───────────────────────────────────────────────────────────
    def _load_user(self):
        if not fetch_one:
            return
        try:
            cols = ("first_name, middle_name, last_name, email"
                    if self._utype != "student" else
                    "first_name, middle_name, last_name, email, "
                    "student_id, course, phone, address")
            row = fetch_one(f"SELECT {cols} FROM users WHERE email = %s",
                            (self._email,))
            if row:
                self.after(0, self._populate, row)
        except Exception as e:
            print(f"[Profile] load error: {e}")

    def _populate(self, row):
        for key, (entry, var, _) in self._entries.items():
            var.set(row.get(key, "") or "")
        full = " ".join(filter(None, [row.get("first_name"),
                                      row.get("last_name")]))
        if full:
            self._name_label.config(text=full)
            self._draw_avatar(full[0].upper())

    # ── Edit toggle ────────────────────────────────────────────────────────────
    def _toggle_edit(self):
        self._editing = not self._editing
        self._edit_btn.config(
            text="✕  Cancel" if self._editing else "✏  Edit",
            bg=GRAY if self._editing else PURPLE)
        for _, (entry, _, editable) in self._entries.items():
            if editable:
                entry.config(
                    state="normal" if self._editing else "disabled",
                    bg=INPUT_BG if self._editing else DISABLED_BG)
        if self._editing:
            self._save_btn.pack(anchor="w", padx=24, pady=(0, 16))
        else:
            self._save_btn.pack_forget()

    # ── Save profile ───────────────────────────────────────────────────────────
    def _save_profile(self):
        first  = self._entries["first_name"][1].get().strip()
        middle = self._entries["middle_name"][1].get().strip()
        last   = self._entries["last_name"][1].get().strip()
        if not first or not last:
            messagebox.showerror("Validation", "First and last name are required.")
            return
        self._save_btn.config(state="disabled", text="Saving…", bg=GRAY)

        extra = {}
        for key in ("course", "phone", "address"):
            if key in self._entries:
                extra[key] = self._entries[key][1].get().strip() or None

        threading.Thread(target=self._do_save,
                         args=(first, middle, last, extra), daemon=True).start()

    def _do_save(self, first, middle, last, extra):
        try:
            if execute:
                sets = "first_name=%s, middle_name=%s, last_name=%s"
                vals = [first, middle or None, last]
                for k, v in extra.items():
                    sets += f", {k}=%s"
                    vals.append(v)
                vals.append(self._email)
                execute(f"UPDATE users SET {sets} WHERE email=%s", tuple(vals))
            self.after(0, self._on_save_done, first, last)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: self._save_btn.config(
                state="normal", text="💾  Save Changes", bg=PURPLE))

    def _on_save_done(self, first, last):
        self._save_btn.config(state="normal", text="💾  Save Changes", bg=PURPLE)
        full = f"{first} {last}".strip()
        self._name_label.config(text=full)
        self._draw_avatar(full[0].upper())
        if self.app:
            self.app._user_name = full
        self._toggle_edit()
        messagebox.showinfo("Saved", "Profile updated successfully!")

    # ── Change password ────────────────────────────────────────────────────────
    def _change_password(self):
        current = self._pw_vars["current"].get()
        new     = self._pw_vars["new"].get()
        confirm = self._pw_vars["confirm"].get()
        if not current or not new or not confirm:
            messagebox.showerror("Validation", "Please fill in all password fields.")
            return
        if new != confirm:
            messagebox.showerror("Validation", "New passwords do not match.")
            return
        if len(new) < 6:
            messagebox.showerror("Validation",
                                 "Password must be at least 6 characters.")
            return
        threading.Thread(target=self._do_change_pw,
                         args=(current, new), daemon=True).start()

    def _do_change_pw(self, current, new):
        try:
            if not fetch_one or not execute:
                raise Exception("DB not available.")
            row = fetch_one("SELECT password FROM users WHERE email=%s",
                            (self._email,))
            if not row:
                raise Exception("User not found.")
            if verify_password and not verify_password(current, row["password"]):
                self.after(0, lambda: messagebox.showerror(
                    "Error", "Current password is incorrect."))
                return
            hashed = hash_password(new) if hash_password else new
            execute("UPDATE users SET password=%s WHERE email=%s",
                    (hashed, self._email))
            self.after(0, self._on_pw_done)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))

    def _on_pw_done(self):
        for var in self._pw_vars.values():
            var.set("")
        messagebox.showinfo("Success", "Password updated successfully!")


# backward-compat alias so any old import of ProfileFrame still works
ProfileFrame = ProfileSettingsPage