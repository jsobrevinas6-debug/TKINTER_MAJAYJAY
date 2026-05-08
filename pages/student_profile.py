import tkinter as tk
import hashlib
import threading

BG        = "#F7FAFC"
WHITE     = "#FFFFFF"
PURPLE1   = "#667EEA"
PURPLE2   = "#764BA2"
BORDER    = "#E2E8F0"
TEXT_DARK = "#2D3748"
TEXT_GRAY = "#718096"
RED       = "#F56565"
GREEN     = "#48BB78"
INPUT_BG  = "#F7FAFC"


def _hash(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()


class StudentProfilePage(tk.Frame):
    def __init__(self, parent, user: dict):
        super().__init__(parent, bg=BG)
        self.pack(fill="both", expand=True)
        self.user = user
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="My Profile",
                 bg=BG, fg=PURPLE1,
                 font=("Helvetica", 20, "bold")).pack(anchor="w", padx=32, pady=(32, 4))
        tk.Label(self, text="View and update your account details.",
                 bg=BG, fg=TEXT_GRAY,
                 font=("Helvetica", 11)).pack(anchor="w", padx=32, pady=(0, 12))

        # ── Scrollable area ───────────────────────────────────────────────────
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_resize(e):
            canvas.itemconfig(win_id, width=e.width)
        canvas.bind("<Configure>", _on_resize)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        # ── Card ──────────────────────────────────────────────────────────────
        card = tk.Frame(inner, bg=WHITE, bd=0,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(padx=32, pady=(0, 32), fill="x")

        # Read-only info
        self._info_row(card, "Email",     self.user.get("email", ""))
        self._info_row(card, "User Type", self.user.get("user_type", "student").capitalize())

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=20, pady=12)

        # Editable name fields
        self._field_label(card, "First Name")
        self.first_var = tk.StringVar(value=self.user.get("first_name", ""))
        self._entry(card, self.first_var)

        self._field_label(card, "Last Name")
        self.last_var = tk.StringVar(value=self.user.get("last_name", ""))
        self._entry(card, self.last_var)

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=20, pady=12)

        # Password fields with show/hide toggles
        self._field_label(card, "New Password (leave blank to keep current)")
        self.pwd_var = tk.StringVar()
        self.pwd_entry, self._show_pwd = self._pwd_entry(card, self.pwd_var)

        self._field_label(card, "Confirm New Password")
        self.confirm_var = tk.StringVar()
        self.confirm_entry, self._show_confirm = self._pwd_entry(card, self.confirm_var)

        # Message label
        self.msg_var = tk.StringVar()
        self.msg_label = tk.Label(card, textvariable=self.msg_var,
                                  bg=WHITE, fg=RED,
                                  font=("Helvetica", 10), wraplength=500)
        self.msg_label.pack(fill="x", padx=20, pady=(4, 4))

        # Save button
        self.save_btn = tk.Button(card, text="Save Changes",
                                  bg=PURPLE1, fg=WHITE,
                                  activebackground=PURPLE2, activeforeground=WHITE,
                                  relief="flat", bd=0, cursor="hand2",
                                  font=("Helvetica", 12, "bold"),
                                  padx=20, pady=8, command=self._on_save)
        self.save_btn.pack(pady=(4, 20))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _info_row(self, parent, label: str, value: str):
        row = tk.Frame(parent, bg=WHITE)
        row.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(row, text=f"{label}:", bg=WHITE, fg=TEXT_GRAY,
                 font=("Helvetica", 11), width=12, anchor="w").pack(side="left")
        tk.Label(row, text=value, bg=WHITE, fg=TEXT_DARK,
                 font=("Helvetica", 11, "bold"), anchor="w").pack(side="left")

    def _field_label(self, parent, text):
        tk.Label(parent, text=text, bg=WHITE, fg=TEXT_DARK,
                 font=("Helvetica", 11, "bold"), anchor="w").pack(
            fill="x", padx=20, pady=(10, 2))

    def _entry(self, parent, var, show=None):
        e = tk.Entry(parent, textvariable=var, show=show or "",
                     bg=INPUT_BG, fg=TEXT_DARK,
                     font=("Helvetica", 11), relief="flat",
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=PURPLE1)
        e.pack(fill="x", padx=20, pady=(0, 4), ipady=6)
        e.bind("<FocusIn>",  lambda ev: e.config(highlightcolor=PURPLE1))
        e.bind("<FocusOut>", lambda ev: e.config(highlightcolor=BORDER))
        return e

    def _pwd_entry(self, parent, var):
        """Password entry with show/hide toggle. Returns (entry, state_list)."""
        frame = tk.Frame(parent, bg=WHITE)
        frame.pack(fill="x", padx=20, pady=(0, 4))

        entry = tk.Entry(frame, textvariable=var, show="•",
                         bg=INPUT_BG, fg=TEXT_DARK,
                         font=("Helvetica", 11), relief="flat",
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=PURPLE1)
        entry.pack(side="left", fill="x", expand=True, ipady=6)
        entry.bind("<FocusIn>",  lambda ev: entry.config(highlightcolor=PURPLE1))
        entry.bind("<FocusOut>", lambda ev: entry.config(highlightcolor=BORDER))

        visible = [False]

        def _toggle():
            visible[0] = not visible[0]
            entry.config(show="" if visible[0] else "•")
            btn.config(text="🙈" if visible[0] else "👁")

        btn = tk.Button(frame, text="👁", bg=INPUT_BG, fg=TEXT_GRAY,
                        relief="flat", bd=0, cursor="hand2",
                        font=("Helvetica", 11), command=_toggle)
        btn.pack(side="right", padx=(4, 0))

        return entry, visible

    # ── Save ──────────────────────────────────────────────────────────────────
    def _on_save(self):
        self._show_msg("")
        first   = self.first_var.get().strip()
        last    = self.last_var.get().strip()
        pwd     = self.pwd_var.get().strip()
        confirm = self.confirm_var.get().strip()

        if not first:
            return self._show_msg("First name cannot be empty.")
        if not last:
            return self._show_msg("Last name cannot be empty.")
        if pwd and len(pwd) < 6:
            return self._show_msg("Password must be at least 6 characters.")
        if pwd != confirm:
            return self._show_msg("Passwords do not match.")
        if not self.user.get("id"):
            return self._show_msg("User ID not found. Please log in again.")

        self._set_loading(True)
        threading.Thread(target=self._do_save,
                         args=(first, last, pwd), daemon=True).start()

    def _do_save(self, first: str, last: str, pwd: str):
        try:
            from db import execute
            if pwd:
                execute(
                    "UPDATE users SET first_name=%s, last_name=%s, name=%s, password=%s WHERE id=%s",
                    (first, last, f"{first} {last}", _hash(pwd), self.user["id"]))
            else:
                execute(
                    "UPDATE users SET first_name=%s, last_name=%s, name=%s WHERE id=%s",
                    (first, last, f"{first} {last}", self.user["id"]))

            self.user["first_name"] = first
            self.user["last_name"]  = last
            self.user["name"]       = f"{first} {last}"

            self.after(0, self._set_loading, False)
            self.after(0, self.pwd_var.set, "")
            self.after(0, self.confirm_var.set, "")
            self.after(0, self._show_msg, "Profile updated successfully!", GREEN)

        except Exception as exc:
            self.after(0, self._set_loading, False)
            self.after(0, self._show_msg, f"Error: {exc}")

    def _set_loading(self, loading: bool):
        self.save_btn.config(
            text="Saving…" if loading else "Save Changes",
            state="disabled" if loading else "normal",
            bg="#A0AEC0" if loading else PURPLE1)

    def _show_msg(self, msg: str, color: str = RED):
        self.msg_var.set(msg)
        self.msg_label.config(fg=color)
