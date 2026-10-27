#!/usr/bin/env python3
"""Run the game in a virtual display and take screenshots along a key path.

usage: shoot.py <outdir> <step>...   step = key:<xdotool keys> | wait:<seconds> | shot:<name>
"""
import os
import shutil
import subprocess
import sys
import time

GAME = "/home/claude/usdx/game/ultrastardx"
HOME = "/tmp/usdxhome"
DISPLAY = ":77"


def write_config(theme="Karaoke", skin="Negro", songmenu="Roulette", players="1", extra="", res="1280x720", fullscreen="Off"):
    cfgdir = "/home/claude/usdx/game"
    os.makedirs(cfgdir, exist_ok=True)
    with open(os.path.join(cfgdir, "config.ini"), "w") as f:
        f.write(f"""[Game]
Language=Spanish
SongMenu={songmenu}
Players={players}
Tabs=Off
[Graphics]
Resolution={res}
ResolutionFullscreen={res}
FullScreen={fullscreen}
VisualizerBackground=Off
[Themes]
Theme={theme}
Skin={skin}
[Sound]
PreviewVolume=0
[Directories]
SongDir1=/tmp/usdxtest/songs
{extra}
""")


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    opts = {}
    steps = []
    for a in sys.argv[2:]:
        if a.startswith("cfg:"):
            k, v = a[4:].split("=", 1)
            opts[k] = v
        else:
            steps.append(a)
    scr = opts.pop("screen", opts.get("res", "1280x720"))
    write_config(**opts)
    xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", scr + "x24", "-nolisten", "tcp"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    env = dict(os.environ, DISPLAY=DISPLAY, HOME=HOME, SDL_AUDIODRIVER="dummy", LIBGL_ALWAYS_SOFTWARE="1")
    log = open(os.path.join(out, "game.log"), "w")
    game = subprocess.Popen([GAME], env=env, stdout=log, stderr=subprocess.STDOUT)
    try:
        time.sleep(float(os.environ.get("SHOOT_START", "8")))
        for st in steps:
            kind, _, arg = st.partition(":")
            if kind == "key":
                for k in arg.split():
                    subprocess.run(["xdotool", "key", "--clearmodifiers", k], env=env)
                    time.sleep(0.6)
            elif kind == "wait":
                time.sleep(float(arg))
            elif kind == "shot":
                subprocess.run(["import", "-display", DISPLAY, "-window", "root",
                                os.path.join(out, arg + ".png")], env=env)
            elif kind == "move":
                x, y = arg.split(",")
                subprocess.run(["xdotool", "mousemove", x, y], env=env)
            elif kind == "click":
                subprocess.run(["xdotool", "click", "1"], env=env)
            elif kind == "type":
                subprocess.run(["xdotool", "type", "--delay", "120", arg], env=env)
            if game.poll() is not None:
                print("game exited early, code", game.returncode)
                break
    finally:
        game.terminate()
        try:
            game.wait(5)
        except subprocess.TimeoutExpired:
            game.kill()
        xvfb.terminate()
    errlog = "/home/claude/usdx/game/Error.log"
    if os.path.exists(errlog):
        shutil.copy(errlog, os.path.join(out, "Error.log"))


if __name__ == "__main__":
    main()
