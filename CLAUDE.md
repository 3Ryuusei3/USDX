# SuperStar — project context

Fork of UltraStar Deluxe (Free Pascal + SDL2 + OpenGL), restyled and renamed to
**SuperStar** (formerly UltraStar Core). It is played on an M3 Mac at 16:9. Read this first; it saves
re-discovering the code.

## Where things live

- Repo on the Mac: `~/Downloads/Karaoke/USDX`, branch `master`. The songs are on
  an external disk ("Todo").
- Install on the Mac: `bash ~/Downloads/Karaoke/actualizar-karaoke.sh ~/Downloads/Karaoke/USDX`.
  This runs `make macos-standalone-app`, then copies the result to
  `SuperStar.app` in /Applications or ~/Applications and signs it.
- The theme is called **Karaoke** (`game/themes/Karaoke.ini` + `game/themes/Karaoke/`).
  - It is fully generated. Never hand-edit the ini or the PNGs; change the
    Python and rebuild.
  - Skins: Negro, AzulNoche, Berenjena, Hueso.
- Design canvas (claude.ai artifact "Karaoke — rediseño",
  https://claude.ai/artifact/PKqP4DQtMu4qKkppRTcyEb). It has one artboard per
  screen: Main, Players, SongSelect (list), SongRoulette, SongGrid (chessboard),
  Sing, Score, Options (microphones page), OptionsGrid, Loading, System.
  - Most artboards are written by `tools/theme-karaoke/gen_design.py <project dir>`,
    which copies the game's coordinates. Read the canvas files first: the
    script needs the existing `Main.dc.html` for its theme helper.
  - When a screen changes, update its artboard too.

## Theme generator (`tools/theme-karaoke/`)

```
python3 tools/theme-karaoke/build_theme.py      # writes Karaoke.ini, skins, PNGs
```

- `palette.py`: colour tokens per skin (Bg, Surface, Surface2/3, Text, Text2,
  Text3, Accent, AccentText, Divider, Scrim, ScrimText, P1..P6 + Dark, Gold,
  NoteBlue…).
- `assets.py`: PIL textures (SCALE 2, supersampling 4, premultiplied
  downsampling). Provides panel, pill, circle, icon(key, size), chip, keycap,
  notes (soft shadow, no outline), tinted, rect, transparent.
- `screens.py`: hand layouts of every screen.
  - `Screen` helper: header, footer, panel, static, icon, text.
  - Layout functions: main, name (player cards), song_common, song_roulette,
    song_chessboard, song_list, sing, score, options, options_sub, popups,
    loading.
  - A generic pass at the end handles the rest.
  - Layout constants: W=1280, H=720, M=48 (side margin), FOOT_Y footer line.
- `build_theme.py`: Builder, restyle_all, write_skins, gradient_bg (the moving
  gradient background `K_bg`, `[*Background] Motion=1`).
- `inifile.py`: case-insensitive ini sections.

## Engine extensions (all theme-gated: other themes behave as before)

- **Display**
  - SetRenderSize with letterbox (`KeepAspect`); UpdateViewMetrics;
    WindowToView for the mouse.
  - HiDPI DrawScale.
- **Texts and textures**
  - `TText.MinSize`: shrinks the text, then cuts it with an ellipsis; LineCount.
  - Text `Shadow=<px>`: soft dark shadow (UText.FontShadow, eight faint
    copies in two rings). The score text in USingScores uses it too.
  - `TTexture.Rot`: rotation around the centre, in radians (URenderer_OpenGL
    DrawTexture).
- **Buttons** (`UMenuButton`)
  - Colour easing; `SelectScale` grows the selected button; `DAlpha` fades the
    deselected ones; SelProg.
  - Animated icon: theme keys `IconTex/IconX/IconY/IconW/IconH/IconColor/IconDColor/IconScale/IconSpin/IconWobble`.
  - `TextDX`: the texts of the selected button slide right.
- **Select slides** (`UMenuSelectSlide`): colour easing, value slide-in, DAlpha,
  STUColor.
  - `Font`/`Style` set the label and value font (the default was family 0).
  - `ArrowTint=1` tints the arrows, which are white chevrons, in the value's
    colour.
- **Background** (`UMenuBackgroundTexture`): `Motion=1` makes a 1.3× image drift.
- **Song menu** (`UScreenSong`, `UCoverLoader`)
  - Chessboard layout: a 5×4 grid, then a wide card with a 232 px cover, the
    details beside it, the features and duet parts below, and the scores at
    the bottom.
  - Scores are hidden for duets and songs without scores.
  - Covers load asynchronously: a background thread plus an LRU texture cache
    (512 px, 240 entries).
  - `[Song<Mode>CoverShape] Square=1 Radius=57`: covers are cut to a square with
    rounded corners (radius in 1/1000 of the side).
  - Wrap-around navigation (ScrollListsTo).
  - Details block (Title/Artist/Year/TextInfo); icons flowed one after another
    (`[Song<Mode>Icons] Flow/Gap`).
  - List mode has its own Detail* texts.
  - The change sound plays only on the first key press (`KeyIsRepeat`, set in
    UMain from SDL `_repeat`).
- **Name screen** (`UScreenName`): player cards (`[NameCards]`), DrawCards,
  SwitchPlayer, MicLabel.
- **Main menu** (`UScreenMain`): one preview picture per entry (`MainPreview<N>Static<M>`).
  - The pieces fade and slide in on change (AnimatePreview).
  - Then they keep moving with the static keys
    `IdleDX/DY/DW/DH/Scale/Rot/Alpha/Period/Phase/Wave`.
    - Wave 0 is a sine.
    - Wave 1 is a smooth back and forth.
    - Wave 2 is a sweep: `IdleStart`/`IdleDur` are fractions of the period,
      `IdleFade` fades out from that fraction on, and `IdleCrop` cuts the
      texture instead of squeezing it.
    - The ¡Canta! preview uses Wave 2: the pitch line sweeps and each note
      fills as it passes.
- **Sing**
  - `UDraw.SingDrawLanes` draws, for each lane in use, an optional veil
    (`LaneAlpha`) and the HUD texture (`HudTex/HudW/HudX/HudY/HudH/HudAlpha`),
    placed relative to the lane's top-left corner.
  - Also NoteScale, NoteCapScale, MissScale, LineAlpha, LanePad3.
  - `[SingLineBonus]` sizes the line bonus badge; it is centred on
    `Sing<P>Static2.X`, with Y relative to it.
  - Karaoke layout:
    - Lanes for 1 and 2 players are at y 92 and 408 (LS 18).
    - Each player's row sits just above its staff.
    - At the left is the name in a box of the player's colour. The game sizes
      the box to the name (`[SingNoteArea] NameBoxPad`, FitNameBox in
      UScreenSingView) and picks dark or light text.
    - At the right are the sing bar and the score (`Shadow=3`); the line bonus
      badge sits left of the bar and the oscilloscope left of that.
    - The duet lyrics bar is between the lanes; the main lyrics bar is at y 596
      with H 104.
- **Loading screen** (`UScreenLoading`): status in words (`LOADING_*` language
  keys).
  - `[LoadingMark] Notes=2,3,4,5,6 Line=7 Dot=8 Texts=1,0` gives the static
    and text indices.
  - The pitch line sweeps over the note bars; the
    texts fade in.
  - The bars are dim tracks that fill with colour from the left as the line passes (fill overlays, TexX2 crop), then fade out and the pass starts again.
  - It only redraws when the loader reports progress (at most every 30 ms).
- **Name**: window title and Info.plist say "SuperStar".
- **Debug FPS** (UDisplay.DrawDebugInformation): just the number, top right,
  JetBrains Mono with a shadow.

## Build and test (Linux container)

```
cd usdx && make                          # binary: game/ultrastardx
python3 tools/theme-karaoke/shoot.py <outdir> [cfg:key=val] steps...
```

- `shoot.py` runs the game under Xvfb.
  - `cfg:` keys: theme, skin, songmenu (Roulette|Chessboard|List), players,
    res, fullscreen, screen.
  - Steps: `wait:s`, `key:<xdotool keys>`, `shot:name`, `type:text`,
    `move:x,y`, `click`.
  - Test songs are in `/tmp/usdxtest/songs`. They include a duet and a song
    with a very long title.
- Software GL shows a popup at start, so the first step is `key:Return`.
- Typical path to the song menu: `wait:8 key:Return wait:1.5 key:Return wait:2 key:Return wait:4`.
  - The next `key:Return` starts a song, and one more dismisses the "no
    microphone" popup.
  - `key:o` in the main menu opens the options.
- `sheet.py <dir> a b c d` makes a contact sheet.

## FPC gotchas

- Fields must be declared before methods in a class section.
- Add `sdl2` to `uses` for SDL_GetTicks.
- A set constructor can't hold values above 255.
- Write a middle dot as `UTF8Encode(WideChar($B7))`.
- TRenderer.LoadTexture(Data,…) is protected: use the cracker class
  `TRendererAccess`.

## Mac delivery

- The session reaches `~/Downloads/Karaoke` through the device bridge.
- Deliver changes with `git apply` (a patch made with `git diff`) and leave
  them uncommitted.
  - **Never commit, amend or push in the Mac repo: the user commits himself.**
