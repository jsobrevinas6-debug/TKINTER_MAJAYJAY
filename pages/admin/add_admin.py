import tkinter as tk
from tkinter import ttk
import threading

BG       = "#F7FAFC"
WHITE    = "#FFFFFF"
PURPLE   = "#667EEA"
PURPLE2  = "#764BA2"
BORDER   = "#E2E8F0"
DARK     = "#2D3748"
GRAY     = "#718096"
MED      = "#4A5568"
INPUT_BG = "#F7FAFC"
SHADOW   = "#CBD5E0"
DIVIDER  = "#E2E8F0"
RED      = "#F56565"
GREEN    = "#48BB78"


class AddAdminPage(tk.Frame):
    def __init__(self, parent, app=None, on_success=None, **_):
        super().__init__(parent, bg=BG)
        self.app        = app
        self.on_success = on_success  # callback after successful add
        self._show_pwd  = False
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        # Top bar
        topbar = tk.Frame(self, bg=WHITE, height=64)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Frame(topbar, bg=BORDER, height=1).pack(side="bottom", fill="x")
        tk.Label(topbar, text="Add Admin Account",
                 bg=WHITE, fg=DARK,
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=28, pady=16)

        # Scrollable body
        scroll_canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        scroll_canvas.pack(fill="both", expand=True)

        inner = tk.Frame(scroll_canvas, bg=BG)
        wid   = scroll_canvas.create_window((0, 0), window=inner, anchor="n")

        def _update_scroll(e=None):
            bbox = scroll_canvas.bbox("all")
            if bbox:
                scroll_canvas.configure(scrollregion=bbox)
        inner.bind("<Configure>", _update_scroll)
        scroll_canvas.bind("<Configure>",
                           lambda e: scroll_canvas.itemconfig(wid, width=e.width))
        scroll_canvas.bind("<MouseWheel>",
                           lambda e: scroll_canvas.yview_scroll(
                               int(-1 * (e.delta / 120)), "units"))

        # Shadow card
        center = tk.Frame(inner, bg=BG)
        center.pack(pady=(24, 32), padx=32, fill="x")
        shadow = tk.Frame(center, bg=SHADOW)
        shadow.pack(fill="x")
        card = tk.Frame(shadow, bg=WHITE, padx=36, pady=32)
        card.pack(fill="x", padx=2, pady=2)

        # ── Section: Personal Information ──────────────────────────────────────
        self._section(card, "👤  Personal Information")

        row1 = tk.Frame(card, bg=WHITE)
        row1.pack(fill="x")
        self._field_col(row1, "First Name *",  "first_name",  side="left")
        tk.Frame(row1, bg=WHITE, width=16).pack(side="left")
        self._field_col(row1, "Middle Name",   "middle_name", side="left")
        tk.Frame(row1, bg=WHITE, width=16).pack(side="left")
        self._field_col(row1, "Last Name *",   "last_name",   side="left")

        # ── Section: Account Credentials ──────────────────────────────────────
        self._section(card, "🔐  Account Credentials")

        self._flabel(card, "Email Address *")
        self._input(card, "email")

        self._flabel(card, "Password *")
        pwd_wrap = tk.Frame(card, bg=WHITE, highlightthickness=1,
                            highlightbackground=BORDER, highlightcolor=PURPLE)
        pwd_wrap.pack(fill="x", pady=(0, 4))
        self._vars["password"] = tk.StringVar()
        self._pwd_entry = tk.Entry(pwd_wrap, textvariable=self._vars["password"],
                                   show="•", bg=INPUT_BG, fg=DARK,
                                   insertbackground=PURPLE,
                                   relief="flat", bd=0,
                                   font=("Segoe UI", 11))
        self._pwd_entry.pack(side="left", fill="x", expand=True,
                             ipady=10, padx=(12, 0))
        self._pwd_entry.bind("<FocusIn>",
            lambda e: pwd_wrap.config(highlightbackground=PURPLE))
        self._pwd_entry.bind("<FocusOut>",
            lambda e: pwd_wrap.config(highlightbackground=BORDER))
        eye = tk.Label(pwd_wrap, text="👁", bg=INPUT_BG, fg=GRAY,
                       font=("Segoe UI", 11), cursor="hand2", padx=10)
        eye.pack(side="right")
        eye.bind("<Button-1>", lambda e: self._toggle_pwd())

        self._flabel(card, "Confirm Password *")
        self._input(card, "confirm_password", show="•")

        # ── Message ────────────────────────────────────────────────────────────
        self.msg_var = tk.StringVar()
        self.msg_lbl = tk.Label(card, textvariable=self.msg_var,
                                bg=WHITE, fg=RED,
                                font=("Segoe UI", 9),
                                wraplength=500, justify="left")
        self.msg_lbl.pack(fill="x", pady=(8, 0))

        # ── Divider ────────────────────────────────────────────────────────────
        div = tk.Frame(card, bg=WHITE)
        div.pack(fill="x", pady=(16, 16))
        tk.Frame(div, bg=BORDER, height=1).place(relx=0, rely=0.5,
                                                  relwidth=0.38, anchor="w")
        tk.Label(div, text="  Create Account  ",
                 bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 9)).pack()
        tk.Frame(div, bg=BORDER, height=1).place(relx=1, rely=0.5,
                                                  relwidth=0.38, anchor="e")

        # ── Submit button ──────────────────────────────────────────────────────
        self.submit_btn = tk.Button(card, text="Create Account →",
                                    bg=PURPLE, fg=WHITE,
                                    activebackground=PURPLE2,
                                    activeforeground=WHITE,
                                    relief="flat", bd=0,
                                    font=("Segoe UI", 12, "bold"),
                                    cursor="hand2",
                                    command=self._submit)
        self.submit_btn.pack(fill="x", ipady=11)
        self.submit_btn.bind("<Enter>",
            lambda e: self.submit_btn.config(bg=PURPLE2))
        self.submit_btn.bind("<Leave>",
            lambda e: self.submit_btn.config(
                bg="#A0AEC0" if self.submit_btn["state"] == "disabled"
                else PURPLE))

    # ── Widget helpers ─────────────────────────────────────────────────────────
    def _vars_init(self):
        if not hasattr(self, "_vars"):
            self._vars = {}

    def _section(self, parent, text):
        tk.Frame(parent, bg=DIVIDER, height=1).pack(fill="x", pady=(20, 0))
        tk.Label(parent, text=text, bg=WHITE, fg=PURPLE,
                 font=("Segoe UI", 11, "bold"),
                 anchor="w").pack(fill="x", pady=(10, 4))

    def _flabel(self, parent, text):
        tk.Label(parent, text=text, bg=WHITE, fg=DARK,
                 font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill="x", pady=(10, 4))

    def _input(self, parent, key, show=None):
        if not hasattr(self, "_vars"):
            self._vars = {}
        wrap = tk.Frame(parent, bg=WHITE, highlightthickness=1,
                        highlightbackground=BORDER, highlightcolor=PURPLE)
        wrap.pack(fill="x", pady=(0, 4))
        self._vars[key] = tk.StringVar()
        e = tk.Entry(wrap, textvariable=self._vars[key],
                     show=show or "",
                     bg=INPUT_BG, fg=DARK,
                     insertbackground=PURPLE,
                     relief="flat", bd=0,
                     font=("Segoe UI", 11))
        e.pack(fill="x", ipady=10, padx=12)
        e.bind("<FocusIn>",
               lambda ev, w=wrap: w.config(highlightbackground=PURPLE))
        e.bind("<FocusOut>",
               lambda ev, w=wrap: w.config(highlightbackground=BORDER))
        return e

    def _field_col(self, parent, label, key, side="left"):
        if not hasattr(self, "_vars"):
            self._vars = {}
        col = tk.Frame(parent, bg=WHITE)
        col.pack(side=side, fill="x", expand=True)
        self._flabel(col, label)
        wrap = tk.Frame(col, bg=WHITE, highlightthickness=1,
                        highlightbackground=BORDER, highlightcolor=PURPLE)
        wrap.pack(fill="x", pady=(0, 4))
        self._vars[key] = tk.StringVar()
        e = tk.Entry(wrap, textvariable=self._vars[key],
                     bg=INPUT_BG, fg=DARK,
                     insertbackground=PURPLE,
                     relief="flat", bd=0,
                     font=("Segoe UI", 11))
        e.pack(fill="x", ipady=10, padx=12)
        e.bind("<FocusIn>",
               lambda ev, w=wrap: w.config(highlightbackground=PURPLE))
        e.bind("<FocusOut>",
               lambda ev, w=wrap: w.config(highlightbackground=BORDER))
        return e

    def _toggle_pwd(self):
        self._show_pwd = not self._show_pwd
        self._pwd_entry.config(show="" if self._show_pwd else "•")

    # ── Submit ─────────────────────────────────────────────────────────────────
    def _submit(self):
        self.msg_var.set("")
        first   = self._vars["first_name"].get().strip()
        middle  = self._vars["middle_name"].get().strip()
        last    = self._vars["last_name"].get().strip()
        email   = self._vars["email"].get().strip()
        pwd     = self._vars["password"].get().strip()
        confirm = self._vars["confirm_password"].get().strip()
        role    = "admin"

        if not first:
            return self._show_msg("Please enter the first name.")
        if not last:
            return self._show_msg("Please enter the last name.")
        if not email or "@" not in email:
            return self._show_msg("Please enter a valid email address.")
        if not pwd:
            return self._show_msg("Please enter a password.")
        if len(pwd) < 6:
            return self._show_msg("Password must be at least 6 characters.")
        if pwd != confirm:
            return self._show_msg("Passwords do not match.")

        self._set_loading(True)
        threading.Thread(target=self._do_create,
                         args=(first, middle, last, email, pwd, role),
                         daemon=True).start()

    def _do_create(self, first, middle, last, email, pwd, role):
        try:
            from db import register_user, fetch_one
            existing = fetch_one(
                "SELECT user_id FROM users WHERE email = %s", (email,))
            if existing:
                self.after(0, self._show_msg,
                           "An account with this email already exists.")
                self.after(0, self._set_loading, False)
                return
            register_user(email, pwd, first, middle or None, last,
                          user_type=role)
            self.after(0, self._on_success, role, email)
        except Exception as exc:
            self.after(0, self._show_msg, f"Error: {exc}")
            self.after(0, self._set_loading, False)

    def _on_success(self, role, email):
        self._set_loading(False)
        self._show_msg(f"✅ Admin account created for {email}!", GREEN)
        for key, var in self._vars.items():
            var.set("")
        if self.on_success:
            self.after(1500, self.on_success)

    def _set_loading(self, loading: bool):
        self.submit_btn.config(
            text="Creating…" if loading else "Create Account →",
            state="disabled" if loading else "normal",
            bg="#A0AEC0" if loading else PURPLE)

    def _show_msg(self, msg: str, color: str = RED):
        self.msg_var.set(msg)
        self.msg_lbl.config(fg=color)
