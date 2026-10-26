"""Puzzle 7 -- Rhythm Lock.

A rhythm (a sequence of coloured notes) plays over the speaker.  Player 2
replays it on the buttons; each press sounds its tone and Player 1 sees the note
name appear, confirming the sequence.  A wrong press resets the attempt.
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
                    self.solved = True
            else:
                self.progress = 0
                self.pressed = []
                self.wrong = 0.5

    def draw(self, surface, area):
        self.title(surface, area)
        ui.text(surface, "Player 1 reads these names aloud as Player 2 presses:",
                area.centerx, area.y + 56, size=18, color=config.GREY,
                align="midtop")
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
            ui.text(surface, "Wrong note - the sequence reset.", area.centerx,
                    y + 70, size=18, color=config.DANGER, align="midtop")

        col = config.ACCENT if not self.playing else config.WARN
        pygame.draw.rect(surface, col, self.play_btn, border_radius=10)
        ui.text(surface, "PLAYING..." if self.playing else "PLAY RHYTHM  (L)",
                self.play_btn.centerx, self.play_btn.centery, size=20,
                color=config.BLACK, align="center", bold=True)
