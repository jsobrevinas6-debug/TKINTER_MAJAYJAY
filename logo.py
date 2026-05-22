"""Shared logo loader — returns a circular-cropped PhotoImage of majayjay.jpg."""
import os
from PIL import Image, ImageTk, ImageDraw

# Always resolve relative to this file, regardless of working directory
_LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "majayjay.jpg")
_cache: dict = {}


def get_logo(size: int = 60) -> "ImageTk.PhotoImage | None":
    """Return a circular PhotoImage at *size* x *size* px, or None on error."""
    if size in _cache:
        return _cache[size]
    try:
        img = Image.open(_LOGO_PATH).convert("RGBA")
        img = img.resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        photo = ImageTk.PhotoImage(img)
        _cache[size] = photo
        return photo
    except Exception as e:
        print(f"[logo] could not load logo: {e}")
        return None
