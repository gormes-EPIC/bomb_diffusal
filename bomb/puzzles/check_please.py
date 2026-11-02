"""Puzzle 11 -- Check, Please!  (mate-in-one chess)

The screen shows a chess position and whose turn it is.  Four squares are lit in
the four button colours (red / yellow / green / blue); on exactly one of them a
piece can move to put the enemy king in check (it is, in fact, checkmate).  The
team works out which coloured square is the checking move and Player 2 presses
that colour.  Wrong colour -> a strike; right colour -> disarmed.

The positions are fixed mate-in-ones from ``puzzle_data.CHECK_PUZZLES``.
"""

from __future__ import annotations

import random

import pygame

from .. import audio, config, ui
from ..puzzle_data import CHECK_PUZZLES
from .base import Puzzle

# Filled chess figurines (U+265A..F); coloured white or black with an outline.
GLYPH = {"K": "♚", "Q": "♛", "R": "♜",
         "B": "♝", "N": "♞", "P": "♟"}

LIGHT_SQ = (235, 224, 193)
DARK_SQ = (118, 150, 86)
PIECE_W = (248, 248, 248)
PIECE_B = (28, 30, 34)


def _sq(name: str):
    return (ord(name[0]) - 97, int(name[1]))      # "e4" -> (file 0-7, rank 1-8)


class CheckPlease(Puzzle):
    name = "CHECK PLEASE"
    blurb = "Press the colour of the square that puts the enemy king in check."

    def start(self):
        self.hw.all_leds_off()
        self.wrong = False
        self.puzzle = random.choice(CHECK_PUZZLES)
        self.turn = self.puzzle["turn"]
        self.board = self._parse(self.puzzle["fen"])

        # Lay the four button colours on the mate square + three decoys.
        squares = [self.puzzle["mate"]] + list(self.puzzle["decoys"])
        colors = list(config.BTN_ORDER)
        random.shuffle(colors)
        self.square_color = {s: c for s, c in zip(squares, colors)}
        self.correct_color = self.square_color[self.puzzle["mate"]]
        self._layout()

    @staticmethod
    def _parse(fen):
        board = {}
        for r, row in enumerate(fen.split("/")):
            rank = 8 - r
            f = 0
            for ch in row:
                if ch.isdigit():
                    f += int(ch)
                else:
                    board[(f, rank)] = ("w" if ch.isupper() else "b", ch.upper())
                    f += 1
        return board

    def _layout(self):
        a = pygame.Rect(0, 64, config.play_width(), config.SCREEN_HEIGHT - 64)
        self.cell = 92
        board_px = self.cell * 8
        self.bx = a.centerx - board_px // 2
        self.by = a.y + 120
        self.cx = a.centerx
        self.bottom = self.by + board_px

    def _cell_rect(self, file, rank):
        # White at the bottom: rank 8 on top row, rank 1 on the bottom.
        return pygame.Rect(self.bx + file * self.cell,
                           self.by + (8 - rank) * self.cell,
                           self.cell, self.cell)

    # ---------------------------------------------------------------- update
    def update(self, dt, inputs):
        for c in inputs.button_down:
            if c == self.correct_color:
                self.solved = True
                audio.play(880, 200, 0.35)
            else:
                self.wrong = True
                audio.play(160, 240, 0.35)
                self.strike()

    # ------------------------------------------------------------------ draw
    def draw(self, surface, area):
        side = "WHITE" if self.turn == "w" else "BLACK"
        ui.text(surface, f"{side} TO PLAY", self.cx, area.y + 26, size=40,
                color=config.ACCENT, align="midtop", bold=True)

        self._draw_board(surface)
        self._draw_highlights(surface)
        self._draw_pieces(surface)

        msg = ("Press the colour of the square that checks the king."
               if not self.wrong else
               "Not check - that colour was wrong. Try another.")
        col = config.DANGER if self.wrong else config.LIGHT
        ui.text(surface, msg, self.cx, self.bottom + 24, size=22, color=col,
                align="midtop")

    def _draw_board(self, surface):
        for file in range(8):
            for rank in range(1, 9):
                rect = self._cell_rect(file, rank)
                light = (file + rank) % 2 == 1
                pygame.draw.rect(surface, LIGHT_SQ if light else DARK_SQ, rect)
        # thin frame + file/rank coordinates for easy reference
        frame = pygame.Rect(self.bx, self.by, self.cell * 8, self.cell * 8)
        pygame.draw.rect(surface, (60, 66, 76), frame, 3)
        for file in range(8):
            ui.text(surface, chr(97 + file),
                    self.bx + file * self.cell + self.cell // 2,
                    self.by + self.cell * 8 + 6, size=16, color=config.GREY,
                    align="midtop")
        for rank in range(1, 9):
            ui.text(surface, str(rank), self.bx - 14,
                    self.by + (8 - rank) * self.cell + self.cell // 2,
                    size=16, color=config.GREY, align="midright")

    def _draw_highlights(self, surface):
        for name, ckey in self.square_color.items():
            rect = self._cell_rect(*_sq(name))
            color = config.BTN_COLORS[ckey]
            glow = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            glow.fill((*color, 110))
            surface.blit(glow, rect)
            pygame.draw.rect(surface, color, rect, 6)
            # colour initial in the corner (clear even if colours are hard to tell)
            ui.text(surface, ckey[0].upper(), rect.x + 12, rect.y + 8, size=22,
                    color=config.WHITE, align="topleft", bold=True)

    def _draw_pieces(self, surface):
        f = ui.font(int(self.cell * 0.82))
        for (file, rank), (color, kind) in self.board.items():
            rect = self._cell_rect(file, rank)
            self._blit_piece(surface, f, GLYPH[kind], rect.center, color)

    @staticmethod
    def _blit_piece(surface, f, glyph, center, color):
        fill = PIECE_W if color == "w" else PIECE_B
        outline = PIECE_B if color == "w" else (225, 225, 225)
        base = f.render(glyph, True, outline)
        rect = base.get_rect(center=center)
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2),
                       (-2, -2), (2, 2), (-2, 2), (2, -2)):
            surface.blit(base, (rect.x + dx, rect.y + dy))
        top = f.render(glyph, True, fill)
        surface.blit(top, top.get_rect(center=center))
