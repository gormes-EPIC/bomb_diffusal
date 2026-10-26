"""Top-level game: module selection, the always-on bomb timer, and the
title / intro / playing / solved / win / lose flow."""

from __future__ import annotations

import random

import pygame

from . import config, ui
from .puzzles import ALL_PUZZLES

TITLE, INTRO, PLAYING, SOLVED, WIN, LOSE = range(6)
SOLVED_FLASH_TIME = 1.4


class Game:
    def __init__(self, screen, hw):
        self.screen = screen
        self.hw = hw
        self.encoder_pos = 0
        self.state = TITLE
        self.started = False
        self._reset()

    # ------------------------------------------------------------------ setup
    def _reset(self):
        n = min(config.PUZZLES_PER_GAME, len(ALL_PUZZLES))
        self.lineup = random.sample(ALL_PUZZLES, n)   # 6 of 10, random order
        self.needed = n
        self.index = 0
        self.solved_count = 0
        self.remaining = config.TOTAL_TIME
        self.module = None
        self.flash_t = 0.0
        self.started = False
        self.state = TITLE

    def _enter_module(self, i):
        self.index = i
        self.module = self.lineup[i](self)
        self.state = INTRO

    def _begin_game(self):
        self.started = True
        self._enter_module(0)

    def _start_playing(self):
        self.module.start()
        self.state = PLAYING

    # ------------------------------------------------------------------ events
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        if self.state == TITLE:
            if self._is_go(event):
                self._begin_game()
        elif self.state == INTRO:
            if self._is_go(event):
                self._start_playing()
        elif self.state == PLAYING:
            self.module.handle_event(event)
        elif self.state in (WIN, LOSE):
            if self._is_go(event):
                self._reset()

    @staticmethod
    def _is_go(event):
        return ((event.type == pygame.KEYDOWN and
                 event.key in (pygame.K_SPACE, pygame.K_RETURN)) or
                (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1))

    # ------------------------------------------------------------------ update
    def update(self, dt, inputs):
        self.encoder_pos += inputs.encoder_delta

        if self.state in (INTRO, PLAYING, SOLVED):
            self.remaining -= dt
            if self.remaining <= 0:
                self.remaining = 0
                self._fail()
                return

        if self.state == PLAYING:
            self.module.update(dt, inputs)
            if self.module.solved:
                self.module.stop()
                self.solved_count += 1
                if self.solved_count >= self.needed:
                    self.hw.all_leds_off()
                    self.state = WIN
                else:
                    self.state = SOLVED
                    self.flash_t = SOLVED_FLASH_TIME
        elif self.state == SOLVED:
            self.flash_t -= dt
            if self.flash_t <= 0:
                self._enter_module(self.index + 1)

    def _fail(self):
        if self.module:
            self.module.stop()
        self.hw.all_leds_off()
        self.state = LOSE

    # -------------------------------------------------------------------- draw
    def draw(self):
        s = self.screen
        s.fill(config.BLACK)
        area = pygame.Rect(0, 64, config.play_width(),
                           config.SCREEN_HEIGHT - 64)

        if self.state == TITLE:
            self._draw_title(s)
        elif self.state == INTRO:
            self._draw_intro(s, area)
        elif self.state == PLAYING:
            self.module.draw(s, area)
        elif self.state == SOLVED:
            self.module.draw(s, area)
            self._draw_banner(s, "MODULE DISARMED", config.OK)
        elif self.state == WIN:
            self._draw_end(s, "BOMB DEFUSED", config.OK,
                           "You disarmed every module. The team wins!")
        elif self.state == LOSE:
            self._draw_end(s, "BOOM", config.DANGER,
                           "The timer reached zero.")

        if self.started and self.state in (INTRO, PLAYING, SOLVED):
            ui.draw_timer_bar(s, self.remaining, config.TOTAL_TIME,
                              self.solved_count, self.needed)
        ui.draw_hardware_panel(s, self.hw, self.encoder_pos)

    def _draw_title(self, s):
        cx = config.play_width() // 2
        ui.text(s, config.TITLE, cx, 180, size=84, color=config.DANGER,
                align="midtop", bold=True)
        ui.text(s, "a two-player cooperative defusal game",
                cx, 280, size=24, color=config.GREY, align="midtop")
        lines = [
            "Player 1 has the Screen, Mouse, Keyboard and the Decoder Cards.",
            "Player 2 has the LEDs, Buttons, Rotary Encoder and the Manual.",
            "Six modules, 30 minutes. Talk to each other. Disarm them all.",
        ]
        for i, ln in enumerate(lines):
            ui.text(s, ln, cx, 360 + i * 36, size=22, color=config.LIGHT,
                    align="midtop")
        self._pulse_prompt(s, "PRESS SPACE TO ARM THE BOMB", 560)

    def _draw_intro(self, s, area):
        # No module name and no instructions -- figuring out the module is the
        # puzzle. Just a neutral "ready" gate between modules.
        cx = config.play_width() // 2
        ui.text(s, f"MODULE {self.index + 1} OF {self.needed}", cx, 250,
                size=34, color=config.LIGHT, align="midtop", bold=True)
        self._pulse_prompt(s, "PRESS SPACE WHEN READY", 350)

    def _draw_banner(self, s, msg, color):
        cx = config.play_width() // 2
        box = pygame.Rect(0, 0, 520, 90)
        box.center = (cx, config.SCREEN_HEIGHT - 90)
        overlay = pygame.Surface(box.size, pygame.SRCALPHA)
        overlay.fill((*color, 40))
        s.blit(overlay, box)
        pygame.draw.rect(s, color, box, 3, border_radius=10)
        ui.text(s, msg, box.centerx, box.centery, size=40, color=color,
                align="center", bold=True)

    def _draw_end(self, s, msg, color, sub):
        cx = config.play_width() // 2
        ui.text(s, msg, cx, 220, size=96, color=color, align="midtop", bold=True)
        ui.text(s, sub, cx, 350, size=26, color=config.LIGHT, align="midtop")
        ui.text(s, f"Modules disarmed: {self.solved_count} / {self.needed}"
                f"   -   Time left: {ui.format_time(self.remaining)}",
                cx, 400, size=22, color=config.GREY, align="midtop")
        self._pulse_prompt(s, "PRESS SPACE TO PLAY AGAIN", 520)

    @staticmethod
    def _pulse_prompt(s, msg, y):
        a = 0.55 + 0.45 * abs((pygame.time.get_ticks() % 1200) / 600 - 1)
        col = tuple(int(c * a) for c in config.WHITE)
        ui.text(s, msg, config.play_width() // 2, y, size=26, color=col,
                align="midtop", bold=True)
