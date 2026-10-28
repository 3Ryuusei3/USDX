#!/usr/bin/env python3
"""Writes the canvas artboards that mirror the current SuperStar screens
(Karaoke theme, 1280x720). Usage: gen_design.py <project dir>"""
import os
import re
import sys

OUT = sys.argv[1]
SRC = open(os.path.join(OUT, "Main.dc.html"), encoding="utf-8").read()
# the theme helper of the existing artboards (base colour -> tokens)
THEME_JS = SRC[SRC.index("function makeTheme"):SRC.index("class Component")]

ACC = "{{accent}}"
P = {"blue": "#4F9DFF", "mint": "#2FD39A", "violet": "#C08CFF", "gold": "#FFC53D", "pink": "#FF6FAE"}
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&amp;family=Inter+Tight:wght@500;600;700'
         '&amp;family=JetBrains+Mono:wght@400;500;700&amp;display=swap" rel="stylesheet">')
DISPLAY = "font-family: 'Inter Tight', Inter, sans-serif"
MONO = "font-family: 'JetBrains Mono', monospace"
SHADOW_T = "text-shadow: 0 1px 2px rgba(0,0,0,0.75), 0 0 6px rgba(0,0,0,0.55)"
NOTE_SHADOW = "box-shadow: 0 3px 8px rgba(0,0,0,0.45)"


def page(title, body, extra_js="", extra_vals="", props=None):
    props = props or ('{"accent":{"editor":"color","default":"#FF5A36","options":["#FF5A36","#4F9DFF","#2FD39A","#F2F2EF"]},'
                      '"base":{"editor":"color","default":"#0E0F12","options":["#0E0F12","#14213D","#2A1B3D","#F4F1EA"]},'
                      '"$preview":{"width":1280,"height":720}}')
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
{FONTS}
<style>
body{{margin:0}}
button{{font:inherit;color:inherit;background:none;border:0;padding:0;cursor:pointer;text-align:left}}
a{{color:var(--fg)}}a:hover{{color:#FFFFFF}}
input::placeholder{{color:var(--fg3)}}
</style>
</helmet>
{body}
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{props}'>
{THEME_JS}{extra_js}
class Component extends DCLogic {{
  renderVals() {{
    const accent = this.props.accent ?? '#FF5A36';
    const theme = makeTheme(this.props.base ?? '#0E0F12', accent);
    // the moving gradient of the backgrounds: warm at the top left, cool at
    // the bottom right (the game lets it drift slowly)
    const h = theme.hex;
    const bgGrad = 'radial-gradient(900px 620px at 12% 0%, color-mix(in srgb, ' + accent + ' 13%, ' + h.bg + '), transparent 72%), '
      + 'radial-gradient(1000px 700px at 95% 105%, color-mix(in srgb, #4F9DFF 14%, ' + h.bg + '), transparent 70%), ' + h.bg;
    {extra_vals}
    return {{ themeVars: theme.vars, accent, bgGrad{', ' + 'extra' if extra_vals else ''} }};
  }}
}}
</script>
</body>
</html>
"""


def root(inner):
    return ('<div style="{{themeVars}} width: 1280px; height: 720px; position: relative; overflow: hidden; '
            'color: var(--fg); font-family: Inter, system-ui, sans-serif; background: {{bgGrad}}">\n' + inner + '\n</div>')


def ab(x, y, w=None, h=None, extra=""):
    s = f"position: absolute; left: {x}px; top: {y}px;"
    if w is not None:
        s += f" width: {w}px;"
    if h is not None:
        s += f" height: {h}px;"
    return s + (" " + extra if extra else "")


MIC = ('<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{{accent}}" stroke-width="2" '
       'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3"></rect>'
       '<path d="M5 11a7 7 0 0 0 14 0M12 18v3"></path></svg>')


def header(crumbs=(), search=False):
    out = [f'<header style="{ab(0, 0, 1280, 76)}">',
           f'<div style="{ab(46, 25)}">{MIC}</div>',
           f'<span style="{ab(76, 25)} {DISPLAY}; font-weight: 600; font-size: 20px; letter-spacing: -0.01em">SuperStar</span>']
    x = 220
    for i, c in enumerate(crumbs):
        last = i == len(crumbs) - 1
        out.append(f'<span style="{ab(x, 26)} font-size: 16px; color: var(--muted)">/</span>')
        out.append(f'<span style="{ab(x + 22, 27)} font-size: 15px; color: {"var(--fg)" if last else "var(--fg2)"}">{c}</span>')
        x += 22 + 9 * len(c) + 40
    if search:
        out.append(f'''<div style="{ab(932, 18, 300, 40)} border-radius: 20px; background: var(--s1); display: flex; align-items: center; gap: 10px; padding: 0 12px 0 16px; box-sizing: border-box">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--fg3)" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><path d="M20 20l-3.5-3.5"></path></svg>
<label for="q" style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0)">Buscar canción</label>
<input id="q" placeholder="Buscar canción o artista" style="flex: 1; font: inherit; font-size: 15px; color: var(--fg); background: transparent; border: 0; outline: none; padding: 0; min-width: 0">
{keycap("J")}
</div>''')
    out.append('</header>')
    return "\n".join(out)


def keycap(k):
    return (f'<span style="{MONO}; font-size: 12px; font-weight: 500; color: var(--bg); background: var(--fg2); '
            f'border-radius: 6px; padding: 3px 7px; line-height: 18px">{k}</span>')


def footer(items):
    out = [f'<div style="{ab(0, 656, 1280, 1)} background: var(--div)"></div>',
           f'<footer style="{ab(48, 670)} display: flex; align-items: center; gap: 30px; font-size: 15px; color: var(--fg2)">']
    for k, label in items:
        out.append(f'<div style="display: flex; align-items: center; gap: 10px">{keycap(k)}<span>{label}</span></div>')
    out.append('</footer>')
    return "\n".join(out)


def cover(x, y, s, bg, fg, radius=None, extra="", band=True):
    """Flat stand-in for a song cover: colour, a disc, a darker band."""
    r = radius if radius is not None else round(s * 0.057)
    return (f'<div style="{ab(x, y, s, s)} border-radius: {r}px; overflow: hidden; background: {bg}; {extra}" aria-hidden="true">'
            f'<div style="{ab(round(s * 0.27), round(s * 0.16), round(s * 0.46), round(s * 0.46))} border-radius: 50%; background: {fg}"></div>'
            + (f'<div style="{ab(0, round(s * 0.74), s, s - round(s * 0.74))} background: rgba(0,0,0,0.22)"></div>' if band else "")
            + '</div>')


COVERS = [("#23413A", "#A6F5E4"), ("#3B2F4A", "#C9A7F0"), ("#3A2E2A", "#E8A87C"), ("#2B3A67", "#8FB8E8"),
          ("#40302A", "#F2C14E"), ("#3A2A33", "#F08FA8"), ("#263240", "#7FD8B4"), ("#2E3A2A", "#B8D98A"),
          ("#2A3340", "#E8E1C4")]


def chip(label, icon):
    icons = {
        "video": '<rect x="3" y="6" width="13" height="12" rx="2"></rect><path d="M16 10l5-3v10l-5-3z"></path>',
        "duet": '<circle cx="9" cy="8" r="3"></circle><circle cx="17" cy="9" r="2.5"></circle><path d="M3 19c0-3 3-5 6-5s6 2 6 5M15 14c3 0 6 1.5 6 4.5"></path>',
        "medley": '<path d="M4 7h11M4 12h8M4 17h5M17 9v9M17 18l3-3M17 18l-3-3"></path>',
    }
    return (f'<span style="display: inline-flex; align-items: center; gap: 6px; height: 28px; padding: 0 12px; border-radius: 14px; '
            f'border: 1.5px solid var(--fg2); color: var(--fg2); font-size: 15px; box-sizing: border-box">'
            f'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{icons[icon]}</svg>{label}</span>')


def write(name, html):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote", name, len(html))


# ---------------------------------------------------------------------------
def main_menu():
    b = [header()]
    b.append(f'<div style="{ab(68, 106)} font-size: 12px; font-weight: 600; letter-spacing: 0.08em; color: var(--fg3)">MENÚ PRINCIPAL</div>')
    items = ["¡Canta!", "Fiesta", "Jukebox", "Estadísticas", "Editor", "Opciones"]
    b.append(f'<nav aria-label="Menú principal" style="{ab(0, 0)}">')
    y = 134
    for i, label in enumerate(items):
        sel = i == 0
        if sel:
            # the selected row grows a little and its text slides in
            b.append(f'<button style="{ab(43, y - 1, 470, 58)} border-radius: 14px; background: var(--s2)">'
                     f'<span style="{ab(26, 20)} {MONO}; font-size: 13px; color: var(--accent-ink)">0{i + 1}</span>'
                     f'<span style="{ab(73, 11)} {DISPLAY}; font-weight: 600; font-size: 28px; letter-spacing: -0.02em">{label}</span></button>')
        else:
            b.append(f'<button style="{ab(48, y, 460, 56)} border-radius: 14px; color: var(--fg2)">'
                     f'<span style="{ab(20, 20)} {MONO}; font-size: 13px; color: var(--fg3)">0{i + 1}</span>'
                     f'<span style="{ab(62, 12)} {DISPLAY}; font-weight: 500; font-size: 28px; letter-spacing: -0.02em">{label}</span></button>')
        y += 60
    b.append(f'<div style="{ab(68, y + 8, 420, 1)} background: var(--div)"></div>')
    y += 20
    for label in ("Acerca de", "Salir"):
        b.append(f'<button style="{ab(48, y, 460, 44)} border-radius: 12px; color: var(--fg3)">'
                 f'<span style="{ab(62, 11)} font-size: 18px">{label}</span></button>')
        y += 48
    b.append('</nav>')
    # right card with the picture of the selected entry
    px, py = 548, 100
    b.append(f'<section style="{ab(px, py, 684, 532)} border-radius: 24px; background: var(--s1)">')
    b.append(f'<h1 style="{ab(44, 58)} margin: 0; {DISPLAY}; font-weight: 700; font-size: 72px; line-height: 1; letter-spacing: -0.035em">¡Canta!</h1>')
    b.append(f'<p style="{ab(44, 158, 440)} margin: 0; font-size: 20px; line-height: 1.45; color: var(--fg2)">Juego rápido: cantar solo o acompañado</p>')
    sx, sy = 44, 290
    b.append(f'<div style="{ab(sx, sy, 596, 200)}" aria-hidden="true">')
    for i in range(4):
        b.append(f'<div style="{ab(0, 30 + i * 40, 596, 1)} background: var(--div)"></div>')
    # empty tracks that fill with colour as the pitch line passes (it sweeps
    # from left to right, then the notes fade and it starts again)
    line_x = 310
    for x, y_, w, col in [(0, 103, 84, P["blue"]), (96, 83, 52, P["blue"]), (160, 63, 112, P["blue"]), (284, 43, 66, P["gold"]),
                          (362, 63, 44, P["blue"]), (418, 103, 100, P["blue"]), (530, 123, 56, P["blue"])]:
        fill = max(0, min(w, line_x - x))
        b.append(f'<div style="{ab(x, y_, w, 14)} border-radius: 7px; overflow: hidden; background: color-mix(in srgb, {col} 22%, transparent)">'
                 + (f'<div style="width: {fill}px; height: 14px; background: {col}"></div>' if fill else '') + '</div>')
    b.append(f'<div style="{ab(line_x - 1, 36, 2, 120)} background: {ACC}"></div>')
    b.append(f'<div style="{ab(line_x - 6, 30, 12, 12)} border-radius: 6px; background: {ACC}"></div>')
    b.append('</div></section>')
    b.append(footer([("↑ ↓", "Navegar"), ("Enter", "Seleccionar"), ("C", "Créditos")]))
    write("Main.dc.html", page("Menú principal", root("\n".join(b))))


# ---------------------------------------------------------------------------
def players():
    b = [header(["¡Canta!", "Jugadores"])]
    b.append(f'<h1 style="{ab(48, 94)} margin: 0; {DISPLAY}; font-weight: 700; font-size: 48px; letter-spacing: -0.03em">¿Quién canta?</h1>')
    b.append(f'<p style="{ab(48, 152)} margin: 0; font-size: 17px; color: var(--fg2)">Elige a cada jugador con ← →, escribe su nombre y su dificultad.</p>')
    # number of players
    b.append(f'<div style="{ab(944, 96, 160, 44)} border-radius: 12px; background: var(--s2); display: flex; align-items: center; justify-content: center; font-size: 15px; color: var(--fg)">Nº de jugadores</div>')
    chev = lambda d, x: f'<svg style="position: absolute; {x}; top: 12px" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0E0F12" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="{d}"></path></svg>'
    b.append(f'<button aria-label="Número de jugadores: 2" style="{ab(1112, 96, 120, 44)} border-radius: 12px; background: {ACC}; color: #0E0F12; display: flex; align-items: center; justify-content: center; font-size: 15px">2'
             + chev("M14.5 6l-6 6 6 6", "left: 6px") + chev("M9.5 6l6 6-6 6", "right: 6px") + '</button>')
    cw, ch = 381, 270
    for i, (name, col, cname, mic, diff) in enumerate((("Manuel", P["blue"], "Azul", "Micrófono 1 · izquierdo", 1),
                                                         ("Lucía", P["mint"], "Verde", "Micrófono 1 · derecho", 2))):
        cx, cy = 48 + i * (cw + 20), 206
        sel = i == 0
        ring = f"box-shadow: 0 0 0 2px var(--line2);" if sel else ""
        b.append(f'<article aria-label="Jugador {i + 1}" style="{ab(cx, cy, cw, ch)} border-radius: 22px; background: var(--s1); {ring}">')
        b.append(f'<div style="{ab(24, 24, 56, 56)} border-radius: 28px; background: {col}; color: #0E0F12; display: flex; align-items: center; justify-content: center; {DISPLAY}; font-weight: 700; font-size: 24px">{name[0]}</div>')
        b.append(f'<label for="p{i + 1}" style="{ab(98, 30)} font-size: 11px; font-weight: 600; letter-spacing: 0.06em; color: var(--fg2)">JUGADOR {i + 1}</label>')
        b.append(f'<input id="p{i + 1}" value="{name}" style="{ab(98, 46, cw - 122, 34)} font: inherit; {DISPLAY}; font-weight: 600; font-size: 22px; color: var(--fg); background: transparent; border: 0; border-bottom: 2px solid {col if sel else "var(--line)"}; outline: none; padding: 0 0 4px 0">')
        b.append(f'<div style="{ab(24, 112)} display: flex; align-items: center; gap: 8px; font-size: 14px; color: var(--fg2)">'
                 f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{col}" stroke-width="2" stroke-linecap="round" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3"></rect><path d="M5 11a7 7 0 0 0 14 0M12 18v3"></path></svg>{mic}</div>')
        b.append(f'<span style="{ab(40, 172)} font-size: 14px; color: var(--fg2)">Color</span>')
        b.append(f'<button style="{ab(120, 160, cw - 144, 40)} border-radius: 12px; background: {col}; color: #0E0F12; font-size: 15px; display: flex; align-items: center; justify-content: center">{cname}'
                 f'<svg style="position: absolute; right: 8px; top: 10px" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0E0F12" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M9.5 6l6 6-6 6"></path></svg></button>')
        b.append(f'<div role="group" aria-label="Dificultad" style="{ab(20, 212, cw - 40, 44)} border-radius: 12px; background: var(--bg); display: flex; gap: 4px; padding: 4px; box-sizing: border-box">')
        for j, d in enumerate(("Fácil", "Medio", "Difícil")):
            on = j == diff
            b.append(f'<button style="flex: 1; border-radius: 10px; text-align: center; font-size: 15px; {"background: var(--s3); color: var(--fg); font-weight: 600" if on else "color: var(--fg2)"}">{d}</button>')
        b.append('</div></article>')
    b.append(footer([("↑ ↓", "Navegar"), ("A–Z", "Escribir nombre"), ("Enter", "Elegir canción"), ("Esc", "Atrás")]))
    write("Players.dc.html", page("Jugadores", root("\n".join(b))))


# ---------------------------------------------------------------------------
def sing():
    LS = 18
    b = []
    # stand-in for the music video
    b.append('''<div aria-hidden="true">
<div style="position: absolute; inset: 0; background: {{v.sky}}"></div>
<div style="position: absolute; left: 860px; top: 120px; width: 260px; height: 260px; border-radius: 130px; background: {{v.sun}}"></div>
<div style="position: absolute; left: -160px; top: 380px; width: 980px; height: 560px; border-radius: 490px; background: {{v.hill1}}"></div>
<div style="position: absolute; left: 520px; top: 420px; width: 980px; height: 560px; border-radius: 490px; background: {{v.hill2}}"></div>
<div style="position: absolute; left: 470px; top: 236px; width: 70px; height: 70px; border-radius: 35px; background: {{v.figure}}"></div>
<div style="position: absolute; left: 440px; top: 300px; width: 130px; height: 260px; border-radius: 60px 60px 0 0; background: {{v.figure}}"></div>
</div>''')
    # progress line + time chip
    b.append(f'<div style="{ab(0, 0, 1280, 4)} background: rgba(14,15,18,0.7)"><div style="width: 38%; height: 4px; background: {ACC}"></div></div>')
    b.append(f'<div style="{ab(1136, 18, 112, 34)} border-radius: 17px; background: rgba(14,15,18,0.92); color: #F2F2EF; {MONO}; font-size: 15px; display: flex; align-items: center; justify-content: center">-02:18</div>')

    shape = [(0, 6, 110), (122, 5, 60), (194, 4, 140), (346, 3, 80, True), (438, 4, 64), (514, 6, 120), (646, 7, 70),
             (740, 5, 150, True), (910, 6, 90), (1012, 4, 140)]
    lanes = [("Manuel", P["blue"], "4.120", 0.8, 92, "¡Genial!", ["hit", "hit", "hit", "hit"]),
             ("Lucía", P["mint"], "3.065", 0.5, 408, None, ["hit", "miss", "hit", "miss"])]
    cursor = 470
    for name, col, score, level, top, bonus, states in lanes:
        b.append(f'<section aria-label="{name}" style="{ab(0, 0)}">')
        # staff lines (no veil behind the notes)
        for i in range(10):
            b.append(f'<div style="{ab(56, top + 10 + i * LS, 1168, 1)} background: rgba(242,242,239,0.18)" aria-hidden="true"></div>')
        for k, n in enumerate(shape):
            x, row, w = n[0], n[1], n[2]
            gold = len(n) > 3
            y = top + 10 + row * LS - 8
            st = states[k] if k < 4 else ("current" if k == 4 else "future")
            if st == "hit":
                bg = P["gold"] if gold else col
            elif st == "miss":
                bg = "rgba(14,15,18,0.85)"
            else:
                bg = "color-mix(in srgb, " + P["gold"] + " 55%, #5E5E5E)" if gold else "#5E5E5E"
            inner = ""
            if st == "current":
                inner = f'<div style="position: absolute; left: 0; top: 0; height: 16px; width: {cursor - x}px; border-radius: 8px; background: {col}"></div>'
            hgt = 16 if st != "miss" else 13
            b.append(f'<div style="{ab(80 + x, y + (16 - hgt) // 2, w, hgt)} border-radius: 8px; overflow: hidden; background: {bg}; {NOTE_SHADOW}" aria-hidden="true">{inner}</div>')
        # row just above the staff: the name in a box of the player's colour
        # at the left end; sing bar and score (soft shadow) at the right end
        rt = top - 32
        ink = "#0E0F12" if col in (P["mint"], P["gold"]) else "#F2F2EF"
        b.append(f'<span style="{ab(56, rt + 2)} height: 28px; padding: 0 10px; border-radius: 8px; background: {col}; color: {ink}; font-size: 17px; font-weight: 600; display: inline-flex; align-items: center">{name}</span>')
        b.append(f'<div style="{ab(1042, rt + 12, 110, 8)} border-radius: 4px; background: rgba(14,15,18,0.55); overflow: hidden" aria-hidden="true"><div style="width: {int(level * 100)}%; height: 8px; background: {col}"></div></div>')
        b.append(f'<span style="{ab(1166, rt + 1)} {MONO}; font-weight: 700; font-size: 24px; color: #F2F2EF; {SHADOW_T}">{score}</span>')
        if bonus:
            b.append(f'<div style="{ab(877, rt + 2, 150, 28)} border-radius: 14px; background: color-mix(in srgb, {ACC} 35%, #0E0F12); border: 1.5px solid {ACC}; box-sizing: border-box; display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 600; color: #F2F2EF">{bonus}</div>')
        b.append('</section>')
    # lyrics: duet bar between the lanes, main bar at the bottom
    def lyrics(y, h, sung, rest, nxt, col, big):
        return (f'<section aria-label="Letra" style="{ab(32, y, 1216, h)} border-radius: 22px; background: #0E0F12; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px">'
                f'<p style="margin: 0; {DISPLAY}; font-weight: 600; font-size: {big}px; letter-spacing: -0.01em"><span style="color: {col}">{sung}</span><span style="color: #F2F2EF">{rest}</span></p>'
                f'<p style="margin: 0; font-size: {big - 12}px; font-weight: 600; color: #8E8E8E">{nxt}</p></section>')
    b.append(lyrics(278, 92, "Bajo las lu", "ces de neón", "bailamos sin pensar en volver", P["blue"], 32))
    b.append(lyrics(596, 104, "Bajo las ", "luces de neón", "bailamos sin pensar en volver", P["mint"], 36))
    extra_vals = ("const bright = (this.props.video ?? 'Vídeo claro') === 'Vídeo claro';\n"
                  "    const extra = bright ? { sky: '#F4A261', sun: '#FFE8A3', hill1: '#E76F51', hill2: '#C4513C', figure: '#2A1E2E' }\n"
                  "      : { sky: '#1B1F2A', sun: '#2C3347', hill1: '#161A23', hill2: '#12151D', figure: '#0B0D12' };")
    html = page("Cantando", root("\n".join(b)).replace("{{v.", "{{extra."), extra_vals=extra_vals,
                props=('{"accent":{"editor":"color","default":"#FF5A36","options":["#FF5A36","#4F9DFF","#2FD39A","#F2F2EF"]},'
                       '"video":{"editor":"enum","options":["Vídeo claro","Vídeo oscuro"],"default":"Vídeo claro"},'
                       '"base":{"editor":"color","default":"#0E0F12","options":["#0E0F12","#14213D","#2A1B3D","#F4F1EA"]},'
                       '"$preview":{"width":1280,"height":720}}'))
    write("Sing.dc.html", html)


# ---------------------------------------------------------------------------
SONG_FOOT = [("↑ ↓", "Navegar"), ("Enter", "Cantar"), ("Espacio", "Parte del dueto"), ("M", "Menú"), ("J", "Buscar"), ("P", "Listas")]


def scores(x, y, vx):
    return (f'<div style="{ab(x, y)} font-size: 15px; color: var(--fg3)">Máximo:</div>'
            f'<div style="{ab(x, y + 28)} font-size: 15px; color: var(--fg3)">Media:</div>'
            f'<div style="{ab(vx - 80, y - 1, 80)} text-align: right; {MONO}; font-size: 16px">8.420</div>'
            f'<div style="{ab(vx - 80, y + 27, 80)} text-align: right; {MONO}; font-size: 16px">6.915</div>')


def roulette():
    b = [header(["Elige la canción"], search=True)]
    b.append('<div aria-label="Canciones">')
    # covers behind, then the one in front with its ring
    b.append(cover(127, 207, 160, *COVERS[3], extra="opacity: 0.45"))
    b.append(cover(990, 207, 160, *COVERS[6], extra="opacity: 0.45"))
    b.append(cover(194, 133, 263, *COVERS[2], extra="opacity: 0.6"))
    b.append(cover(823, 133, 263, *COVERS[1], extra="opacity: 0.6"))
    b.append(cover(490, 104, 300, *COVERS[0]))
    b.append(f'<div style="{ab(482, 96, 316, 316)} border-radius: 25px; border: 3px solid {ACC}; box-sizing: border-box" aria-hidden="true"></div>')
    b.append('</div>')
    b.append(f'<div style="{ab(300, 424, 680)} display: flex; flex-direction: column; align-items: center; text-align: center">'
             f'<h1 style="margin: 0; {DISPLAY}; font-weight: 700; font-size: 34px; letter-spacing: -0.02em; line-height: 38px">Noches de agosto</h1>'
             f'<div style="margin-top: 10px; font-size: 18px; color: var(--fg2)">Carla Brava</div>'
             f'<div style="margin-top: 8px; {MONO}; font-size: 14px; color: var(--fg3)">2021</div>'
             f'<div style="margin-top: 6px; font-size: 15px; color: var(--fg3)">Pop · Español</div>'
             f'<div style="margin-top: 14px; display: flex; gap: 8px">{chip("Vídeo", "video")}{chip("Versión corta", "medley")}</div></div>')
    b.append(scores(1000, 466, 1232))
    b.append(f'<div style="{ab(48, 620)} {MONO}; font-size: 14px; color: var(--fg3)">1 / 9</div>')
    b.append(footer(SONG_FOOT))
    write("SongRoulette.dc.html", page("Selección de canción · ruleta", root("\n".join(b))))


def grid():
    b = [header(["Elige la canción"], search=True)]
    cell, pad, gx, gy = 118, 14, 56, 104
    b.append('<div aria-label="Canciones">')
    sel = 2
    for i in range(14):
        r, c = divmod(i, 5)
        x, y = gx + c * (cell + pad), gy + r * (cell + pad)
        bg, fg = COVERS[i % len(COVERS)]
        if i == sel:
            continue
        b.append(f'<button aria-label="Canción {i + 1}" style="{ab(x, y, cell, cell)} border-radius: 7px">{cover(0, 0, cell, bg, fg, extra="opacity: 0.8")}</button>')
    x, y = gx + sel * (cell + pad) - 11, gy - 11
    bg, fg = COVERS[sel % len(COVERS)]
    b.append(f'<button aria-label="Luces de neón" style="{ab(x, y, cell + 22, cell + 22)} border-radius: 8px">{cover(0, 0, cell + 22, bg, fg)}</button>')
    b.append('</div>')
    px, py, pw, ph = 730, 96, 502, 540
    b.append(f'<section style="{ab(px, py, pw, ph)} border-radius: 24px; background: var(--s1)">')
    b.append(cover(28, 28, 232, bg, fg))
    b.append(f'<div style="{ab(284, 40, pw - 312)} display: flex; flex-direction: column">'
             f'<h1 style="margin: 0; {DISPLAY}; font-weight: 700; font-size: 26px; letter-spacing: -0.02em; line-height: 30px">Luces de neón</h1>'
             f'<div style="margin-top: 10px; font-size: 18px; color: var(--fg2)">Marea Alta</div>'
             f'<div style="margin-top: 8px; {MONO}; font-size: 14px; color: var(--fg3)">2019</div>'
             f'<div style="margin-top: 6px; font-size: 15px; color: var(--fg3)">Pop · Español</div></div>')
    b.append(f'<div style="{ab(28, 282)} display: flex; gap: 8px">{chip("Vídeo", "video")}{chip("Versión corta", "medley")}</div>')
    b.append(f'<div style="{ab(28, ph - 136, pw - 56, 1)} background: var(--div)"></div>')
    b.append(scores(28, ph - 86, 260))
    b.append(f'<div style="{ab(pw - 80, ph - 40, 52)} text-align: right; {MONO}; font-size: 14px; color: var(--fg3)">3 / 9</div>')
    b.append('</section>')
    b.append(footer(SONG_FOOT))
    write("SongGrid.dc.html", page("Selección de canción · cuadrícula", root("\n".join(b))))


def song_list():
    b = [header(["Elige la canción"], search=True)]
    songs = [("Noches de agosto", "Carla Brava", "2021"), ("Papel mojado", "Doble Fondo", "2014"),
             ("Papel mojado (Dueto)", "Doble Fondo", "2014"), ("Volver a empezar", "Elena Vidal", "2020"),
             ("Tormenta", "La Brújula", "2012"), ("Kilómetro cero", "Los Satélites", "2016"),
             ("Una canción con un título larguísimo que no cabe en ningún…", "Los Satélites del Norte y la Orquesta Imposible", "2014"),
             ("Luces de neón", "Marea Alta", "2019")]
    b.append('<div aria-label="Canciones">')
    for i, (t, a_, y_) in enumerate(songs):
        y = 100 + i * 64
        sel = i == 0
        bg, fg = COVERS[i % len(COVERS)]
        long_ = len(t) > 40
        b.append(f'<button style="{ab(48, y, 560, 60)} border-radius: 14px; {"background: var(--s2)" if sel else ""}">'
                 + cover(10, 8, 44, bg, fg, radius=3, extra="" if sel else "opacity: 0.75")
                 + f'<span style="{ab(70, 10, 380)} font-size: {15 if long_ else 18}px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: {"var(--fg)" if sel else "var(--fg2)"}">{t}</span>'
                 f'<span style="{ab(70, 33, 380)} font-size: 15px; color: var(--fg3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{a_}</span>'
                 f'<span style="{ab(484, 20, 60)} text-align: right; {MONO}; font-size: 14px; color: var(--fg3)">({y_})</span></button>')
    b.append('</div>')
    px, py, pw, ph = 632, 96, 600, 540
    bg, fg = COVERS[0]
    b.append(f'<section style="{ab(px, py, pw, ph)} border-radius: 22px; background: var(--s1)">')
    b.append(cover(28, 28, 280, bg, fg))
    b.append(f'<div style="{ab(332, 32, pw - 360)} display: flex; flex-direction: column">'
             f'<h1 style="margin: 0; {DISPLAY}; font-weight: 700; font-size: 26px; letter-spacing: -0.02em; line-height: 30px">Noches de agosto</h1>'
             f'<div style="margin-top: 10px; font-size: 18px; color: var(--fg2)">Carla Brava</div>'
             f'<div style="margin-top: 8px; {MONO}; font-size: 14px; color: var(--fg3)">2021</div>'
             f'<div style="margin-top: 6px; font-size: 15px; color: var(--fg3)">Pop · Español</div></div>')
    b.append(f'<div style="{ab(28, 330)} display: flex; gap: 8px">{chip("Vídeo", "video")}</div>')
    b.append(scores(340, ph - 104, pw - 28))
    b.append(f'<div style="{ab(28, ph - 40)} {MONO}; font-size: 14px; color: var(--fg3)">1 / 9</div>')
    b.append('</section>')
    b.append(footer(SONG_FOOT))
    write("SongSelect.dc.html", page("Selección de canción · lista", root("\n".join(b))))


# ---------------------------------------------------------------------------
ICONS = {
    "gear": '<circle cx="12" cy="12" r="3"></circle><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"></path><circle cx="12" cy="12" r="7"></circle>',
    "monitor": '<rect x="3" y="4" width="18" height="12" rx="2"></rect><path d="M12 16v4M8 20h8"></path>',
    "speaker": '<path d="M4 9h4l5-4v14l-5-4H4z"></path><path d="M17 9a4 4 0 0 1 0 6"></path>',
    "keyboard": '<rect x="2" y="6" width="20" height="12" rx="2"></rect><path d="M6 10h1M10 10h1M14 10h1M18 10h1M7 14h10"></path>',
    "lyric": '<path d="M5 6h14M12 6v13"></path>',
    "palette": '<path d="M12 3a9 9 0 1 0 0 18c1.5 0 2-1 2-2s-1-2 0-3 2-1 3-1a4 4 0 0 0 4-4c0-4-4-8-9-8z"></path><circle cx="8" cy="10" r="1"></circle><circle cx="12" cy="7" r="1"></circle><circle cx="16" cy="10" r="1"></circle>',
    "mic": '<rect x="9" y="3" width="6" height="11" rx="3"></rect><path d="M5 11a7 7 0 0 0 14 0M12 18v3"></path>',
    "sliders": '<path d="M4 7h10M18 7h2M4 17h4M12 17h8"></path><circle cx="16" cy="7" r="2"></circle><circle cx="10" cy="17" r="2"></circle>',
    "globe": '<circle cx="12" cy="12" r="9"></circle><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"></path>',
    "camera": '<rect x="3" y="7" width="18" height="13" rx="2"></rect><path d="M8 7l2-3h4l2 3"></path><circle cx="12" cy="13" r="3.5"></circle>',
    "play": '<path d="M7 4.5v15l12-7.5z"></path>',
    "back": '<path d="M19 12H5M11 6l-6 6 6 6"></path>',
}


def options_grid():
    b = [header(["Opciones"])]
    b.append(f'<h1 style="{ab(48, 96)} margin: 0; {DISPLAY}; font-weight: 700; font-size: 52px; letter-spacing: -0.03em">Opciones</h1>')
    b.append(f'<p style="{ab(48, 162)} margin: 0; font-size: 18px; color: var(--fg2)">Cambiar los ajustes de vídeo</p>')
    tiles = [("Juego", "gear"), ("Gráficos", "monitor"), ("Sonido", "speaker"), ("Input", "keyboard"), ("Letras", "lyric"),
             ("Apariencia", "palette"), ("Micrófonos", "mic"), ("Avanzado", "sliders"), ("Internet", "globe"),
             ("Cámara", "camera"), ("Jukebox", "play"), ("Atrás", "back")]
    tw, th = 284, 124
    b.append('<nav aria-label="Opciones">')
    for i, (label, ic) in enumerate(tiles):
        x, y = 48 + (i % 4) * (tw + 16), 216 + (i // 4) * (th + 12)
        sel = i == 1
        if sel:
            # selected: grows a little, accent ring; the icon grows, takes the
            # accent colour and swings
            g = 1.04
            x2, y2, w2, h2 = x - tw * (g - 1) / 2, y - th * (g - 1) / 2, tw * g, th * g
            b.append(f'<button style="{ab(round(x2), round(y2), round(w2), round(h2))} border-radius: 18px; background: var(--s1); box-shadow: inset 0 0 0 2px {ACC}">'
                     f'<svg style="{ab(18, 18)} transform: rotate(-8deg)" width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="{ACC}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[ic]}</svg>'
                     f'<span style="{ab(round(w2) - 50, 24, 30)} text-align: right; {MONO}; font-size: 14px; color: var(--accent-ink)">{i + 1:02d}</span>'
                     f'<span style="{ab(23, round(h2) - 48)} {DISPLAY}; font-weight: 600; font-size: 22px">{label}</span></button>')
        else:
            b.append(f'<button style="{ab(x, y, tw, th)} border-radius: 18px; background: var(--s1)">'
                     f'<svg style="{ab(22, 22)}" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="var(--fg2)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[ic]}</svg>'
                     f'<span style="{ab(tw - 52, 24, 30)} text-align: right; {MONO}; font-size: 14px; color: var(--fg3)">{i + 1:02d}</span>'
                     f'<span style="{ab(22, th - 46)} {DISPLAY}; font-weight: 500; font-size: 22px; color: var(--fg2)">{label}</span></button>')
    b.append('</nav>')
    b.append(footer([("↑ ↓", "Navegar"), ("Enter", "Abrir"), ("Esc", "Atrás")]))
    write("OptionsGrid.dc.html", page("Opciones", root("\n".join(b))))


def loading():
    b = []
    mx, my = 538, 228
    notes = [(0, 44, 30, P["blue"]), (38, 30, 26, P["blue"]), (72, 16, 42, P["gold"]), (122, 30, 30, P["blue"]), (160, 42, 44, P["blue"])]
    line_x = mx + 100
    b.append(f'<div aria-hidden="true">')
    for x, y, w, col in notes:
        # empty track, filled with colour up to the marker (like a sung note)
        fill = max(0, min(w, line_x - (mx + x)))
        b.append(f'<div style="{ab(mx + x, my + y, w, 10)} border-radius: 5px; overflow: hidden; background: color-mix(in srgb, {col} 22%, transparent)">'
                 + (f'<div style="width: {fill}px; height: 10px; background: {col}"></div>' if fill else '') + '</div>')
    b.append(f'<div style="{ab(line_x - 1, my, 2, 64)} background: {ACC}"></div>')
    b.append(f'<div style="{ab(line_x - 5, my + 16, 10, 10)} border-radius: 5px; background: {ACC}"></div>')
    b.append('</div>')
    b.append(f'<h1 style="{ab(0, 312, 1280)} margin: 0; text-align: center; {DISPLAY}; font-weight: 700; font-size: 48px; letter-spacing: -0.03em">SuperStar</h1>')
    b.append(f'<p style="{ab(0, 414, 1280)} margin: 0; text-align: center; font-size: 16px; color: var(--fg2)">Leyendo canciones · 812 de 1.240</p>')
    b.append(f'<div style="{ab(460, 452, 360, 4)} border-radius: 2px; background: color-mix(in srgb, {ACC} 25%, transparent)" role="progressbar" aria-label="Cargando canciones" aria-valuenow="65" aria-valuemin="0" aria-valuemax="100"><div style="width: 65%; height: 4px; border-radius: 2px; background: {ACC}"></div></div>')
    b.append(f'<div style="{ab(1032, 668, 200)} text-align: right; font-size: 13px; color: var(--fg3)">SuperStar 2026.10</div>')
    write("Loading.dc.html", page("Pantalla de carga", root("\n".join(b))))


main_menu()
players()
sing()
roulette()
grid()
song_list()
options_grid()
loading()

# the remaining artboards keep their design: only the new name and the mic
for name in ("Options.dc.html", "Score.dc.html"):
    p = os.path.join(OUT, name)
    s = open(p, encoding="utf-8").read()
    s = s.replace('<div style="width: 12px; height: 12px; border-radius: 3px; background: {{accent}}"></div>',
                  MIC.replace('width="24" height="24"', 'width="22" height="22"'))
    s = re.sub(r'(<span style="[^"]*">)Karaoke(</span>)', r'\1SuperStar\2', s, count=1)
    s = s.replace("UltraStar Core", "SuperStar")
    open(p, "w", encoding="utf-8").write(s)
    print("renamed in", name)

p = os.path.join(OUT, "System.dc.html")
s = open(p, encoding="utf-8").read()
s = s.replace("Todo plano: sin degradados ni sombras.",
              "Superficies planas sobre un fondo con un degradado suave que se mueve despacio.")
s = s.replace("box-shadow: 0 0 0 2px #0E0F12, 0 0 0 4px color-mix(in srgb, #F2F2EF 80%, transparent);",
              "box-shadow: 0 3px 8px rgba(0,0,0,0.35);")
s = s.replace("Sobre el vídeo, cada nota lleva un aro oscuro y otro claro: siempre destaca uno de los dos, sea cual sea el color de detrás.",
              "Las notas no llevan borde: una sombra suave las separa del vídeo. Los nombres y puntos de cada jugador van encima de su pentagrama, sin fondo, también con sombra.")
open(p, "w", encoding="utf-8").write(s)
print("updated System.dc.html")
