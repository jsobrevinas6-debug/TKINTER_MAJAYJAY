import tkinter as tk
from tkinter import filedialog, messagebox
import threading

try:
    from student_dashboard import supabase, BG, WHITE, PURPLE, PURPLE2, BORDER, TEXT_DARK, TEXT_GRAY
except ImportError:
    BG=WHITE=PURPLE=PURPLE2=BORDER=TEXT_DARK=TEXT_GRAY=""
    supabase = None

INPUT_BG  = "#F7FAFC"
DISABLED  = "#EDF2F7"
VIOLET    = "#7E57C2"
GREEN_TXT = "#48BB78"
RED       = "#E53E3E"


class ProfileFrame(tk.Frame):
    def __init__(self, parent, name, email, dashboard, **_):
        super().__init__(parent, bg=BG)
        self.name      = name
        self.email     = email
        self.dashboard = dashboard
        self._editing  = False
        self._saving   = False
        self._photo_path = None
        self._entries  = {}
        self._build()

    # ── Build UI ───────────────────────────────────────────────────────────────
    def _build(self):
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG)
        wid = canvas.create_window((0,0), window=inner, anchor="nw")

        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(wid, width=e.width)
        canvas.bind("<Configure>", _resize)
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

        # ── Header banner ──────────────────────────────────────────────────────
        hdr = tk.Frame(inner, bg=VIOLET)
        hdr.pack(fill="x")

        # Edit/Cancel toggle
        self._toggle_btn = tk.Button(
            hdr, text="✏ Edit",
            bg=WHITE, fg=VIOLET,
            relief="flat", bd=0,
            font=("Helvetica",10,"bold"),
            padx=12, pady=4, cursor="hand2",
            command=self._toggle_edit)
        self._toggle_btn.pack(anchor="ne", padx=16, pady=(12,0))

        # Avatar circle
        self._avatar_canvas = tk.Canvas(hdr, width=100, height=100,
                                        bg=VIOLET, highlightthickness=0)
        self._avatar_canvas.pack(pady=(4,0))
        self._draw_avatar()

        self._photo_btn = tk.Button(
            hdr, text="📷 Change Photo",
            bg=VIOLET, fg=WHITE,
            relief="flat", bd=0,
            font=("Helvetica",9), cursor="hand2",
            command=self._pick_photo,
            state="disabled")
        self._photo_btn.pack(pady=(4,0))

        tk.Label(hdr, text=self.name,
                 bg=VIOLET, fg=WHITE,
                 font=("Helvetica",16,"bold")).pack(pady=(8,2))
        tk.Label(hdr, text="Scholar",
                 bg=VIOLET, fg="#D1C4E9",
                 font=("Helvetica",10)).pack(pady=(0,20))

        # ── Form area ──────────────────────────────────────────────────────────
        body = tk.Frame(inner, bg=BG)
        body.pack(fill="both", padx=32, pady=20)

        # Personal Information
        self._section_label(body,"Personal Information")
        personal = [
            ("Full Name",     "name",       self.name,  False),
            ("Email",         "email",      self.email, False),
            ("Phone Number",  "phone",      "09171234567", True),
            ("Address",       "address",    "Los Baños, Laguna", True),
        ]
        for label, key, default, editable in personal:
            self._profile_field(body, label, key, default, editable)

        self._section_label(body,"Academic Information")
        academic = [
            ("Student ID", "student_id", "2024-12345",        False),
            ("Course",     "course",     "BS Computer Science", True),
        ]
        for label, key, default, editable in academic:
            self._profile_field(body, label, key, default, editable)

        # Scholarship status card
        self._section_label(body,"Scholarship Status")
        status_card = tk.Frame(body, bg=WHITE,
                               highlightbackground=GREEN_TXT,
                               highlightthickness=1)
        status_card.pack(fill="x", pady=(4,12))
        tk.Label(status_card, text="✅  Active Scholar",
                 bg=WHITE, fg=GREEN_TXT,
                 font=("Helvetica",13,"bold"),
                 padx=16, pady=8, anchor="w").pack(fill="x")
        tk.Label(status_card, text="Mayor's Scholarship Program",
                 bg=WHITE, fg=TEXT_GRAY,
                 font=("Helvetica",10),
                 padx=16, pady=(0,12), anchor="w").pack(fill="x")

        # Save button (hidden until editing)
        self._save_btn = tk.Button(
            body, text="💾 Save Changes",
            bg=VIOLET, fg=WHITE,
            activebackground=PURPLE2,
            relief="flat", bd=0,
            font=("Helvetica",12,"bold"),
            height=2, cursor="hand2",
            command=self._save_profile)
        # Not packed yet — shown when editing

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _section_label(self, parent, text):
        tk.Label(parent, text=text,
                 bg=BG, fg=VIOLET,
                 font=("Helvetica",13,"bold"),
                 anchor="w").pack(fill="x", pady=(16,4))

    def _profile_field(self, parent, label, key, default, editable):
        tk.Label(parent, text=label,
                 bg=BG, fg=TEXT_GRAY,
                 font=("Helvetica",9), anchor="w").pack(fill="x")
        var = tk.StringVar(value=default)
        state = "disabled"  # start read-only
        bg    = DISABLED
        e = tk.Entry(parent, textvariable=var, state=state,
                     bg=bg, fg=TEXT_DARK,
                     disabledbackground=DISABLED,
                     disabledforeground=TEXT_DARK,
                     insertbackground=VIOLET,
                     relief="flat", bd=0,
                     font=("Helvetica",12),
                     highlightthickness=1,
                     highlightbackground=BORDER,
                     highlightcolor=VIOLET)
        e.pack(fill="x", ipady=8, pady=(2,10))
        self._entries[key] = (e, var, editable)

    def _draw_avatar(self, path=None):
        c = self._avatar_canvas
        c.delete("all")
        initial = self.name[0].upper() if self.name else "S"
        if path:
            try:
                from PIL import Image, ImageTk
                img = Image.open(path).resize((96,96))
                self._photo_img = ImageTk.PhotoImage(img)
                c.create_oval(2,2,98,98, fill=WHITE, outline=WHITE)
                c.create_image(50,50, image=self._photo_img)
                return
            except ImportError:
                pass
        c.create_oval(2,2,98,98, fill=WHITE, outline=WHITE)
        c.create_text(50,50, text=initial,
                      fill=VIOLET, font=("Helvetica",36,"bold"))

    def _pick_photo(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images","*.jpg *.jpeg *.png")])
        if path:
            self._photo_path = path
            self._draw_avatar(path)

    # ── Edit toggle ────────────────────────────────────────────────────────────
    def _toggle_edit(self):
        self._editing = not self._editing
        self._toggle_btn.config(
            text="✕ Cancel" if self._editing else "✏ Edit")
        self._photo_btn.config(
            state="normal" if self._editing else "disabled")

        for key, (entry, var, editable) in self._entries.items():
            if editable:
                if self._editing:
                    entry.config(state="normal", bg=INPUT_BG)
                else:
                    entry.config(state="disabled", bg=DISABLED)

        if self._editing:
            self._save_btn.pack(fill="x", pady=(8,20))
        else:
            self._save_btn.pack_forget()

    # ── Save ───────────────────────────────────────────────────────────────────
    def _save_profile(self):
        if self._saving:
            return
        self._saving = True
        self._save_btn.config(state="disabled", text="Saving…", bg="#A0AEC0")
        threading.Thread(target=self._do_save, daemon=True).start()

    def _do_save(self):
        import time
        time.sleep(0.8)  # simulate API call
        self.after(0, self._on_saved)

    def _on_saved(self):
        self._saving = False
        self._save_btn.config(state="normal",
                              text="💾 Save Changes", bg=VIOLET)
        self._toggle_edit()  # exit edit mode
        messagebox.showinfo("Saved","Profile updated successfully!")