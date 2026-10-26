"""Hand-made screens of the Karaoke theme, laid out on the 1280x720 canvas
following the design mock-ups.

Conventions (see build_theme.py for the fonts and palette.py for colours):
* header: 76 px, accent square + "Karaoke" + breadcrumb, 48 px side margin
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
        self.ini.set(prefix + "Background", od(Type="Texture", Tex="K_bg"))

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
        """Accent square, wordmark and an optional breadcrumb."""
        self.panel(M, 32, 12, 12, r=3, color="Accent")
        self.text(M + 22, 25, "Karaoke", size=20, font=FONT_DISPLAY, style=REGULAR)
        x = M + 120
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
                         Color="Surface2", DColor="Bg", Texts=2, Reflection=0))
        ini.set(name + "Text1", text_section(label, 62, 12, 28, "Text", "Text2", FONT_DISPLAY, REGULAR))
        ini.set(name + "Text2", text_section(numtxt, 20, 20, 15, "AccentText", "Text3", FONT_MONO))
        y += row_h + 4
    s.panel(M + 20, y + 8, row_w - 40, 1, r=0, color="Divider")
    y += 20
    small = a.panel(row_w, 44, 12)
    for name, label in (("MainButtonAbout", "Acerca de"), ("MainButtonExit", "SING_EXIT")):
        ini.set(name, od(X=M, Y=y, W=row_w, H=44, Tex=small, Type="Transparent",
                         Color="Surface2", DColor="Bg", Texts=1, Reflection=0))
        ini.set(name + "Text1", text_section(label, 62, 11, 18, "Text", "Text3", FONT_INTER))
        y += 48

    # right: what the selected entry does
    px, py, pw, ph = 548, 100, W - M - 548, 532
    s.panel(px, py, pw, ph, r=24, color="Surface")
    ini.set("MainTextDescription", text_section("", px + 44, py + 64, 72, "Text", font=FONT_DISPLAY, style=BOLD))
    ini.set("MainTextDescriptionLong", text_section("", px + 44, py + 160, 20, "Text2", w=440))
    # detail: a stave with note bars and the pitch marker
    sx, sy = px + 44, py + 300
    for i in range(4):
        s.panel(sx, sy + 30 + i * 40, pw - 88, 1, r=0, color="Divider")
    bars = [(0, 103, 84, "NoteBlue"), (96, 83, 52, "NoteBlue"), (160, 63, 112, "NoteBlue"),
            (284, 43, 66, "Gold"), (362, 63, 44, None), (418, 103, 100, None), (530, 123, 56, None)]
    for x, y_, w, col in bars:
        if col:
            s.panel(sx + x, sy + y_, w, 14, r=7, color=col)
        else:
            s.static(sx + x, sy + y_, w, 14, a.panel(w, 14, 7, outline=2), color="Line2")
    s.panel(sx + 356, sy + 36, 2, 120, r=0, color="Accent")
    s.panel(sx + 351, sy + 58, 12, 12, r=6, color="Accent")

    s.footer([("ButtonNavi", "Navegar"), ("ButtonEnter", "Seleccionar"), ("ButtonC", "Créditos")])


# ---------------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------------
def players(b):
    ini, a = b.ini, b.assets
    s = Screen(b, "Name")
    s.header(["¡Canta!", "Jugadores"])
    s.text(M, 100, "¿Quién canta?", size=52, font=FONT_DISPLAY, style=BOLD)
    s.text(M, 164, "Pon nombre a cada micrófono y elige la dificultad.", size=18, color="Text2")

    # number of players (top right)
    ini.set("NameSelectPlayerCount", od(
        X=820, Y=112, W=190, H=44, SkipX=8, SBGW=214, Text="NAME_PLAYERS_COUNT", TextSize=18,
        Tex=a.panel(190, 44, 12), Type="Transparent", TexSBG=a.panel(214, 44, 12), TypeSBG="Transparent",
        Color="Surface2", DColor="Surface", TColor="Text", TDColor="Text2",
        SBGColor="Accent", SBGDColor="Surface2", STColor="OnAccent", STUColor="Text", STDColor="Text",
        ArrowW=24, ArrowH=24))

    # row of players: avatar in the player's colour + name
    chip = 76
    for i in range(6):
        x = M + 24 + i * 196
        ini.set("NamePlayerSelectStatic%d" % (i + 1), od(
            X=x, Y=222, W=chip, H=chip, Tex=a.circle(chip), Color="P%dDark" % (i + 1), Type="Transparent", Z=1))
        ini.set("NamePlayerSelectStatic%dText" % (i + 1), od(
            X=x + chip // 2, Y=306, Font=FONT_INTER, Style=BOLD, Size=17, Align=1, Color="Text", Z=1))
        # no avatar pictures: each player is its colour
        ini.set("NamePlayerSelectStatic%dAvatar" % (i + 1), od(X=x, Y=222, W=0, H=0, Z=1))
    # ring around the player being edited (X is relative to the player)
    ini.set("NamePlayerSelectCurrent", od(X=-8, Y=214, W=chip + 16, H=chip + 16, Z=0.95,
                                          Tex=a.panel(chip + 16, chip + 16, (chip + 16) // 2, outline=3),
                                          Color="Accent", DColor="Accent", Type="Transparent"))

    # editor of the current player
    py = 352
    s.panel(M, py, W - 2 * M, 280, r=24, color="Surface")
    ini.set("NamePlayerButtonAvatar", od(X=0, Y=0, W=0, H=0, Tex=a.transparent(), Type="Transparent"))
    ini.set("NamePlayerAvatar", od(X=0, Y=0, W=0, H=0, Reflection=0))
    ini.set("NamePlayerScrollAvatar", od(Count=3, Distance=24, Reflection=0, Show=0))

    fx = M + 32
    fw = W - 2 * M - 64
    s.text(fx, py + 26, "NOMBRE", size=13, color="Text3", style=BOLD)
    ini.set("NamePlayerButtonName", od(X=fx, Y=py + 52, W=fw, H=60, Z=1,
                                       Tex=a.panel(fw, 60, 14), Color="P1Dark", DColor="P1Light",
                                       Type="Transparent", Texts=1))
    ini.set("NamePlayerButtonNameText1", text_section("", 24, 14, 28, "OnAccent", font=FONT_DISPLAY))
    lw_ = 220
    slide = od(TexSBG=a.panel(fw - lw_ - 8, 48, 12), TypeSBG="Transparent",
               Tex=a.panel(lw_, 48, 12), Type="Transparent",
               X=fx, W=lw_, H=48, SkipX=8, SBGW=fw - lw_ - 8, TextSize=20, ArrowW=24, ArrowH=24,
               Color="Surface2", DColor="Surface", TColor="Text", TDColor="Text2",
               SBGDColor="PlayerDark", SBGColor="PlayerLight", STColor="OnAccent", STDColor="Text", Z=1)
    ini.set("NameSelectPlayerColor", OrderedDict(slide, Y=str(py + 136), Text="Color"))
    ini.set("NameSelectPlayerLevel", OrderedDict(slide, Y=str(py + 196), Text="PARTY_DIFFICULTY"))

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
    s.static(cx - 9, cy - 9, cw + 18, cw + 18, a.panel(cw + 18, cw + 18, 26, outline=3), color="Accent", z=0.96)
    song_details(b, "SongRoulette", W // 2 - 340, 424, 680, align=1, title=34)
    ini.set("SongRouletteTextNumber", od(X=M, Y=620, Z=0.95, Color="Text3", Font=FONT_MONO, Size=14, Align=0))


def song_chessboard(b):
    ini, a = b.ini, b.assets
    px, py, pw, ph = 872, 96, W - M - 872, 540
    s = song_common(b, "Chessboard", score_x=px + 24, score_y=py + 450)
    s.panel(px, py, pw, ph, r=22, color="Surface")
    cell, pad = 118, 14
    sel = 180
    ini.set("SongChessboardCover", od(X=M + 8, Y=104, W=cell, H=cell, Rows=4, Cols=6, Padding=pad,
                                      SelectX=px + 24, SelectY=py + 24, SelectW=sel, SelectH=sel,
                                      SelectReflection=0, ZoomThumbW=cell + 22, ZoomThumbH=cell + 22, Reflections=0))
    song_details(b, "SongChessboard", px + 24, py + 222, pw - 48, align=0, title=26)
    ini.set("SongChessboardTextNumber", od(X=px + pw - 24, Y=py + 28, Z=0.97, Color="Text3", Font=FONT_MONO,
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
LANE_X, LANE_W, LANE_H = 32, W - 64, 136
LANES = (70, 404)          # top of the lane of player 1 and player 2
LS = 13                    # line spacing (pitch step = LS / 2)
HUD_W = 200


def sing(b):
    ini, a = b.ini, b.assets
    s = Screen(b, "Sing")
    ini.set("SingBackground", od(Type="Texture", Tex="K_bg"))

    # note lanes: a light veil (the code draws it only under lanes in use);
    # every note carries its own dark + light ring (see assets.notes)
    lines_top = [t + 10 for t in LANES]
    base = [lt + 7 * LS for lt in lines_top]
    ini.set("SingNoteArea", od(
        Left=LANE_X + HUD_W + 24, Right=LANE_X + LANE_W - 24, LineSpacing=LS, LineSpacing3=12,
        Top3Rows1=236, Top3Rows2=376, Top3Rows3=516, LanePad3=20,
        Top1Row=base[1], Top2Rows1=base[0], Top2Rows2=base[1],
        Left3=184, Right3=W - 184, NoteScale=1.1, NoteCapScale=2,
        LineColor="ScrimText", LineAlpha=0.18,
        LaneTex=a.panel(LANE_W, LANE_H, 20), LaneLeft=LANE_X, LaneRight=LANE_X + LANE_W,
        LanePadTop=10, LanePadBottom=LANE_H - 9 * LS - 10, LaneColor="Scrim", LaneAlpha=0.3,
        HudTex=a.panel(HUD_W, LANE_H, 20), HudW=HUD_W, HudAlpha=0.35))

    # score card of each player, at the left end of its lane: drawn with the
    # lane (SingNoteArea Hud*), below the name and avatar; ScoreBG itself is
    # empty, since the game draws it over them. The texts have a dark outline,
    # so they read over any video.
    ini.set("SingDefaultScoreBG", od(Tex="ScoreBG", W=HUD_W, H=LANE_H, Type="Colorized"))
    # line bonus: a badge hanging on the bottom edge of the score card
    ini.set("SingLineBonus", od(W=150, H=30, Y=LANE_H - 15, Size=16, Font=FONT_INTER, Style=1))

    def player(prefix, top, color):
        x = LANE_X
        ini.set("Sing%sStatic" % prefix, od(X=x + 18, Y=top + 18, W=26, H=26, Tex=a.circle(26),
                                            Color=color, Type="Transparent", Alpha=1))
        ini.set("Sing%sAvatar" % prefix, od(X=x + 22, Y=top + 22, W=0, H=0, Z=1, Alpha=0))
        ini.set("Sing%sText" % prefix, od(X=x + 54, Y=top + 17, Text="PLAYERNAME", Font=FONT_INTER, Style=OUTLINE,
                                          Size=20, Color="ScrimText", Align=0))
        # no ScoreBG here (W = 0): the card comes with the lane. X/Y still
        # place the line bonus badge (centred on X, see SingLineBonus)
        ini.set("Sing%sStatic2" % prefix, od(X=x + HUD_W // 2, Y=top, W=0, H=LANE_H))
        ini.set("Sing%sTextScore" % prefix, od(Text="00000", X=x + 18, Y=top + 52, Font=FONT_MONO, Style=OUTLINE,
                                               Size=34, Color="ScrimText", Align=0))
        ini.set("Sing%sSingBar" % prefix, od(X=x + 18, Y=top + 104, W=HUD_W - 36, H=8))
        ini.set("Sing%sOscilloscope" % prefix, od(X=x + 18, Y=top + 116, W=HUD_W - 36, H=12))

    player("P1", LANES[1], "P1Dark")          # one player: lower lane, next to the lyrics
    player("P1TwoP", LANES[0], "P1Dark")
    player("P2R", LANES[1], "P2Dark")

    # no avatar pictures in any layout
    for name in list(ini.sections):
        if re.match(r"^Sing\w*Avatar$", name):
            ini.set(name, od(X=0, Y=0, W=0, H=0, Z=1, Alpha=0))

    # 3 or more players (no lanes): a small dark card behind each score
    own = ("P1", "P1TwoP", "P2R")
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
        ini.set(name, od(Tex="ScoreBG", Type="Colorized", X=x0, Y=y0, W=x1 - x0, H=y1 - y0))
        ini.set("Sing%sTextScore" % pre, od(Text="00000", X=sx, Y=sy, Font=FONT_MONO, Style=OUTLINE,
                                             Size=28, Color="ScrimText", Align=0))
        nm = resolved(ini, "Sing%sText" % pre)
        if nm:
            nm.update(od(Font=FONT_INTER, Style=OUTLINE, Color="ScrimText"))
            nm["Size"] = str(min(int(nm.get("Size", 20)), 20))
            ini.set("Sing%sText" % pre, nm)

    # lyrics: a solid panel at the bottom; duets get a second one in the middle
    ly = H - 24 - 140
    ini.set("SingLyricsBar", od(Tex=a.panel(LANE_W, 140, 22), X=LANE_X, Y=ly, W=LANE_W, H=140,
                                Color="Scrim", Type="Transparent"))
    ini.set("SingLyricsUpperBar", od(X=96, W=W - 192, Y=ly + 18, H=56, IndicatorYOffset=4))
    ini.set("SingLyricsLowerBar", od(X=96, W=W - 192, Y=ly + 82, H=40))
    for p_ in ("SingLyricsDuetP2UpperBar", "SingLyricsDuetP2LowerBar"):
        ini.set(p_, OrderedDict(ini.get(p_.replace("DuetP2", ""))))
    dy = 220
    ini.set("SingLyricsBarDuet", od(Tex=a.panel(LANE_W, 120, 22), X=LANE_X, Y=dy, W=LANE_W, H=120,
                                    Color="Scrim", Type="Transparent"))
    ini.set("SingLyricsDuetP1UpperBar", od(X=96, W=W - 192, Y=dy + 14, H=50, IndicatorYOffset=4))
    ini.set("SingLyricsDuetP1LowerBar", od(X=96, W=W - 192, Y=dy + 70, H=36))

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
    ini.set("ScoreTextArtistTitle", text_section("ArtistTitle", W - M, 26, 16, "Text2", align=2))

    def card(n, cx, cy, cw, ch, pcol):
        bar_w = 56 if cw > 450 else 40
        bx = cx + cw - 28 - bar_w
        inner = bx - 24 - (cx + 28)          # width of the left column
        big = cw > 450
        ini.set("ScorePlayer%dStatic1" % n, od(X=cx, Y=cy, W=cw, H=ch, Z=0.1, Tex=a.panel(cw, ch, 24),
                                               Color="Surface", Type="Transparent"))
        ini.set("ScorePlayer%dStatic2" % n, od(X=cx + 28, Y=cy + 28, W=56, H=56, Z=0.9, Tex=a.circle(56),
                                               Color=pcol, Type="Transparent"))
        ini.set("ScorePlayer%dAvatar" % n, od(X=cx + 32, Y=cy + 32, W=0, H=0, Z=1))
        ini.set("ScoreTextName%d" % n, text_section("P%d" % n, cx + 100, cy + 38, 26, "Text", font=FONT_DISPLAY))
        ini.set("ScoreTextTotal%d" % n, text_section("SING_TOTAL", cx + 28, cy + 112, 15, "Text3"))
        ini.set("ScoreTextTotalSCore%d" % n, text_section("00000", cx + 28, cy + 134, 72 if big else 54, "Text",
                                                           font=FONT_MONO))
        ini.set("ScoreStaticRatingPicture%d" % n, od(X=cx + 28, Y=cy + 238, W=inner, H=12, Z=0.85))
        ini.set("ScoreTextScore%d" % n, od(X=cx + 28, Y=cy + 260, W=inner, Color="Text", Font=FONT_DISPLAY,
                                           Style=REGULAR, Size=26 if big else 22, Text="Tone Deaf", Align=0))
        rows = (("Notes", "SING_NOTES", "BoxDark", "ScoreBar_box_dark"),
                ("LineBonus", "SING_PHRASE_BONUS", "BoxLight", "ScoreBar_box_light"),
                ("GoldenNotes", "SING_GOLDEN_NOTES", "BoxLightest", "ScoreBar_box_lightest"))
        for i, (key, label, box, tex) in enumerate(rows):
            y = cy + 330 + i * 46
            ini.set("ScoreStatic%s%d" % (box, n), od(Tex=tex, X=cx + 28, Y=y + 4, W=12, H=12, Color=pcol,
                                                      Type="Colorized"))
            ini.set("ScoreText%s%d" % (key, n), text_section(label, cx + 50, y, 17, "Text2"))
            ini.set("ScoreText%sScore%d" % (key, n), text_section("0000", cx + 28 + inner, y - 1, 18, "Text",
                                                                  font=FONT_MONO, align=2))
            if i < 2:
                ini.set("ScorePlayer%dStatic%d" % (n, 3 + i), od(X=cx + 28, Y=y + 32, W=inner, H=1, Z=0.5,
                                                                 Tex=a.rect(), Color="Divider", Type="Transparent"))
        # the animated bar: track + fill (re-hued with the player colour)
        top, bh = cy + 28, ch - 56
        # the track is a plain static (the game does not draw BackLevel);
        # its Z puts it below the bars, which the game draws itself
        ini.set("ScorePlayer%dStatic5" % n, od(X=bx, Y=top, W=bar_w, H=bh, Z=0.2, Tex=a.panel(bar_w, bh, 12),
                                               Color="Surface3", Type="Transparent"))
        ini.set("ScoreStaticBackLevel%d" % n, od(Tex=a.panel(bar_w, bh, 12), X=bx, Y=top, W=bar_w, H=bh,
                                                  Color="Surface3", Type="Transparent"))
        ini.set("ScoreStaticBackLevelRound%d" % n, od(Tex=a.transparent(), X=bx, Y=top, W=bar_w, H=1,
                                                       Color="Surface3", Type="Transparent"))
        ini.set("ScoreStaticLevel%d" % n, od(Tex="ScoreLevel", X=bx, Y=top + bh - 10, W=bar_w, H=10, Color=pcol,
                                              Type="Colorized"))
        ini.set("ScoreStaticLevelRound%d" % n, od(Tex=a.transparent(), X=bx, Y=top + bh - 10, W=bar_w, H=1,
                                                   Color=pcol, Type="Transparent"))
        # send-score button (only with score websites)
        btn = ini.get("ScoreButtonSend%d" % n)
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
        s.icon(x + 22, y + 22, 24, icon, color="Text2")
        name = "OptionsButton" + key
        ini.set(name, od(X=x, Y=y, W=tw, H=th, Tex=ring, DTex=a.transparent(), Type="Transparent",
                         Color="Accent", DColor="Surface", Texts=2, Reflection=0))
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
    # mark: three note bars and the pitch line, above the name
    mx, my = W // 2 - 60, 236
    for x, y_, w_, col in ((0, 40, 34, "NoteBlue"), (42, 28, 30, "NoteBlue"), (80, 14, 40, "Gold")):
        s.panel(mx + x, my + y_, w_, 10, r=5, color=col)
    s.panel(mx + 100, my, 2, 64, r=1, color="Accent")
    s.panel(mx + 96, my + 10, 10, 10, r=5, color="Accent")
    s.text(W // 2, 316, "Karaoke", size=48, font=FONT_DISPLAY, style=BOLD, align=1)
    s.text(W - M, H - 44, "US_VERSION", size=13, color="Text3", align=2)


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
    # select slides of the other screens: same colours as the options rows
    b.ini.set("DefaultSelectSlide", od(
        Color="Surface2", DColor="Bg", TColor="Text", TDColor="Text2",
        SBGColor="Accent", SBGDColor="Surface", STColor="OnAccent", STUColor="Text", STDColor="Text3",
        TextSize=18), replace=False)
    # select slide arrows: drawn at the size of the icons
    for name, kv in b.ini.sections.items():
        if "ArrowW" in kv or name.endswith("SelectSlide"):
            kv["ArrowW"] = "24"
            kv["ArrowH"] = "24"
