import tkinter as tk
from tkinter import messagebox
import threading
from home_frame import HomeFrame   # ← import only, do NOT redefine below


# ── Palette ────────────────────────────────────────────────────────────────────
BG        = "#F7FAFC"
WHITE     = "#FFFFFF"
PURPLE    = "#667EEA"
PURPLE2   = "#764BA2"
BORDER    = "#E2E8F0"
TEXT_DARK = "#2D3748"
TEXT_GRAY = "#718096"
SIDEBAR   = "#2D3748"
SIDEBAR_H = "#4A5568"


class StudentDashboard(tk.Tk):
    def __init__(self, name: str, email: str = "student@example.com"):
        super().__init__()
        self.name  = name
        self.email = email
        self.title("Majayjay Scholars")
        self.geometry("1100x700")
        self.minsize(800, 560)
        self.configure(bg=BG)
        self._center()
        self._current_frame = None
        self._build()
        self._show_home()

    def _center(self):
        self.update_idletasks()
        w, h = 1100, 700
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── Layout ─────────────────────────────────────────────────────────────────
    def _build(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=SIDEBAR, width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # Content area
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

    def _build_sidebar(self):
        s = self.sidebar

        # Avatar circle
        avatar = tk.Canvas(s, width=72, height=72, bg=SIDEBAR,
                           highlightthickness=0)
        avatar.pack(pady=(28, 6))
        avatar.create_oval(4, 4, 68, 68, fill=PURPLE, outline=PURPLE2, width=2)
        initials = "".join(w[0].upper() for w in self.name.split()[:2])
        avatar.create_text(36, 36, text=initials, fill=WHITE,
                           font=("Segoe UI", 16, "bold"))

        tk.Label(s, text=self.name,
                 bg=SIDEBAR, fg=WHITE,
                 font=("Segoe UI", 11, "bold"),
                 wraplength=180, justify="center").pack()
        tk.Label(s, text=self.email,
                 bg=SIDEBAR, fg="#A0AEC0",
                 font=("Segoe UI", 8),
                 wraplength=180, justify="center").pack(pady=(2, 18))

        tk.Frame(s, bg="#4A5568", height=1).pack(fill="x", padx=16, pady=4)

        nav_items = [
            ("🏠", "Home",              self._show_home),
            ("📝", "Apply Scholarship", self._show_apply),
            ("📋", "My Applications",   self._show_applications),
            ("🔄", "Renewal",           self._show_renew),
            ("👤", "My Profile",        self._show_profile),
        ]

        self._nav_btns = {}
        for icon, label, cmd in nav_items:
            btn = tk.Button(s, text=f"  {icon}  {label}", anchor="w",
                            bg=SIDEBAR, fg=WHITE,
                            activebackground=SIDEBAR_H,
                            activeforeground=WHITE,
                            relief="flat", bd=0,
                            font=("Segoe UI", 10),
                            padx=12, pady=11,
                            cursor="hand2",
                            command=cmd)
            btn.pack(fill="x")
            self._nav_btns[label] = btn

        # Spacer + Logout
        tk.Frame(s, bg=SIDEBAR).pack(fill="both", expand=True)
        tk.Frame(s, bg="#4A5568", height=1).pack(fill="x", padx=16, pady=4)
        tk.Button(s, text="  🚪  Log Out", anchor="w",
                  bg=SIDEBAR, fg="#FC8181",
                  activebackground="#742A2A", activeforeground=WHITE,
                  relief="flat", bd=0,
                  font=("Segoe UI", 10),
                  padx=12, pady=11,
                  cursor="hand2",
                  command=self._logout).pack(fill="x", pady=(0, 14))

    def _highlight_nav(self, active_label):
        for label, btn in self._nav_btns.items():
            btn.config(bg=PURPLE if label == active_label else SIDEBAR)

    # ── Frame switching ─────────────────────────────────────────────────────────
    def _swap(self, FrameClass, nav_label, **kwargs):
        if self._current_frame:
            self._current_frame.destroy()
        self._current_frame = FrameClass(
            self.content,
            name=self.name,
            email=self.email,
            dashboard=self,
            **kwargs
        )
        self._current_frame.pack(fill="both", expand=True)
        self._highlight_nav(nav_label)

    def _show_home(self):
        if self._current_frame:
            self._current_frame.destroy()
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
        try:
            from apply_scholarship import ApplyFrame
            self._swap(ApplyFrame, "Apply Scholarship")
        except ImportError:
            messagebox.showerror("Error", "apply_scholarship.py not found.")

    def _show_applications(self):
        try:
            from my_applications import ApplicationsFrame
            self._swap(ApplicationsFrame, "My Applications")
        except ImportError:
            messagebox.showerror("Error", "my_applications.py not found.")

    def _show_renew(self):
        try:
            from renewal_scholarship import RenewFrame
            threading.Thread(target=self._check_renewal_open, daemon=True).start()
        except ImportError:
            messagebox.showerror("Error", "renewal_scholarship.py not found.")

    def _check_renewal_open(self):
        """Check DB if renewal window is open before showing the renew page."""
        try:
            from db import fetch_one
            row = fetch_one("SELECT is_open FROM renewal_settings LIMIT 1")
            is_open = row and row.get("is_open", 0)
        except Exception:
            is_open = False

        def _load():
            if is_open:
                from renewal_scholarship import RenewFrame
                self._swap(RenewFrame, "Renewal")
            else:
                messagebox.showinfo(
                    "Renewal Closed",
                    "The renewal window is currently closed.\n"
                    "Please check back later."
                )
        self.after(0, _load)

    def _show_profile(self):
        try:
            from student_profile import StudentProfilePage
            self._swap(StudentProfilePage, "My Profile")
        except ImportError:
            messagebox.showerror("Error", "student_profile.py not found.")

    def _logout(self):
        if messagebox.askyesno("Log Out", "Are you sure you want to log out?"):
            self.destroy()
            try:
                from login import LoginWindow
                LoginWindow().mainloop()
            except ImportError:
                pass


# ── Entry point (standalone test) ──────────────────────────────────────────────
if __name__ == "__main__":
    StudentDashboard(
        name="Justin Sobrevinas",
        email="jsobrevinas6@gmail.com"
    ).mainloop()