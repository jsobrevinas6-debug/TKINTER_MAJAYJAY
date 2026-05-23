"""
Shared sidebar component for all user types.
Usage:
    from pages.sidebar import Sidebar
    Sidebar(parent, user_type="mayor", name="Juan", on_nav=..., on_logout=...)
"""
import tkinter as tk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

try:
    from logo import get_logo
except Exception:
    get_logo = lambda size=60: None

# ── Palette ────────────────────────────────────────────────────────────────────
WHITE      = "#FFFFFF"
PURPLE     = "#667EEA"
BORDER     = "#E2E8F0"
DARK       = "#2D3748"
NAV_ACTIVE = "#6B70D6"
NAV_HOVER  = "#EEF2FF"
RED_FG     = "#E53E3E"
RED_HOV    = "#742A2A"

# Nav items per user type
_NAV_ITEMS = {
    "student": [
        "Home",
        "Apply Scholarship",
        "My Applications",
        "Renewal",
        "Profile Settings",
    ],
    "mayor": [
        "Dashboard",
        "Scholar Records",
        "Renewal Settings",
        "Profile Settings",
    ],
    "admin": [
        "Dashboard",
        "Add Admin",
        "Profile Settings",
    ],
}

_PANEL_LABELS = {
    "student": "Student Dashboard",
    "mayor":   "Mayor Dashboard",
    "admin":   "Admin Dashboard",
}


class Sidebar(tk.Frame):
    """
    Reusable sidebar for student, mayor, and admin dashboards.

    Parameters
    ----------
    parent      : tk widget
    user_type   : "student" | "mayor" | "admin"
    name        : display name shown in the header
    active_item : nav label that starts highlighted
    on_nav      : callable(label) — called when a nav button is clicked
    on_logout   : callable() — called when Log Out is clicked
    width       : sidebar width in px (default 238)
    """

    def __init__(self, parent, user_type="student", name="",
                 active_item=None, on_nav=None, on_logout=None,
                 width=238, **kwargs):
        super().__init__(parent, bg=WHITE, width=width, **kwargs)
        self.pack_propagate(False)

        self.user_type   = user_type
        self.name        = name
        self.on_nav      = on_nav or (lambda label: None)
        self.on_logout   = on_logout or (lambda: None)
        self._nav_btns   = {}
        self._logo_photo = None

        nav_items   = _NAV_ITEMS.get(user_type, [])
        active_item = active_item or (nav_items[0] if nav_items else "")

        self._build(nav_items, active_item)

    # ── Build ──────────────────────────────────────────────────────────────────
    def _build(self, nav_items, active_item):
        # Gradient header canvas
        hdr = tk.Canvas(self, height=170, bg=WHITE, highlightthickness=0)
        hdr.pack(fill="x")
        hdr.bind("<Configure>", lambda e: self._draw_header(hdr))
        self._hdr_canvas = hdr

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=18)

        nav_frame = tk.Frame(self, bg=WHITE)
        nav_frame.pack(fill="x", pady=(10, 0))

        for label in nav_items:
            is_active = (label == active_item)
            btn = tk.Button(
                nav_frame, text=f"  {label}", anchor="w",
                bg=NAV_ACTIVE if is_active else WHITE,
                fg=WHITE      if is_active else DARK,
                activebackground=NAV_HOVER, activeforeground=DARK,
                relief="flat", bd=0,
                font=("Segoe UI", 10),
                padx=18, pady=10, cursor="hand2",
                command=lambda l=label: self._on_click(l))
            btn.pack(fill="x", padx=10, pady=3)
            if not is_active:
                btn.bind("<Enter>",
                         lambda e, b=btn: b.config(bg=NAV_HOVER)
                         if b["bg"] != NAV_ACTIVE else None)
                btn.bind("<Leave>",
                         lambda e, b=btn: b.config(bg=WHITE)
                         if b["bg"] == NAV_HOVER else None)
            self._nav_btns[label] = btn

        # Spacer
        tk.Frame(self, bg=WHITE).pack(fill="both", expand=True)
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=18, pady=(12, 6))

        # Logout
        lo = tk.Button(self, text="  Log Out", anchor="w",
                       bg=WHITE, fg=RED_FG,
                       activebackground=RED_HOV, activeforeground=WHITE,
                       relief="flat", bd=0,
                       font=("Segoe UI", 10),
                       padx=18, pady=10, cursor="hand2",
                       command=self.on_logout)
        lo.pack(fill="x", padx=10, pady=(0, 14))
        lo.bind("<Enter>", lambda e: lo.config(bg=RED_HOV, fg=WHITE))
        lo.bind("<Leave>", lambda e: lo.config(bg=WHITE, fg=RED_FG))

    # ── Header gradient + logo ─────────────────────────────────────────────────
    def _draw_header(self, c):
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        steps = 44
        for i in range(steps):
            t = i / steps
            r = int(0x66 + (0x76 - 0x66) * t)
            g = int(0x7E + (0x4B - 0x7E) * t)
            b = int(0xEA + (0xA2 - 0xEA) * t)
            c.create_rectangle(0, i * h // steps, w, (i + 1) * h // steps,
                                fill=f"#{r:02x}{g:02x}{b:02x}", outline="")

        cx, cy, radius = w // 2, 58, 30
        logo = get_logo(radius * 2)
        if logo:
            self._logo_photo = logo
            c.create_image(cx, cy, image=self._logo_photo)
        else:
            c.create_oval(cx - radius, cy - radius,
                          cx + radius, cy + radius, fill=WHITE, outline="")
            c.create_text(cx, cy, text="MJS",
                          fill=PURPLE, font=("Segoe UI", 14, "bold"))

        c.create_text(cx, cy + radius + 18,
                      text=self.name or "User",
                      fill=WHITE, font=("Segoe UI", 11, "bold"))
        c.create_text(cx, cy + radius + 35,
                      text=_PANEL_LABELS.get(self.user_type, ""),
                      fill="#DDE3FF", font=("Segoe UI", 8))

    # ── Nav click ──────────────────────────────────────────────────────────────
    def _on_click(self, label):
        self.set_active(label)
        self.on_nav(label)

    # ── Public helpers ─────────────────────────────────────────────────────────
    def set_active(self, label):
        """Highlight the given nav item and unhighlight the rest."""
        for lbl, btn in self._nav_btns.items():
            if lbl == label:
                btn.config(bg=NAV_ACTIVE, fg=WHITE)
            else:
                btn.config(bg=WHITE, fg=DARK)

    def refresh_header(self):
        """Redraw the gradient header (call after resizing)."""
        self._draw_header(self._hdr_canvas)
