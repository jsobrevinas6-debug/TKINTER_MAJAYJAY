import tkinter as tk
from tkinter import messagebox

# ── Shared colors ──────────────────────────────────────────────────────────────
BG        = "#F7FAFC"
WHITE     = "#FFFFFF"
PURPLE    = "#667EEA"
PURPLE2   = "#764BA2"
GREEN     = "#48BB78"
BORDER    = "#E2E8F0"
TEXT_DARK = "#2D3748"
TEXT_GRAY = "#718096"
SIDEBAR   = "#2D3748"
SIDEBAR_H = "#4A5568"


class App(tk.Tk):
    """
    Single Tk root — one mainloop, pages swap as frames inside self.container.
    """

    def __init__(self):
        super().__init__()
        self.title("Majayjay Scholars")
        self.geometry("580x660")
        self.configure(bg=BG)
        self._center(580, 660)

        # Session state
        self._user_name  = ""
        self._user_email = ""
        self._user_type  = ""

        # One container all pages fill
        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True)

        self._current = None
        self.show_login()

    # ── Window helpers ─────────────────────────────────────────────────────────
    def _center(self, w, h):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _resize(self, w, h):
        self.geometry(f"{w}x{h}")
        self._center(w, h)

    def _swap(self, widget):
        if self._current:
            self._current.destroy()
        self._current = widget
        widget.pack(fill="both", expand=True)

    # ── Navigation methods (called by page frames) ─────────────────────────────

    def show_login(self):
        self._resize(580, 660)
        from pages.login import LoginPage
        self._swap(LoginPage(self.container, app=self))

    def show_register(self):
        self._resize(600, 780)
        from pages.registration import RegistrationPage
        self._swap(RegistrationPage(self.container, app=self))

    def show_student_dashboard(self, name: str, email: str):
        self._user_name  = name
        self._user_email = email
        self._user_type  = "student"
        self._resize(1060, 720)
        from pages.student_dashboard import StudentDashboard
        self._swap(StudentDashboard(self.container,
                                    name=name, email=email, app=self))

    def show_mayor_dashboard(self, name: str = "", email: str = ""):
        if name:
            self._user_name  = name
            self._user_email = email
            self._user_type  = "mayor"
        self._resize(1060, 720)
        from pages.mayor_dashboard import MayorDashboard
        self._swap(MayorDashboard(self.container,
                                   name=self._user_name,
                                   email=self._user_email,
                                   app=self))

    def show_mayor_pending(self):
        self._resize(1060, 720)
        from pages.pending_scholars import PendingScholarsFrame
        self._swap(PendingScholarsFrame(self.container,
                                        name=self._user_name,
                                        email=self._user_email,
                                        app=self))

    def show_mayor_records(self):
        self._resize(1200, 720)
        from pages.scholar_records import ScholarRecordsFrame
        self._swap(ScholarRecordsFrame(self.container,
                                       name=self._user_name,
                                       email=self._user_email,
                                       app=self))

    def show_admin_dashboard(self, name: str = "", email: str = ""):
        """Placeholder — build admin pages similarly."""
        if name:
            self._user_name  = name
            self._user_email = email
            self._user_type  = "admin"
        self._resize(1060, 720)
        # Swap for admin page when ready
        # from pages.admin_dashboard import AdminDashboard
        # self._swap(AdminDashboard(...))
        messagebox.showinfo("Admin",
                            f"Welcome Admin {self._user_name}!\n"
                            "(Admin dashboard coming soon)")

    # ── Called by login page after successful authentication ───────────────────
    def on_login_success(self, user: dict):
        """
        Route to the correct dashboard basemnasd on user_type from DB.
        `user` is the full row dict returned by db.login().
        """
        name  = (user.get("name") or
                 f"{user.get('first_name','')} {user.get('last_name','')}".strip() or
                 user.get("email","").split("@")[0])
        email = user.get("email","")
        utype = user.get("user_type","student")

        if utype == "admin":
            self.show_admin_dashboard(name, email)
        elif utype == "mayor":
            self.show_mayor_dashboard(name, email)
        else:
            self.show_student_dashboard(name, email)

    # ── Logout ─────────────────────────────────────────────────────────────────
    def logout(self):
        self._user_name  = ""
        self._user_email = ""
        self._user_type  = ""
        self.show_login()


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Optional: test DB before opening window
    try:
        from db import test_connection
        test_connection()
    except Exception as e:
        print(f"[DB] {e}")
    App().mainloop()