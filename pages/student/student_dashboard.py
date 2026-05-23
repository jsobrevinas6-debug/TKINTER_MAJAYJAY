import tkinter as tk
from tkinter import messagebox
import threading
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

try:
    from pages.sidebar import Sidebar
except ImportError:
    from sidebar import Sidebar

BG        = "#F7FAFC"
WHITE     = "#FFFFFF"
BORDER    = "#E2E8F0"
TEXT_DARK = "#2D3748"


class StudentDashboard(tk.Frame):
    def __init__(self, parent, name: str, email: str = "student@example.com", app=None, **_):
        super().__init__(parent, bg=BG)
        self.app = app
        self.name = name
        self.email = email
        self._current_frame = None
        self._sidebar = None
        self._build()
        self._show_home()

    def _build(self):
        self._sidebar = Sidebar(
            self, user_type="student", name=self.name,
            active_item="Home",
            on_nav=self._on_nav,
            on_logout=self._logout,
        )
        self._sidebar.pack(side="left", fill="y")

        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

    def _on_nav(self, label):
        if label == "Home":
            self._show_home()
        elif label == "Apply Scholarship":
            self._show_apply()
        elif label == "My Applications":
            self._show_applications()
        elif label == "Renewal":
            self._show_renew()
        elif label == "Profile Settings":
            self._show_profile()

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
        self._sidebar.set_active(nav_label)

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
        if self._sidebar:
            self._sidebar.set_active("Home")

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
        from pages.profile_settings import ProfileSettingsPage
        if self._current_frame:
            self._current_frame.destroy()
        self._current_frame = ProfileSettingsPage(
            self.content,
            name=self.name,
            email=self.email,
            user_type="student",
            app=self.app,
            dashboard=self,
        )
        self._current_frame.pack(fill="both", expand=True)
        self._sidebar.set_active("Profile Settings")

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
