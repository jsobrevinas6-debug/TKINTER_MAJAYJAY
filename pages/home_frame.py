import tkinter as tk
from tkinter import ttk

# ── Palette ────────────────────────────────────────────────────────────────────
BG        = "#F7FAFC"
WHITE     = "#FFFFFF"
PURPLE    = "#667EEA"
PURPLE2   = "#764BA2"
BORDER    = "#E2E8F0"
TEXT_DARK = "#2D3748"
TEXT_GRAY = "#718096"
TEXT_MUTED= "#A0AEC0"
SIDEBAR   = "#2D3748"
BADGE_BG  = "#667EEA"
CARD_SHADOW = "#DDE3EE"


class HomeFrame(tk.Frame):
    """
    Recreates the web-based Student Dashboard home page in Tkinter.

    Sections:
      1. Header bar (title + welcome badge)
      2. About the Scholarship
      3. Eligibility Requirements
      4. Required Documents
      5. Where to Apply / Walk-in
      6. How to Apply
    """

    def __init__(self, parent, name="Student", email="", dashboard=None,
                 on_apply=None, on_renew=None, on_apps=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self.name       = name
        self.email      = email
        self.dashboard  = dashboard
        self.on_apply   = on_apply
        self.on_renew   = on_renew
        self.on_apps    = on_apps
        self._build()

    # ─────────────────────────────────────────────────────────────────────
    def _build(self):
        # ── Top header bar ────────────────────────────────────────────────
        header = tk.Frame(self, bg=WHITE, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="≡", bg=WHITE, fg=TEXT_DARK,
                 font=("Segoe UI", 16)).pack(side="left", padx=(16, 8), pady=10)
        tk.Label(header, text="Student Dashboard", bg=WHITE, fg=TEXT_DARK,
                 font=("Segoe UI", 13, "bold")).pack(side="left", pady=10)

        # Right side: welcome + badge
        badge_frame = tk.Frame(header, bg=WHITE)
        badge_frame.pack(side="right", padx=20, pady=10)

        first = self.name.split()[0] if self.name else "Student"
        tk.Label(badge_frame, text=f"Welcome,  {first}",
                 bg=WHITE, fg=TEXT_GRAY,
                 font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))

        badge = tk.Label(badge_frame, text=" STUDENT ",
                         bg=BADGE_BG, fg=WHITE,
                         font=("Segoe UI", 9, "bold"),
                         padx=8, pady=3)
        badge.pack(side="left")

        # thin separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Scrollable body ───────────────────────────────────────────────
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG)
        win = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win, width=e.width)
        canvas.bind("<Configure>", _on_configure)

        canvas.bind("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1*(e.delta//120), "units")
            if canvas.winfo_exists() else None)

        self._populate(inner)

    # ─────────────────────────────────────────────────────────────────────
    def _populate(self, parent):
        P = 24   # horizontal padding

        # 1. About the Scholarship
        self._section_card(
            parent, P,
            title="About the Scholarship",
            body=(
                "The Majayjay Mayor's Scholarship Program is a local government initiative "
                "that provides financial assistance to deserving students from Majayjay, Laguna. "
                "The program aims to support academically qualified residents who wish to pursue "
                "higher education but face financial constraints. Scholars receive assistance each "
                "semester for as long as they maintain the required academic standing and continue "
                "to meet the eligibility criteria."
            )
        )

        # 2. Eligibility Requirements
        reqs = [
            "Must be a bonafide resident of Majayjay, Laguna",
            "Must be currently enrolled in a college or university",
            "Must have a General Weighted Average (GWA) of 2.00 or better",
            "Must not be a recipient of any other government scholarship",
            "Must demonstrate financial need",
            "Must be of good moral character",
        ]
        self._bullet_card(parent, P, "Eligibility Requirements", reqs)

        # 3. Required Documents
        self._documents_card(parent, P)

        # 4. Where to Apply / Walk-in
        self._walkin_card(parent, P)

        # 5. How to Apply
        steps = [
            ("Click ", "Apply Scholarship",
             " in the sidebar to fill out the application form"),
            ("Upload all required documents in JPG, PNG, or PDF format (max 5MB each)",),
            ("Submit your application and wait for the mayor's office to review it",),
            ("Track your application status under ", "My Applications", " in the sidebar"),
            ("Once approved, you may renew each semester through ",
             "Renew Scholarship", " when the renewal window is open"),
        ]
        self._how_card(parent, P, steps)

        # bottom spacer
        tk.Frame(parent, bg=BG, height=30).pack()

    # ─────────────────────────────────────────────────────────────────────
    # Card helpers
    # ─────────────────────────────────────────────────────────────────────
    def _card(self, parent, padx):
        """Returns a white rounded-style card frame."""
        outer = tk.Frame(parent, bg=BG)
        outer.pack(fill="x", padx=padx, pady=(0, 18))

        card = tk.Frame(outer, bg=WHITE,
                        highlightbackground=BORDER,
                        highlightthickness=1)
        card.pack(fill="x")
        return card

    def _card_title(self, card, text):
        tk.Label(card, text=text, bg=WHITE, fg=TEXT_DARK,
                 font=("Segoe UI", 12, "bold"),
                 anchor="w").pack(fill="x", padx=20, pady=(18, 8))
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=20)

    def _section_card(self, parent, padx, title, body):
        card = self._card(parent, padx)
        self._card_title(card, title)
        tk.Label(card, text=body, bg=WHITE, fg=TEXT_GRAY,
                 font=("Segoe UI", 10),
                 wraplength=820, justify="left",
                 anchor="w").pack(fill="x", padx=20, pady=(10, 18))

    def _bullet_card(self, parent, padx, title, items):
        card = self._card(parent, padx)
        self._card_title(card, title)
        for item in items:
            row = tk.Frame(card, bg=WHITE)
            row.pack(fill="x", padx=20, pady=2)
            tk.Label(row, text="●", bg=WHITE, fg=PURPLE,
                     font=("Segoe UI", 8)).pack(side="left", padx=(0, 8))
            tk.Label(row, text=item, bg=WHITE, fg=TEXT_DARK,
                     font=("Segoe UI", 10), anchor="w").pack(side="left")
        tk.Frame(card, bg=BG, height=10).pack()

    def _documents_card(self, parent, padx):
        card = self._card(parent, padx)
        self._card_title(card, "Required Documents")

        docs = [
            ("🏫", "School ID",
             "Valid school-issued identification card"),
            ("📷", "ID Picture",
             "Recent 2×2 or passport-size photo"),
            ("📄", "Birth Certificate",
             "PSA-issued birth certificate"),
            ("📊", "Grades / Transcript",
             "Latest official grades or transcript of records"),
            ("📋", "Certificate of Registration",
             "COR for the current semester"),
        ]

        # Row 1 – first 4 docs
        row1 = tk.Frame(card, bg=WHITE)
        row1.pack(fill="x", padx=20, pady=(12, 6))
        for icon, title, desc in docs[:4]:
            self._doc_tile(row1, icon, title, desc)

        # Row 2 – last doc (left-aligned)
        row2 = tk.Frame(card, bg=WHITE)
        row2.pack(fill="x", padx=20, pady=(0, 16))
        self._doc_tile(row2, *docs[4])

    def _doc_tile(self, parent, icon, title, desc):
        tile = tk.Frame(parent, bg=WHITE,
                        highlightbackground=BORDER,
                        highlightthickness=1,
                        width=190, height=90)
        tile.pack(side="left", padx=(0, 10), pady=4)
        tile.pack_propagate(False)

        inner = tk.Frame(tile, bg=WHITE)
        inner.pack(fill="both", expand=True, padx=10, pady=10)

        hdr = tk.Frame(inner, bg=WHITE)
        hdr.pack(fill="x")
        tk.Label(hdr, text=icon, bg=WHITE,
                 font=("Segoe UI", 13)).pack(side="left")
        tk.Label(hdr, text=title, bg=WHITE, fg=PURPLE,
                 font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(side="left", padx=6)
        tk.Label(inner, text=desc, bg=WHITE, fg=TEXT_MUTED,
                 font=("Segoe UI", 8),
                 wraplength=155, justify="left",
                 anchor="w").pack(fill="x", pady=(4, 0))

    def _walkin_card(self, parent, padx):
        card = self._card(parent, padx)
        self._card_title(card, "Where to Apply / Walk-in")

        tk.Label(card,
                 text=("You may also visit the Majayjay Municipal Hall in person "
                       "to inquire or submit your documents directly to the mayor's office."),
                 bg=WHITE, fg=TEXT_GRAY, font=("Segoe UI", 10),
                 wraplength=820, justify="left", anchor="w"
                 ).pack(fill="x", padx=20, pady=(10, 12))

        # Map placeholder
        map_frame = tk.Frame(card, bg="#E8EDF5",
                             highlightbackground=BORDER,
                             highlightthickness=1,
                             height=180)
        map_frame.pack(fill="x", padx=20, pady=(0, 8))
        map_frame.pack_propagate(False)

        inner = tk.Frame(map_frame, bg="#E8EDF5")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(inner, text="🗺️", bg="#E8EDF5",
                 font=("Segoe UI", 32)).pack()
        tk.Label(inner, text="Majayjay Municipal Hall", bg="#E8EDF5",
                 fg=TEXT_DARK, font=("Segoe UI", 11, "bold")).pack()
        tk.Label(inner, text="Majayjay, Laguna", bg="#E8EDF5",
                 fg=TEXT_GRAY, font=("Segoe UI", 9)).pack()

        # Address bar
        addr_bar = tk.Frame(card, bg=WHITE)
        addr_bar.pack(fill="x", padx=20, pady=(0, 16))
        tk.Label(addr_bar, text="📍", bg=WHITE,
                 font=("Segoe UI", 10)).pack(side="left")
        tk.Label(addr_bar,
                 text="Majayjay Municipal Hall, Majayjay, Laguna  |  "
                      "Monday – Friday, 8:00 AM – 5:00 PM",
                 bg=WHITE, fg=TEXT_GRAY,
                 font=("Segoe UI", 9)).pack(side="left", padx=6)

    def _how_card(self, parent, padx, steps):
        card = self._card(parent, padx)
        self._card_title(card, "How to Apply")

        for i, parts in enumerate(steps, 1):
            row = tk.Frame(card, bg=WHITE)
            row.pack(fill="x", padx=20, pady=3)

            # Bullet circle with number
            circ = tk.Canvas(row, width=22, height=22,
                             bg=WHITE, highlightthickness=0)
            circ.pack(side="left", padx=(0, 8))
            circ.create_oval(2, 2, 20, 20, fill=PURPLE, outline=PURPLE)
            circ.create_text(11, 11, text=str(i),
                             fill=WHITE, font=("Segoe UI", 8, "bold"))

            # Inline text (supports bold keyword segments)
            txt_frame = tk.Frame(row, bg=WHITE)
            txt_frame.pack(side="left", fill="x")

            if len(parts) == 1:
                tk.Label(txt_frame, text=parts[0], bg=WHITE, fg=TEXT_DARK,
                         font=("Segoe UI", 10), anchor="w").pack(side="left")
            else:
                # alternating normal / bold segments
                for j, seg in enumerate(parts):
                    bold = (j % 2 == 1)
                    tk.Label(txt_frame, text=seg, bg=WHITE,
                             fg=PURPLE if bold else TEXT_DARK,
                             font=("Segoe UI", 10, "bold" if bold else "normal"),
                             anchor="w").pack(side="left")

        tk.Frame(card, bg=BG, height=10).pack()


# ── Standalone test ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Majayjay Scholars – Dashboard Home")
    root.geometry("1000x680")
    root.configure(bg=BG)

    # Minimal sidebar for testing
    sidebar = tk.Frame(root, bg=SIDEBAR, width=200)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    logo_c = tk.Canvas(sidebar, width=56, height=56,
                        bg=SIDEBAR, highlightthickness=0)
    logo_c.pack(pady=(24, 4))
    logo_c.create_oval(4, 4, 52, 52, fill=PURPLE, outline=PURPLE2, width=2)
    logo_c.create_text(28, 28, text="MJS", fill="white",
                        font=("Segoe UI", 13, "bold"))

    tk.Label(sidebar, text="MajayjayScholars", bg=SIDEBAR, fg=WHITE,
             font=("Segoe UI", 10, "bold")).pack()

    for item in ["🏠  Dashboard", "📋  My Applications",
                 "🔄  Renew Scholarship", "📝  Apply Scholarship",
                 "👤  Profile Settings"]:
        active = item == "🏠  Dashboard"
        tk.Button(sidebar, text=item, anchor="w",
                  bg=PURPLE if active else SIDEBAR, fg=WHITE,
                  activebackground=PURPLE, activeforeground=WHITE,
                  relief="flat", bd=0, padx=16, pady=9,
                  font=("Segoe UI", 10), cursor="hand2"
                  ).pack(fill="x")

    tk.Frame(sidebar, bg=SIDEBAR).pack(fill="both", expand=True)
    tk.Button(sidebar, text="→  Logout", anchor="w",
              bg=SIDEBAR, fg="#FC8181",
              activebackground="#742A2A", activeforeground=WHITE,
              relief="flat", bd=0, padx=16, pady=9,
              font=("Segoe UI", 10), cursor="hand2"
              ).pack(fill="x", pady=(0, 12))

    # Main content
    content = tk.Frame(root, bg=BG)
    content.pack(side="left", fill="both", expand=True)

    HomeFrame(content, name="Jared Santos",
              email="jared@example.com").pack(fill="both", expand=True)

    root.mainloop()