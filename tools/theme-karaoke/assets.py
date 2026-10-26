"""Flat image assets of the Karaoke theme.

Almost everything is drawn white on transparent: the theme tints each image
with a named colour (Color = Surface, Accent, ...), so one set of images serves
every skin. Images are drawn at 2x the size they are shown at on the
1280x720 canvas, so they stay sharp on high-density screens.

Exceptions:
* note pieces: the game recolours them by replacing the hue only, so they carry
  their real grey/colour values and a dark + light ring that keeps every note
  visible over any video;
* key caps and icons with a fixed look.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

SCALE = 2          # image pixels per canvas pixel
SS = 4             # supersampling for anti-aliasing
WHITE = (255, 255, 255, 255)


class Assets:
    def __init__(self, outdir, fontdir):
        self.outdir = outdir
        self.fontdir = fontdir
        self.files = {}        # skin texture name -> file name
        os.makedirs(outdir, exist_ok=True)

    # -- helpers ---------------------------------------------------------
    def _save(self, name, filename, im):
        im.save(os.path.join(self.outdir, filename), optimize=True)
        self.files[name] = filename
        return name

    @staticmethod
    def _canvas(w, h):
        return Image.new("RGBA", (w * SS, h * SS), (255, 255, 255, 0))

    @staticmethod
    def _down(im, w, h):
        # resample with premultiplied alpha, so the edges don't pick up the
        # colour of the transparent pixels (dark fringes on light skins)
        if im.mode == "RGBA":
            out = im.convert("RGBa").resize((w, h), Image.LANCZOS).convert("RGBA")
            # white shapes (tinted by the game): make every pixel white, the
            # transparent ones too, since the GPU filters them in as well
            r, g, b_, a = out.split()
            if min(r.getextrema()[0], g.getextrema()[0], b_.getextrema()[0]) >= 0 and \
                    all(px >= 250 for px, al in zip(r.getdata(), a.getdata()) if al > 8):
                white = Image.new("L", out.size, 255)
                out = Image.merge("RGBA", (white, white, white, a))
            return out
        return im.resize((w, h), Image.LANCZOS)

    def font(self, file, size):
        return ImageFont.truetype(os.path.join(self.fontdir, file), size)

    # -- shapes (white, tinted by the theme) --------------------------------
    def panel(self, w, h, r, outline=0):
        """Rounded rectangle of w x h canvas pixels, radius r (filled, or a
        ring of the given width)."""
        name = "K_panel_%dx%d_r%d%s" % (w, h, r, ("_o%d" % outline) if outline else "")
        if name in self.files:
            return name
        pw, ph = w * SCALE, h * SCALE
        im = self._canvas(pw, ph)
        d = ImageDraw.Draw(im)
        rr = min(r, w / 2, h / 2) * SCALE * SS
        box = (0, 0, pw * SS - 1, ph * SS - 1)
        if outline:
            d.rounded_rectangle(box, rr, outline=WHITE, width=int(outline * SCALE * SS))
        else:
            d.rounded_rectangle(box, rr, fill=WHITE)
        return self._save(name, name + ".png", self._down(im, pw, ph))

    def panel_rgba(self, w, h, r, rgba, name=None):
        """Rounded rectangle with a fixed colour (for images the game
        recolours itself, e.g. by replacing the hue)."""
        name = name or "K_panelc_%dx%d_r%d_%02x%02x%02x%02x" % ((w, h, r) + tuple(rgba))
        if name in self.files:
            return name
        pw, ph = w * SCALE, h * SCALE
        im = self._canvas(pw, ph)
        ImageDraw.Draw(im).rounded_rectangle((0, 0, pw * SS - 1, ph * SS - 1), r * SCALE * SS, fill=tuple(rgba))
        return self._save(name, name + ".png", self._down(im, pw, ph))

    def pause_overlay(self, w, h, label="Pausa"):
        """Dimmed screen with a card in the middle (the pause popup)."""
        name = "K_pause"
        if name in self.files:
            return name
        im = Image.new("RGBA", (w, h), (14, 15, 18, 150))
        d = ImageDraw.Draw(im)
        cw, ch = 280, 120
        x0, y0 = (w - cw) // 2, (h - ch) // 2
        d.rounded_rectangle((x0, y0, x0 + cw, y0 + ch), 22, fill=(22, 24, 29, 255))
        f = self.font("Inter/InterDisplay-Bold.ttf", 40)
        bb = d.textbbox((0, 0), label, font=f)
        d.text((x0 + (cw - (bb[2] - bb[0])) / 2 - bb[0], y0 + (ch - (bb[3] - bb[1])) / 2 - bb[1]), label,
               font=f, fill=(242, 242, 239, 255))
        return self._save(name, name + ".png", im)

    def rating_ladder(self, level, w=300, h=12, steps=8, colors=None, suffix=""):
        """The rating shown on the score screen: a row of segments, the
        current level bright, the levels already passed dimmed. colors =
        (current, passed, ahead) as RGBA, from the skin palette."""
        name = "K_rating_%d%s" % (level, suffix)
        if name in self.files:
            return name
        pw, ph = w * SCALE, h * SCALE
        im = self._canvas(pw, ph)
        d = ImageDraw.Draw(im)
        gap = 4 * SCALE * SS
        seg = (pw * SS - gap * (steps - 1)) / steps
        for i in range(steps):
            x0 = i * (seg + gap)
            cur, done, ahead = colors or ((242, 242, 239, 255), (150, 150, 155, 140), (120, 120, 125, 70))
            col = cur if i == level else (done if i < level else ahead)
            d.rounded_rectangle((x0, 0, x0 + seg, ph * SS - 1), 3 * SCALE * SS, fill=col)
        return self._save(name, name + ".png", self._down(im, pw, ph))

    def bonus_badge(self, w, h, ring=2):
        """Line bonus popup. The game re-hues it with the colour of the rating
        (red .. green), so it is drawn saturated: a dark body and a bright
        ring of the same hue."""
        name = "K_linebonus"
        if name in self.files:
            return name
        pw, ph = w * SCALE, h * SCALE
        im = self._canvas(pw, ph)
        d = ImageDraw.Draw(im)
        rr = ph * SS / 2
        box = (0, 0, pw * SS - 1, ph * SS - 1)
        d.rounded_rectangle(box, rr, fill=(255, 77, 77, 255))
        k = ring * SCALE * SS
        d.rounded_rectangle((k, k, pw * SS - 1 - k, ph * SS - 1 - k), rr - k, fill=(64, 13, 13, 235))
        return self._save(name, name + ".png", self._down(im, pw, ph))

    def tinted(self, name, rgb, suffix):
        """Copy of a saved white image in a fixed colour (for images the
        game draws without tinting them)."""
        new = name + suffix
        if new in self.files:
            return new
        im = Image.open(os.path.join(self.outdir, self.files[name])).convert("RGBA")
        solid = Image.new("RGBA", im.size, tuple(rgb) + (255,))
        solid.putalpha(im.getchannel("A"))
        return self._save(new, new + ".png", solid)

    def pill(self, w, h):
        return self.panel(w, h, h // 2)

    def circle(self, d_):
        return self.panel(d_, d_, d_ // 2)

    def dashed_panel(self, w, h, r, width=2, dash=10, gap=7):
        name = "K_dashed_%dx%d_r%d" % (w, h, r)
        if name in self.files:
            return name
        pw, ph = w * SCALE, h * SCALE
        full = self._canvas(pw, ph)
        ImageDraw.Draw(full).rounded_rectangle((0, 0, pw * SS - 1, ph * SS - 1), r * SCALE * SS,
                                               outline=WHITE, width=width * SCALE * SS)
        # cut the outline into dashes along x and y
        mask = Image.new("L", full.size, 0)
        md = ImageDraw.Draw(mask)
        step = (dash + gap) * SCALE * SS
        for x in range(0, full.size[0], step):
            md.rectangle((x, 0, x + dash * SCALE * SS, full.size[1]), fill=255)
        mask2 = Image.new("L", full.size, 0)
        md2 = ImageDraw.Draw(mask2)
        for y in range(0, full.size[1], step):
            md2.rectangle((0, y, full.size[0], y + dash * SCALE * SS), fill=255)
        a = full.split()[3]
        from PIL import ImageChops
        horiz = ImageChops.multiply(a, mask)
        vert = ImageChops.multiply(a, mask2)
        # horizontal edges keep x-dashes, vertical edges keep y-dashes
        edge = Image.new("L", full.size, 0)
        ed = ImageDraw.Draw(edge)
        band = (r + width) * SCALE * SS
        ed.rectangle((band, 0, full.size[0] - band, full.size[1]), fill=255)
        out_a = ImageChops.add(ImageChops.multiply(horiz, edge), ImageChops.multiply(vert, ImageChops.invert(edge)))
        full.putalpha(out_a)
        return self._save(name, name + ".png", self._down(full, pw, ph))

    def rect(self, w=8, h=8):
        name = "K_rect"
        if name not in self.files:
            self._save(name, name + ".png", Image.new("RGBA", (w, h), WHITE))
        return name

    def transparent(self):
        name = "K_none"
        if name not in self.files:
            self._save(name, name + ".png", Image.new("RGBA", (4, 4), (0, 0, 0, 0)))
        return name

    def hline(self, w, thickness=1):
        return self.panel(w, thickness, 0)

    # -- icons (white strokes, 24-unit grid like common icon sets) -----------
    ICONS = {
        "mic": [("rrect", (9, 2, 15, 14), 3), ("arc", (5, 3, 19, 17), 0, 180), ("line", (12, 17, 12, 22))],
        "search": [("circle", (4, 4, 18, 18)), ("line", (16, 16, 21, 21))],
        "play": [("poly", ((7, 4.5), (7, 19.5), (19, 12)), True)],
        "pause": [("rect", (6, 4, 10, 20), True), ("rect", (14, 4, 18, 20), True)],
        "video": [("rrect", (3, 6, 16, 18), 2), ("poly", ((16, 10), (21, 7), (21, 17), (16, 14)), False)],
        "medley": [("line", (4, 18, 4, 8)), ("line", (10, 18, 10, 4)), ("line", (16, 18, 16, 11)), ("line", (22, 18, 22, 9))],
        "duet": [("circle", (3, 5, 11, 13)), ("circle", (13, 5, 21, 13)), ("arc", (1, 14, 13, 26), 180, 360), ("arc", (11, 14, 23, 26), 180, 360)],
        "rap": [("line", (5, 7, 19, 7)), ("line", (5, 12, 16, 12)), ("line", (5, 17, 12, 17))],
        "menu": [("line", (4, 7, 20, 7)), ("line", (4, 12, 20, 12)), ("line", (4, 17, 20, 17))],
        "star": [("poly", ((12, 2.5), (14.8, 9), (21.5, 9.3), (16.2, 13.6), (18, 20.5), (12, 16.6), (6, 20.5), (7.8, 13.6), (2.5, 9.3), (9.2, 9)), True)],
        "trophy": [("line", (8, 21, 16, 21)), ("line", (12, 17, 12, 21)), ("rrect", (7, 3, 17, 12), 4), ("arc", (2, 4, 9, 11), 90, 270), ("arc", (15, 4, 22, 11), 270, 90)],
        "error": [("circle", (3, 3, 21, 21)), ("line", (12, 7, 12, 13)), ("dot", (12, 16.5))],
        "question": [("circle", (3, 3, 21, 21)), ("arc", (8.5, 6, 15.5, 13), 200, 30), ("line", (12, 13, 12, 14)), ("dot", (12, 17))],
        "gear": [("circle", (8, 8, 16, 16)), ("circle", (4, 4, 20, 20))],
        "stats": [("line", (5, 20, 5, 12)), ("line", (10, 20, 10, 6)), ("line", (15, 20, 15, 14)), ("line", (20, 20, 20, 9))],
        "party": [("circle", (3, 4, 10, 11)), ("circle", (14, 4, 21, 11)), ("arc", (1, 13, 12, 24), 180, 360), ("arc", (12, 13, 23, 24), 180, 360)],
        "note": [("circle", (4, 14, 11, 21)), ("line", (11, 17.5, 11, 4)), ("line", (11, 4, 19, 6))],
        "cd": [("circle", (3, 3, 21, 21)), ("circle", (9.5, 9.5, 14.5, 14.5))],
        "close": [("line", (6, 6, 18, 18)), ("line", (18, 6, 6, 18))],
        "random": [("line", (4, 7, 9, 7)), ("line", (9, 7, 15, 17)), ("line", (15, 17, 20, 17)), ("line", (4, 17, 9, 17)), ("line", (9, 17, 15, 7)), ("line", (15, 7, 20, 7))],
        "repeat": [("rrect", (4, 7, 20, 17), 4)],
        "next": [("poly", ((5, 5), (5, 19), (16, 12)), True), ("rect", (17, 5, 19.5, 19), True)],
        "prev": [("poly", ((19, 5), (19, 19), (8, 12)), True), ("rect", (4.5, 5, 7, 19), True)],
        "list": [("dot", (5, 7)), ("dot", (5, 12)), ("dot", (5, 17)), ("line", (9, 7, 20, 7)), ("line", (9, 12, 20, 12)), ("line", (9, 17, 20, 17))],
        "pin": [("line", (12, 15, 12, 21)), ("rrect", (8, 3, 16, 9), 1), ("poly", ((6, 15), (18, 15), (16, 9), (8, 9)), False)],
        "lyric": [("line", (5, 6, 19, 6)), ("line", (12, 6, 12, 19))],
        "arrow_left": [("poly", ((15, 5), (8, 12), (15, 19)), False)],
        "arrow_right": [("poly", ((9, 5), (16, 12), (9, 19)), False)],
        "plus": [("line", (12, 5, 12, 19)), ("line", (5, 12, 19, 12))],
        "joker": [("star", None)],
        "monitor": [("rrect", (3, 4, 21, 16), 2), ("line", (12, 16, 12, 20)), ("line", (8, 20, 16, 20))],
        "speaker": [("poly", ((4, 9), (8, 9), (13, 5), (13, 19), (8, 15), (4, 15)), False), ("arc", (10, 7, 19, 17), 300, 60)],
        "keyboard": [("rrect", (2, 6, 22, 18), 2), ("dot", (6.5, 10)), ("dot", (10.2, 10)), ("dot", (13.8, 10)),
                     ("dot", (17.5, 10)), ("line", (8, 14, 16, 14))],
        "palette": [("circle", (3, 3, 21, 21)), ("dot", (8, 10)), ("dot", (12, 7)), ("dot", (16, 10)), ("dot", (15, 15))],
        "sliders": [("line", (4, 7, 20, 7)), ("line", (4, 17, 20, 17)), ("circle", (12.5, 4.5, 17.5, 9.5)),
                    ("circle", (6.5, 14.5, 11.5, 19.5))],
        "globe": [("circle", (3, 3, 21, 21)), ("line", (3.5, 12, 20.5, 12)), ("arc", (8, 3, 16, 21), 0, 360)],
        "camera": [("rrect", (3, 7, 21, 19), 3), ("circle", (8.5, 9.5, 15.5, 16.5)), ("line", (9, 4.5, 15, 4.5))],
        "chev_up": [("line", (6, 15, 12, 9)), ("line", (12, 9, 18, 15))],
        "chev_down": [("line", (6, 9, 12, 15)), ("line", (12, 15, 18, 9))],
        "back": [("line", (5, 12, 19, 12)), ("line", (5, 12, 10, 7)), ("line", (5, 12, 10, 17))],
    }

    def icon(self, key, size=24, stroke=2.0):
        name = "K_icon_%s_%d" % (key, size)
        if name in self.files:
            return name
        px = size * SCALE
        im = self._canvas(px, px)
        d = ImageDraw.Draw(im)
        k = px * SS / 24.0
        sw = max(1, int(round(stroke * k)))

        def P(x, y):
            return (x * k, y * k)

        for item in self.ICONS[key]:
            kind = item[0]
            if kind == "line":
                x1, y1, x2, y2 = item[1]
                d.line((P(x1, y1), P(x2, y2)), fill=WHITE, width=sw)
                for (x, y) in ((x1, y1), (x2, y2)):
                    cx, cy = P(x, y)
                    d.ellipse((cx - sw / 2, cy - sw / 2, cx + sw / 2, cy + sw / 2), fill=WHITE)
            elif kind == "circle":
                x1, y1, x2, y2 = item[1]
                d.ellipse((*P(x1, y1), *P(x2, y2)), outline=WHITE, width=sw)
            elif kind == "rrect":
                x1, y1, x2, y2 = item[1]
                d.rounded_rectangle((*P(x1, y1), *P(x2, y2)), item[2] * k, outline=WHITE, width=sw)
            elif kind == "rect":
                x1, y1, x2, y2 = item[1]
                d.rectangle((*P(x1, y1), *P(x2, y2)), fill=WHITE)
            elif kind == "arc":
                x1, y1, x2, y2 = item[1]
                d.arc((*P(x1, y1), *P(x2, y2)), item[2], item[3], fill=WHITE, width=sw)
            elif kind == "poly":
                pts = [P(x, y) for x, y in item[1]]
                if item[2]:
                    d.polygon(pts, fill=WHITE)
                else:
                    d.line(pts + [pts[0]], fill=WHITE, width=sw, joint="curve")
            elif kind == "dot":
                cx, cy = P(*item[1])
                r = sw * 0.75
                d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE)
            elif kind == "star":
                pass
        return self._save(name, name + ".png", self._down(im, px, px))

    # -- key caps of the legend ------------------------------------------
    def keycap(self, label, h=24, font_file="JetBrainsMono/JetBrainsMono-Medium.ttf"):
        """White rounded cap with the label cut out (transparent), tinted by
        the theme. Width follows the label."""
        safe = "".join(c if c.isalnum() else "_" for c in label) or "k"
        name = "K_key_%s" % safe
        if name in self.files:
            return name, self._key_w[name]
        if not hasattr(self, "_key_w"):
            self._key_w = {}
        f = self.font(font_file, int(12 * SCALE * SS))
        tw = f.getlength(label)
        w = int(math.ceil(tw / (SCALE * SS))) + 16
        w = max(w, h)
        pw, ph = w * SCALE, h * SCALE
        im = self._canvas(pw, ph)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, pw * SS - 1, ph * SS - 1), 6 * SCALE * SS, fill=WHITE)
        # punch the label out of the cap
        mask = Image.new("L", im.size, 0)
        md = ImageDraw.Draw(mask)
        bbox = md.textbbox((0, 0), label, font=f)
        tx = (im.size[0] - (bbox[2] - bbox[0])) / 2 - bbox[0]
        ty = (im.size[1] - (bbox[3] - bbox[1])) / 2 - bbox[1]
        md.text((tx, ty), label, font=f, fill=255)
        a = im.split()[3]
        from PIL import ImageChops
        im.putalpha(ImageChops.subtract(a, mask))
        self._save(name, name + ".png", self._down(im, pw, ph))
        self._key_w[name] = w
        return name, w

    def chip(self, icon_key, label, h=28, font_file="Inter/Inter-Medium.ttf"):
        """Outlined pill with an icon and a label (white, tinted by the
        theme): the features of a song. Returns (name, width)."""
        safe = "".join(c if c.isalnum() else "_" for c in label)
        name = "K_chip_%s_%s" % (icon_key, safe)
        if not hasattr(self, "_chip_w"):
            self._chip_w = {}
        if name in self.files:
            return name, self._chip_w[name]
        k = SCALE * SS
        f = self.font(font_file, int(14 * k))
        tw = f.getlength(label) / k
        icon = 16
        w = int(math.ceil(12 + icon + 6 + tw + 12))
        pw, ph = w * SCALE, h * SCALE
        im = self._canvas(pw, ph)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, pw * SS - 1, ph * SS - 1), ph * SS / 2, outline=WHITE,
                            width=int(1.5 * k))
        # icon: drawn with the icon routine at its size, pasted in
        ic = Image.open(os.path.join(self.outdir, self.files[self.icon(icon_key)])).convert("RGBA")
        ic = ic.resize((int(icon * k), int(icon * k)), Image.LANCZOS)
        im.alpha_composite(ic, (int(12 * k), int((h - icon) / 2 * k)))
        bbox = d.textbbox((0, 0), label, font=f)
        d.text((int((12 + icon + 6) * k) - bbox[0], (ph * SS - (bbox[3] - bbox[1])) / 2 - bbox[1]), label,
               font=f, fill=WHITE)
        self._save(name, name + ".png", self._down(im, pw, ph))
        self._chip_w[name] = w
        return name, w

    # -- note pieces -------------------------------------------------------
    def notes(self, prefix, body, rap=False):
        """Left cap, tiling middle and right cap of a note. body is the RGB of
        the note body; the game replaces only its hue. Every note has a dark
        ring and a light ring outside it, so it stays visible over any video.
        Returns the three texture names."""
        H = 64                      # texture height = note height
        ring_light, ring_dark = 6, 6  # out of 64 (= 2px each on a ~22px note)
        light = (242, 242, 239, 204)
        dark = (14, 15, 18, 255)

        def draw(w, kind):
            im = self._canvas(w, H)
            d = ImageDraw.Draw(im)
            s = SS
            R = H * s / 2

            def shape(inset, fill):
                if kind == "mid":
                    d.rectangle((0, inset * s, w * s, H * s - inset * s), fill=fill)
                else:
                    # half of a circle of diameter H (left or right cap)
                    cx = (w * s) if kind == "left" else 0
                    r = R - inset * s
                    d.ellipse((cx - r, R - r, cx + r, R + r), fill=fill)
                    if kind == "left":
                        d.rectangle((cx, inset * s, w * s, H * s - inset * s), fill=fill)
                    else:
                        d.rectangle((0, inset * s, cx, H * s - inset * s), fill=fill)

            shape(0, light)
            shape(ring_light, dark)
            shape(ring_light + ring_dark, body + (255,))
            if rap:
                # rap notes: a row of dark dots inside the body
                if kind == "mid":
                    for x in range(4, w, 16):
                        d.ellipse((x * s, (H / 2 - 4) * s, (x + 8) * s, (H / 2 + 4) * s), fill=dark)
            return self._down(im, w, H)

        names = []
        for kind, w in (("left", 32), ("mid", 64), ("right", 32)):
            n = "%s%s" % (prefix, kind.capitalize())
            self._save(n, n + ".png", draw(w, kind))
            names.append(n)
        return names

    def save_custom(self, name, im):
        return self._save(name, name + ".png", im)
