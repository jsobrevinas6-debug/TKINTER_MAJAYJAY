import tkinter as tk
import threading

try:
    from db import login as db_login
except ImportError:
    db_login = None

# ── Palette ────────────────────────────────────────────────────────────────────
BG        = "#F7FAFC"
WHITE     = "#FFFFFF"
PURPLE    = "#667EEA"
PURPLE2   = "#764BA2"
BORDER    = "#E2E8F0"
TEXT_DARK = "#2D3748"
TEXT_GRAY = "#718096"
TEXT_MED  = "#4A5568"
INPUT_BG  = "#F7FAFC"
RED       = "#F56565"
SHADOW    = "#CBD5E0"


class LoginPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._obscure = True
        self._build_ui()

    def _build_ui(self):
        # ── Gradient header banner ─────────────────────────────────────────────
        banner = tk.Canvas(self, height=220, bg=BG, highlightthickness=0)
        banner.pack(fill="x")
        banner.bind("<Configure>", self._draw_banner)
        self._banner = banner

        # ── Centered card wrapper ──────────────────────────────────────────────
        outer = tk.Frame(self, bg=BG)
        outer.pack(expand=True, fill="both")

        center = tk.Frame(outer, bg=BG)
        center.place(relx=0.5, rely=0.5, anchor="center")

        # Shadow frame (offset trick)
        shadow = tk.Frame(center, bg=SHADOW)
        shadow.pack(padx=0, pady=0)

        card = tk.Frame(shadow, bg=WHITE, padx=36, pady=32)
        card.pack(padx=2, pady=2)

        # ── Email ──────────────────────────────────────────────────────────────
        self._label(card, "Email Address")
        self.email_var = tk.StringVar()
        self._input(card, self.email_var)

        # ── Password ───────────────────────────────────────────────────────────
        self._label(card, "Password")
        pwd_wrap = tk.Frame(card, bg=WHITE, highlightthickness=1,
                            highlightbackground=BORDER,
                            highlightcolor=PURPLE)
        pwd_wrap.pack(fill="x", pady=(0, 4))
        self.password_var = tk.StringVar()
        self.pwd_entry = tk.Entry(pwd_wrap, textvariable=self.password_var,
                                  show="•", bg=INPUT_BG, fg=TEXT_DARK,
                                  insertbackground=PURPLE,
                                  relief="flat", bd=0,
                                  font=("Segoe UI", 11))
        self.pwd_entry.pack(side="left", fill="x", expand=True,
                            ipady=10, padx=(12, 0))
        self.pwd_entry.bind("<Return>", lambda e: self._on_login())
        self.pwd_entry.bind("<FocusIn>",
            lambda e: pwd_wrap.config(highlightbackground=PURPLE,
                                      highlightcolor=PURPLE))
        self.pwd_entry.bind("<FocusOut>",
            lambda e: pwd_wrap.config(highlightbackground=BORDER))

        eye_btn = tk.Label(pwd_wrap, text="👁", bg=INPUT_BG, fg=TEXT_GRAY,
                           font=("Segoe UI", 11), cursor="hand2", padx=10)
        eye_btn.pack(side="right")
        eye_btn.bind("<Button-1>", lambda e: self._toggle_pwd())

        # ── Error ──────────────────────────────────────────────────────────────
        self.error_var = tk.StringVar()
        tk.Label(card, textvariable=self.error_var,
                 bg=WHITE, fg=RED, font=("Segoe UI", 9),
                 wraplength=300, justify="left").pack(fill="x", pady=(2, 0))

        # ── Divider ────────────────────────────────────────────────────────────
        div = tk.Frame(card, bg=WHITE)
        div.pack(fill="x", pady=(14, 14))
        tk.Frame(div, bg=BORDER, height=1).place(relx=0, rely=0.5,
                                                  relwidth=0.42, anchor="w")
        tk.Label(div, text="  Sign In  ", bg=WHITE, fg=TEXT_GRAY,
                 font=("Segoe UI", 9)).pack()
        tk.Frame(div, bg=BORDER, height=1).place(relx=1, rely=0.5,
                                                  relwidth=0.42, anchor="e")

        # ── Sign In button ─────────────────────────────────────────────────────
        self.sign_btn = tk.Button(card, text="Sign In →",
                                   bg=PURPLE, fg=WHITE,
                                   activebackground=PURPLE2,
                                   activeforeground=WHITE,
                                   relief="flat", bd=0,
                                   font=("Segoe UI", 12, "bold"),
                                   cursor="hand2",
                                   command=self._on_login)
        self.sign_btn.pack(fill="x", ipady=11)
        self.sign_btn.bind("<Enter>",
            lambda e: self.sign_btn.config(bg=PURPLE2))
        self.sign_btn.bind("<Leave>",
            lambda e: self.sign_btn.config(
                bg="#A0AEC0" if self.sign_btn["state"] == "disabled"
                else PURPLE))

        # ── Register link ──────────────────────────────────────────────────────
        reg_row = tk.Frame(card, bg=WHITE)
        reg_row.pack(pady=(18, 0))
        tk.Label(reg_row, text="Don't have an account? ",
                 bg=WHITE, fg=TEXT_MED,
                 font=("Segoe UI", 10)).pack(side="left")
        reg = tk.Label(reg_row, text="Register here",
                       bg=WHITE, fg=PURPLE, cursor="hand2",
                       font=("Segoe UI", 10, "bold", "underline"))
        reg.pack(side="left")
        reg.bind("<Button-1>", lambda _: self.app.show_register())

    # ── Banner draw ────────────────────────────────────────────────────────────
    def _draw_banner(self, event=None):
        c = self._banner
        w = c.winfo_width()
        h = c.winfo_height()
        c.delete("all")
        # Simulate gradient with stacked rectangles
        steps = 40
        for i in range(steps):
            r1, g1, b1 = 0x66, 0x7E, 0xEA   # PURPLE
            r2, g2, b2 = 0x76, 0x4B, 0xA2   # PURPLE2
            t = i / steps
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            color = f"#{r:02x}{g:02x}{b:02x}"
            c.create_rectangle(0, i * h // steps,
                                w, (i + 1) * h // steps,
                                fill=color, outline="")
        # Logo circle
        cx, cy, r = w // 2, h // 2 - 10, 38
        c.create_oval(cx - r, cy - r, cx + r, cy + r,
                      fill=WHITE, outline="", stipple="")
        c.create_text(cx, cy, text="MJS",
                      fill=PURPLE, font=("Segoe UI", 18, "bold"))
        # Title
        c.create_text(cx, cy + r + 18, text="Majayjay Scholars",
                      fill=WHITE, font=("Segoe UI", 16, "bold"))
        c.create_text(cx, cy + r + 38, text="Welcome back! Please sign in.",
                      fill="#D6BCFA", font=("Segoe UI", 10))

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _label(self, parent, text):
        tk.Label(parent, text=text, bg=WHITE, fg=TEXT_DARK,
                 font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill="x", pady=(10, 4))

    def _input(self, parent, var):
        wrap = tk.Frame(parent, bg=WHITE, highlightthickness=1,
                        highlightbackground=BORDER,
                        highlightcolor=PURPLE)
        wrap.pack(fill="x", pady=(0, 4))
        e = tk.Entry(wrap, textvariable=var,
                     bg=INPUT_BG, fg=TEXT_DARK,
                     insertbackground=PURPLE,
                     relief="flat", bd=0,
                     font=("Segoe UI", 11))
        e.pack(fill="x", ipady=10, padx=12)
        e.bind("<Return>", lambda ev: self._on_login())
        e.bind("<FocusIn>",
               lambda ev: wrap.config(highlightbackground=PURPLE))
        e.bind("<FocusOut>",
               lambda ev: wrap.config(highlightbackground=BORDER))
        return e

    def _toggle_pwd(self):
        self._obscure = not self._obscure
        self.pwd_entry.config(show="" if not self._obscure else "•")

    # ── Login logic ────────────────────────────────────────────────────────────
    def _on_login(self):
        self.error_var.set("")
        email    = self.email_var.get().strip()
        password = self.password_var.get().strip()
        if not email:
            return self.error_var.set("Please enter your email.")
        if "@" not in email:
            return self.error_var.set("Please enter a valid email.")
        if not password:
            return self.error_var.set("Please enter your password.")
        self._set_loading(True)
        threading.Thread(target=self._do_login,
                         args=(email, password), daemon=True).start()

    def _do_login(self, email, password):
        try:
            if db_login is None:
                raise RuntimeError("db module not found.")
            user = db_login(email, password)
            self.after(0, self._on_success, user)
        except ValueError as e:
            self.after(0, self._on_error, str(e))
        except Exception as e:
            self.after(0, self._on_error, f"Connection error: {e}")

    def _on_success(self, user):
        self._set_loading(False)
        self.app.on_login_success(user)

    def _on_error(self, msg):
        self._set_loading(False)
        self.error_var.set(msg)

    def _set_loading(self, loading):
        self.sign_btn.config(
            text="Signing in…" if loading else "Sign In →",
            state="disabled" if loading else "normal",
            bg="#A0AEC0" if loading else PURPLE)
