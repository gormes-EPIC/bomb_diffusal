"""Puzzle -- Combination Lock.

A spinning safe dial.  Player 2 turns the rotary encoder; the screen shows the
numbered dial rotating under a fixed index mark at the top.  A three-number
combination is shown, each number with the direction it must be dialled in --
clockwise or counter-clockwise.  Land on each number while turning the right
way, hold for a beat, and the tumbler drops; dial all three in order to disarm.

Turning the wrong way, or stopping on the wrong number, simply doesn't engage --
there is no penalty, only the clock.

The dial face itself is a VectorCraft illustration (``docs/assets/combo_dial.png``);
the game loads it and rotates it so the current number sits under the pointer.
"""

from __future__ import annotations

import math
import os
import random

import pygame

from .. import audio, config, ui
from .base import Puzzle

# --------------------------------------------------------------------------- #
# Dial geometry.  The exported illustration has the numbers 0..N-1 spaced evenly
# clockwise from the top, so one encoder detent == one number == STEP_DEG.
# --------------------------------------------------------------------------- #
N = 20
STEP_DEG = 360 / N          # 18 degrees per number
COMBO_LEN = 3
HOLD = 0.35                 # seconds to hold on a number for it to engage
DISPLAY = 460               # on-screen dial diameter (pixels)

CW, CCW = 1, -1             # encoder delta sign for each turn direction
DIR_NAME = {CW: "CW", CCW: "CCW"}

_ASSET = os.path.join(os.path.dirname(__file__), "..", "..",
                      "docs", "assets", "combo_dial.png")
_dial_cache: dict[int, pygame.Surface] = {}


def _dial_image(size: int) -> pygame.Surface | None:
    """Load (once) and pre-scale the VectorCraft dial face to ``size`` px."""
    surf = _dial_cache.get(size)
    if surf is None:
        try:
            raw = pygame.image.load(_ASSET).convert_alpha()
            surf = pygame.transform.smoothscale(raw, (size, size))
        except Exception:
            surf = None            # headless / asset missing -> drawn fallback
        _dial_cache[size] = surf
    return surf


class CombinationLock(Puzzle):
    name = "COMBINATION LOCK"
    blurb = "Dial the three-number combination with the encoder, each the right way."

    def start(self):
        self.hw.all_leds_off()
        self._new_combo()

    def _new_combo(self):
        # Three distinct-from-their-neighbour numbers, alternating directions.
        first = random.choice([CW, CCW])
        nums: list[int] = []
        while len(nums) < COMBO_LEN:
            n = random.randrange(N)
            if not nums or n != nums[-1]:
                nums.append(n)
        self.combo = [(nums[i], first if i % 2 == 0 else -first)
                      for i in range(COMBO_LEN)]

        # Start a few numbers away from the first target, on the wrong side so
        # the opening turn is a real turn in the required direction.
        t0, d0 = self.combo[0]
        self.cur = (t0 - d0 * random.randint(3, N - 3)) % N
        self.step = 0
        self.last_dir = 0          # no turn registered yet
        self.hold = 0.0
        self.flash = 0.0           # brief "engaged" glow after a digit drops

    # ---------------------------------------------------------------- update
    def update(self, dt, inputs):
        if self.solved:
            return
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt)

        if inputs.encoder_delta:
            self.cur = (self.cur + inputs.encoder_delta) % N
            self.last_dir = CW if inputs.encoder_delta > 0 else CCW

        target, want = self.combo[self.step]
        engaged = self.cur == target and self.last_dir == want
        if engaged:
            self.hold += dt
            if self.hold >= HOLD:
                self._drop_digit()
        else:
            self.hold = 0.0

    def _drop_digit(self):
        audio.play(440 + 140 * self.step, 110, 0.3)
        self.step += 1
        self.hold = 0.0
        self.last_dir = 0          # the next digit needs a fresh turn
        self.flash = 0.4
        if self.step >= COMBO_LEN:
            self.solved = True
            audio.play(880, 220, 0.3)

    # ------------------------------------------------------------------ draw
    def draw(self, surface, area):
        cx = area.centerx
        cy = area.centery + 20

        ui.text(surface, "TURN ME", cx, area.y + 16, size=38,
                color=config.ACCENT, align="midtop", bold=True)

        self._draw_combo(surface, cx, area.y + 76)
        self._draw_dial(surface, cx, cy)

    # -- the combination strip ---------------------------------------------
    def _draw_combo(self, surface, cx, y):
        slot_w, slot_h, gap = 150, 92, 26
        total = COMBO_LEN * slot_w + (COMBO_LEN - 1) * gap
        sx = cx - total // 2
        for i, (num, want) in enumerate(self.combo):
            rect = pygame.Rect(sx + i * (slot_w + gap), y, slot_w, slot_h)
            done = i < self.step
            active = i == self.step and not self.solved
            if done:
                edge, fill = config.OK, (30, 60, 42)
            elif active:
                edge, fill = config.ACCENT, (20, 46, 44)
            else:
                edge, fill = (70, 78, 90), (24, 28, 36)
            pygame.draw.rect(surface, fill, rect, border_radius=12)
            pygame.draw.rect(surface, edge, rect, 3, border_radius=12)

            self._draw_turn_arrow(surface, rect.x + 34, rect.centery,
                                  16, want, edge)
            ui.text(surface, str(num), rect.x + 66, rect.centery - 18,
                    size=46, color=config.WHITE, align="midleft", bold=True)
            ui.text(surface, DIR_NAME[want], rect.centerx + 10, rect.bottom - 22,
                    size=15, color=edge, align="midtop", bold=True)
            if done:
                ui.text(surface, "OK", rect.right - 24, rect.y + 10, size=16,
                        color=config.OK, align="midtop", bold=True)

    @staticmethod
    def _draw_turn_arrow(surface, cx, cy, r, direction, color):
        """A little circular arrow showing CW / CCW."""
        # Draw most of a circle, leaving a gap, then an arrowhead at the open end.
        if direction == CW:
            a0, a1 = math.radians(130), math.radians(390)
        else:
            a0, a1 = math.radians(-30), math.radians(230)
        pts = []
        steps = 24
        for k in range(steps + 1):
            a = a0 + (a1 - a0) * k / steps
            pts.append((cx + r * math.cos(a), cy - r * math.sin(a)))
        if len(pts) > 1:
            pygame.draw.lines(surface, color, False,
                              [(int(x), int(y)) for x, y in pts], 3)
        # arrowhead, tangent to the arc at its open end
        hx, hy = cx + r * math.cos(a1), cy - r * math.sin(a1)
        base = math.atan2(-(hy - cy), (hx - cx)) + (math.pi / 2 if direction == CW
                                                    else -math.pi / 2)
        for off in (-0.5, 0.5):
            ex = hx + 9 * math.cos(base + off)
            ey = hy - 9 * math.sin(base + off)
            pygame.draw.line(surface, color, (hx, hy), (ex, ey), 3)

    # -- the rotating dial --------------------------------------------------
    def _draw_dial(self, surface, cx, cy):
        angle = self.cur * STEP_DEG          # CCW-positive brings cur to the top
        img = _dial_image(DISPLAY)
        if img is not None:
            rot = pygame.transform.rotozoom(img, angle, 1.0)
            surface.blit(rot, rot.get_rect(center=(cx, cy)))
        else:
            self._draw_dial_fallback(surface, cx, cy)

        self._draw_pointer(surface, cx, cy)

        # Live read-out of the number currently under the index.
        target, want = (self.combo[self.step] if not self.solved
                        else self.combo[-1])
        on = self.cur == target
        col = config.OK if (self.solved or (on and self.last_dir == want)) \
            else config.WHITE
        ui.text(surface, f"{self.cur:02d}", cx, cy + DISPLAY // 2 + 28,
                size=40, color=col, align="midtop", bold=True, mono=True)
        if self.flash > 0 and not self.solved:
            ui.text(surface, "CLICK", cx, cy - DISPLAY // 2 - 44, size=22,
                    color=config.OK, align="midtop", bold=True)

    def _draw_pointer(self, surface, cx, cy):
        top = cy - DISPLAY // 2
        # A downward index triangle sitting just above the dial's top edge.
        pts = [(cx, top + 18), (cx - 15, top - 14), (cx + 15, top - 14)]
        pygame.draw.polygon(surface, config.ACCENT, pts)
        pygame.draw.polygon(surface, config.BLACK, pts, 2)

    def _draw_dial_fallback(self, surface, cx, cy):
        """Plain vector dial if the PNG can't be loaded (e.g. headless tests)."""
        r = DISPLAY // 2
        pygame.draw.circle(surface, (42, 47, 58), (cx, cy), r)
        pygame.draw.circle(surface, (154, 164, 181), (cx, cy), r, 2)
        for k in range(N):
            a = math.radians(k * STEP_DEG - 90) + math.radians(self.cur * STEP_DEG)
            x = cx + (r - 24) * math.cos(a)
            y = cy + (r - 24) * math.sin(a)
            ui.text(surface, str(k), int(x), int(y), size=22,
                    color=config.LIGHT, align="center")
        pygame.draw.circle(surface, (58, 65, 80), (cx, cy), 52)
