import tkinter as tk
from tkinter import filedialog, messagebox
import threading

try:
    from student_dashboard import supabase, BG, WHITE, PURPLE, PURPLE2, BORDER, TEXT_DARK, TEXT_GRAY
except ImportError:
    BG        = "#F7FAFC"
    WHITE     = "#FFFFFF"
    PURPLE    = "#667EEA"
    PURPLE2   = "#764BA2"
    BORDER    = "#E2E8F0"
    TEXT_DARK = "#2D3748"
    TEXT_GRAY = "#718096"
    supabase  = None

BG        = "#F3F0FF"
CARD_BG   = "#FFFFFF"
INPUT_BG  = "#EDE9FF"
DISABLED  = "#E9E4F7"
VIOLET    = "#667EEA"
VIOLET2   = "#764BA2"
ACCENT    = "#9B8FEF"
BORDER    = "#C4B5FD"
TEXT_DARK = "#2D2748"
TEXT_GRAY = "#6B5FA6"
WHITE     = "#FFFFFF"
RED       = "#E53E3E"
GREEN_TXT = "#48BB78"


class ProfileFrame(tk.Frame):
    def __init__(self, parent, name, email, dashboard, **_):
        super().__init__(parent, bg=BG)
        self.name        = name
        self.email       = email
        self.dashboard   = dashboard
        self._editing    = False
        self._saving     = False
        self._photo_path = None
        self._entries    = {}
        self._build()

    # =========================================================================
    # BUILD
    # =========================================================================
    def _build(self):
        canvas = tk.Canvas(self, bg="#F3F0FF", highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        inner = tk.Frame(canvas, bg="#F3F0FF")
        wid   = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(wid, width=e.width)
        canvas.bind("<Configure>", _resize)
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # ── Gradient header ───────────────────────────────────────────────────
        hdr_canvas = tk.Canvas(inner, height=200, highlightthickness=0)
        hdr_canvas.pack(fill="x")

        def _draw_gradient(e=None):
            hdr_canvas.delete("all")
            w = hdr_canvas.winfo_width()
            h = hdr_canvas.winfo_height()
            steps = 40
            for i in range(steps):
                t = i / steps
                r = int(0x66 + (0x76 - 0x66) * t)
                g = int(0x7E + (0x4B - 0x7E) * t)
                b = int(0xEA + (0xA2 - 0xEA) * t)
                hdr_canvas.create_rectangle(
                    0, i * h // steps, w, (i + 1) * h // steps,
                    fill=f"#{r:02x}{g:02x}{b:02x}", outline="")
            # Avatar circle
            cx, cy, r = w // 2, 72, 36
            hdr_canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                                   fill=WHITE, outline="")
            initial = self.name[0].upper() if self.name else "S"
            hdr_canvas.create_text(cx, cy, text=initial,
                                   fill=VIOLET, font=("Helvetica", 22, "bold"))
            hdr_canvas.create_text(cx, cy + r + 18,
                                   text=self.name,
                                   fill=WHITE, font=("Helvetica", 14, "bold"))
            hdr_canvas.create_text(cx, cy + r + 36,
                                   text="Profile Settings",
                                   fill="#D1C4E9", font=("Helvetica", 9))

        hdr_canvas.bind("<Configure>", lambda e: _draw_gradient())

        # Edit / Cancel button
        self._toggle_btn = tk.Button(
            inner, text="✏  Edit Profile",
            bg=VIOLET, fg=WHITE,
            activebackground=VIOLET2, activeforeground=WHITE,
            relief="flat", bd=0,
            font=("Helvetica", 10, "bold"),
            padx=16, pady=6, cursor="hand2",
            command=self._toggle_edit)
        self._toggle_btn.pack(anchor="center", pady=(12, 0))

        # ── Form body ─────────────────────────────────────────────────────────
        body = tk.Frame(inner, bg="#F3F0FF")
        body.pack(fill="x", padx=32, pady=(16, 20))

        self._section_label(body, "Personal Information")
        for label, key, default, editable in [
            ("Full Name",    "name",    self.name,  False),
            ("Email",        "email",   self.email, False),
            ("Phone Number", "phone",   "",         True),
            ("Address",      "address", "",         True),
        ]:
            self._profile_field(body, label, key, default, editable)

        # ── Change Password ───────────────────────────────────────────────────
        self._section_label(body, "Change Password")
        pw_card = tk.Frame(body, bg=WHITE,
                           highlightbackground="#C4B5FD", highlightthickness=1)
        pw_card.pack(fill="x", pady=(4, 12))

        self._pw_vars = {}
        for label, key in [
            ("Current Password",  "current_pw"),
            ("New Password",      "new_pw"),
            ("Confirm Password",  "confirm_pw"),
        ]:
            tk.Label(pw_card, text=label, bg=WHITE, fg=TEXT_GRAY,
                     font=("Helvetica", 9), anchor="w",
                     padx=16).pack(fill="x", pady=(10, 2))
            var = tk.StringVar()
            self._pw_vars[key] = var
            tk.Entry(pw_card, textvariable=var, show="•",
                     bg=INPUT_BG, fg=TEXT_DARK,
                     insertbackground=VIOLET,
                     relief="flat", bd=0,
                     font=("Helvetica", 11),
                     highlightthickness=1,
                     highlightbackground=BORDER,
                     highlightcolor=VIOLET
                     ).pack(fill="x", padx=16, ipady=7, pady=(0, 2))

        self._pw_err = tk.StringVar()
        tk.Label(pw_card, textvariable=self._pw_err,
                 bg=WHITE, fg=RED,
                 font=("Helvetica", 9),
                 anchor="w", padx=16).pack(fill="x")

        tk.Button(pw_card, text="🔒  Change Password",
                  bg=VIOLET, fg=WHITE,
                  activebackground=VIOLET2, activeforeground=WHITE,
                  relief="flat", bd=0,
                  font=("Helvetica", 11, "bold"),
                  padx=16, pady=8, cursor="hand2",
                  command=self._change_password
                  ).pack(fill="x", padx=16, pady=(8, 16))

        # Save button (shown only when editing)
        self._save_btn = tk.Button(
            body, text="💾  Save Changes",
            bg=VIOLET, fg=WHITE,
            activebackground=VIOLET2, activeforeground=WHITE,
            relief="flat", bd=0,
            font=("Helvetica", 12, "bold"),
            height=2, cursor="hand2",
            command=self._save_profile)

    # =========================================================================
    # HELPERS
    # =========================================================================
    def _section_label(self, parent, text):
        tk.Label(parent, text=text,
                 bg="#F3F0FF", fg=VIOLET,
                 font=("Helvetica", 13, "bold"),
                 anchor="w").pack(fill="x", pady=(16, 4))

    def _profile_field(self, parent, label, key, default, editable):
        tk.Label(parent, text=label,
                 bg="#F3F0FF", fg="#6B5FA6",
                 font=("Helvetica", 9), anchor="w").pack(fill="x")
        var   = tk.StringVar(value=default)
        state = "disabled"
        bg    = "#E9E4F7"
        e = tk.Entry(parent, textvariable=var, state=state,
                     bg=bg, fg="#2D2748",
                     disabledbackground="#E9E4F7",
                     disabledforeground="#2D2748",
                     insertbackground=VIOLET,
                     relief="flat", bd=0,
                     font=("Helvetica", 12),
                     highlightthickness=1,
                     highlightbackground="#C4B5FD",
                     highlightcolor=VIOLET)
        e.pack(fill="x", ipady=8, pady=(2, 10))
        self._entries[key] = (e, var, editable)

    # =========================================================================
    # EDIT TOGGLE
    # =========================================================================
    def _toggle_edit(self):
        self._editing = not self._editing
        self._toggle_btn.config(
            text="✕  Cancel" if self._editing else "✏  Edit Profile")

        for key, (entry, var, editable) in self._entries.items():
            if editable:
                entry.config(
                    state="normal" if self._editing else "disabled",
                    bg="#EDE9FF"  if self._editing else "#E9E4F7")

        if self._editing:
            self._save_btn.pack(fill="x", pady=(8, 20))
        else:
            self._save_btn.pack_forget()

    # =========================================================================
    # SAVE PROFILE
    # =========================================================================
    def _save_profile(self):
        if self._saving:
            return
        self._saving = True
        self._save_btn.config(state="disabled", text="Saving…", bg="#A0AEC0")
        threading.Thread(target=self._do_save, daemon=True).start()

    def _do_save(self):
        import time
        time.sleep(0.8)
        self.after(0, self._on_saved)

    def _on_saved(self):
        self._saving = False
        self._save_btn.config(state="normal",
                              text="💾  Save Changes", bg=VIOLET)
        self._toggle_edit()
        messagebox.showinfo("Saved", "Profile updated successfully!")

    # =========================================================================
    # CHANGE PASSWORD
    # =========================================================================
    def _change_password(self):
        self._pw_err.set("")
        current = self._pw_vars["current_pw"].get()
        new     = self._pw_vars["new_pw"].get()
        confirm = self._pw_vars["confirm_pw"].get()

        if not current:
            return self._pw_err.set("Please enter your current password.")
        if len(new) < 8:
            return self._pw_err.set("New password must be at least 8 characters.")
        if new != confirm:
            return self._pw_err.set("Passwords do not match.")

        threading.Thread(target=self._do_change_pw,
                         args=(current, new), daemon=True).start()

    def _do_change_pw(self, current, new):
        try:
            from db import fetch_one, execute, verify_password, hash_password
            user = fetch_one("SELECT password FROM users WHERE email=%s",
                             (self.email,))
            if not user or not verify_password(current, user["password"]):
                self.after(0, self._pw_err.set,
                           "Current password is incorrect.")
                return
            hashed = hash_password(new)
            execute("UPDATE users SET password=%s WHERE email=%s",
                    (hashed, self.email))
            self.after(0, self._on_pw_changed)
        except Exception as exc:
            self.after(0, self._pw_err.set, f"Error: {exc}")

    def _on_pw_changed(self):
        for v in self._pw_vars.values():
            v.set("")
        messagebox.showinfo("Success", "Password changed successfully!")
