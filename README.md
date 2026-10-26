# Bomb Diffusal

A two-player cooperative "defuse the bomb" game for the Raspberry Pi, in the
spirit of *Keep Talking and Nobody Explodes*. One player sees the screen; the
other holds the manual and the hardware. Neither can win alone.

- **Player 1** - Screen, mouse, keyboard, and the **Decoder Cards**.
- **Player 2** - two RGB LEDs, four coloured buttons, a rotary encoder, and the
  **Field Manual**.

Each game randomly picks **6 of the 10 puzzles** and presents them in a random
order behind a **30-minute** countdown shown at the top of the screen at all
times. Disarm all six and the team wins; let the timer hit zero and it's boom.

This repository contains all three deliverables from the brief:

1. **The two manuals** - [`docs/player1_decoder_cards.md`](docs/player1_decoder_cards.md)
   and [`docs/player2_manual.md`](docs/player2_manual.md) (generated, with images).
2. **The parts list** - [`docs/parts_list.md`](docs/parts_list.md) (components + GPIO wiring).
3. **The program** - the `bomb/` Python package.

## Quick start (desktop)

You can play and develop the whole game on an ordinary computer - no Pi or
wiring needed. When there is no GPIO, Player 2's LEDs/buttons/encoder are shown
in an on-screen panel and driven by the keyboard and mouse.

```bash
pip install -r requirements.txt
python -m bomb            # add --mock to force desktop mode, --fullscreen for kiosk
```

**Player 1 controls** (real inputs): mouse + keyboard (type answers, arrow keys,
Enter, Backspace).
**Player 2 controls** (desktop stand-ins, shown in the right-hand panel):

| Hardware | Desktop key |
| --- | --- |
| Red / Yellow / Green / Blue button | `R` / `Y` / `G` / `B` |
| Rotary encoder | mouse wheel, or `,` (CCW) and `.` (CW) |

Press `Space` to arm the bomb and to advance between modules; `Esc` quits.

## Running on the Raspberry Pi

1. Flash Raspberry Pi OS (with desktop) and boot to the desktop.
2. Wire the electronics per [`docs/parts_list.md`](docs/parts_list.md).
3. Install dependencies, including the Pi-only ones:
   ```bash
   pip install -r requirements.txt
   pip install gpiozero lgpio          # real GPIO backend
   ```
4. Run it (fullscreen kiosk):
   ```bash
   python -m bomb --fullscreen
   ```

The program auto-detects the Pi: if `gpiozero` and a real pin factory are
available it drives the physical LEDs/buttons/encoder; otherwise it falls back
to the desktop mock. To launch automatically on boot, add a `.desktop` file to
`~/.config/autostart/` running `python -m bomb --fullscreen`.

## Hardware test / bring-up

Before relying on the real bomb, run the bench-test tool to confirm every piece
of Player 2's hardware works and to step through all ten puzzles **in order**
(not the random six):

```bash
python tools/hardware_test.py            # auto-detect Pi GPIO, else --mock
```

It runs in two parts:

1. **Self-test** - cycles each RGB LED through red/green/blue/white (so you can
   catch swapped colour channels), lights each button as you press it, reads the
   rotary encoder in both directions, and plays the four button tones.
2. **Puzzles 1-10** - each puzzle in fixed order, with **no bomb timer** and no
   way to lose. Use the on-screen keys to move around:

   | Key | Action |
   | --- | --- |
   | `Space` / `N` | next step / puzzle |
   | `B` / `P` | previous |
   | `R` | restart the current step/puzzle |
   | `S` | force-solve the current puzzle (to verify the solve path) |
   | `T` | (audio step) replay the tones |
   | `Esc` | quit |

## The ten puzzles

| # | Module | Player 1 (screen) | Player 2 (hardware + manual) |
| --- | --- | --- | --- |
| 1 | Color Mixing | three **unlabeled** sliders | sees LED A (target) + LED B (yours) |
| 2 | Morse Code | types the decoded word (Morse card) | reads the LED-A blinks |
| 3 | Simon with a Twist | decodes colours with the Simon card | presses the translated buttons |
| 4 | Invisible Maze | arrow-keys a dot through hidden walls | reads the maze from the manual |
| 5 | Navigation | reads the directions, picks a landmark | traces the route on the map |
| 6 | Turn on the LED | clicks input switches (blank gates) | circuit diagram names each gate |
| 7 | Rhythm Lock | sees the note names appear | replays the rhythm on the buttons |
| 8 | Symbols Lock | clicks the odd-one-out symbol | trait table in the manual |
| 9 | Glyph Addition | reads the symbol equation, types total | symbol-value table in the manual |
| 10 | Rotation Lock | sees the two symbols | spins the encoder to match them |

## Keeping the manuals in sync

The manuals are **generated** from the same data the game uses
(`bomb/puzzle_data.py` and `bomb/glyphs.py`), so paper and bomb can never drift.
After changing any puzzle content, regenerate:

```bash
python tools/generate_manuals.py
```

Then export the two `docs/*.md` files to PDF and print them (the images live in
`docs/assets/`).

## Project layout

```
bomb/                     the game (run with  python -m bomb)
  __main__.py             entry point / main loop
  config.py               screen, timing, colours, GPIO pin map
  puzzle_data.py          morse, simon, mazes, nav routes, circuits, rhythms
  glyphs.py               vector-drawn symbols + their traits/values
  hardware.py             GPIO (gpiozero) or desktop keyboard/mouse mock
  audio.py                tone synthesis (no numpy)
  ui.py                   fonts, timer bar, LED drawing, Player-2 panel
  game.py                 state machine: title/intro/play/solved/win/lose
  puzzles/                one module per puzzle (common Puzzle base class)
tools/
  generate_manuals.py     renders docs/* and docs/assets/* from the data above
docs/
  parts_list.md           components + wiring
  player1_decoder_cards.md
  player2_manual.md
  assets/                 generated PNGs (mazes, map, circuits, symbols)
```

## Testing

The game runs headless for CI/smoke tests with SDL's dummy drivers:

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m bomb --mock   # (Ctrl-C to stop)
```

All ten puzzles, the symbol-puzzle generator, and the full title-to-win flow
have been verified this way.
