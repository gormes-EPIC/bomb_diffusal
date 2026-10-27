"""Puzzle 7 -- Rhythm Lock.

A rhythm (a sequence of coloured notes) plays over the speaker.  Player 2
replays it on the buttons; each press sounds its tone and Player 1 sees the note
name appear, confirming the sequence.

The rotary encoder selects the mode: turn it counter-clockwise for TESTING and
clockwise for PRODUCTION.  In TESTING the team can practice freely -- wrong
presses never count as a mistake, and a correct run just confirms the rhythm
without disarming.  Only in PRODUCTION does a wrong press cost a mistake and a
correct run actually disarm the module.
"""

from __future__ import annotations

import random

import pygame

from .. import audio, config, ui
from ..puzzle_data import BUTTON_TONE, RHYTHMS
from .base import Puzzle

NOTE_MS = 300
GAP_MS = 140


class Rhythm(Puzzle):
    name = "RHYTHM LOCK"
    blurb = "Press PLAY to hear the rhythm, then replay it on the buttons."

    def start(self):
        self.seq = random.choice(RHYTHMS)
        self.progress = 0
        self.pressed = []           # note names shown to Player 1
        self.wrong = 0.0
        self.ok_flash = 0.0         # "practice run correct" confirmation
        self.testing = True         # encoder: CCW = testing, CW = production
        # playback animation state
        self.playing = False
        self.play_i = 0
        self.play_t = 0.0
        self._geom()

    def _geom(self):
        a = pygame.Rect(0, 64, config.play_width(), config.SCREEN_HEIGHT - 64)
        self.play_btn = pygame.Rect(0, 0, 220, 60)
        self.play_btn.center = (a.centerx, a.bottom - 70)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_l:
            self._start_playback()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.play_btn.collidepoint(event.pos):
                self._start_playback()

    def _start_playback(self):
        if not self.playing:
            self.playing = True
            self.play_i = -1
            self.play_t = (NOTE_MS + GAP_MS) / 1000.0  # trigger first immediately

    def update(self, dt, inputs):
        if self.wrong > 0:
            self.wrong = max(0, self.wrong - dt)
        if self.ok_flash > 0:
            self.ok_flash = max(0, self.ok_flash - dt)

        # Rotary encoder selects the mode: clockwise = production, CCW = testing.
        if inputs.encoder_delta > 0:
            self.testing = False
        elif inputs.encoder_delta < 0:
            self.testing = True

        # drive demo playback
        if self.playing:
            self.play_t += dt
            if self.play_t >= (NOTE_MS + GAP_MS) / 1000.0:
                self.play_t = 0.0
                self.play_i += 1
                if self.play_i >= len(self.seq):
                    self.playing = False
                else:
                    audio.play(BUTTON_TONE[self.seq[self.play_i]], NOTE_MS, 0.35)

        # player input
        for c in inputs.button_down:
            audio.play(BUTTON_TONE[c], NOTE_MS, 0.35)
            if c == self.seq[self.progress]:
                self.progress += 1
                self.pressed.append(c)
                if self.progress == len(self.seq):
                    if self.testing:
                        # Practice run complete: confirm it, but don't disarm.
                        self.ok_flash = 1.0
                        self.progress = 0
                        self.pressed = []
                    else:
                        self.solved = True
            else:
                self.progress = 0
                self.pressed = []
                self.wrong = 0.5
                if not self.testing:        # no mistakes while testing
                    self.strike()

    def draw(self, surface, area):
        self._draw_mode(surface, area)
        # note-name slots
        n = len(self.seq)
        slot = 110
        sx = area.centerx - n * slot // 2
        y = area.centery - 20
        for i in range(n):
            x = sx + i * slot + slot // 2
            filled = i < len(self.pressed)
            rect = pygame.Rect(x - 48, y - 30, 96, 60)
            col = config.BTN_COLORS[self.pressed[i]] if filled else (44, 50, 60)
            pygame.draw.rect(surface, col, rect, border_radius=8)
            pygame.draw.rect(surface, config.GREY, rect, 1, border_radius=8)
            if filled:
                ui.text(surface, self.pressed[i].upper(), x, y, size=20,
                        color=config.BLACK, align="center", bold=True)
            else:
                ui.text(surface, i + 1, x, y, size=20, color=config.GREY,
                        align="center")
        if self.wrong > 0:
            msg = ("Wrong note - reset (testing, no penalty)." if self.testing
                   else "Wrong note - the sequence reset.")
            ui.text(surface, msg, area.centerx, y + 70, size=18,
                    color=config.WARN if self.testing else config.DANGER,
                    align="midtop")
        elif self.ok_flash > 0:
            ui.text(surface, "Rhythm correct - switch to PRODUCTION to disarm.",
                    area.centerx, y + 70, size=18, color=config.OK,
                    align="midtop")

        col = config.ACCENT if not self.playing else config.WARN
        pygame.draw.rect(surface, col, self.play_btn, border_radius=10)
        ui.text(surface, "PLAYING..." if self.playing else "PLAY",
                self.play_btn.centerx, self.play_btn.centery, size=20,
                color=config.BLACK, align="center", bold=True)

    def _draw_mode(self, surface, area):
        """Mode indicator + how the encoder switches it."""
        if self.testing:
            label, col = "TESTING - no penalty", config.WARN
        else:
            label, col = "PRODUCTION - live", config.DANGER
        box = pygame.Rect(0, 0, 440, 44)
        box.center = (area.centerx, area.y + 40)
        pygame.draw.rect(surface, (26, 30, 38), box, border_radius=10)
        pygame.draw.rect(surface, col, box, 2, border_radius=10)
        ui.text(surface, label, box.centerx, box.centery, size=22, color=col,
                align="center", bold=True)
        ui.text(surface, "turn knob:  left = TESTING    right = PRODUCTION",
                area.centerx, box.bottom + 10, size=15, color=config.GREY,
                align="midtop")
