"""Hand-made screens of the Karaoke theme, laid out on the 1280x720 canvas
following the design mock-ups.

Conventions (see build_theme.py for the fonts and palette.py for colours):
* header: 76 px, microphone + "SuperStar" + breadcrumb, 48 px side margin
* footer: divider at y 656, legend key caps + labels
* surfaces: Surface (cards), Surface2 (selected rows), Surface3 (chips)
"""

from collections import OrderedDict

from build_theme import (BOLD, FONT_DISPLAY, FONT_INTER, FONT_MONO, H, OUTLINE, REGULAR, W)

M = 48            # side margin
FOOT_Y = 656      # footer divider
HEAD_H = 76


def od(**kw):
    return OrderedDict((k, str(v)) for k, v in kw.items())


class Screen:
    """Collects the free statics/texts of one screen (<Prefix>StaticN,
    <Prefix>TextN) and removes the ones the scaled base theme had."""

    def __init__(self, b, prefix, keep_statics=False, keep_texts=False):
        self.b = b
        self.ini = b.ini
        self.a = b.assets
        self.prefix = prefix
        self.ns = 0
        self.nt = 0
        self.groups = {}       # "NonParty" -> [statics, texts]
        if not keep_statics:
            self._drop(prefix + "Static", numbered=True)
        if not keep_texts:
            self._drop(prefix + "Text", numbered=True)
        self.ini.set(prefix + "Background", od(Type="Texture", Tex="K_bg", Motion=1))

    def _drop(self, base, numbered):
        for name in list(self.ini.sections):
            if name.startswith(base) and name[len(base):].isdigit():
                self.ini.remove(name)

    # -- free elements ----------------------------------------------------
    def _name(self, kind, group):
        if group is None:
            if kind == "Static":
                self.ns += 1
                return "%sStatic%d" % (self.prefix, self.ns)
            self.nt += 1
            return "%sText%d" % (self.prefix, self.nt)
        if group not in self.groups:
            self.groups[group] = [0, 0]
            self._drop(self.prefix + "Static" + group, True)
            self._drop(self.prefix + "Text" + group, True)
        i = 0 if kind == "Static" else 1
        self.groups[group][i] += 1
        return "%s%s%s%d" % (self.prefix, kind, group, self.groups[group][i])

    def static(self, x, y, w, h, tex, color="Surface", alpha=1, z=None, typ="Transparent", group=None):
        sec = od(X=x, Y=y, W=w, H=h, Tex=tex, Color=color, Type=typ)
        if alpha != 1:
            sec["Alpha"] = alpha
        if z is not None:
            sec["Z"] = z
        self.ini.set(self._name("Static", group), sec)
        return sec

    def panel(self, x, y, w, h, r=14, color="Surface", alpha=1, z=None, group=None):
        return self.static(x, y, w, h, self.a.panel(w, h, r), color, alpha, z, group=group)

    def icon(self, x, y, size, key, color="Text2", group=None, z=None):
        return self.static(x, y, size, size, self.a.icon(key), color, z=z, group=group)

    def text(self, x, y, text, size=16, color="Text", font=FONT_INTER, style=REGULAR, align=0, w=None, z=None,
             group=None):
        sec = od(X=x, Y=y, Text=text, Size=size, Color=color, Font=font, Style=style, Align=align)
        if w:
            sec["W"] = w
        if z is not None:
            sec["Z"] = z
        self.ini.set(self._name("Text", group), sec)
        return sec

    # -- common chrome --------------------------------------------------------
    def header(self, crumbs=()):
        """Microphone mark, name and an optional breadcrumb."""
        self.icon(M - 2, 26, 24, "mic", color="Accent")
        self.text(M + 28, 26, "SuperStar", size=20, font=FONT_DISPLAY, style=BOLD)
        x = M + 172
        for i, c in enumerate(crumbs):
            last = i == len(crumbs) - 1
            self.text(x, 26, "/", size=18, color="Muted")
            x += 22
            self.text(x, 27, c, size=16, color="Text" if last else "Text2")
            x += int(len(c) * 8.6) + 14

    def footer(self, legend, divider=True, group=None):
        """legend: list of (texture name of a key cap, text)."""
        if divider:
            self.panel(0, FOOT_Y, W, 1, r=0, color="Divider")
        x = M
        for tex, label in legend:
            kw = self.b.key_w.get(tex, 40)
            self.static(x, FOOT_Y + 20, kw, 24, tex, color="Text2", z=0.96, group=group)
            self.text(x + kw + 10, FOOT_Y + 21, label, size=16, color="Text2", z=0.96, group=group)
            x += kw + 10 + int(len(label) * 8.4) + 30


def text_section(text, x, y, size, color="Text", dcolor=None, font=FONT_INTER, style=REGULAR, align=0, w=None):
    sec = od(X=x, Y=y, Text=text, Size=size, Color=color, Font=font, Style=style, Align=align)
    if dcolor:
        sec["DColor"] = dcolor
    if w:
        sec["W"] = w
    return sec


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------
def main_menu(b):
    ini, a = b.ini, b.assets
    ini.remove_prefix("MainButton")
    s = Screen(b, "Main")
    s.header()

    s.text(M + 20, 106, "MENÚ PRINCIPAL", size=13, color="Text3", style=BOLD)
    items = [
        ("MainButtonSolo", "SING_SING", "01"),
        ("MainButtonMulti", "SING_MULTI", "02"),
        ("MainButtonJukebox", "SING_JUKEBOX", "03"),
        ("MainButtonStats", "SING_STATS", "04"),
        ("MainButtonEditor", "SING_EDITOR", "05"),
        ("MainButtonOptions", "SING_GAME_OPTIONS", "06"),
    ]
    y = 134
    row_w, row_h = 460, 56
    tex = a.panel(row_w, row_h, 14)
    for name, label, numtxt in items:
        ini.set(name, od(X=M, Y=y, W=row_w, H=row_h, Tex=tex, Type="Transparent",
                         Color="Surface2", DColor="Bg", Texts=2, Reflection=0, SelectScale=1.02, TextDX=6))
        ini.set(name + "Text1", text_section(label, 62, 12, 28, "Text", "Text2", FONT_DISPLAY, REGULAR))
        ini.set(name + "Text2", text_section(numtxt, 20, 20, 15, "AccentText", "Text3", FONT_MONO))
        y += row_h + 4
    s.panel(M + 20, y + 8, row_w - 40, 1, r=0, color="Divider")
    y += 20
    small = a.panel(row_w, 44, 12)
    for name, label in (("MainButtonAbout", "Acerca de"), ("MainButtonExit", "SING_EXIT")):
        ini.set(name, od(X=M, Y=y, W=row_w, H=44, Tex=small, Type="Transparent",
                         Color="Surface2", DColor="Bg", Texts=1, Reflection=0, TextDX=6))
        ini.set(name + "Text1", text_section(label, 62, 11, 18, "Text", "Text3", FONT_INTER))
        y += 48

    # right: what the selected entry does
    px, py, pw, ph = 548, 100, W - M - 548, 532
    s.panel(px, py, pw, ph, r=24, color="Surface")
    ini.set("MainTextDescription", text_section("", px + 44, py + 64, 72, "Text", font=FONT_DISPLAY, style=BOLD))
    ini.set("MainTextDescriptionLong", text_section("", px + 44, py + 160, 20, "Text2", w=440))
    # picture of the selected entry (the game shows one group at a time and
    # lets its pieces slide in)
    main_previews(b, px + 44, py + 290, pw - 88, 200)

    s.footer([("ButtonNavi", "Navegar"), ("ButtonEnter", "Seleccionar"), ("ButtonC", "Créditos")])


def main_previews(b, sx, sy, sw, sh):
    """One small flat illustration per main menu entry: MainPreviewNStaticM."""
    ini, a = b.ini, b.assets
    ini.remove_prefix("MainPreview")
    groups = []

    def g():
        groups.append([])
        return groups[-1]

    # idle motion of a piece while its entry is selected (see TThemeStatic
    # Idle*): keys without the "Idle" prefix, e.g. dict(DY=3, Period=2400)
    def idle_keys(sec, idle):
        for k, v in (idle or {}).items():
            sec["Idle" + k] = str(v)

    def panel(grp, x, y, w, h, r, color, outline=0, alpha=1, idle=None):
        tex = a.panel(w, h, r, outline=outline) if outline else a.panel(w, h, r)
        sec = od(X=sx + x, Y=sy + y, W=w, H=h, Tex=tex, Color=color, Type="Transparent")
        if alpha != 1:
            sec["Alpha"] = alpha
        idle_keys(sec, idle)
        grp.append(sec)

    def icon(grp, x, y, size, key, color, idle=None):
        sec = od(X=sx + x, Y=sy + y, W=size, H=size, Tex=a.icon(key, size=size), Color=color,
                 Type="Transparent")
        idle_keys(sec, idle)
        grp.append(sec)

    # 1 sing: stave, sung notes, the pitch marker
    st = g()
    for i in range(4):
        panel(st, 0, 30 + i * 40, sw, 1, 0, "Divider")
    # the notes are empty tracks that fill with colour as the pitch line
    # passes over them (a sweep, IdleWave 2); then they fade and it repeats
    notes = [(0, 103, 84, "NoteBlue"), (96, 83, 52, "NoteBlue"), (160, 63, 112, "NoteBlue"), (284, 43, 66, "Gold"),
             (362, 63, 44, "NoteBlue"), (418, 103, 100, "NoteBlue"), (530, 123, 56, "NoteBlue")]
    run, span, period = 0.86, sw + 16, 5600
    for x, y_, w, col in notes:
        panel(st, x, y_, w, 14, 7, col, alpha=0.22)
    for x, y_, w, col in notes:
        # W 1 (0 would mean the texture's own size), grows to the note's width
        sec = od(X=sx + x, Y=sy + y_, W=1, H=14, Tex=a.panel(w, 14, 7), Color=col, Type="Transparent")
        idle_keys(sec, dict(DW=w - 1, Wave=2, Period=period, Start=round(run * (x + 8) / span, 4),
                            Dur=round(run * w / span, 4), Fade=0.9, Crop=1))
        st.append(sec)
    panel(st, -9, 36, 2, 120, 0, "Accent", idle=dict(DX=span, Wave=2, Period=period, Dur=run, Fade=0.94))
    panel(st, -14, 30, 12, 12, 6, "Accent", idle=dict(DX=span, Wave=2, Period=period, Dur=run, Fade=0.94))

    # 2 party: three teams on a podium
    pt = g()
    base = 176
    for i, (x, hgt, col) in enumerate(((150, 96, "NoteBlue"), (250, 140, "Accent"), (350, 70, "NoteMint"))):
        panel(pt, x, base - hgt, 84, hgt, 14, col, alpha=0.9)
        # the heads bounce, each in its own time
        panel(pt, x + 22, base - hgt - 52, 40, 40, 20, col, idle=dict(DY=-7, Period=1500, Phase=i * 0.3))
    icon(pt, 272, base - 140 + 18, 40, "star", "OnAccent", idle=dict(Rot=14, Scale=0.08, Period=2600))
    panel(pt, 110, base, 364, 2, 1, "Line2")

    # 3 jukebox: a playlist with the song that plays
    jb = g()
    for i in range(3):
        y_ = 20 + i * 52
        cur = i == 1
        panel(jb, 0, y_, sw, 44, 12, "Surface3" if cur else "Surface2")
        icon(jb, 14, y_ + 10, 24, "play" if cur else "note", "Accent" if cur else "Text3",
             idle=dict(Scale=0.14, Period=1200) if cur else None)
        panel(jb, 52, y_ + 14, 180 - i * 30, 8, 4, "Text2" if cur else "Line2")
        panel(jb, 52, y_ + 26, 110, 6, 3, "Line2")
    panel(jb, 0, 186, sw, 4, 2, "Line")
    # the song plays on
    panel(jb, 0, 186, int(sw * 0.42), 4, 2, "Accent", idle=dict(DW=int(sw * 0.3), Wave=1, Period=7000))

    # 4 statistics: a bar chart
    sg = g()
    hs = [60, 96, 72, 130, 110, 150, 88, 120]
    bw = 44
    gap = (sw - len(hs) * bw) // (len(hs) - 1)
    for i, hh in enumerate(hs):
        # the bars rise and fall a little, like a live meter
        panel(sg, i * (bw + gap), 176 - hh, bw, hh, 10, "Accent" if i == 5 else "Line2",
              idle=dict(DH=round(hh * 0.12), Period=2200, Phase=round(i * 0.17, 2)))
    panel(sg, 0, 178, sw, 2, 1, "Line")

    # 5 editor: piano roll with notes and the cursor
    ed = g()
    for i in range(6):
        panel(ed, 0, 10 + i * 32, sw, 1, 0, "Divider")
    for i in range(9):
        panel(ed, i * (sw // 8), 10, 1, 160, 0, "Divider")
    for x, y_, w, col in [(20, 116, 90, "NoteViolet"), (130, 84, 60, "NoteViolet"), (200, 52, 130, "Gold"),
                          (350, 84, 80, "NoteViolet"), (450, 116, 110, "NoteViolet")]:
        # the golden note is being stretched
        panel(ed, x, y_, w, 22, 8, col, idle=dict(DW=24, Wave=1, Period=2800) if col == "Gold" else None)
    # the cursor scrubs along the roll
    panel(ed, 340, 0, 2, 182, 0, "Accent", idle=dict(DX=-120, Wave=1, Period=4200))
    panel(ed, 332, 0, 18, 10, 3, "Accent", idle=dict(DX=-120, Wave=1, Period=4200))

    # 6 options: sliders and a switch
    op = g()
    for i, v in enumerate((0.7, 0.35, 0.55)):
        y_ = 30 + i * 52
        panel(op, 0, y_ - 4, 120, 10, 5, "Line2")
        panel(op, 160, y_, sw - 260, 4, 2, "Line")
        # each slider is being adjusted (knob and fill move together)
        mv = dict(Period=3000 + i * 500, Phase=round(i * 0.3, 2))
        panel(op, 160, y_, int((sw - 260) * v), 4, 2, "Accent", idle=dict(mv, DW=28))
        panel(op, 160 + int((sw - 260) * v) - 9, y_ - 7, 18, 18, 9, "Text", idle=dict(mv, DX=28))
    panel(op, sw - 64, 21, 64, 32, 16, "Accent")
    panel(op, sw - 34, 25, 24, 24, 12, "OnAccent", idle=dict(Scale=0.1, Period=1800))

    # 7 about: three voices that meet
    ab = g()
    for i, (x, col) in enumerate(((200, "NoteBlue"), (262, "Gold"), (324, "NoteMint"))):
        # the voices come together and part again
        panel(ab, x, 30, 120, 120, 60, col, alpha=0.75, idle=dict(DX=(1 - i) * 10, Period=3200))
    icon(ab, 296, 66, 48, "note", "OnAccent", idle=dict(Rot=10, DY=-4, Period=2400))

    # 8 exit: goodbye
    ex = g()
    panel(ex, sw // 2 - 70, 20, 140, 140, 70, "Surface3")
    icon(ex, sw // 2 - 32, 58, 64, "back", "Text2", idle=dict(DX=-10, Period=1600))

    for i, grp in enumerate(groups):
        for j, sec in enumerate(grp):
            ini.set("MainPreview%dStatic%d" % (i + 1, j + 1), sec)


# ---------------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------------
def players(b):
    """One card per player (drawn by the game, see [NameCards]): colour with
    the initial, name, microphone, colour and difficulty."""
    ini, a = b.ini, b.assets
    s = Screen(b, "Name")
    s.header(["¡Canta!", "Jugadores"])
    s.text(M, 96, "¿Quién canta?", size=48, font=FONT_DISPLAY, style=BOLD)
    s.text(M, 154, "Elige a cada jugador con ← →, escribe su nombre y su dificultad.", size=17, color="Text2")

    # number of players (top right, in the header)
    ini.set("NameSelectPlayerCount", od(
        X=W - M - 288, Y=96, W=160, H=44, SkipX=8, SBGW=120, Text="NAME_PLAYERS_COUNT", TextSize=16,
        Tex=a.panel(160, 44, 12), Type="Transparent", TexSBG=a.panel(120, 44, 12), TypeSBG="Transparent",
        Color="Surface2", DColor="Bg", TColor="Text", TDColor="Text2",
        SBGColor="Accent", SBGDColor="Surface2", STColor="OnAccent", STUColor="Text", STDColor="Text",
        ArrowW=24, ArrowH=24))

    # the cards
    cx, cy, cw_all, ch_all, cols, gap = M, 206, W - 2 * M, 384, 3, 20
    cw = (cw_all - gap * (cols - 1)) // cols
    chh = 270
    ini.set("NameCards", od(Enabled=1, X=cx, Y=cy, W=cw_all, H=ch_all, Cols=cols, Gap=gap, MaxH=chh,
                            CardTex=a.panel(cw, chh, 22), RingTex=a.panel(cw + 6, chh + 6, 25, outline=2),
                            CircleTex=a.circle(56), SegTex=a.panel(108, 36, 10), TrackTex=a.panel(cw - 40, 44, 12),
                            Font=FONT_INTER, TitleFont=FONT_DISPLAY))
    # old row of players: not shown
    for i in range(6):
        ini.set("NamePlayerSelectStatic%d" % (i + 1), od(X=-200, Y=-200, W=0, H=0, Tex=a.transparent(),
                                                          Type="Transparent"))
        ini.set("NamePlayerSelectStatic%dText" % (i + 1), od(X=-400, Y=-400, Size=1, Color="Text"))
        ini.set("NamePlayerSelectStatic%dAvatar" % (i + 1), od(X=-200, Y=-200, W=0, H=0))
    ini.set("NamePlayerSelectCurrent", od(X=-4000, Y=0, W=10, H=10, Tex=a.transparent(), DTex=a.transparent(),
                                          Type="Transparent", Color="Accent", DColor="Accent"))
    ini.set("NamePlayerButtonAvatar", od(X=0, Y=0, W=0, H=0, Tex=a.transparent(), Type="Transparent"))
    ini.set("NamePlayerAvatar", od(X=0, Y=0, W=0, H=0, Reflection=0))
    ini.set("NamePlayerScrollAvatar", od(Count=3, Distance=24, Reflection=0, Show=0))

    # name field of the edited card (the game places it): a line under the name
    nw = cw - 112
    from PIL import Image, ImageDraw
    line = Image.new("RGBA", (nw * 2, 44 * 2), (255, 255, 255, 0))
    ImageDraw.Draw(line).rectangle((0, 44 * 2 - 4, nw * 2, 44 * 2), fill=(255, 255, 255, 255))
    lname = a.save_custom("K_nameline_%d" % nw, line)
    ini.set("NamePlayerButtonName", od(X=0, Y=0, W=nw, H=44, Z=1, Tex=lname, Color="P1Dark", DColor="P1Light",
                                       Type="Transparent", Texts=1))
    ini.set("NamePlayerButtonNameText1", text_section("", 8, 10, 24, "Text", font=FONT_DISPLAY))
    lw_ = 92
    slide = od(TexSBG=a.panel(cw - 40 - lw_ - 8, 40, 12), TypeSBG="Transparent",
               Tex=a.panel(lw_, 40, 12), Type="Transparent",
               X=0, W=lw_, H=40, SkipX=8, SBGW=cw - 40 - lw_ - 8, TextSize=15, ArrowW=24, ArrowH=24,
               Color="Surface3", DColor="Surface2", TColor="Text", TDColor="Text3",
               SBGDColor="PlayerDark", SBGColor="PlayerLight", STColor="OnAccent", STDColor="OnAccent", Z=1)
    ini.set("NameSelectPlayerColor", OrderedDict(slide, Y="0", Text="Color"))
    ini.set("NameSelectPlayerLevel", OrderedDict(slide, X="-4000", Y="0", Text="PARTY_DIFFICULTY"))

    s.footer([("ButtonNavi", "Navegar"), ("ButtonAZ", "Escribir nombre"), ("ButtonEnter", "Elegir canción"),
              ("ButtonEsc", "Atrás")])


# ---------------------------------------------------------------------------
# Song selection: roulette, chessboard (grid) and list
# ---------------------------------------------------------------------------
CHIPS = (("VideoIcon", "video", "Vídeo"), ("MedleyIcon", "medley", "Versión corta"),
         ("CalculatedMedleyIcon", "medley", "Versión corta"), ("DuetIcon", "duet", "Dueto"),
         ("RapIcon", "rap", "Rap"), ("RapToFreestyleIcon", "rap", "Freestyle"))


def song_details(b, P, x, y, w, align, title=34, prefix="Text", icons=""):
    """Title (up to two lines, then cut), artist, year, the song's features
    as chips (the game lines up the shown ones) and the duet parts. Returns
    the y below the block (for one-line titles)."""
    ini, a = b.ini, b.assets
    cx = x + w // 2 if align == 1 else x
    lh = title + 4
    # at most two lines: below MinSize three lines would fit in H
    ini.set(P + prefix + "Title", od(X=cx, Y=y, W=w, H=2 * title + 4, MinSize=(2 * title + 4) // 3 + 1, Color="Text",
                                     Font=FONT_DISPLAY, Style=BOLD, Size=title, Align=align, Text=""))
    y += lh + 6
    ini.set(P + prefix + "Artist", od(X=cx, Y=y, W=w, H=24, MinSize=14, Color="Text2", Font=FONT_INTER,
                                      Style=REGULAR, Size=18, Align=align, Text=""))
    y += 28
    ini.set(P + prefix + "Year", od(X=cx, Y=y, Color="Text3", Font=FONT_MONO, Style=REGULAR, Size=14,
                                    Align=align, Text=""))
    y += 22
    ini.set(P + "TextInfo", od(X=cx, Y=y, W=w, H=20, MinSize=12, Color="Text3", Font=FONT_INTER, Style=REGULAR,
                               Size=15, Align=align, Text=""))
    y += 32
    for name, key, label in CHIPS:
        cn, cw = a.chip(key, label)
        ini.set(P + icons + name, od(X=cx, Y=y, W=cw, H=28, Z=0.95, Color="Text2", Tex=cn, Type="Transparent"))
    ini.set(P + "Icons", od(Flow=2 if align == 1 else 1, Gap=8))
    y += 40
    # duet: the part each one sings (one player: the first one is yours,
    # Space swaps them)
    dx = cx - 110 if align == 1 else cx
    for i, (dot, off) in enumerate(((a.circle(12), 0), (a.panel(12, 12, 6, outline=2), 130))):
        st = P + "Static2PlayersDuetSingerP%d" % (i + 1)
        ini.set(st, od(X=dx + off, Y=y + 6, W=12, H=12, Z=0.95, Tex=dot, Color="P%dDark" % (i + 1),
                       Type="Transparent"))
        ini.set(P + "Text2PlayersDuetSingerP%d" % (i + 1), od(X=dx + off + 20, Y=y + 1, Z=0.95, Text="",
                                                               Size=16, Color="Text", Font=FONT_INTER,
                                                               Style=REGULAR, Align=0))
    return y + 30


def song_common(b, mode, score_x, score_y):
    """Pieces shared by the three song menus."""
    ini, a = b.ini, b.assets
    P = "Song" + mode
    s = Screen(b, P)
    s.header(["Elige la canción"])
    # covers cut to a square with rounded corners (radius in 1/1000 of the side)
    ini.set(P + "CoverShape", od(Square=1, Radius=57))
    # search hint (the search opens with J)
    sx = W - M - 300
    s.panel(sx, 18, 300, 40, r=20, color="Surface")
    s.icon(sx + 16, 30, 16, "search", color="Text3")
    s.text(sx + 42, 29, "Buscar canción o artista", size=15, color="Text3")
    kn, kw = a.keycap("J")
    s.static(sx + 300 - 14 - kw, 26, kw, 24, kn, color="Text2")

    # category / where am I (tabs mode)
    ini.set(P + "TextCat", text_section("", M, 84, 15, "Text2"))
    ini.set(P + "StaticCat", od(X=0, Y=0, W=1, H=1, Tex=a.transparent(), Color="Bg", Type="Transparent"))

    # info message ("no songs in this category" ...)
    ini.set(P + "InfoMessageBG", od(X=W // 2 - 220, Y=84, W=440, H=36, Z=0.98, Tex=a.pill(440, 36),
                                     Color="Surface3", Type="Transparent"))
    ini.set(P + "InfoMessageText", text_section("", W // 2, 92, 17, "Text", align=1))

    # scores of the selected song: label | web | local
    lab = od(Color="Text3", Font=FONT_INTER, Style=REGULAR, Size=15, Align=0)
    ini.set(P + "TextScore", od(X=score_x, Y=score_y, Color="Text3", Font=FONT_INTER, Style=BOLD, Size=13, Align=0))
    ini.set(P + "TextMaxScore", OrderedDict(lab, X=str(score_x), Y=str(score_y + 26), Text="SONG_SCORE_MAX"))
    ini.set(P + "TextMediaScore", OrderedDict(lab, X=str(score_x), Y=str(score_y + 54), Text="SONG_SCORE_MEDIA"))
    val = od(Color="Text", Font=FONT_MONO, Style=REGULAR, Size=16, Align=2)
    ini.set(P + "TextMaxScore2", OrderedDict(val, X=str(score_x + 150), Y=str(score_y + 25)))
    ini.set(P + "TextMediaScore2", OrderedDict(val, X=str(score_x + 150), Y=str(score_y + 53)))
    ini.set(P + "TextScoreUser", od(X=score_x + 150, Y=score_y + 80, Color="Text3", Font=FONT_INTER, Size=13, Align=2))
    ini.set(P + "TextMaxScoreLocal", OrderedDict(val, X=str(score_x + 232), Y=str(score_y + 25)))
    ini.set(P + "TextMediaScoreLocal", OrderedDict(val, X=str(score_x + 232), Y=str(score_y + 53)))
    ini.set(P + "TextScoreUserLocal", od(X=score_x + 232, Y=score_y + 80, Color="Text3", Font=FONT_INTER, Size=13, Align=2))

    # preview visualiser: off (flat)
    eq = ini.get(P + "Equalizer")
    if eq is not None:
        eq["Visible"] = "0"

    s.panel(0, FOOT_Y, W, 1, r=0, color="Divider")
    sp, spw = a.keycap("Espacio")
    b.key_w[sp] = spw
    s.footer([("ButtonNavi", "Navegar"), ("ButtonEnter", "Cantar"), (sp, "Parte del dueto"),
              ("ButtonM", "Menú"), ("ButtonJ", "Buscar"), ("ButtonP", "Listas")],
             divider=False, group="NonParty")
    return s


def song_roulette(b):
    ini, a = b.ini, b.assets
    s = song_common(b, "Roulette", score_x=W - M - 232, score_y=440)
    cw = 300
    cx, cy = W // 2 - cw // 2, 104
    ini.set("SongRouletteCover", od(X=cx, Y=cy, W=cw, H=cw, Reflections=0))
    # ring around the cover in front
    # concentric with the cover's rounded corners (CoverShape: 17 px of 300)
    s.static(cx - 8, cy - 8, cw + 16, cw + 16, a.panel(cw + 16, cw + 16, 25, outline=3), color="Accent", z=0.96)
    song_details(b, "SongRoulette", W // 2 - 340, 424, 680, align=1, title=34)
    ini.set("SongRouletteTextNumber", od(X=M, Y=620, Z=0.95, Color="Text3", Font=FONT_MONO, Size=14, Align=0))


def song_chessboard(b):
    """Grid of covers (5 x 4) on the left; on the right a wide card with the
    selected song: big cover and the details next to it, its features and
    duet parts below, the scores at the bottom."""
    ini, a = b.ini, b.assets
    cols, rows, cell, pad = 5, 4, 118, 14
    gx, gy = M + 8, 104
    px = gx + cols * cell + (cols - 1) * pad + 28
    py, pw, ph = 96, W - M - px, 540
    s = song_common(b, "Chessboard", score_x=px + 28, score_y=py + ph - 112)
    s.panel(px, py, pw, ph, r=24, color="Surface")
    big = 232
    ini.set("SongChessboardCover", od(X=gx, Y=gy, W=cell, H=cell, Rows=rows, Cols=cols, Padding=pad,
                                      SelectX=px + 28, SelectY=py + 28, SelectW=big, SelectH=big,
                                      SelectReflection=0, ZoomThumbW=cell + 22, ZoomThumbH=cell + 22, Reflections=0))
    # details next to the cover
    tx = px + 28 + big + 24
    tw = px + pw - 28 - tx
    song_details(b, "SongChessboard", tx, py + 40, tw, align=0, title=26)
    # features and duet parts below the cover (the whole width)
    cy = py + 28 + big + 22
    for name, key, label in CHIPS:
        sec = ini.get("SongChessboard" + name)
        sec["X"] = str(px + 28)
        sec["Y"] = str(cy)
    for i in (1, 2):
        st = ini.get("SongChessboardStatic2PlayersDuetSingerP%d" % i)
        tx_ = ini.get("SongChessboardText2PlayersDuetSingerP%d" % i)
        off = 0 if i == 1 else 150
        st["X"], st["Y"] = str(px + 28 + off), str(cy + 50)
        tx_["X"], tx_["Y"] = str(px + 48 + off), str(cy + 45)
    # scores at the bottom of the card (shown when the song has some)
    s.panel(px + 28, py + ph - 136, pw - 56, 1, r=0, color="Divider")
    ini.set("SongChessboardTextNumber", od(X=px + pw - 28, Y=py + ph - 40, Z=0.97, Color="Text3", Font=FONT_MONO,
                                           Size=14, Align=2))


def song_list(b):
    ini, a = b.ini, b.assets
    rows, rh, gap = 8, 60, 4
    lx, ly, lw = M, 100, 560
    px, py, pw, ph = lx + lw + 24, 96, W - M - (lx + lw + 24), 540
    s = song_common(b, "List", score_x=px + pw - 28 - 232, score_y=py + ph - 130)
    s.panel(px, py, pw, ph, r=22, color="Surface")
    ini.set("SongListSelectSong", od(X=lx, Y=ly, W=lw, H=rh, Z=0.5, Rows=rows, Padding=gap,
                                     Tex=a.panel(lw, rh, 14), DTex=a.transparent(), Type="Transparent",
                                     Color="Surface2", DColor="Bg", Reflection=0))
    cv = 44
    big = 280
    ini.set("SongListCover", od(X=lx + 10, Y=ly + (rh - cv) // 2, W=cv, H=cv, Padding=rh + gap - cv,
                                SelectX=px + 28, SelectY=py + 28, SelectW=big, SelectH=big, SelectReflection=0,
                                Reflections=0))
    # rows of the list
    ini.set("SongListTextTitle", od(X=lx + 70, Y=ly + 10, W=380, H=24, MinSize=15, Color="Text", Font=FONT_INTER,
                                    Style=BOLD, Size=18, Align=0, Text=""))
    ini.set("SongListTextArtist", od(X=lx + 70, Y=ly + 33, W=380, H=20, MinSize=13, Color="Text3", Font=FONT_INTER,
                                     Style=REGULAR, Size=15, Align=0, Text=""))
    ini.set("SongListTextYear", od(X=lx + lw - 16, Y=ly + 20, Color="Text3", Font=FONT_MONO, Size=14, Align=2,
                                   Text=""))
    for name, key, x in (("VideoIcon", "video", lw - 104), ("MedleyIcon", "medley", lw - 80),
                         ("CalculatedMedleyIcon", "medley", lw - 80), ("DuetIcon", "duet", lw - 80),
                         ("RapIcon", "rap", lw - 80), ("RapToFreestyleIcon", "rap", lw - 80)):
        ini.set("SongList" + name, od(X=lx + x, Y=ly + 20, W=20, H=20, Z=0.95, Color="Text3",
                                      Tex=a.icon(key), Type="Transparent"))
    # details of the selected song: next to the big cover, features below it
    tx = px + 28 + big + 24
    tw = px + pw - 28 - tx
    song_details(b, "SongList", tx, py + 32, tw, align=0, title=26, prefix="Detail", icons="Detail")
    # the chips and the duet parts go below the cover (wider)
    cy = py + 28 + big + 22
    for name, key, label in CHIPS:
        sec = ini.get("SongListDetail" + name)
        sec["X"] = str(px + 28)
        sec["Y"] = str(cy)
    for i in (1, 2):
        st = ini.get("SongListStatic2PlayersDuetSingerP%d" % i)
        tx_ = ini.get("SongListText2PlayersDuetSingerP%d" % i)
        off = 0 if i == 1 else 150
        st["X"], st["Y"] = str(px + 28 + off), str(cy + 50)
        tx_["X"], tx_["Y"] = str(px + 48 + off), str(cy + 45)
    ini.set("SongListTextNumber", od(X=px + 28, Y=py + ph - 40, Z=0.95, Color="Text3", Font=FONT_MONO,
                                     Size=14, Align=0))


# ---------------------------------------------------------------------------
# Singing
# ---------------------------------------------------------------------------
LS = 16                    # line spacing (pitch step = LS / 2)
LANE_X, LANE_W, LANE_H = 32, W - 64, 9 * LS + 20
PILL_H = 40                # height of each player's row above its staff (8 px of air under the content)
LANES = (92, 408)          # top of the lane of player 1 and player 2
LYRICS_Y, LYRICS_H = 596, 104


def sing(b):
    ini, a = b.ini, b.assets
    s = Screen(b, "Sing")
    ini.set("SingBackground", od(Type="Texture", Tex="K_bg"))

    # note lanes: a light veil (the code draws it only under lanes in use);
    # every note carries its own dark + light ring (see assets.notes)
    lines_top = [t + 10 for t in LANES]
    base = [lt + 7 * LS for lt in lines_top]
    # three rows (3 players, or 6 in two columns): the same row as with two
    # players (name row + staff) with a smaller staff
    LS3 = 12
    ROW3_Y0, ROW3_PITCH = 60, 170
    lane3 = [ROW3_Y0 + k * ROW3_PITCH + PILL_H for k in range(3)]
    base3 = [t + 10 + 7 * LS3 for t in lane3]
    ini.set("SingNoteArea", od(
        Left=LANE_X + 24, Right=LANE_X + LANE_W - 24, LineSpacing=LS, LineSpacing3=LS3,
        Top3Rows1=base3[0], Top3Rows2=base3[1], Top3Rows3=base3[2], LanePad3=24, Guide3Offset=7 * LS3, Duet3Lyrics=1,
        Top1Row=base[1], Top2Rows1=base[0], Top2Rows2=base[1],
        Left3=LANE_X + 24, Right3=LANE_X + LANE_W - 24, NoteScale=1.4, NoteCapScale=2, MissScale=0.8,
        LineColor="ScrimText", LineAlpha=0.18,
        LaneTex=a.panel(LANE_W, LANE_H, 20), LaneLeft=LANE_X, LaneRight=LANE_X + LANE_W,
        LanePadTop=10, LanePadBottom=LANE_H - 9 * LS - 10, LaneColor="Scrim", LaneAlpha=0,
        HudW=0, HudAlpha=0, NameBoxPad=14, NameBoxFixed=1))

    # each player's row just above its staff, without any panel: the
    # oscilloscope at the left end; at the right end, from the right, the name
    # in a pill of the player's colour (fixed size; the game picks a dark or
    # light text, NameBoxFixed), the score with the sing bar under it, and
    # the line bonus badge. The score and the bar have a soft shadow (Shadow)
    # so they read over any video. ScoreBG is empty (W = 0).
    ini.set("SingDefaultScoreBG", od(Tex="ScoreBG", W=0, H=PILL_H, Type="Colorized"))
    # line bonus: a badge that pops up left of the score
    ini.set("SingLineBonus", od(W=150, H=28, Y=2, Size=16, Font=FONT_INTER, Style=1))

    GAP = 8
    PILL_W, SCORE_W = 112, 50
    L0 = LANE_X + 24                         # left end of a full width row: the oscilloscope
    RN0 = LANE_X + LANE_W - 24               # right end of the row (the pill ends here)
    MID = (L0 + RN0) // 2

    def player(prefix, lane_top, color, L=L0, RN=RN0):
        PX = RN - PILL_W                     # pill
        SX = PX - GAP - SCORE_W              # score and bar
        top = lane_top - PILL_H
        ini.set("Sing%sStatic" % prefix, od(X=PX, Y=top + 2, W=PILL_W, H=28, Tex=a.pill(PILL_W, 28),
                                            Color=color, Type="Transparent", Alpha=1))
        ini.set("Sing%sAvatar" % prefix, od(X=PX, Y=top + 2, W=0, H=0, Z=1, Alpha=0))
        ini.set("Sing%sText" % prefix, od(X=PX + PILL_W // 2, Y=top + 6, W=PILL_W - 20, H=20, MinSize=12,
                                          Text="PLAYERNAME", Font=FONT_INTER, Style=BOLD, Size=17,
                                          Color="ScrimText", Align=1))
        # X/Y place the line bonus badge (centred on X, see SingLineBonus)
        ini.set("Sing%sStatic2" % prefix, od(X=SX - GAP - 75, Y=top, W=0, H=PILL_H))
        ini.set("Sing%sTextScore" % prefix, od(Text="00000", X=SX, Y=top + 5, Font=FONT_MONO, Style=BOLD,
                                               Size=22, Color="ScrimText", Align=0, Shadow=3))
        ini.set("Sing%sSingBar" % prefix, od(X=SX, Y=top + 29, W=SCORE_W, H=4))
        ini.set("Sing%sOscilloscope" % prefix, od(X=L, Y=top + 4, W=120 if RN - L > 700 else 96, H=24))

    player("P1", LANES[1], "P1Dark")          # one player: lower lane, next to the lyrics
    player("P1TwoP", LANES[0], "P1Dark")
    player("P2R", LANES[1], "P2Dark")

    # 3 players: three full width rows. 4: two columns of two rows (the
    # staffs of the two players). 6: two columns of three rows. The engine
    # places the notes the same way (UDraw), so the order is: left column
    # from top to bottom, then the right one.
    LEFT = dict(L=L0, RN=MID - 24)           # column cells: a gap in the middle
    RIGHT = dict(L=MID + 10, RN=RN0)
    for n, (pre, duet) in enumerate((("P1ThreeP", "DuetP1ThreeP"), ("P2M", "DuetP2M"), ("P3R", "DuetP3R"))):
        player(pre, lane3[n], "P%dDark" % (n + 1))
        player(duet, lane3[n], "P%dDark" % (n + 1))
    for n, (pre, duet) in enumerate((("P1FourP", "P1DuetFourP"), ("P2FourP", "P2DuetFourP"),
                                     ("P3FourP", "P3DuetFourP"), ("P4FourP", "P4DuetFourP"))):
        player(pre, LANES[n % 2], "P%dDark" % (n + 1), **(LEFT if n < 2 else RIGHT))
        player(duet, LANES[n % 2], "P%dDark" % (n + 1), **(LEFT if n < 2 else RIGHT))
    # the game reads the bar of the 3rd player of 3 as SingP3SingBar (not P3R)
    ini.set("SingP3SingBar", od(X=RN0 - 170, Y=lane3[2] - PILL_H + 29, W=SCORE_W, H=4))
    for n in range(6):
        for pre in ("P%dSixP" % (n + 1), "P%dDuetSixP" % (n + 1)):
            player(pre, lane3[n % 3], "P%dDark" % (n + 1), **(LEFT if n < 3 else RIGHT))

    # no avatar pictures in any layout
    for name in list(ini.sections):
        if re.match(r"^Sing\w*Avatar$", name):
            ini.set(name, od(X=0, Y=0, W=0, H=0, Z=1, Alpha=0))

    # 3 or more players (no lanes): score and name with a soft shadow
    own = ["P1", "P1TwoP", "P2R", "P1ThreeP", "P2M", "P3R", "DuetP1ThreeP", "DuetP2M", "DuetP3R"]
    own += ["P%d%sP" % (n, k) for n in range(1, 7) for k in ("Four", "Six", "DuetFour", "DuetSix")]
    own += ["P%dDuet%sP" % (n, k) for n in range(1, 7) for k in ("Four", "Six")]
    for name in list(ini.sections):
        m = re.match(r"^Sing(\w+)Static2$", name)
        if not m or m.group(1) in own or m.group(1) == "Default":
            continue
        pre = m.group(1)
        sc = resolved(ini, "Sing%sTextScore" % pre)
        bar = resolved(ini, "Sing%sSingBar" % pre)
        if not sc or not bar:
            continue
        sx, sy = int(sc["X"]), int(sc["Y"])
        bx, by, bw_, bh_ = (int(bar[k]) for k in ("X", "Y", "W", "H"))
        x0, y0 = min(sx, bx) - 12, sy - 8
        x1, y1 = max(sx + 110, bx + bw_) + 12, by + bh_ + 10
        # no card: the texts carry a soft shadow (the area still centres the
        # line bonus badge)
        ini.set(name, od(Tex=a.transparent(), Type="Transparent", X=x0, Y=y0, W=x1 - x0, H=y1 - y0))
        ini.set("Sing%sTextScore" % pre, od(Text="00000", X=sx, Y=sy, Font=FONT_MONO, Style=BOLD,
                                             Size=28, Color="ScrimText", Align=0, Shadow=3))
        nm = resolved(ini, "Sing%sText" % pre)
        if nm:
            nm.update(od(Font=FONT_INTER, Style=BOLD, Color="ScrimText", Shadow=3))
            nm["Size"] = str(min(int(nm.get("Size", 20)), 20))
            ini.set("Sing%sText" % pre, nm)

    # lyrics: a solid panel at the bottom; duets get a second one in the middle
    ly = LYRICS_Y
    ini.set("SingLyricsBar", od(Tex=a.panel(LANE_W, LYRICS_H, 22), X=LANE_X, Y=ly, W=LANE_W, H=LYRICS_H,
                                Color="Scrim", Type="Transparent"))
    ini.set("SingLyricsUpperBar", od(X=96, W=W - 192, Y=ly + 10, H=48, IndicatorYOffset=4))
    ini.set("SingLyricsLowerBar", od(X=96, W=W - 192, Y=ly + 62, H=34))
    for p_ in ("SingLyricsDuetP2UpperBar", "SingLyricsDuetP2LowerBar"):
        ini.set(p_, OrderedDict(ini.get(p_.replace("DuetP2", ""))))
    dy = LANES[0] + LANE_H + 4     # between the first lane and the second pill
    dh = LANES[1] - PILL_H - 4 - dy
    ini.set("SingLyricsBarDuet", od(Tex=a.panel(LANE_W, dh, 22), X=LANE_X, Y=dy, W=LANE_W, H=dh,
                                    Color="Scrim", Type="Transparent"))
    ini.set("SingLyricsDuetP1UpperBar", od(X=96, W=W - 192, Y=dy + 8, H=44, IndicatorYOffset=4))
    ini.set("SingLyricsDuetP1LowerBar", od(X=96, W=W - 192, Y=dy + 56, H=30))

    # progress of the song: thin line at the very top + time chip
    ini.set("SingTimeBar", od(Tex=a.rect(), X=0, Y=0, W=W, H=4, Color="Scrim", Type="Transparent", Alpha=0.7))
    ini.set("SingTimeProgress", od(X=0, Y=0, W=W, H=4, Color="Accent"))
    ini.set("SingTimeLabelText", od(Text="", X=0, Y=0, Size=1, Color="ScrimText"))
    s.static(W - LANE_X - 112, 18, 112, 34, a.pill(112, 34), color="Scrim", alpha=0.92)
    ini.set("SingTimeText", od(Text="", X=W - LANE_X - 56, Y=25, Font=FONT_MONO, Style=REGULAR, Size=15,
                               Color="ScrimText", Align=1))
    # song name (medley) and messages
    ini.set("SingSongNameStatic", od(Tex=a.pill(420, 34), X=LANE_X, Y=18, W=420, H=34, Color="Scrim",
                                     Type="Transparent", Alpha=0.92))
    ini.set("SingSongNameText", od(Text="SongNameText", X=LANE_X + 210, Y=25, Font=FONT_INTER, Style=BOLD,
                                   Size=15, Color="ScrimText", Align=1))
    ini.set("SingInfoMessageBG", od(Tex=a.pill(440, 34), X=W // 2 - 220, Y=18, W=440, H=34, Z=0.98,
                                    Color="Scrim", Type="Transparent"))
    ini.set("SingInfoMessageText", od(X=W // 2, Y=25, Color="ScrimText", Font=FONT_INTER, Style=BOLD, Size=15, Align=1))
    ini.set("PausePopUpStatic", od(Tex="Pause", X=0, Y=0, W=W, H=H, Z=0.95, Color="White", Type="Transparent"))


# ---------------------------------------------------------------------------
# Scores
# ---------------------------------------------------------------------------
def score(b):
    ini, a = b.ini, b.assets
    ini.remove_prefix("ScorePlayer", keep=())
    s = Screen(b, "Score")
    s.header(["Puntuaciones"])
    ini.set("ScoreBars", od(Instant=1))      # the bars and points appear at once
    ini.set("ScoreTextArtistTitle", text_section("ArtistTitle", W - M, 26, 16, "Text2", align=2))

    def card(n, cx, cy, cw, ch, pcol, pre="", compact=False):
        """One player's card. pre is "" (1-3 players), "FourP" or "SixP": the
        game loads its own set of sections for 4 and 6 players on one screen,
        laid out as a grid, hence the smaller (compact) card."""
        S = "Score" + pre
        bar_w = 56 if cw > 450 else 40
        if compact:
            bar_w = 32 if cw > 450 else 28
        bx = cx + cw - (20 if compact else 28) - bar_w
        lx = cx + (20 if compact else 28)    # left edge of the content
        inner = bx - 24 - lx                 # width of the left column
        big = cw > 450
        ini.set("%sPlayer%dStatic1" % (S, n), od(X=cx, Y=cy, W=cw, H=ch, Z=0.1, Tex=a.panel(cw, ch, 24),
                                                Color="Surface", Type="Transparent"))
        if compact:
            ini.set("%sPlayer%dStatic2" % (S, n), od(X=lx, Y=cy + 18, W=44, H=44, Z=0.9, Tex=a.circle(44),
                                                    Color=pcol, Type="Transparent"))
            ini.set("%sPlayer%dAvatar" % (S, n), od(X=lx + 4, Y=cy + 22, W=0, H=0, Z=1))
            ini.set("%sTextName%d" % (S, n), text_section("P%d" % n, lx + 58, cy + 24, 22, "Text", font=FONT_DISPLAY))
            ini.set("%sTextTotal%d" % (S, n), text_section("SING_TOTAL", lx, cy + 74, 13, "Text3"))
            ini.set("%sTextTotalScore%d" % (S, n), text_section("00000", lx, cy + 90, 38 if big else 34, "Text",
                                                               font=FONT_MONO))
            ini.set("%sStaticRatingPicture%d" % (S, n), od(X=lx, Y=cy + 138, W=inner, H=8, Z=0.85))
            ini.set("%sTextScore%d" % (S, n), od(X=lx, Y=cy + 150, W=inner, Color="Text", Font=FONT_DISPLAY,
                                                 Style=REGULAR, Size=18 if big else 16, Text="Tone Deaf", Align=0))
            row0, step, ls_, vs_ = cy + 182, 24, 15, 15
        else:
            ini.set("%sPlayer%dStatic2" % (S, n), od(X=cx + 28, Y=cy + 28, W=56, H=56, Z=0.9, Tex=a.circle(56),
                                                    Color=pcol, Type="Transparent"))
            ini.set("%sPlayer%dAvatar" % (S, n), od(X=cx + 32, Y=cy + 32, W=0, H=0, Z=1))
            ini.set("%sTextName%d" % (S, n), text_section("P%d" % n, cx + 100, cy + 38, 26, "Text", font=FONT_DISPLAY))
            ini.set("%sTextTotal%d" % (S, n), text_section("SING_TOTAL", cx + 28, cy + 112, 15, "Text3"))
            ini.set("%sTextTotalScore%d" % (S, n), text_section("00000", cx + 28, cy + 134, 72 if big else 54,
                                                               "Text", font=FONT_MONO))
            ini.set("%sStaticRatingPicture%d" % (S, n), od(X=cx + 28, Y=cy + 238, W=inner, H=12, Z=0.85))
            ini.set("%sTextScore%d" % (S, n), od(X=cx + 28, Y=cy + 260, W=inner, Color="Text", Font=FONT_DISPLAY,
                                                 Style=REGULAR, Size=26 if big else 22, Text="Tone Deaf", Align=0))
            row0, step, ls_, vs_ = cy + 330, 46, 17, 18
        rows = (("Notes", "SING_NOTES", "BoxDark", "ScoreBar_box_dark"),
                ("LineBonus", "SING_PHRASE_BONUS", "BoxLight", "ScoreBar_box_light"),
                ("GoldenNotes", "SING_GOLDEN_NOTES", "BoxLightest", "ScoreBar_box_lightest"))
        for i, (key, label, box, tex) in enumerate(rows):
            y = row0 + i * step
            ini.set("%sStatic%s%d" % (S, box, n), od(Tex=tex, X=lx, Y=y + (3 if compact else 4), W=12 if not compact else 10,
                                                    H=12 if not compact else 10, Color=pcol, Type="Colorized"))
            ini.set("%sText%s%d" % (S, key, n), text_section(label, lx + (22 if compact else 22), y, ls_, "Text2"))
            ini.set("%sText%sScore%d" % (S, key, n), text_section("0000", lx + inner, y - 1, vs_, "Text",
                                                                  font=FONT_MONO, align=2))
            if i < 2:
                ini.set("%sPlayer%dStatic%d" % (S, n, 3 + i), od(X=lx, Y=y + (step - 6 if compact else 32), W=inner,
                                                                 H=1, Z=0.5, Tex=a.rect(), Color="Divider",
                                                                 Type="Transparent"))
        # the animated bar: track + fill (re-hued with the player colour)
        top, bh = cy + (18 if compact else 28), ch - (36 if compact else 56)
        # the track is a plain static (the game does not draw BackLevel);
        # its Z puts it below the bars, which the game draws itself
        ini.set("%sPlayer%dStatic5" % (S, n), od(X=bx, Y=top, W=bar_w, H=bh, Z=0.2, Tex=a.panel(bar_w, bh, 12),
                                                Color="Surface3", Type="Transparent"))
        ini.set("%sStaticBackLevel%d" % (S, n), od(Tex=a.panel(bar_w, bh, 12), X=bx, Y=top, W=bar_w, H=bh,
                                                   Color="Surface3", Type="Transparent"))
        ini.set("%sStaticBackLevelRound%d" % (S, n), od(Tex=a.transparent(), X=bx, Y=top, W=bar_w, H=1,
                                                        Color="Surface3", Type="Transparent"))
        ini.set("%sStaticLevel%d" % (S, n), od(Tex="ScoreLevel", X=bx, Y=top + bh - 10, W=bar_w, H=10, Color=pcol,
                                               Type="Colorized"))
        ini.set("%sStaticLevelRound%d" % (S, n), od(Tex=a.transparent(), X=bx, Y=top + bh - 10, W=bar_w, H=1,
                                                    Color=pcol, Type="Transparent"))
        # send-score button (only with score websites)
        btn = ini.get("ScoreButtonSend%d" % n) if not pre else None
        if btn is not None:
            ini.set("ScoreButtonSend%d" % n, od(X=cx + 28, Y=cy + ch - 70, W=200, H=40, Tex=a.panel(200, 40, 12),
                                                Color="Accent", DColor="Surface3", Type="Transparent", Texts=1))
            ini.set("ScoreButtonSend%dText1" % n, text_section("SCORE_SEND", 100, 10, 16, "OnAccent", "Text",
                                                               align=1))

    cy, ch = 100, 532
    card(1, 340, cy, 600, ch, "P1Dark")                       # 1 player
    card(2, M, cy, 580, ch, "P1Dark")                         # 2 players
    card(3, W - M - 580, cy, 580, ch, "P2Dark")
    cw3 = (W - 2 * M - 2 * 20) // 3                           # 3 players
    for i in range(3):
        card(4 + i, M + i * (cw3 + 20), cy, cw3, ch, "P%dDark" % (i + 1))

    # 4 and 6 players on one screen: the game loads other sections for them
    # (ScoreFourP*, ScoreSixP*), as a 2 x 2 and a 3 x 2 grid of smaller cards
    ini.remove_prefix("ScoreFourP", keep=())
    ini.remove_prefix("ScoreSixP", keep=())
    gap, gh = 20, 256
    cw4 = (W - 2 * M - gap) // 2
    for n in range(4):                       # P1 P2 on the top row, P3 P4 below
        card(n + 1, M + (n % 2) * (cw4 + gap), cy + (n // 2) * (gh + gap), cw4, gh, "P%dDark" % (n + 1),
             pre="FourP", compact=True)
    for n in range(6):                       # P1 P2 P3 on the top row, P4 P5 P6 below
        card(n + 1, M + (n % 3) * (cw3 + gap), cy + (n // 3) * (gh + gap), cw3, gh, "P%dDark" % (n + 1),
             pre="SixP", compact=True)

    ini.set("ScoreStaticNavigate", od(X=M + 160, Y=FOOT_Y + 20, W=b.key_w["ButtonNavi"], H=24, Tex="ButtonNavi",
                                      Color="Text2", Type="Transparent", Z=0.5))
    ini.set("ScoreTextNavigate", text_section("SING_LEGEND_NAVIGATE", M + 160 + b.key_w["ButtonNavi"] + 10,
                                              FOOT_Y + 21, 16, "Text2"))
    s.footer([("ButtonEnter", "Continuar")])



# ---------------------------------------------------------------------------
# Options: a 4 x 3 grid of tiles (the game moves 4 buttons per row)
# ---------------------------------------------------------------------------
OPTION_TILES = [
    ("Game", "SING_OPTIONS_GAME", "gear"), ("Graphics", "SING_OPTIONS_GRAPHICS", "monitor"),
    ("Sound", "SING_OPTIONS_SOUND", "speaker"), ("Input", "SING_OPTIONS_INPUT", "keyboard"),
    ("Lyrics", "SING_OPTIONS_LYRICS", "lyric"), ("Themes", "SING_OPTIONS_THEMES", "palette"),
    ("Record", "SING_OPTIONS_RECORD", "mic"), ("Advanced", "SING_OPTIONS_ADVANCED", "sliders"),
    ("Network", "SING_OPTIONS_NETWORK", "globe"), ("Webcam", "SING_OPTIONS_WEBCAM", "camera"),
    ("Jukebox", "SING_OPTIONS_JUKEBOX", "play"), ("Exit", "SING_OPTIONS_EXIT", "back"),
]


def options(b):
    ini, a = b.ini, b.assets
    ini.remove_prefix("OptionsButton")
    s = Screen(b, "Options")
    s.header(["Opciones"])
    s.text(M, 100, "SING_OPTIONS", size=52, font=FONT_DISPLAY, style=BOLD)
    ini.set("OptionsTextDescription", text_section("", M, 164, 18, "Text2"))

    cols, gap = 4, 16
    tw = (W - 2 * M - (cols - 1) * gap) // cols
    th = 124
    y0 = 216
    ring = a.panel(tw, th, 18, outline=2)
    for i, (key, label, icon) in enumerate(OPTION_TILES):
        x = M + (i % cols) * (tw + gap)
        y = y0 + (i // cols) * (th + 12)
        # the tile itself is a static; the button only adds the focus ring
        s.panel(x, y, tw, th, r=18, color="Surface")
        name = "OptionsButton" + key
        # the icon belongs to the button: on selection it grows, takes the
        # accent colour and swings (the gear turns)
        motion = od(IconSpin=180) if icon == "gear" else od(IconWobble=16)
        ini.set(name, od(X=x, Y=y, W=tw, H=th, Tex=ring, DTex=a.transparent(), Type="Transparent",
                         Color="Accent", DColor="Surface", Texts=2, Reflection=0, SelectScale=1.04,
                         IconTex=a.icon(icon, size=40), IconX=22, IconY=22, IconW=26, IconH=26,
                         IconColor="Accent", IconDColor="Text2", IconScale=1.3, **motion))
        ini.set(name + "Text1", text_section(label, 22, th - 46, 22, "Text", "Text2", FONT_DISPLAY, REGULAR))
        ini.set(name + "Text2", text_section("%02d" % (i + 1), tw - 22, 24, 14, "AccentText", "Text3",
                                             FONT_MONO, align=2))
    s.footer([("ButtonNavi", "Navegar"), ("ButtonEnter", "Abrir"), ("ButtonEsc", "Atrás")])


def options_sub(b):
    """The settings pages (game, graphics, sound...): one list of rows."""
    ini, a = b.ini, b.assets
    ini.remove_prefix("OptionsSubLegend")
    s = Screen(b, "OptionsSub")
    s.header(["Opciones"])
    ini.set("OptionsSubTextWhereAmI", text_section("", M, 96, 40, "Text", font=FONT_DISPLAY, style=BOLD))
    ini.set("OptionsSubTextDescription", text_section("", M, 150, 18, "Text2"))

    top, row_h, vgap = 200, 48, 8
    lw, skip = 420, 8
    vw = W - 2 * M - 16 - lw - skip          # 16: room for the scroll bar
    area_h = 7 * (row_h + vgap) - vgap
    ini.set("OptionsSubArea", od(X=M, Y=top, W=lw + skip + vw, H=area_h, WidgetVSpacing=vgap,
                                 ButtonBackVSpacing=16))
    ini.set("OptionsSubScrollBar", od(HSpacing=8, W=6, Color="Surface2", HColor="Text3", CColor="Muted"))
    ini.set("OptionsSubSelectSlide", od(
        Text="", X=M, W=lw, H=row_h, SkipX=skip, SBGW=vw, TextSize=18,
        Tex=a.panel(lw, row_h, 12), Type="Transparent", TexSBG=a.panel(vw, row_h, 12), TypeSBG="Transparent",
        Color="Surface2", DColor="Bg", TColor="Text", TDColor="Text2",
        SBGColor="Accent", SBGDColor="Surface", STColor="OnAccent", STUColor="Text", STDColor="Text3",
        ArrowW=24, ArrowH=24))
    full = lw + skip + vw
    ini.set("OptionsSubButton", od(X=M, W=full, H=row_h, Tex=a.panel(full, row_h, 12), Type="Transparent",
                                   Color="Accent", DColor="Surface", Texts=1, Reflection=0))
    ini.set("OptionsSubButtonText1", text_section("", full // 2, 13, 18, "OnAccent", "Text", align=1))
    ini.set("OptionsSubButtonExit", od(X=M, W=200, H=row_h, Tex=a.panel(200, row_h, 12), Type="Transparent",
                                       Color="Accent", DColor="Surface2", Texts=1, Reflection=0))
    ini.set("OptionsSubButtonExitText1", text_section("", 100, 13, 18, "OnAccent", "Text", align=1))
    s.footer([("ButtonNavi", "Navegar"), ("ButtonEsc", "Atrás")])


# ---------------------------------------------------------------------------
# Other screens (party, statistics, editor, about...): the content keeps the
# layout of the base theme; title, legend and chrome follow the theme
# ---------------------------------------------------------------------------
import os
import re

_SPANISH = None


def tr(key):
    """Spanish text of a translation key (to measure the legend)."""
    global _SPANISH
    if _SPANISH is None:
        _SPANISH = {}
        path = os.path.join(os.path.dirname(__file__), "..", "..", "game", "languages", "Spanish.ini")
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if "=" in line:
                    k, v = line.split("=", 1)
                    _SPANISH[k.strip()] = v.strip()
    return _SPANISH.get(key, key)


def resolved(ini, name, depth=0):
    sec = ini.get(name)
    if sec is None or depth > 8:
        return OrderedDict()
    out = OrderedDict()
    if "Inherits" in sec:
        out.update(resolved(ini, sec["Inherits"], depth + 1))
    for k, v in sec.items():
        if k != "Inherits":
            out[k] = v
    return out


def small(size):
    """Base theme text sizes are for a big title style; scale them to the
    body sizes of this theme."""
    size = int(float(size))
    return size if size <= 22 else max(15, int(round(size * 0.58)))


def generic_page(b, prefix):
    ini = b.ini
    title = desc = where = None
    legend_tex, legend_txt = [], []
    keep_st, keep_tx = [], []
    for kind in ("Static", "Text"):
        names = [n for n in ini.sections if n.startswith(prefix + kind) and n[len(prefix + kind):].isdigit()]
        names.sort(key=lambda n: int(n[len(prefix + kind):]))
        for n in names:
            raw = ini.get(n)
            sec = resolved(ini, n)
            inh = raw.get("Inherits", "")
            if kind == "Static":
                tex = sec.get("Tex", "")
                if inh.startswith(("DefaultBar", "DefaultIcon", "DefaultPartyIcon")) or \
                        (tex.endswith("Icon") and int(sec.get("Y", 999)) < 70):
                    continue
                if inh == "DefaultLegendStatic" or inh.endswith("LegendStatic") or \
                        (tex in b.key_w and int(sec.get("Y", 0)) >= 600):
                    legend_tex.append((int(sec.get("X", 0)), tex))
                    continue
                # decorative strips above/below the old panels
                if int(sec.get("H", 0)) == 24 and int(sec.get("W", 0)) > 300 and sec.get("Color") == "Surface2":
                    continue
                keep_st.append(sec)
            else:
                text = sec.get("Text", "")
                if inh == "DefaultTextWhereAmI" or text.endswith("WHEREAMI"):
                    where = text
                    continue
                if inh == "DefaultLegendText" or text.startswith("SING_LEGEND") or int(sec.get("Y", 0)) >= 640:
                    legend_txt.append((int(sec.get("X", 0)), text))
                    continue
                if inh == "DefaultPartyTitleText" or (int(sec.get("Y", 999)) < 40 and int(sec.get("Size", 0)) >= 40):
                    title = title or text
                    continue
                if inh == "PartyNewRoundText2" or (60 <= int(sec.get("Y", 0)) < 100 and int(sec.get("Size", 0)) >= 30):
                    desc = desc or text
                    continue
                keep_tx.append(sec)
    s = Screen(b, prefix)
    s.header([title or where or ""])
    if desc:
        s.text(W - M, 27, desc, size=16, color="Text3", align=2)
    for sec in keep_st:
        ini.set(s._name("Static", None), sec)
    for sec in keep_tx:
        if "Size" in sec:
            sec["Size"] = str(small(sec["Size"]))
        ini.set(s._name("Text", None), sec)
    legend_tex = [t for _, t in sorted(legend_tex)]
    legend_txt = [t for _, t in sorted(legend_txt)]
    s.footer([(t, tr(x)) for t, x in zip(legend_tex, legend_txt)])
    # texts of the buttons and slides of this screen
    for name in list(ini.sections):
        if not name.startswith(prefix) or re.match(re.escape(prefix) + r"(Static|Text)\d+$", name):
            continue
        if prefix == "Edit" and name.startswith(("EditSub", "EditConvert", "EditOpen")):
            continue
        sec = ini.get(name)
        if "Text" in name and "Size" in sec:
            sec["Size"] = str(small(sec["Size"]))
        # button texts: relative to the button, vertically centred
        m = re.match(r"^(.*)Text\d+$", name)
        if m and ini.get(m.group(1)) is not None and "Texts" in resolved(ini, m.group(1)):
            btn = resolved(ini, m.group(1))
            r = resolved(ini, name)
            bw_, bh_ = int(btn.get("W", 0)), int(btn.get("H", 0))
            if bw_ and int(r.get("X", 0)) > bw_:
                sec["X"] = str(bw_ // 2 if r.get("Align") == "1" else 16)
            if bh_ and "Size" in r:
                sec["Size"] = "18"
                sec["Y"] = str(max(0, (bh_ - 18) // 2 - 1))
        # long texts in panels (statistics, about): some padding
        if name.endswith("TextOverview"):
            r = resolved(ini, name)
            sec["X"] = str(int(r["X"]) + 20)
            sec["Y"] = str(int(r["Y"]) + 18)
            if "W" in r:
                sec["W"] = str(int(r["W"]) - 40)
        if "Select" in name and "TextSize" in sec:
            sec["TextSize"] = str(small(sec["TextSize"]))


GENERIC = ["JukeboxPlaylist", "PartyOptions", "PartyPlayer", "PartyRounds", "PartyNewRound", "PartyScore",
           "PartyWin", "PartyTournamentPlayer", "PartyTournamentOptions", "PartyTournamentRounds",
           "PartyTournamentWin", "AboutMain", "StatMain", "StatDetail", "EditConvert", "EditOpen"]


def party_rows(b):
    """Party setup screens that are just a list of select slides: the same
    rows as the settings pages (label box + value box), from the left margin."""
    ini, a = b.ini, b.assets
    row_h, vgap, lw, skip = 48, 8, 420, 8
    vw = W - 2 * M - lw - skip
    for prefix in ("PartyOptions", "PartyRounds", "PartyTournamentOptions", "PartyTournamentRounds"):
        names = [n for n in ini.sections if re.match(r"^%sSelect\w+$" % prefix, n)]
        names.sort(key=lambda n: int(resolved(ini, n).get("Y", 0)))
        for i, n in enumerate(names):
            old = resolved(ini, n)
            ini.set(n, od(
                Text=old.get("Text", ""), X=M, Y=120 + i * (row_h + vgap), W=lw, H=row_h, SkipX=skip, SBGW=vw,
                TextSize=18, Font=FONT_INTER, Style=REGULAR, ArrowTint=1, ArrowW=24, ArrowH=24,
                Tex=a.panel(lw, row_h, 12), Type="Transparent", TexSBG=a.panel(vw, row_h, 12), TypeSBG="Transparent",
                Color="Surface2", DColor="Bg", TColor="Text", TDColor="Text2",
                SBGColor="Accent", SBGDColor="Surface", STColor="OnAccent", STUColor="Text", STDColor="Text3"))


def party_round(b):
    """Next-round screen: the texts centred in their boxes."""
    ini = b.ini
    P = "PartyNewRound"

    def geo(name):
        r = resolved(ini, name)
        return int(float(r.get("Y", 0))), int(float(r.get("H", 0)))

    def put(text, static, size, dy=None):
        sec = ini.get(P + text)
        if sec is None or ini.get(P + static) is None:
            return
        sy, sh = geo(P + static)
        sec["Size"] = str(size)
        sec["Y"] = str(sy + ((sh - size) // 2 - 1 if dy is None else dy))

    for i in (1, 2, 3):
        put("TextNameTeam%d" % i, "StaticTeam%d" % i, 20, 8)
        put("TextTeam%dPlayers" % i, "StaticTeam%d" % i, 14, 35)
        put("TextScoreTeam%d" % i, "StaticTeam%d" % i, 30)
        put("TextNextPlayer%d" % i, "StaticNextPlayer%d" % i, 20)
    for i in range(1, 8):
        put("TextRound%d" % i, "StaticRound%d" % i, 15)
        put("TextWinner%d" % i, "StaticRound%d" % i, 15)
    put("Text5", "Static2", 16)
    put("Text6", "Static2", 16)
    put("Text7", "Static3", 32)
    put("TextNextRoundNo", "Static3", 32)
    put("TextNextRound", "Static4", 17)


def edit_menu(b):
    """Editor entry screen: import a MIDI file or go back."""
    ini, a = b.ini, b.assets
    s = Screen(b, "Edit")
    s.header(["SING_EDIT"])
    s.text(M, 100, "SING_EDIT", size=52, font=FONT_DISPLAY, style=BOLD)
    s.text(M, 164, "SING_EDIT_MENU_DESCRIPTION", size=18, color="Text2")
    bw, bh = 260, 56
    tex = a.panel(bw, bh, 14)
    for i, key in enumerate(("Convert", "EditHeaders", "AdjustGap", "Exit")):
        name = "EditButton" + key
        sec = ini.get(name)
        text = resolved(ini, name + "Text1").get("Text", "")
        ini.set(name, od(X=M + i * (bw + 12) if key != "Exit" else M + bw + 12, Y=220, W=bw, H=bh, Tex=tex,
                         Type="Transparent", Color="Accent", DColor="Surface2", Texts=1, Reflection=0))
        ini.set(name + "Text1", text_section(text, bw // 2, 17, 20, "OnAccent", "Text", align=1))
    ini.set("EditTextDescription", text_section("", M, 300, 18, "Text2", w=640))
    s.footer([("ButtonNavi", "Navegar"), ("ButtonEnter", "Seleccionar"), ("ButtonEsc", "Atrás")])


# ---------------------------------------------------------------------------
# Popups: a card over the dimmed screen
# ---------------------------------------------------------------------------
def popups(b):
    ini, a = b.ini, b.assets

    def card_popup(prefix, buttons, cw=520, ch=236):
        cx, cy = (W - cw) // 2, (H - ch) // 2
        ini.remove_prefix(prefix + "Static")
        ini.set(prefix + "Static1", od(X=cx, Y=cy, W=cw, H=ch, Z=1, Tex=a.panel(cw, ch, 24), Color="Surface2",
                                       Type="Transparent"))
        ini.set(prefix + "Text1", od(X=cx + 32, Y=cy + 28, Z=1, Text=resolved(ini, prefix + "Text1").get("Text", ""),
                                     Size=15, Color="Text3", Font=FONT_INTER, Style=BOLD, Align=0))
        ini.set(prefix + "Text", od(X=W // 2, Y=cy + 74, W=cw - 64, Z=1, Text="", Size=22, Color="Text",
                                    Font=FONT_INTER, Style=REGULAR, Align=1))
        bw, bh, gap = 150, 48, 12
        total = len(buttons) * bw + (len(buttons) - 1) * gap
        x = (W - total) // 2
        for i, label in enumerate(buttons):
            name = "%sButton%d" % (prefix, i + 1)
            ini.set(name, od(X=x, Y=cy + ch - bh - 28, W=bw, H=bh, Z=1, Tex=a.panel(bw, bh, 14), Type="Transparent",
                             Color="Accent", DColor="Surface3", Texts=1, Reflection=0))
            ini.set(name + "Text1", od(X=bw // 2, Y=13, Z=1, Text=label, Size=18, Color="OnAccent", DColor="Text",
                                       Font=FONT_INTER, Style=REGULAR, Align=1))
            x += bw + gap

    card_popup("CheckPopup", ["YES", "NO"])
    card_popup("ErrorPopup", ["OK"])

    # song menu: a list of actions (buttons and slides share the rows)
    cw, rows, rh = 420, 5, 48
    ch = 84 + rows * (rh + 6) + 18
    cx, cy = (W - cw) // 2, (H - ch) // 2
    ini.remove_prefix("SongMenuStatic")
    ini.set("SongMenuStatic1", od(X=cx, Y=cy, W=cw, H=ch, Z=0.96, Tex=a.panel(cw, ch, 24), Color="Surface2",
                                  Type="Transparent"))
    ini.set("SongMenuStatic2", od(X=cx + 28, Y=cy + 30, W=24, H=24, Z=0.97, Tex=a.icon("menu"), Color="Text2",
                                  Type="Transparent"))
    ini.set("SongMenuTextMenu", od(X=cx + 64, Y=cy + 28, Z=0.97, Text="MENU", Size=22, Color="Text",
                                   Font=FONT_DISPLAY, Style=REGULAR, Align=0))
    bw = cw - 48
    for i in range(1, rows + 1):
        y = cy + 84 + (i - 1) * (rh + 6)
        name = "SongMenuButton%d" % i
        text = resolved(ini, name + "Text1").get("Text", "")
        ini.set(name, od(X=cx + 24, Y=y, Z=0.97, W=bw, H=rh, Tex=a.panel(bw, rh, 14), Type="Transparent",
                         Color="Accent", DColor="Surface3", Texts=1, Reflection=0))
        ini.set(name + "Text1", od(X=20, Y=13, Z=0.97, Text=text, Size=18, Color="OnAccent", DColor="Text",
                                   Font=FONT_INTER, Style=REGULAR, Align=0))
        if i <= 3:
            ini.set("SongMenuSelectSlide%d" % i, od(
                Text="", X=cx + 24, Y=y, Z=0.97, W=0, H=rh, SkipX=0, SBGW=bw, TextSize=18,
                Tex=a.transparent(), Type="Transparent", TexSBG=a.panel(bw, rh, 14), TypeSBG="Transparent",
                ShowArrows=1, OneItemOnly=1, Color="Surface3", DColor="Surface3", TColor="Text", TDColor="Text",
                SBGColor="Accent", SBGDColor="Surface3", STColor="OnAccent", STUColor="Text", STDColor="Text2"))

    # jump to (search): a bar at the top, the song list stays visible
    cw, ch = 600, 228
    cx, cy = (W - cw) // 2, 84
    ini.remove_prefix("SongJumptoStatic")
    ini.remove_prefix("SongJumptoText")
    ini.set("SongJumptoStatic1", od(X=cx, Y=cy, W=cw, H=ch, Z=0.965, Tex=a.panel(cw, ch, 24), Color="Surface2",
                                    Type="Transparent"))
    ini.set("SongJumptoStatic2", od(X=cx + 28, Y=cy + 28, W=24, H=24, Z=0.97, Tex=a.icon("search"), Color="Text2",
                                    Type="Transparent"))
    ini.set("SongJumptoStatic3", od(X=cx + 24, Y=cy + 72, W=cw - 48, H=48, Z=0.97, Tex=a.panel(cw - 48, 48, 14),
                                    Color="Surface3", Type="Transparent"))
    ini.set("SongJumptoText1", od(X=cx + 64, Y=cy + 28, Z=0.97, Text="SONG_JUMPTO_TYPE_DESC", Size=20, Color="Text",
                                  Font=FONT_DISPLAY, Style=REGULAR, Align=0))
    ini.set("SongJumptoButtonSearchText", od(X=cx + 24, Y=cy + 72, Z=0.97, W=cw - 48, H=48, Color="Text",
                                             Texts=1))
    ini.set("SongJumptoButtonSearchTextText1", od(X=20, Y=12, Z=0.97, Text="", Size=22, Color="Text",
                                                  Font=FONT_INTER, Style=REGULAR, Align=0))
    ini.set("SongJumptoSelectSlideType", od(
        Text="", X=cx + 24, Y=cy + 132, Z=0.97, W=0, H=40, SkipX=0, SBGW=cw - 48, TextSize=16,
        Tex=a.transparent(), Type="Transparent", TexSBG=a.panel(cw - 48, 40, 12), TypeSBG="Transparent",
        ShowArrows=1, OneItemOnly=1, Color="Surface3", DColor="Surface3", TColor="Text", TDColor="Text",
        SBGColor="Accent", SBGDColor="Surface3", STColor="OnAccent", STUColor="Text", STDColor="Text2"))
    ini.set("SongJumptoTextFound", od(X=cx + 24, Y=cy + 186, Z=0.97, Text="SONG_JUMPTO_HELP", Size=16,
                                      Color="Text2", Font=FONT_INTER, Style=REGULAR, Align=0))


def loading(b):
    """Start screen. The game uses Static1/Static2 as progress bars (search
    for songs, reading them) and Text1 as the status line."""
    a = b.assets
    s = Screen(b, "Loading")
    bw = 360
    bx = W // 2 - bw // 2
    s.static(bx, 452, 0, 4, a.rect(), color="Accent")                    # 1: search (not shown)
    s.static(bx, 452, bw, 4, a.panel(bw, 4, 2), color="Accent")          # 2: reading songs
    s.text(W // 2, 416, "SING_LOADING", size=16, color="Text2", align=1)  # 1: status
    # mark: note bars and the pitch line, above the name. The game animates
    # it ([LoadingMark]): the line runs over the bars, its dot rides on them
    # and each bar lights up while it is "sung"
    notes = ((0, 44, 30, "NoteBlue"), (38, 30, 26, "NoteBlue"), (72, 16, 42, "Gold"),
             (122, 30, 30, "NoteBlue"), (160, 42, 44, "NoteBlue"))
    mw = 204
    mx, my = W // 2 - mw // 2, 228
    for x, y_, w_, col in notes:
        s.panel(mx + x, my + y_, w_, 10, r=5, color=col)            # statics 2..6
    s.panel(mx - 16, my, 2, 64, r=1, color="Accent")                 # 7: line
    s.panel(mx - 20, my + 44, 10, 10, r=5, color="Accent")           # 8: dot
    s.text(W // 2, 316, "SuperStar", size=48, font=FONT_DISPLAY, style=BOLD, align=1)
    s.text(W - M, H - 44, "US_VERSION", size=13, color="Text3", align=2)
    b.ini.set("LoadingMark", od(Notes="2,3,4,5,6", Line=7, Dot=8, Texts="1,0"))


def duet_singers(b):
    """Song screens: the singer names of a duet as a coloured dot + name."""
    ini, a = b.ini, b.assets
    for name in list(ini.sections):
        m = re.match(r"^Song(\w*)Static(\d)PlayersDuetSingerP(\d)$", name)
        if not m or m.group(2) == "2":   # two parts: see song_details
            continue
        st = resolved(ini, name)
        if "X" not in st:
            continue
        x, y, h = int(st["X"]), int(st["Y"]), int(st.get("H", 36))
        ini.set(name, od(X=x + 4, Y=y + h // 2 - 6, W=12, H=12, Z=st.get("Z", "0.95"), Tex=a.circle(12),
                         Color=st.get("Color", "P1Dark"), Type="Transparent"))
        tname = name.replace("Static", "Text", 1)
        tx = resolved(ini, tname)
        if tx:
            ini.set(tname, od(X=x + 24, Y=y + h // 2 - 11, Z=st.get("Z", "0.95"), Text="", Size=16, Color="Text",
                              Font=FONT_INTER, Style=REGULAR, Align=0))

def build(b):
    main_menu(b)
    players(b)
    song_roulette(b)
    song_chessboard(b)
    song_list(b)
    sing(b)
    score(b)
    options(b)
    options_sub(b)
    for prefix in GENERIC:
        generic_page(b, prefix)
    party_rows(b)
    party_round(b)
    edit_menu(b)
    popups(b)
    loading(b)
    duet_singers(b)
    # icons drawn "Colorized" keep their white (only the hue is replaced):
    # draw them tinted instead, in the text colours
    for name, sec in b.ini.sections.items():
        tex = resolved(b.ini, name).get("Tex", "")
        f = b.skin_tex.get(tex, tex)
        if resolved(b.ini, name).get("Type", "").lower() == "colorized" and str(f).startswith("K_icon"):
            sec["Type"] = "Transparent"
            sec["Color"] = "Text"
            if "DColor" in resolved(b.ini, name):
                sec["DColor"] = "Text3"
    for n, icon in (("JukeboxSongListUp", "chev_up"), ("JukeboxSongListDown", "chev_down")):
        r = resolved(b.ini, n)
        if r:
            x = int(r["X"]) + int(r["W"]) // 2 - 12
            b.ini.set(n, od(X=x, Y=int(r["Y"]) - 3, W=24, H=24, Tex=b.assets.icon(icon), Type="Transparent",
                            Color="Text", DColor="Text3"))
    # boxes that blended into a flat background (DColor Bg) are transparent
    # now that the background has a gradient: they fade in when selected
    for name, sec in b.ini.sections.items():
        if sec.get("DColor") == "Bg" and ("Tex" in sec or "SkipX" in sec or name.endswith("SelectSlide")):
            sec["DAlpha"] = "0"
    # select slides of the other screens: same colours as the options rows
    b.ini.set("DefaultSelectSlide", od(
        Color="Surface2", DColor="Bg", DAlpha=0, TColor="Text", TDColor="Text2",
        SBGColor="Accent", SBGDColor="Surface", STColor="OnAccent", STUColor="Text", STDColor="Text3",
        TextSize=18), replace=False)
    # select slides: Inter for the label and the values (not the base font),
    # chevrons in the colour of the value text
    for name, kv in b.ini.sections.items():
        if "SkipX" in kv or "SBGW" in kv or name.endswith("SelectSlide"):
            kv.setdefault("Font", str(FONT_INTER))
            kv.setdefault("Style", str(REGULAR))
            kv["ArrowTint"] = "1"
    # select slide arrows: a bit smaller than the icons, away from the edges
    for name, kv in b.ini.sections.items():
        if "ArrowW" in kv or name.endswith("SelectSlide"):
            kv["ArrowW"] = "20"
            kv["ArrowH"] = "20"
            kv["ArrowInset"] = "12"
