import tkinter as tk
from tkinter import messagebox
import threading

try:
    from db import fetch_one, register_user
    from email_service import send_otp, verify_otp, clear_otp
    EMAIL_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    fetch_one = register_user = send_otp = verify_otp = clear_otp = None
    EMAIL_AVAILABLE = False

# ── Palette ────────────────────────────────────────────────────────────────────
BG       = "#F7FAFC"
WHITE    = "#FFFFFF"
PURPLE   = "#667EEA"
PURPLE2  = "#764BA2"
BORDER   = "#E2E8F0"
DARK     = "#2D3748"
GRAY     = "#718096"
MED      = "#4A5568"
INPUT_BG = "#F7FAFC"
DISABLED = "#EDF2F7"
RED      = "#F56565"
GREEN    = "#48BB78"
SHADOW   = "#CBD5E0"


class RegistrationPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app              = app
        self._code_sent       = False
        self._email_verified  = False
        self._show_pwd        = False
        self._vars            = {}
        self._profile_entries = {}
        self._sent_code       = None
        self._build()

    def _build(self):
        # ── Gradient header banner ─────────────────────────────────────────────
        banner = tk.Canvas(self, height=220, bg=BG, highlightthickness=0)
        banner.pack(fill="x")
        banner.bind("<Configure>", self._draw_banner)
        self._banner = banner

        # Back button overlaid top-left on banner
        back = tk.Label(self, text="← Back", bg=PURPLE, fg=WHITE,
                        font=("Segoe UI", 10, "bold"), cursor="hand2",
                        padx=10, pady=4)
        back.place(x=12, y=12)
        back.bind("<Button-1>", lambda _: self.app.show_login())
        back.bind("<Enter>",    lambda e: back.config(bg=PURPLE2))
        back.bind("<Leave>",    lambda e: back.config(bg=PURPLE))

        # ── Scrollable body ────────────────────────────────────────────────────
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

        def _scroll(e):
            try:
                scroll_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            except Exception:
                pass
        scroll_canvas.bind("<MouseWheel>", _scroll)
        inner.bind("<MouseWheel>", _scroll)

        # ── Shadow card ────────────────────────────────────────────────────────
        center = tk.Frame(inner, bg=BG)
        center.pack(pady=(24, 30))

        shadow = tk.Frame(center, bg=SHADOW)
        shadow.pack()
        card = tk.Frame(shadow, bg=WHITE, padx=36, pady=28)
        card.pack(padx=2, pady=2)

        # ── STEP 1: Email ──────────────────────────────────────────────────────
        self._slabel(card, "① Verify Your Email")
        self._flabel(card, "Email Address *")
        self._vars["email"] = tk.StringVar()
        self._email_entry = self._input(card, self._vars["email"])

        self._email_err = tk.StringVar()
        tk.Label(card, textvariable=self._email_err,
                 bg=WHITE, fg=RED, font=("Segoe UI", 9),
                 wraplength=300, justify="left").pack(fill="x")

        self._send_btn = tk.Button(
            card, text="📧 Send Verification Code",
            bg=PURPLE, fg=WHITE, activebackground=PURPLE2,
            activeforeground=WHITE, relief="flat", bd=0,
            font=("Segoe UI", 11, "bold"), cursor="hand2",
            command=self._send_code)
        self._send_btn.pack(fill="x", ipady=10, pady=(8, 4))
        self._send_btn.bind("<Enter>",
            lambda e: self._send_btn.config(bg=PURPLE2))
        self._send_btn.bind("<Leave>",
            lambda e: self._send_btn.config(
                bg="#A0AEC0" if self._send_btn["state"] == "disabled"
                else PURPLE))

        # ── STEP 2: OTP (hidden until sent) ───────────────────────────────────
        self._otp_card = tk.Frame(card, bg=WHITE)

        self._slabel(self._otp_card, "② Enter Verification Code")
        self._flabel(self._otp_card, "6-Digit Code *")
        self._vars["otp"] = tk.StringVar()
        self._otp_entry   = self._input(self._otp_card, self._vars["otp"])

        self._otp_err = tk.StringVar()
        tk.Label(self._otp_card, textvariable=self._otp_err,
                 bg=WHITE, fg=RED, font=("Segoe UI", 9)).pack(fill="x")

        self._verify_btn = tk.Button(
            self._otp_card, text="✔ Verify Code",
            bg=PURPLE, fg=WHITE, activebackground=PURPLE2,
            activeforeground=WHITE, relief="flat", bd=0,
            font=("Segoe UI", 11, "bold"), cursor="hand2",
            command=self._verify_code)
        self._verify_btn.pack(fill="x", ipady=10, pady=(8, 4))
        self._verify_btn.bind("<Enter>",
            lambda e: self._verify_btn.config(bg=PURPLE2))
        self._verify_btn.bind("<Leave>",
            lambda e: self._verify_btn.config(
                bg="#A0AEC0" if self._verify_btn["state"] == "disabled"
                else PURPLE))

        resend_row = tk.Frame(self._otp_card, bg=WHITE)
        resend_row.pack(anchor="w", pady=(2, 0))
        tk.Label(resend_row, text="Didn't receive it?",
                 bg=WHITE, fg=GRAY, font=("Segoe UI", 9)).pack(side="left")
        lnk = tk.Label(resend_row, text=" Resend Code",
                       bg=WHITE, fg=PURPLE, cursor="hand2",
                       font=("Segoe UI", 9, "bold", "underline"))
        lnk.pack(side="left")
        lnk.bind("<Button-1>", lambda _: self._send_code(resend=True))

        # ── STEP 3: Profile (hidden until verified) ────────────────────────────
        self._profile_card = tk.Frame(card, bg=WHITE)

        self._slabel(self._profile_card, "③ Personal Information")

        for label, key in [("First Name *",  "first_name"),
                            ("Middle Name",   "middle_name"),
                            ("Last Name *",   "last_name")]:
            self._flabel(self._profile_card, label)
            self._vars[key] = tk.StringVar()
            e = self._input(self._profile_card, self._vars[key], disabled=True)
            self._profile_entries[key] = e

        self._slabel(self._profile_card, "④ Set Password")

        for label, key in [("Password *",         "password"),
                            ("Confirm Password *", "confirm_password")]:
            self._flabel(self._profile_card, label)
            self._vars[key] = tk.StringVar()
            pwd_wrap = tk.Frame(self._profile_card, bg=WHITE,
                                highlightthickness=1,
                                highlightbackground=BORDER,
                                highlightcolor=PURPLE)
            pwd_wrap.pack(fill="x", pady=(0, 4))
            e = tk.Entry(pwd_wrap, textvariable=self._vars[key],
                         show="•", state="disabled",
                         bg=DISABLED, fg=DARK,
                         disabledbackground=DISABLED,
                         disabledforeground="#A0AEC0",
                         insertbackground=PURPLE,
                         relief="flat", bd=0,
                         font=("Segoe UI", 11))
            e.pack(side="left", fill="x", expand=True, ipady=10, padx=(12, 0))
            e.bind("<FocusIn>",
                   lambda ev, w=pwd_wrap: w.config(highlightbackground=PURPLE))
            e.bind("<FocusOut>",
                   lambda ev, w=pwd_wrap: w.config(highlightbackground=BORDER))
            self._profile_entries[key] = e

        eye = tk.Label(self._profile_card, text="👁 Show/Hide Password",
                       bg=WHITE, fg=GRAY, cursor="hand2",
                       font=("Segoe UI", 9))
        eye.pack(anchor="e", pady=(2, 0))
        eye.bind("<Button-1>", lambda e: self._toggle_pwd())

        self._reg_err = tk.StringVar()
        tk.Label(self._profile_card, textvariable=self._reg_err,
                 bg=WHITE, fg=RED, font=("Segoe UI", 9),
                 wraplength=300, justify="left").pack(fill="x", pady=(4, 0))

        # Divider
        div = tk.Frame(self._profile_card, bg=WHITE)
        div.pack(fill="x", pady=(14, 14))
        tk.Frame(div, bg=BORDER, height=1).place(relx=0, rely=0.5,
                                                  relwidth=0.3, anchor="w")
        tk.Label(div, text="  Complete Registration  ",
                 bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 9)).pack()
        tk.Frame(div, bg=BORDER, height=1).place(relx=1, rely=0.5,
                                                  relwidth=0.3, anchor="e")

        self._reg_btn = tk.Button(
            self._profile_card, text="🎓 Register →",
            bg="#A0AEC0", fg=WHITE, relief="flat", bd=0,
            font=("Segoe UI", 12, "bold"), cursor="hand2",
            state="disabled", command=self._complete)
        self._reg_btn.pack(fill="x", ipady=11)
        self._reg_btn.bind("<Enter>",
            lambda e: self._reg_btn.config(
                bg=PURPLE2 if self._reg_btn["state"] == "normal" else "#A0AEC0"))
        self._reg_btn.bind("<Leave>",
            lambda e: self._reg_btn.config(
                bg="#A0AEC0" if self._reg_btn["state"] == "disabled"
                else PURPLE))

        # ── Footer ─────────────────────────────────────────────────────────────
        foot = tk.Frame(card, bg=WHITE)
        foot.pack(pady=(18, 0))
        tk.Label(foot, text="Already have an account? ",
                 bg=WHITE, fg=MED,
                 font=("Segoe UI", 10)).pack(side="left")
        lnk2 = tk.Label(foot, text="Sign in",
                         bg=WHITE, fg=PURPLE, cursor="hand2",
                         font=("Segoe UI", 10, "bold", "underline"))
        lnk2.pack(side="left")
        lnk2.bind("<Button-1>", lambda _: self.app.show_login())

    # ── Banner draw ────────────────────────────────────────────────────────────
    def _draw_banner(self, event=None):
        c = self._banner
        w = c.winfo_width()
        h = c.winfo_height()
        c.delete("all")
        steps = 40
        for i in range(steps):
            r1, g1, b1 = 0x66, 0x7E, 0xEA
            r2, g2, b2 = 0x76, 0x4B, 0xA2
            t = i / steps
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            c.create_rectangle(0, i * h // steps,
                                w, (i + 1) * h // steps,
                                fill=f"#{r:02x}{g:02x}{b:02x}", outline="")
        cx, cy, r = w // 2, h // 2 - 10, 38
        c.create_oval(cx - r, cy - r, cx + r, cy + r,
                      fill=WHITE, outline="")
        c.create_text(cx, cy, text="MJS",
                      fill=PURPLE, font=("Segoe UI", 18, "bold"))
        c.create_text(cx, cy + r + 18, text="Majayjay Scholars",
                      fill=WHITE, font=("Segoe UI", 16, "bold"))
        c.create_text(cx, cy + r + 38, text="Create your account below.",
                      fill="#D6BCFA", font=("Segoe UI", 10))

    # ── Widget helpers ─────────────────────────────────────────────────────────
    def _slabel(self, parent, text):
        tk.Label(parent, text=text, bg=WHITE, fg=PURPLE,
                 font=("Segoe UI", 11, "bold"),
                 anchor="w").pack(fill="x", pady=(14, 4))

    def _flabel(self, parent, text):
        tk.Label(parent, text=text, bg=WHITE, fg=DARK,
                 font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill="x", pady=(8, 4))

    def _input(self, parent, var, disabled=False):
        state = "disabled" if disabled else "normal"
        bg    = DISABLED   if disabled else INPUT_BG
        wrap  = tk.Frame(parent, bg=WHITE, highlightthickness=1,
                         highlightbackground=BORDER,
                         highlightcolor=PURPLE)
        wrap.pack(fill="x", pady=(0, 4))
        e = tk.Entry(wrap, textvariable=var,
                     state=state, bg=bg, fg=DARK,
                     disabledbackground=DISABLED,
                     disabledforeground="#A0AEC0",
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
        ch = "" if self._show_pwd else "•"
        for key in ("password", "confirm_password"):
            e = self._profile_entries[key]
            if str(e["state"]) == "normal":
                e.config(show=ch)

    # ── Step 1: Send OTP ───────────────────────────────────────────────────────
    def _send_code(self, resend=False):
        self._email_err.set("")
        email = self._vars["email"].get().strip()
        if not email:
            return self._email_err.set("Please enter your email.")
        if "@" not in email or "." not in email:
            return self._email_err.set("Enter a valid email address.")
        self._send_btn.config(state="disabled", text="Sending…", bg="#A0AEC0")
        threading.Thread(target=self._do_send,
                         args=(email, resend), daemon=True).start()

    def _do_send(self, email, resend):
        try:
            if not resend and fetch_one:
                existing = fetch_one(
                    "SELECT user_id FROM users WHERE email=%s", (email,))
                if existing:
                    self.after(0, self._email_err.set,
                               "This email is already registered.")
                    self.after(0, lambda: self._send_btn.config(
                        state="normal",
                        text="📧 Send Verification Code",
                        bg=PURPLE))
                    return

            if not send_otp:
                self.after(0, self._email_err.set,
                           "Email service is unavailable. Cannot send OTP.")
                self.after(0, lambda: self._send_btn.config(
                    state="normal",
                    text="📧 Send Verification Code",
                    bg=PURPLE))
                return

            code = send_otp(email)
            self._sent_code = code
            self.after(0, self._on_code_sent, email)

        except Exception as e:
            self.after(0, self._email_err.set, f"Email sending failed: {e}")
            self.after(0, lambda: self._send_btn.config(
                state="normal",
                text="📧 Send Verification Code",
                bg=PURPLE))

    def _on_code_sent(self, email):
        self._code_sent = True
        self._send_btn.config(state="disabled", text="✔ Code Sent", bg=GREEN)
        self._email_entry.config(state="disabled", bg=DISABLED)
        self._otp_card.pack(fill="x")
        messagebox.showinfo(
            "Code Sent! 📧",
            f"A 6-digit verification code was sent to:\n{email}\n\n"
            f"Please check your inbox and spam folder.")

    # ── Step 2: Verify OTP ─────────────────────────────────────────────────────
    def _verify_code(self):
        self._otp_err.set("")
        code  = self._vars["otp"].get().strip()
        email = self._vars["email"].get().strip()
        if len(code) != 6 or not code.isdigit():
            return self._otp_err.set("Please enter the 6-digit code.")
        self._verify_btn.config(state="disabled",
                                text="Verifying…", bg="#A0AEC0")
        threading.Thread(target=self._do_verify,
                         args=(email, code), daemon=True).start()

    def _do_verify(self, email, code):
        try:
            if not verify_otp:
                self.after(0, self._otp_err.set,
                           "Email service unavailable. Cannot verify OTP.")
                self.after(0, lambda: self._verify_btn.config(
                    state="normal", text="✔ Verify Code", bg=PURPLE))
                return
            ok = verify_otp(email, code)
            if ok:
                self.after(0, self._on_verified)
            else:
                self.after(0, self._otp_err.set,
                           "Invalid or expired code. Try again.")
                self.after(0, lambda: self._verify_btn.config(
                    state="normal", text="✔ Verify Code", bg=PURPLE))
        except Exception as e:
            self.after(0, self._otp_err.set, str(e))
            self.after(0, lambda: self._verify_btn.config(
                state="normal", text="✔ Verify Code", bg=PURPLE))

    def _on_verified(self):
        self._email_verified = True
        self._verify_btn.config(state="disabled",
                                text="✅ Email Verified!", bg=GREEN)
        self._otp_entry.config(state="disabled", bg=DISABLED)
        self._profile_card.pack(fill="x")
        for key, entry in self._profile_entries.items():
            entry.config(state="normal", bg=INPUT_BG,
                         show="•" if "password" in key else "")
        self._reg_btn.config(state="normal", bg=PURPLE)
        messagebox.showinfo("Verified! ✅",
                            "Email verified!\nNow complete your profile below.")

    # ── Step 3: Complete registration ──────────────────────────────────────────
    def _complete(self):
        self._reg_err.set("")
        if not self._email_verified:
            return self._reg_err.set("Please verify your email first.")

        first = self._vars["first_name"].get().strip()
        mid   = self._vars["middle_name"].get().strip()
        last  = self._vars["last_name"].get().strip()
        email = self._vars["email"].get().strip()
        pwd   = self._vars["password"].get().strip()
        cpwd  = self._vars["confirm_password"].get().strip()

        if not first:
            return self._reg_err.set("First name is required.")
        if not last:
            return self._reg_err.set("Last name is required.")
        if not pwd:
            return self._reg_err.set("Password is required.")
        if len(pwd) < 6:
            return self._reg_err.set("Password must be at least 6 characters.")
        if pwd != cpwd:
            return self._reg_err.set("Passwords do not match.")

        self._reg_btn.config(state="disabled",
                             text="Registering…", bg="#A0AEC0")
        threading.Thread(target=self._do_register,
                         args=(email, pwd, first, mid, last),
                         daemon=True).start()

    def _do_register(self, email, pwd, first, mid, last):
        try:
            if register_user:
                register_user(email, pwd, first, mid or None, last)
            if clear_otp:
                clear_otp(email)
            self.after(0, self._on_registered)
        except Exception as e:
            self.after(0, lambda: self._reg_btn.config(
                state="normal", text="🎓 Register →", bg=PURPLE))
            self.after(0, self._reg_err.set, f"Error: {e}")

    def _on_registered(self):
        self._reg_btn.config(state="normal",
                             text="🎓 Register →", bg=PURPLE)
        messagebox.showinfo("Success! 🎉",
                            "Account created successfully!\nYou can now sign in.")
        self.app.show_login()
