#!/usr/bin/env python3
"""Hardware test / bring-up tool for the Bomb Diffusal build.

Run it on the Raspberry Pi (or any desktop, with --mock) to make sure every
piece of Player 2's hardware works, then walk through all ten puzzles IN ORDER
so you can confirm each one reacts correctly on real hardware.

    python tools/hardware_test.py            # auto-detect Pi GPIO, else mock
    python tools/hardware_test.py --mock     # force desktop keyboard/mouse mock

It has two parts:

  1. SELF-TEST  - cycles both RGB LEDs through red/green/blue/white (so you can
     confirm colour wiring), lights each button as you press it, reads the
     rotary encoder in both directions, and plays the four button tones.

  2. PUZZLES    - runs puzzles 1..10 in fixed order (not the random 6 the real
     game picks).  There is NO bomb timer here and you cannot "lose" - it is a
     bench test.

Keys (shown on screen at all times):
    SPACE / N   next stage          B / P   previous stage
    R           restart this stage  S       force-solve the current puzzle
    ESC / close quit
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from bomb import audio, config, ui  # noqa: E402
from bomb.hardware import create_hardware  # noqa: E402
from bomb.puzzle_data import BUTTON_TONE  # noqa: E402
from bomb.puzzles import ALL_PUZZLES  # noqa: E402


class _Shim:
    """Stands in for the Game object; puzzles only ever touch ``.hw``."""

    def __init__(self, hw):
        self.hw = hw
        self.encoder_pos = 0


# --------------------------------------------------------------------------- #
# Stage 0: raw hardware self-test
# --------------------------------------------------------------------------- #
class SelfTest:
    name = "HARDWARE SELF-TEST"
    STEPS = ["LED A", "LED B", "BUTTONS", "ROTARY ENCODER", "AUDIO / BUZZER"]
    CYCLE = [("RED", (255, 0, 0)), ("GREEN", (0, 255, 0)),
             ("BLUE", (0, 0, 255)), ("WHITE", (255, 255, 255)),
             ("OFF", (0, 0, 0))]

    def __init__(self, shim):
        self.shim = shim
        self.hw = shim.hw
        self.solved = False

    def start(self):
        self.step = 0
        self.t = 0.0
        self.ci = 0
        self.seen_buttons = set()
        self.enc_min = 0
        self.enc_max = 0
        self.enc_start = self.shim.encoder_pos
        self.hw.all_leds_off()
        self.audio_clock = 0.0
        self.audio_seq = []
        self.audio_triggered = False

    def stop(self):
        self.hw.all_leds_off()

    def next_step(self):
        self.hw.all_leds_off()
        if self.step < len(self.STEPS) - 1:
            self.step += 1
            self.t = 0.0
            self.ci = 0
            self.audio_triggered = False
            self.audio_seq = []
            if self.STEPS[self.step] == "ROTARY ENCODER":
                self.enc_start = self.shim.encoder_pos
                self.enc_min = self.enc_max = 0
            return True
        return False      # done with self-test -> advance to puzzles

    def prev_step(self):
        self.hw.all_leds_off()
        if self.step > 0:
            self.step -= 1
            self.t = 0.0
            self.ci = 0
            return True
        return False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_t \
                and self.STEPS[self.step] == "AUDIO / BUZZER":
            self._play_tones()

    def _play_tones(self):
        # queue four rising tones; update() plays them in sequence
        self.audio_seq = [(self.audio_clock + k * 0.28, c)
                          for k, c in enumerate(config.BTN_ORDER)]
        self.audio_triggered = True

    def update(self, dt, inputs):
        step = self.STEPS[self.step]
        self.t += dt
        if step in ("LED A", "LED B"):
            if self.t >= 0.8:
                self.t = 0.0
                self.ci = (self.ci + 1) % len(self.CYCLE)
            led = self.hw.led_a if step == "LED A" else self.hw.led_b
            led.set_color(self.CYCLE[self.ci][1])
        elif step == "BUTTONS":
            for c in inputs.button_down:
                self.seen_buttons.add(c)
        elif step == "ROTARY ENCODER":
            rel = self.shim.encoder_pos - self.enc_start
            self.enc_min = min(self.enc_min, rel)
            self.enc_max = max(self.enc_max, rel)
        elif step == "AUDIO / BUZZER":
            self.audio_clock += dt
            if not self.audio_triggered and self.t >= 0.3:
                self._play_tones()
            for t in [x for x in self.audio_seq if x[0] <= self.audio_clock]:
                audio.play(BUTTON_TONE[t[1]], 220, 0.35)
                self.audio_seq.remove(t)
            for c in inputs.button_down:       # live: press a button -> its tone
                audio.play(BUTTON_TONE[c], 220, 0.35)

    def draw(self, surface, area):
        ui.text(surface, f"Step {self.step + 1}/{len(self.STEPS)}: "
                f"{self.STEPS[self.step]}", area.centerx, area.y + 16,
                size=26, color=config.ACCENT, align="midtop", bold=True)
        step = self.STEPS[self.step]
        cx, cy = area.centerx, area.centery

        if step in ("LED A", "LED B"):
            name, col = self.CYCLE[self.ci]
            led = self.hw.led_a if step == "LED A" else self.hw.led_b
            ui.draw_led(surface, (cx, cy), 60, led.color, step)
            ui.text(surface, f"expecting: {name}", cx, cy + 90, size=24,
                    color=config.WHITE, align="midtop", bold=True)
            ui.text(surface, "Confirm this LED shows each colour. If red/green/"
                    "blue are swapped, fix the wiring (or channel order).",
                    cx, cy + 130, size=16, color=config.GREY, align="midtop",
                    max_width=680)
        elif step == "BUTTONS":
            ui.text(surface, "Press each button. Each lights and gets a check.",
                    cx, area.y + 90, size=18, color=config.GREY, align="midtop")
            bw = 130
            sx = cx - 2 * bw
            for i, c in enumerate(config.BTN_ORDER):
                bx = sx + i * bw + bw // 2
                held = self.hw.button_state.get(c, False)
                seen = c in self.seen_buttons
                colr = config.BTN_COLORS[c]
                pygame.draw.circle(surface, colr if (held or seen) else
                                   tuple(int(v * 0.4) for v in colr), (bx, cy), 42)
                if held:
                    pygame.draw.circle(surface, config.WHITE, (bx, cy), 46, 3)
                ui.text(surface, c.capitalize(), bx, cy + 54, size=18,
                        color=config.LIGHT, align="midtop")
                if seen:
                    ui.text(surface, "OK", bx, cy - 8, size=22,
                            color=config.BLACK, align="center", bold=True)
            if len(self.seen_buttons) == 4:
                ui.text(surface, "All four buttons OK - press SPACE.", cx,
                        cy + 110, size=20, color=config.OK, align="midtop", bold=True)
        elif step == "ROTARY ENCODER":
            rel = self.shim.encoder_pos - self.enc_start
            ui.text(surface, "Turn the encoder. Clockwise should go UP.",
                    cx, area.y + 90, size=18, color=config.GREY, align="midtop")
            ui.text(surface, f"{rel:+d}", cx, cy - 20, size=72, color=config.WHITE,
                    align="center", bold=True, mono=True)
            cw = "clockwise OK" if self.enc_max > 0 else "turn clockwise..."
            ccw = "counter-clockwise OK" if self.enc_min < 0 else "turn counter-clockwise..."
            ui.text(surface, cw, cx, cy + 50, size=18,
                    color=config.OK if self.enc_max > 0 else config.GREY, align="midtop")
            ui.text(surface, ccw, cx, cy + 74, size=18,
                    color=config.OK if self.enc_min < 0 else config.GREY, align="midtop")
        elif step == "AUDIO / BUZZER":
            ui.text(surface, "You should hear four rising tones.", cx, cy - 20,
                    size=22, color=config.WHITE, align="midtop")
            ui.text(surface, "Press T to replay, or press any colour button "
                    "to hear its tone.", cx, cy + 20, size=16, color=config.GREY,
                    align="midtop", max_width=680)
            if audio._READY is False:
                ui.text(surface, "(no audio device found on this machine)",
                        cx, cy + 60, size=16, color=config.WARN, align="midtop")


# --------------------------------------------------------------------------- #
# Puzzle stage wrapper
# --------------------------------------------------------------------------- #
class PuzzleStage:
    def __init__(self, shim, cls, index):
        self.shim = shim
        self.cls = cls
        self.index = index
        self.name = f"PUZZLE {index + 1}/10: {cls.name}"

    def start(self):
        self.puzzle = self.cls(self.shim)
        self.puzzle.start()
        self.flash = 0.0

    def stop(self):
        self.puzzle.stop()

    def restart(self):
        self.puzzle.stop()
        self.start()

    def force_solve(self):
        self.puzzle.solved = True

    def handle_event(self, event):
        if not self.puzzle.solved:
            self.puzzle.handle_event(event)

    def update(self, dt, inputs):
        if not self.puzzle.solved:
            self.puzzle.update(dt, inputs)
        else:
            self.flash += dt

    def draw(self, surface, area):
        self.puzzle.draw(surface, area)
        if self.puzzle.solved:
            box = pygame.Rect(0, 0, 420, 70)
            box.center = (area.centerx, area.bottom - 60)
            ov = pygame.Surface(box.size, pygame.SRCALPHA)
            ov.fill((*config.OK, 40))
            surface.blit(ov, box)
            pygame.draw.rect(surface, config.OK, box, 3, border_radius=10)
            ui.text(surface, "SOLVED - SPACE for next", box.centerx,
                    box.centery, size=26, color=config.OK, align="center", bold=True)


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
def build_stages(shim):
    stages = [SelfTest(shim)]
    for i, cls in enumerate(ALL_PUZZLES):
        stages.append(PuzzleStage(shim, cls, i))
    return stages


def draw_footer(surface, stage_i, n):
    y = config.SCREEN_HEIGHT - 28
    pygame.draw.rect(surface, config.DARK,
                     (0, config.SCREEN_HEIGHT - 40, config.play_width(), 40))
    ui.text(surface, "SPACE/N next   B/P prev   R restart   S force-solve   ESC quit",
            16, y, size=15, color=config.GREY, align="midleft", mono=True)
    ui.text(surface, f"stage {stage_i + 1}/{n}", config.play_width() - 16, y,
            size=15, color=config.GREY, align="midright", mono=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bomb Diffusal hardware test")
    ap.add_argument("--mock", action="store_true",
                    help="force desktop keyboard/mouse mock hardware")
    ap.add_argument("--fullscreen", action="store_true")
    args = ap.parse_args(argv)

    audio.pre_init()        # must precede pygame.init() so tones don't crackle
    pygame.init()
    audio.init()
    flags = pygame.FULLSCREEN if args.fullscreen else 0
    screen = pygame.display.set_mode(
        (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), flags)
    pygame.display.set_caption("Bomb Diffusal - Hardware Test")
    clock = pygame.time.Clock()

    hw = create_hardware(force_mock=args.mock)
    print("hardware backend:", "MOCK (desktop)" if hw.is_mock else "Raspberry Pi GPIO")
    shim = _Shim(hw)
    stages = build_stages(shim)

    i = 0
    stages[i].start()
    header_area = pygame.Rect(0, 10, config.play_width(), config.SCREEN_HEIGHT - 50)

    def goto(n):
        nonlocal i
        if 0 <= n < len(stages):
            stages[i].stop()
            i = n
            stages[i].start()

    running = True
    try:
        while running:
            dt = min(clock.tick(config.FPS) / 1000.0, 0.1)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    break
                hw.process_event(event)

                stage = stages[i]
                advanced = False
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_n):
                        # In the self-test, SPACE walks the sub-steps first,
                        # then moves on to the puzzles.
                        if isinstance(stage, SelfTest):
                            if not stage.next_step():
                                goto(i + 1)
                        else:
                            goto(i + 1)
                        advanced = True
                    elif event.key in (pygame.K_b, pygame.K_p):
                        if isinstance(stage, SelfTest):
                            if not stage.prev_step():
                                goto(i - 1)
                        else:
                            goto(i - 1)
                        advanced = True
                    elif event.key == pygame.K_r:
                        stage.restart() if isinstance(stage, PuzzleStage) \
                            else stage.start()
                        advanced = True
                    elif event.key == pygame.K_s and isinstance(stage, PuzzleStage):
                        stage.force_solve()
                        advanced = True
                if not advanced:
                    stages[i].handle_event(event)

            inputs = hw.poll()
            shim.encoder_pos += inputs.encoder_delta
            stages[i].update(dt, inputs)

            screen.fill(config.BLACK)
            # header label
            ui.text(screen, stages[i].name, config.play_width() // 2, 14,
                    size=22, color=config.WARN, align="midtop", bold=True)
            pygame.draw.line(screen, config.WARN, (0, 48),
                             (config.play_width(), 48), 1)
            area = pygame.Rect(0, 56, config.play_width(),
                               config.SCREEN_HEIGHT - 56 - 40)
            stages[i].draw(screen, area)
            draw_footer(screen, i, len(stages))
            ui.draw_hardware_panel(screen, hw, shim.encoder_pos)
            pygame.display.flip()
    finally:
        hw.cleanup()
        pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
