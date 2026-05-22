import tkinter as tk
from tkinter import messagebox
import threading

try:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    from logo import get_logo
except Exception:
    get_logo = lambda size=60: None

BG = "#F7FAFC"
WHITE = "#FFFFFF"
PURPLE = "#667EEA"
PURPLE2 = "#764BA2"
BORDER = "#E2E8F0"
TEXT_DARK = "#2D3748"
TEXT_GRAY = "#718096"
SIDEBAR_BG = WHITE
SIDEBAR_TEXT = TEXT_DARK
SIDEBAR_MUTED = TEXT_GRAY
SIDEBAR_LINE = BORDER
NAV_ACTIVE = "#6B70D6"
NAV_HOVER = "#EEF2FF"


class StudentDashboard(tk.Frame):
    def __init__(self, parent, name: str, email: str = "student@example.com", app=None, **_):
        super().__init__(parent, bg=BG)
        self.app = app
        self.name = name
        self.email = email
        self._current_frame = None
        self._build()
        self._show_home()

    def _build(self):
        self.sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

    def _build_sidebar(self):
        s = self.sidebar

        avatar = tk.Canvas(s, width=72, height=72, bg=SIDEBAR_BG, highlightthickness=0)
        avatar.pack(pady=(28, 6))
        logo = get_logo(64)
        if logo:
            self._logo_photo = logo
            avatar.create_image(36, 36, image=self._logo_photo)
        else:
            avatar.create_oval(4, 4, 68, 68, fill=PURPLE, outline=PURPLE2, width=2)
            initials = "".join(word[0].upper() for word in self.name.split()[:2])
            avatar.create_text(36, 36, text=initials, fill=WHITE, font=("Segoe UI", 16, "bold"))

        tk.Label(
            s,
            text=self.name,
            bg=SIDEBAR_BG,
            fg=TEXT_DARK,
            font=("Segoe UI", 11, "bold"),
            wraplength=180,
            justify="center",
        ).pack()
        tk.Label(
            s,
            text=self.email,
            bg=SIDEBAR_BG,
            fg=SIDEBAR_MUTED,
            font=("Segoe UI", 8),
            wraplength=180,
            justify="center",
        ).pack(pady=(2, 18))

        tk.Frame(s, bg=SIDEBAR_LINE, height=1).pack(fill="x", padx=16, pady=4)

        nav_items = [
            ("Home", self._show_home),
            ("Apply Scholarship", self._show_apply),
            ("My Applications", self._show_applications),
            ("Renewal", self._show_renew),
            ("My Profile", self._show_profile),
        ]

        self._nav_btns = {}
        for label, command in nav_items:
            btn = tk.Button(
                s,
                text=f"  {label}",
                anchor="w",
                bg=SIDEBAR_BG,
                fg=SIDEBAR_TEXT,
                activebackground=NAV_HOVER,
                activeforeground=TEXT_DARK,
                relief="flat",
                bd=0,
                font=("Segoe UI", 10),
                padx=12,
                pady=11,
                cursor="hand2",
                command=command,
            )
            btn.pack(fill="x", padx=8, pady=2)
            btn.bind(
                "<Enter>",
                lambda _event, b=btn: b.config(bg=NAV_HOVER)
                if b["bg"] != NAV_ACTIVE else None,
            )
            btn.bind(
                "<Leave>",
                lambda _event, b=btn: b.config(bg=SIDEBAR_BG)
                if b["bg"] == NAV_HOVER else None,
            )
            self._nav_btns[label] = btn

        tk.Frame(s, bg=SIDEBAR_BG).pack(fill="both", expand=True)
        tk.Frame(s, bg=SIDEBAR_LINE, height=1).pack(fill="x", padx=16, pady=4)
        tk.Button(
            s,
            text="  Log Out",
            anchor="w",
            bg=SIDEBAR_BG,
            fg="#E53E3E",
            activebackground="#742A2A",
            activeforeground=WHITE,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10),
            padx=12,
            pady=11,
            cursor="hand2",
            command=self._logout,
        ).pack(fill="x", padx=8, pady=(0, 14))

    def _highlight_nav(self, active_label):
        for label, btn in self._nav_btns.items():
            active = label == active_label
            btn.config(
                bg=NAV_ACTIVE if active else SIDEBAR_BG,
                fg=WHITE if active else SIDEBAR_TEXT,
                activebackground=NAV_ACTIVE if active else NAV_HOVER,
                activeforeground=WHITE if active else TEXT_DARK,
            )

    def _swap(self, FrameClass, nav_label, **kwargs):
        if self._current_frame:
            self._current_frame.destroy()
        self._current_frame = FrameClass(
            self.content,
            name=self.name,
            email=self.email,
            dashboard=self,
            **kwargs,
        )
        self._current_frame.pack(fill="both", expand=True)
        self._highlight_nav(nav_label)

    def _show_home(self):
        if self._current_frame:
            self._current_frame.destroy()
        from pages.home_frame import HomeFrame

        self._current_frame = HomeFrame(
            self.content,
            name=self.name,
            email=self.email,
            dashboard=self,
            on_apply=self._show_apply,
            on_renew=self._show_renew,
            on_apps=self._show_applications,
        )
        self._current_frame.pack(fill="both", expand=True)
        self._highlight_nav("Home")

    def _show_apply(self):
        from pages.student.apply_scholarship import ApplyFrame
        self._swap(ApplyFrame, "Apply Scholarship")

    def _show_applications(self):
        from pages.student.my_applications import ApplicationsFrame
        self._swap(ApplicationsFrame, "My Applications")

    def _show_renew(self):
        threading.Thread(target=self._check_renewal_open, daemon=True).start()

    def _check_renewal_open(self):
        try:
            from db import fetch_one
            row = fetch_one("SELECT is_open FROM renewal_settings LIMIT 1")
            is_open = row and row.get("is_open", 0)
        except Exception:
            is_open = False

        def _load():
            if is_open:
                from pages.student.renewal_scholarship import RenewFrame
                self._swap(RenewFrame, "Renewal")
            else:
                messagebox.showinfo(
                    "Renewal Closed",
                    "The renewal window is currently closed.\nPlease check back later.",
                )

        self.after(0, _load)

    def _show_profile(self):
        from pages.student.student_profile import ProfileFrame
        self._swap(ProfileFrame, "My Profile")

    def _logout(self):
        if messagebox.askyesno("Log Out", "Are you sure you want to log out?"):
            if self.app:
                self.app.logout()
            else:
                self.winfo_toplevel().destroy()


if __name__ == "__main__":
    StudentDashboard(
        name="Justin Sobrevinas",
        email="jsobrevinas6@gmail.com",
    ).mainloop()
