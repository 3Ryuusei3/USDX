#!/usr/bin/env python3
"""Builds the Karaoke theme (game/themes/Karaoke.ini + game/themes/Karaoke/).

    python3 tools/theme-karaoke/build_theme.py

1. Every screen of the Modern theme is taken as a starting point, scaled from
   its 800x600 canvas to the 1280x720 widescreen canvas (uniformly, centred),
   with its shapes replaced by flat rounded panels and its colours mapped to the
   Karaoke palette. That way no screen is ever left undefined.
2. The screens of the design (main menu, players, song selection in its three
   modes, singing, scores, options, popups) are then laid out by hand on the
   full 1280x720 canvas in screens.py.
3. Skins only change the [Colors]: one per base colour (see palette.py).
"""

import os
import re
import shutil
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from assets import Assets           # noqa: E402
from inifile import Ini             # noqa: E402
from palette import SKINS, make_palette  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
THEMES = os.path.join(ROOT, "game", "themes")
MODERN_INI = os.path.join(THEMES, "Modern.ini")
MODERN_SKIN = os.path.join(THEMES, "Modern", "Blue.ini")
MODERN_DIR = os.path.join(THEMES, "Modern")
OUT_INI = os.path.join(THEMES, "Karaoke.ini")
OUT_DIR = os.path.join(THEMES, "Karaoke")
FONT_DIR = os.path.join(ROOT, "game", "fonts")

W, H = 1280, 720
S = 1.2            # 800x600 -> 1280x720, uniform
OX = 160           # centre the old 4:3 layouts horizontally

# font families, in the order of game/fonts/fonts.ini
FONT_NOTO, FONT_INTER, FONT_DISPLAY, FONT_MONO = 0, 3, 4, 5
REGULAR, BOLD, OUTLINE = 0, 1, 2

X_KEYS = {"X", "SelectX"}
Y_KEYS = {"Y", "SelectY"}
LEN_KEYS = {"W", "H", "SelectW", "SelectH", "Size", "TextSize", "SkipX", "SBGW",
            "ReflectionSpacing", "DeSelectReflectionSpacing", "SelectReflectionSpacing",
            "Space", "PieceW", "PieceH", "Padding", "ArrowW", "ArrowH", "ZoomThumbW",
            "ZoomThumbH", "Distance", "WidgetVSpacing", "HSpacing", "ButtonBackVSpacing",
            "MinTextSize", "IndicatorYOffset", "BottomY", "Length"}

# textures that are just shapes: replaced by flat panels of the exact size
SHAPE_TEX = {
    "Button", "ButtonF", "Rectangle", "MainBar", "SelectBG", "PlayerNumberBox", "P",
    "ScoreBG", "JukeboxSongListBackground", "SongSelection1", "SongSelection2",
    "SongSelection3", "SongSelection4", "SongSelection5", "Leiste1", "Leiste2",
    "interface_dialog_background", "interface_dialog_background2",
    "interface_dialog_backgroundtop", "interface_dialog_backgroundtop2",
    "JukeboxSongOptionsBackground", "PartyRoundBG1", "PartyRoundBG2", "PartyRoundBG3",
    "PartyRoundBG4", "PartyScoreBG1", "PartyScoreBG2", "StatMainBG1", "StatMainBG2",
    "StatMainBG3", "StatDetailBG1", "LyricBar", "LyricBarDuet", "SongName",
    "PartyPlayerSelectBG", "PartyTeamButton1", "PartyTeamButton2", "PartyTeamButton3",
    "PartyTeamButton4", "PartyTeamButton5", "PartyPlayerButton", "SongMessage", "TimeBar1",
    "JukeboxTimeBar1", "JukeboxSongMenuTimeBar", "JukeboxCurrentSongBackground",
    "ButtonSendScore", "ScoreBox", "ScoreGlassBox", "PartyTeamPoints", "prevbackground",
    "SelectFrame", "CurrentPlayer",
}
BG_TEX = {"MainBG", "SongBG", "PartyBG", "OptionsBG", "EditBG", "EditSubBG", "LoadingBG",
          "ScoreScreenBG", "HighScoresBG"}

# Modern colour names -> Karaoke colour names
TEXT_COLORS = {
    "White": "Text", "WhiteGray": "Text2", "Silver": "Text2", "GrayLightest": "Text2",
    "GrayLight": "Text2", "ColorLightest": "Text2", "ColorLight": "Text2", "Gray": "Text3",
    "GrayDark": "Text3", "ColorDark": "AccentText", "Black": "Text", "GrayPopup": "Text2",
    "Red": "AccentText", "DarkRed": "AccentText", "LightRed": "AccentText", "Yellow": "Gold",
}
SHAPE_COLORS = {
    "White": "Surface", "WhiteGray": "Surface", "GrayLightest": "Surface2",
    "GrayLight": "Surface2", "Gray": "Surface3", "GrayDark": "Surface3", "GrayPopup": "Surface",
    "Black": "Bg", "ColorDark": "Surface3", "ColorLight": "Surface2", "ColorLightest": "Surface2",
    "Red": "Accent", "DarkRed": "Accent", "LightRed": "Accent",
}


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def fmt(v):
    return str(int(round(v)))


class Builder:
    def __init__(self):
        self.ini = Ini.read(MODERN_INI)
        self.assets = Assets(OUT_DIR, FONT_DIR)
        self.skin_tex = OrderedDict()     # texture name -> file (shared by all skins)

    # -- inheritance-aware lookup -------------------------------------------
    def eff(self, name, key, depth=0):
        sec = self.ini.get(name)
        if sec is None or depth > 10:
            return None
        if key in sec:
            return sec[key]
        parent = sec.get("Inherits")
        return self.eff(parent, key, depth + 1) if parent else None

    # -- 1. scale every section of Modern -------------------------------------
    @staticmethod
    def is_button_text(name):
        # button texts are positioned relative to their button
        return bool(re.search(r"Button.*Text\d*$", name)) or name in (
            "DefaultButtonText", "DefaultButtonFadeText") or re.search(r"Collection\d*Text\d+$", name)

    def scale_all(self):
        for name, sec in self.ini.sections.items():
            if name in ("Theme", "Colors"):
                continue
            rel = self.is_button_text(name)
            x = num(sec.get("X"))
            w = num(sec.get("W"))
            full_w = x == 0 and w == 800
            for k in list(sec):
                v = num(sec[k])
                if v is None:
                    continue
                if k in X_KEYS:
                    if full_w:
                        sec[k] = "0"
                    else:
                        sec[k] = fmt(v * S + (0 if rel else OX))
                elif k in Y_KEYS:
                    sec[k] = fmt(v * S)
                elif k in LEN_KEYS:
                    if k == "W" and full_w:
                        sec[k] = str(W)
                    elif k == "H" and v == 600:
                        sec[k] = str(H)
                    else:
                        sec[k] = fmt(v * S)
            # sections that only inherit a full-width X/W keep spanning the canvas
            if "W" in sec and sec["W"] == "960" and num(self.eff(name, "X")) in (0, 160):
                pass

    # -- 2. restyle: flat shapes, palette colours, fonts ---------------------
    def restyle_all(self):
        for name, sec in self.ini.sections.items():
            if name in ("Theme", "Colors"):
                continue
            tex = self.eff(name, "Tex")
            # screen backgrounds (not statics that happen to be called
            # ...Background, like in the jukebox or the editor)
            is_bg_section = name.endswith("Background") and self.eff(name, "W") is None
            if is_bg_section and (self.eff(name, "Type") or "").lower() == "fade":
                # popups: the screen below stays visible, dimmed
                alpha = max(float(self.eff(name, "Alpha") or 0.4), 0.5)
                sec.clear()
                sec.update(OrderedDict([("Type", "Fade"), ("ColR", "0.04"), ("ColG", "0.04"), ("ColB", "0.05"),
                                        ("Alpha", "%.2f" % alpha)]))
                continue
            if is_bg_section:
                sec.clear()
                sec["Type"] = "Texture"
                sec["Tex"] = "K_bg"
                continue
            has_size = "Size" in sec or "Font" in sec
            is_slide = name.endswith("SelectSlide") or "SkipX" in sec or "SBGW" in sec
            is_button = "Button" in name and not self.is_button_text(name)

            # textures
            if tex in BG_TEX and "Tex" in sec:
                sec["Tex"] = "K_bg"
                sec["Color"] = "White"
            elif tex in SHAPE_TEX:
                w = num(self.eff(name, "W"))
                h = num(self.eff(name, "H"))
                if w and h:
                    r = min(14, int(h // 2))
                    sec["Tex"] = self.assets.panel(int(w), int(h), r)
                    sec.setdefault("Type", "Transparent")
            for k in ("TexSBG",):
                if sec.get(k) in SHAPE_TEX:
                    sw = num(self.eff(name, "SBGW")) or 200
                    sh = num(self.eff(name, "H")) or 30
                    sec[k] = self.assets.panel(int(sw), int(sh), min(10, int(sh // 2)))
            if sec.get("Type", "").lower() == "colorized" and (sec.get("Tex") or "").startswith("K_"):
                sec["Type"] = "Transparent"
            # legend key caps keep their own width
            if sec.get("Tex") in getattr(self, "key_w", {}):
                sec["W"] = str(self.key_w[sec["Tex"]])
                sec["H"] = "24"
                sec["Type"] = "Transparent"
                sec["Color"] = "Text2"

            # colours
            def remap(key, table, default=None):
                v = sec.get(key)
                if v is None:
                    return
                if v in table:
                    sec[key] = table[v]
                elif default and not re.match(r"P\d|Team|Player|Gold|Bronze|Silver", v):
                    sec[key] = default

            if is_slide:
                remap("Color", {}, "Surface3")
                remap("DColor", {}, "Surface2")
                remap("TColor", TEXT_COLORS, "Text")
                remap("TDColor", TEXT_COLORS, "Text2")
                remap("SBGColor", {}, "Accent")
                remap("SBGDColor", {}, "Surface3")
                remap("STColor", {}, "OnAccent")
                remap("STDColor", {}, "Text")
            elif is_button and "Tex" in sec:
                remap("Color", {}, "Accent")
                remap("DColor", {}, "Surface2")
            elif has_size or "Text" in name:
                remap("Color", TEXT_COLORS)
                remap("DColor", TEXT_COLORS)
            else:
                t = sec.get("Tex", "")
                if t.startswith("K_icon") or t.startswith("K_key"):
                    remap("Color", TEXT_COLORS)
                else:
                    remap("Color", SHAPE_COLORS)
                    remap("DColor", SHAPE_COLORS)

            # flat: no mirror reflections
            for k in ("Reflection", "Reflections", "SelectReflection"):
                if k in sec:
                    sec[k] = "0"

            # fonts: Inter for everything that was the default sans
            if has_size and "Font" in sec:
                sec["Font"] = str(FONT_INTER)

        # button texts: dark on the accent when selected, normal text otherwise
        for name, sec in self.ini.sections.items():
            if self.is_button_text(name) and "Collection" not in name:
                sec["Color"] = "OnAccent"
                sec["DColor"] = "Text"

    # -- textures referenced by name from the code / skin -------------------
    def skin_textures(self):
        """Start from the Modern skin; the images it uses are copied unless
        replaced by a flat one below."""
        skin = Ini.read(MODERN_SKIN)
        for k, v in skin.get("Textures").items():
            self.skin_tex[k] = v
        a = self.assets

        def put(name, tex_name):
            self.skin_tex[name] = a.files[tex_name]

        # notes: target notes grey, sung notes coloured (hue set per player)
        plain = a.notes("K_notePlain", (92, 92, 96))
        sung = a.notes("K_noteSung", (79, 157, 255))
        plain_r = a.notes("K_notePlainRap", (92, 92, 96), rap=True)
        sung_r = a.notes("K_noteSungRap", (79, 157, 255), rap=True)
        none = a.transparent()
        for i, part in enumerate(("Left", "Mid", "Right")):
            put("NotePlain" + part, plain[i])
            put("Gray" + part, sung[i])
            put("NotePlain%sRap" % part, plain_r[i])
            put("Gray%sRap" % part, sung_r[i])
            put("NoteBG" + part, none)        # no glow: flat
            put("NoteBG%sRap" % part, none)

        # legend key caps
        for tex, label in (("ButtonNavi", "↑ ↓"), ("ButtonEnter", "Enter"), ("ButtonEsc", "Esc"),
                           ("ButtonAZ", "A–Z"), ("ButtonM", "M"), ("ButtonP", "P"), ("ButtonJ", "J"),
                           ("ButtonC", "C"), ("ButtonAlt", "Alt"), ("Button13", "1–6"),
                           ("ButtonDel", "Supr"), ("ButtonIns", "Ins")):
            n, w = a.keycap(label)
            put(tex, n)
            self.key_w = getattr(self, "key_w", {})
            self.key_w[tex] = w

        # icons
        for tex, icon in (("MainIcon", "mic"), ("MainSearch", "search"), ("IconOption", "gear"),
                          ("IconEdit", "gear"), ("IconSongMenu", "menu"), ("ScoreIcon", "star"),
                          ("PartyIcon", "party"), ("StatIcon", "stats"), ("VideoIcon", "video"),
                          ("SongCD", "cd"), ("IconError", "error"), ("IconQuestion", "question"),
                          ("icon_song_menu", "menu"), ("icon_song_search", "search"),
                          ("icon_song_video", "video"), ("icon_song_medley", "medley"),
                          ("icon_song_calcmedley", "medley"), ("icon_song_duet", "duet"),
                          ("icon_song_rap", "rap"), ("icon_song_rap_to_freestyle", "rap"),
                          ("JukeboxRandom", "random"), ("JukeboxRepeat", "repeat"),
                          ("JukeboxLyric", "lyric"), ("JukeboxOptions", "gear"), ("JukeboxClose", "close"),
                          ("JukeboxFix", "pin"), ("JukeboxSongMenuPlayPause", "play"),
                          ("JukeboxSongMenuNext", "next"), ("JukeboxSongMenuPrevious", "prev"),
                          ("JukeboxSongMenuPlaylist", "list"),
                          ("Select_ArrowLeft", "arrow_left"), ("Select_ArrowRight", "arrow_right")):
            put(tex, a.icon(icon))

        # simple shapes used by the code
        put("Ball", a.circle(16))
        put("LyricHelpBar", a.panel(32, 32, 8))
        put("LineBonusBack", a.bonus_badge(150, 30))
        put("SingBarBack", a.pill(160, 8))
        put("SingBarBar", a.pill(16, 8))
        put("SingBarFront", none)
        put("TimeBar", a.rect())
        put("ProgressBar", a.rect())
        put("JukeboxTimeBar", a.rect())
        put("ButtonFade", none)
        put("PlayerNumberBox", a.panel(40, 40, 10))
        for i in range(1, 7):
            put("PlayerIDBox%02d" % i, a.pill(64, 28))
        put("LyricIconD_P6", a.pill(64, 28))
        # score bars: flat; the game re-hues them with the player colour
        lvl = a.panel_rgba(16, 16, 0, (79, 157, 255, 255), name="K_level")
        put("ScoreLevel", lvl)
        put("ScoreLevelRound", none)
        for k, col in (("ScoreLevel_Dark", (60, 120, 205, 255)), ("ScoreLevel_Light", (79, 157, 255, 255)),
                       ("ScoreLevel_Lightest", (150, 195, 255, 255))):
            put(k, a.panel_rgba(16, 16, 0, col, name="K_" + k))
            put(k + "_Round", none)
        for i in range(8):
            put("Rating_%d" % i, a.rating_ladder(i))
        for k in ("ScoreBar_box_lightest", "ScoreBar_box_light", "ScoreBar_box_dark"):
            put(k, a.panel(16, 16, 4))
        put("ScoreEndCap", none)
        put("ScoreLine", a.rect())
        put("ScoreBox", a.panel(64, 64, 14))
        put("ScoreGlassBox", none)
        put("AvatarFrame", a.circle(96))
        put("AvatarFrame2", a.circle(96))
        put("SelectFrame", a.panel(96, 96, 22, outline=3))
        put("CurrentPlayer", a.panel(96, 96, 22))
        put("SongCover", a.panel(256, 256, 20))
        put("SongMessage", a.panel(400, 60, 14))
        put("SongName", a.pill(400, 34))
        put("Pause", a.pause_overlay(W, H))
        # score card on the sing screen: neutral dark, 45 % opaque (the game
        # only replaces its hue with the player colour)
        put("ScoreBG", a.panel_rgba(120, 56, 14, (12, 12, 12, 150)))   # 3+ players; 1-2: card with the lane
        for i in range(1, 7):
            put("NoAvatar_P%d" % i, a.circle(96))

    # -- output --------------------------------------------------------------
    def copy_unreplaced(self):
        for name, f in list(self.skin_tex.items()):
            if f.startswith("K_"):
                continue
            src = os.path.join(MODERN_DIR, f)
            if os.path.isfile(src):
                shutil.copyfile(src, os.path.join(OUT_DIR, f))

    def write_skins(self):
        for file, display, base in SKINS:
            p = make_palette(base)
            # one 8x8 solid image per skin for the backgrounds
            from PIL import Image
            bg_file = "K_bg_%s.png" % file
            Image.new("RGB", (8, 8), p["Bg"]).save(os.path.join(OUT_DIR, bg_file))
            ini = Ini()
            ini.set("Skin", OrderedDict([("Theme", "Karaoke"), ("Name", display), ("Color", "Black"),
                                         ("Creator", "Karaoke")]))
            tex = OrderedDict(self.skin_tex)
            tex["K_bg"] = bg_file
            # select slide arrows (the game does not tint them)
            for k in ("Select_ArrowLeft", "Select_ArrowRight"):
                n = self.assets.tinted(os.path.splitext(self.skin_tex[k])[0], p["Text2"], "_" + file)
                tex[k] = self.assets.files[n]
            # rating ladder in the skin's own tones
            cols = (p["Text"] + (255,), p["Muted"] + (255,), p["Line"] + (255,))
            for i in range(8):
                n = self.assets.rating_ladder(i, colors=cols, suffix="_" + file)
                tex["Rating_%d" % i] = self.assets.files[n]
            for n, f in self.assets.files.items():
                tex.setdefault(n, f)
            ini.set("Textures", tex)
            ini.set("Colors", OrderedDict((k, "%d %d %d" % v) for k, v in p.items() if not k.startswith("_")))
            ini.write(os.path.join(OUT_DIR, file + ".ini"),
                      header="; Skin of the Karaoke theme: base colour %s. Generated by tools/theme-karaoke." % display)

    def write_theme(self):
        p = make_palette(SKINS[0][2])
        colors = self.ini.get("Colors")
        for k, v in p.items():
            if not k.startswith("_"):
                colors[k] = "%d %d %d" % v
        theme = self.ini.set("Theme", OrderedDict([
            ("Name", "Karaoke"), ("Creator", "Karaoke"), ("US_Version", "USD 110"),
            ("DefaultSkin", "Negro"), ("RenderWidth", str(W)), ("RenderHeight", str(H)), ("KeepAspect", "1")]))
        # [Theme] first
        self.ini.sections.move_to_end("Theme", last=False)
        self.ini.write(OUT_INI, header="; Karaoke theme (1280x720). Generated by tools/theme-karaoke/build_theme.py - edit the generator, not this file.")


def main():
    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    b = Builder()
    b.scale_all()
    b.skin_textures()
    b.restyle_all()
    import screens
    screens.build(b)
    b.copy_unreplaced()
    b.write_theme()
    b.write_skins()
    print("theme written: %s (%d sections, %d images)" % (OUT_INI, len(b.ini.sections), len(os.listdir(OUT_DIR))))


if __name__ == "__main__":
    main()
