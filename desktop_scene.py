"""Tkinter renderer for the game's bottom-left-origin drawing API."""
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tkinter as tk
import tkinter.font as tkfont
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageFont, ImageTk

__all__ = ['Scene', 'Rect', 'fill', 'stroke', 'stroke_weight', 'no_fill',
           'no_stroke', 'tint', 'rect', 'ellipse', 'line', 'text', 'image', 'sound']
_active = None


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    def __iter__(self):
        return iter((self.x, self.y, self.w, self.h))

    def __contains__(self, point):
        return self.x <= point.x < self.x + self.w and self.y <= point.y < self.y + self.h

    def center(self):
        return SimpleNamespace(x=self.x + self.w / 2, y=self.y + self.h / 2)


def _color(values):
    if len(values) == 1 and isinstance(values[0], str):
        return values[0], 1
    if len(values) == 1:
        values = values[0]
    rgb = values[:3]
    return '#' + ''.join(f'{max(0, min(255, round(c * 255))):02x}' for c in rgb), values[3] if len(values) > 3 else 1


def fill(*values):
    _active.fill_color, _active.fill_alpha = _color(values)


def stroke(*values):
    _active.stroke_color, _ = _color(values)


def stroke_weight(value):
    _active.stroke_width = value


def no_fill():
    _active.fill_color = ''


def no_stroke():
    _active.stroke_color = ''


def tint(*values):
    _active.text_color, _ = _color(values)


def _shape(kind, x, y, w, h):
    s = _active
    # Tk stippling approximates translucent overlays while keeping backgrounds visible.
    stipple = 'gray50' if s.fill_alpha < 0.85 else ''
    return getattr(s.canvas, kind)(x, s.size.h - y - h, x + w, s.size.h - y,
        fill=s.fill_color, outline=s.stroke_color if s.stroke_width else '',
        width=s.stroke_width, stipple=stipple)


def rect(x, y, w, h):
    return _shape('create_rectangle', x, y, w, h)


def ellipse(x, y, w, h):
    return _shape('create_oval', x, y, w, h)


def line(x1, y1, x2, y2):
    s = _active
    return s.canvas.create_line(x1, s.size.h - y1, x2, s.size.h - y2,
                               fill=s.stroke_color or s.text_color, width=s.stroke_width)


def text(value, font_name, font_size, x, y):
    s = _active
    family = s.default_font
    if 'Hiragino' in font_name:
        family = s.japanese_font
    elif 'Emoji' in font_name:
        family = s.emoji_font
    weight = 'bold' if any(t in font_name for t in ('Bold', 'W6', 'Medium')) else 'normal'
    if s.raster_text:
        s.draw_text_image(str(value), font_name, max(1, round(font_size)), x, y, weight)
    else:
        s.canvas.create_text(x, s.size.h - y, text=value, fill=s.text_color,
                             font=(family, -max(1, round(font_size)), weight))


def image(filename, x, y, w, h):
    s = _active
    key = (filename, round(w), round(h))
    if key not in s.images:
        # Keep only the current window size; resizing must not grow the cache forever.
        s.images = {k: v for k, v in s.images.items() if k[1:] == key[1:]}
        with Image.open(Path(__file__).parent / filename) as source:
            s.images[key] = ImageTk.PhotoImage(source.resize(key[1:], Image.Resampling.LANCZOS), master=s.root)
    s.canvas.create_image(x, s.size.h - y - h, image=s.images[key], anchor='nw')


class _Sound:
    def play_effect(self, name):
        if _active is not None:
            _active.root.bell()


sound = _Sound()


class Scene:
    def __init__(self, root):
        self.root = root
        self.size = SimpleNamespace(w=1200, h=1000)
        self.canvas = tk.Canvas(root, highlightthickness=0, background='#152231')
        self.canvas.pack(fill='both', expand=True)
        self.images = {}
        self.pending = set()
        self.frame_timer = None
        self.text_images = {}
        self.frame_images = []
        self.font_paths = {}
        self.fill_color, self.fill_alpha = 'white', 1
        self.stroke_color, self.stroke_width = '', 0
        self.text_color = 'white'
        fonts = set(tkfont.families(root))
        self.raster_text = 'Noto Sans CJK JP' not in fonts and bool(shutil.which('fc-match'))
        self.default_font = tkfont.nametofont('TkDefaultFont', root).actual('family')
        self.japanese_font = next((f for f in ('Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Noto Sans CJK JP') if f in fonts), 'sans-serif')
        self.emoji_font = next((f for f in ('Apple Color Emoji', 'Segoe UI Emoji', 'Noto Emoji', 'Noto Color Emoji') if f in fonts), 'sans-serif')
        self.canvas.bind('<Button-1>', self._click)
        self.root.bind('<Escape>', lambda event: self.root.destroy())
        self.root.bind('<Destroy>', self._destroy, add='+')
        self.setup()

    def draw_text_image(self, value, requested_font, size, x, y, weight):
        # Some Linux Tk builds only expose legacy X11 bitmap fonts. Pillow uses
        # Unicode TrueType fonts even on those builds, including Japanese/emoji.
        family = ('Noto Color Emoji' if 'Emoji' in requested_font else
                  'Noto Sans CJK JP' if ('Hiragino' in requested_font or
                      any('\u3000' <= char <= '\u9fff' for char in value)) else 'DejaVu Sans')
        query = family + (':style=Bold' if weight == 'bold' and 'Emoji' not in family else '')
        if query not in self.font_paths:
            self.font_paths[query] = subprocess.check_output(
                ['fc-match', '-f', '%{file}', query], text=True).strip()
        key = (value, query, size, self.text_color)
        if key not in self.text_images:
            try:
                font = ImageFont.truetype(self.font_paths[query], size)
                render_size = size
            except OSError:
                # Color emoji fonts commonly offer a single fixed strike.
                render_size = 109
                font = ImageFont.truetype(self.font_paths[query], render_size)
            box = font.getbbox(value)
            bitmap = Image.new('RGBA', (max(1, box[2] - box[0] + 4), max(1, box[3] - box[1] + 4)))
            ImageDraw.Draw(bitmap).text((2 - box[0], 2 - box[1]), value,
                                        font=font, fill=self.text_color, embedded_color=True)
            if render_size != size:
                bitmap = bitmap.resize((max(1, round(bitmap.width * size / render_size)),
                                        max(1, round(bitmap.height * size / render_size))), Image.Resampling.LANCZOS)
            if len(self.text_images) > 512:
                self.text_images.clear()
            self.text_images[key] = ImageTk.PhotoImage(bitmap, master=self.root)
        self.frame_images.append(self.text_images[key])
        self.canvas.create_image(x, self.size.h - y, image=self.text_images[key])

    def delay(self, seconds, callback):
        def run():
            self.pending.discard(token)
            callback()
        token = self.root.after(round(seconds * 1000), run)
        self.pending.add(token)

    def cancel_delays(self):
        for token in self.pending:
            self.root.after_cancel(token)
        self.pending.clear()

    def _click(self, event):
        self.touch_began(SimpleNamespace(location=SimpleNamespace(x=event.x, y=self.size.h - event.y)))

    def frame(self):
        global _active
        _active = self
        self.size.w = max(1, self.canvas.winfo_width())
        self.size.h = max(1, self.canvas.winfo_height())
        self.update()
        self.canvas.delete('all')
        self.frame_images.clear()
        self.draw()

    def _destroy(self, event):
        if event.widget is self.root:
            self.cancel_delays()
            if self.frame_timer is not None:
                self.root.after_cancel(self.frame_timer)
                self.frame_timer = None

    def run(self):
        def tick():
            self.frame()
            self.frame_timer = self.root.after(33, tick)
        self.frame_timer = self.root.after_idle(tick)
        self.root.mainloop()
