# Bomb Diffusal - Parts List & Wiring

Parts to build one "bomb". Player 1 drives the screen with a mouse and keyboard;
all of the electronics below belong to **Player 2**.

## Core computer & Player 1 station

| # | Part | Notes |
| --- | --- | --- |
| 1 | Raspberry Pi 4 or 5 (2 GB+) | Runs the game in pygame. A Pi 400 works too. |
| 1 | microSD card (16 GB+) | Raspberry Pi OS (with desktop). |
| 1 | USB-C power supply | Official PSU recommended (steady 5 V/3 A+). |
| 1 | Monitor / display | HDMI monitor or the official 7" touchscreen. This is **Player 1's** screen. |
| 1 | USB keyboard | Player 1 input (typing answers, arrow keys). |
| 1 | USB mouse | Player 1 input (sliders, clicking). |

## Player 2 electronics

| # | Part | Notes |
| --- | --- | --- |
| 2 | RGB LED, common-cathode | "LED A" (target) and "LED B" (team). Common-anode also OK - set `LED_COMMON_ANODE = True` in `bomb/config.py`. |
| 6 | Resistor, 220-330 Ω | One per LED colour channel (2 LEDs x 3 channels). |
| 4 | Momentary push button | Colour the caps **Red, Yellow, Green, Blue**. Wired to GND; the Pi uses internal pull-ups. |
| 1 | Rotary encoder (KY-040 or bare EC11) | For the Rotation Lock puzzle. |
| 1 | Speaker **or** passive buzzer | Rhythm/Morse audio. Easiest: a small USB or 3.5 mm powered speaker. A piezo buzzer on GPIO 12 is a cheaper fallback. |
| 1 | Half-size breadboard or protoboard | Prototyping. Solder to protoboard for a durable build. |
| 1 | GPIO breakout / T-Cobbler + ribbon | Optional but makes wiring tidy. |
| ~30 | Jumper wires (M-M, M-F) | Connections. |

## Enclosure & extras

| # | Part | Notes |
| --- | --- | --- |
| 1 | Project enclosure / box | The "bomb" body. Cut holes for LEDs, buttons, encoder. |
| - | Standoffs, screws, hot glue | Mounting. |
| 1 set | **Printed manuals** | `docs/player1_decoder_cards.md` and `docs/player2_manual.md`, exported to PDF and printed. |
| 1 | **Printed ruler + protractor** on transparency | For the Navigation puzzle. The ruler scale **must match** the map's 1-mile scale bar. _[PLACEHOLDER: lay out and print on clear film.]_ |

## GPIO wiring (BCM numbering)

These are the pins the program expects. They are defined once in
`bomb/config.py` (`PINS`); change them there if you wire it differently.

| Signal | BCM pin | Connect to |
| --- | --- | --- |
| LED A - Red | GPIO 17 | 220-330 Ω -> LED A red leg |
| LED A - Green | GPIO 27 | 220-330 Ω -> LED A green leg |
| LED A - Blue | GPIO 22 | 220-330 Ω -> LED A blue leg |
| LED B - Red | GPIO 5 | 220-330 Ω -> LED B red leg |
| LED B - Green | GPIO 6 | 220-330 Ω -> LED B green leg |
| LED B - Blue | GPIO 13 | 220-330 Ω -> LED B blue leg |
| Button Red | GPIO 16 | Button -> GND |
| Button Yellow | GPIO 20 | Button -> GND |
| Button Green | GPIO 21 | Button -> GND |
| Button Blue | GPIO 26 | Button -> GND |
| Encoder CLK (A) | GPIO 23 | KY-040 CLK |
| Encoder DT (B) | GPIO 24 | KY-040 DT |
| Encoder SW | GPIO 25 | KY-040 SW (push, optional) |
| Buzzer (optional) | GPIO 12 | Piezo buzzer + -> GND |
| LED cathodes | GND | Common-cathode leg of each RGB LED |
| KY-040 + / GND | 3V3 / GND | Encoder power |

**Wiring notes**

- Common-cathode RGB LEDs: the longest leg goes to **GND**, each colour leg
  goes through its resistor to the listed GPIO. For common-anode LEDs, the
  common leg goes to **3V3** and you must set `LED_COMMON_ANODE = True`.
- Buttons use the Pi's **internal pull-ups** (configured in software), so each
  button only needs one leg to its GPIO and the other to **GND** - no external
  resistor required.
- The KY-040 board already has pull-ups; a bare EC11 encoder needs them (the Pi's
  internal pull-ups are used in software, so a bare encoder works directly).
- Keep LED-A and LED-B physically apart and labelled on the enclosure so Player 2
  can tell "target" (A) from "team" (B) in the Color Mixing puzzle.

## Build order (matches the activity brief)

1. **Manuals first.** Print `player1_decoder_cards.md` and `player2_manual.md`
   (regenerate them with `python tools/generate_manuals.py` if you change any
   puzzle data). Add the ruler/protractor transparency.
2. **Parts list / wiring.** Gather the parts above and wire per the table.
3. **Program.** Install and run (see the top-level `README.md`).
