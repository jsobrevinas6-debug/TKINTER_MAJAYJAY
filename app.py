import tkinter as tk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BG = "#F7FAFC"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Majayjay Scholars")
        self.geometry("580x660")
        self.configure(bg=BG)
        self._center(580, 660)

        self._user_name  = ""
        self._user_email = ""
        self._user_type  = ""

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

    # ── Navigation ─────────────────────────────────────────────────────────────
    def show_login(self):
        self._resize(580, 660)
        from pages.login.login import LoginPage
        self._swap(LoginPage(self.container, app=self))

    def show_register(self):
        self._resize(600, 780)
        from pages.login.registration import RegistrationPage
        self._swap(RegistrationPage(self.container, app=self))

    def show_student_dashboard(self, name: str, email: str):
        self._user_name  = name
        self._user_email = email
        self._user_type  = "student"
        self._resize(1060, 720)
        from pages.student.student_dashboard import StudentDashboard
        self._swap(StudentDashboard(self.container,
                                    name=name, email=email, app=self))

    def show_mayor_dashboard(self, name: str = "", email: str = ""):
        if name:
            self._user_name  = name
            self._user_email = email
            self._user_type  = "mayor"
        self._resize(1060, 720)
        from pages.mayor.mayor_dashboard import MayorDashboard
        self._swap(MayorDashboard(self.container,
                                   name=self._user_name,
                                   email=self._user_email,
                                   app=self))

    def show_mayor_records(self):
        self._resize(1200, 720)
        from pages.mayor.records import RecordsFrame
        self._swap(RecordsFrame(self.container,
                                name=self._user_name,
                                email=self._user_email,
                                app=self))

    def show_records(self):
        self.show_mayor_records()

    def show_scholar_records(self):
        self.show_mayor_records()


    def show_renewal_settings(self):
        self.show_mayor_renewal_settings()

    def show_mayor_renewal_settings(self):
        self._resize(1100, 760)
        from pages.mayor.renewal_settings import RenewalSettingsFrame
        self._swap(RenewalSettingsFrame(self.container,
                                        name=self._user_name,
                                        email=self._user_email,
                                        app=self))

    def show_admin_dashboard(self, name: str = "", email: str = ""):
        if name:
            self._user_name  = name
            self._user_email = email
            self._user_type  = "admin"
        self._resize(1200, 720)
        from pages.admin.admin_dashboard import AdminDashboard
        self._swap(AdminDashboard(self.container,
                                  name=self._user_name,
                                  email=self._user_email,
                                  app=self))

    # ── Auth ───────────────────────────────────────────────────────────────────
    def on_login_success(self, user: dict):
        name  = (user.get("name") or
                 f"{user.get('first_name','')} {user.get('last_name','')}".strip() or
                 user.get("email", "").split("@")[0])
        email = user.get("email", "")
        utype = user.get("user_type", "student")

        if utype == "admin":
            self.show_admin_dashboard(name, email)
        elif utype == "mayor":
            self.show_mayor_dashboard(name, email)
        else:
            self.show_student_dashboard(name, email)

    def logout(self):
        self._user_name  = ""
        self._user_email = ""
        self._user_type  = ""
        self.show_login()


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        from db import test_connection
        test_connection()
    except Exception as e:
        print(f"[DB] {e}")
    App().mainloop()