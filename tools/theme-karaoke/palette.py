"""Colour palette of the Karaoke theme.

Same rule as the design mock-ups: everything is derived from one base colour.
Surfaces step towards white on a dark base and towards black on a light one;
text is light or dark, whichever contrasts more with the base, and the dimmer
text tones are the dimmest that still pass their contrast target.
"""

LIGHT_INK = (242, 242, 239)
DARK_INK = (17, 18, 20)

ACCENT = (0xFF, 0x5A, 0x36)
ON_ACCENT = (0x0E, 0x0F, 0x12)
GOLD = (0xFF, 0xC5, 0x3D)

# the skins: file name, display name, base colour
SKINS = [
    ("Negro", "Negro", (0x0E, 0x0F, 0x12)),
    ("AzulNoche", "Azul noche", (0x14, 0x21, 0x3D)),
    ("Berenjena", "Berenjena", (0x2A, 0x1B, 0x3D)),
    ("Hueso", "Hueso", (0xF4, 0xF1, 0xEA)),
]


def mix(a, b, t):
    return tuple(av + (bv - av) * t for av, bv in zip(a, b))


def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    x, y = lum(a), lum(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


def rgb_int(c):
    return tuple(int(round(max(0, min(255, v)))) for v in c)


def make_palette(base, accent=ACCENT):
    bg = base
    is_dark = contrast(bg, LIGHT_INK) >= contrast(bg, DARK_INK)
    ink = LIGHT_INK if is_dark else DARK_INK
    to = (255, 255, 255) if is_dark else (0, 0, 0)
    k = 1.0 if is_dark else 0.8

    def step(t):
        return mix(bg, to, t * k)

    s2 = step(0.08)

    def dim(target):
        t = 0.6
        while t > 0:
            c = mix(ink, bg, t)
            if contrast(c, s2) >= target and contrast(c, bg) >= target:
                return c
            t -= 0.02
        return ink

    def ink_for(color, target):
        t = 0.0
        while t <= 1.0001:
            c = mix(color, ink, t)
            if contrast(c, s2) >= target and contrast(c, bg) >= target:
                return c
            t += 0.05
        return ink

    # dark version of the base: behind the note lanes and score cards on the
    # sing screen, which must stay dark over any video, also with a light skin
    scrim = (6, 6, 8)
    t = 0.0
    while t <= 1.0001:
        c = mix(bg, (6, 6, 8), t)
        if lum(c) <= 0.006:
            scrim = c
            break
        t += 0.02

    p = {
        "Bg": bg,
        "Surface": step(0.04),
        "Surface2": step(0.08),
        "Surface3": step(0.11),
        "Divider": step(0.07),
        "Line": step(0.16),
        "Line2": step(0.22),
        "Muted": step(0.30),
        "Highlight": step(0.20),
        "Text": ink,
        "Text2": dim(7),
        "Text3": dim(4.6),
        "Accent": accent,
        "AccentText": ink_for(accent, 4.5),
        "OnAccent": ON_ACCENT,
        "Gold": GOLD,
        "Scrim": scrim,
        "ScrimText": LIGHT_INK,
        "ScrimText2": (0xAE, 0xAE, 0xAD),
        "NoteBlue": (0x4F, 0x9D, 0xFF),
        "NoteMint": (0x2F, 0xD3, 0x9A),
        "NoteViolet": (0xC0, 0x8C, 0xFF),
    }
    p = {k: rgb_int(v) for k, v in p.items()}
    p["_is_dark"] = is_dark
    return p


if __name__ == "__main__":
    for file, name, base in SKINS:
        p = make_palette(base)
        print(name, {k: "#%02X%02X%02X" % v for k, v in p.items() if not k.startswith("_")})
