"""Shared drawing helpers: fonts, the timer bar, LED rendering and the
on-screen hardware panel (what Player 2 would see / do, for desktop play)."""

from __future__ import annotations

import pygame

from . import config

_fonts: dict[tuple, pygame.font.Font] = {}


def font(size: int, bold: bool = False, mono: bool = False) -> pygame.font.Font:
    key = (size, bold, mono)
    f = _fonts.get(key)
    if f is None:
        name = "dejavusansmono,consolas,monospace" if mono \
            else "dejavusans,arial,sans"
        f = pygame.font.SysFont(name, size, bold=bold)
        _fonts[key] = f
    return f


def text(surf, s, x, y, size=24, color=config.WHITE, align="topleft",
         bold=False, mono=False, max_width=None):
    f = font(size, bold, mono)
    if max_width:
        return _wrapped(surf, s, x, y, f, color, max_width)
    img = f.render(str(s), True, color)
    rect = img.get_rect()
    setattr(rect, align, (x, y))
    surf.blit(img, rect)
    return rect


def _wrapped(surf, s, x, y, f, color, max_width):
    words = str(s).split(" ")
    line, cy = "", y
    lh = f.get_linesize()
    for w in words:
        test = (line + " " + w).strip()
        if f.size(test)[0] > max_width and line:
            surf.blit(f.render(line, True, color), (x, cy))
            line, cy = w, cy + lh
        else:
            line = test
    if line:
        surf.blit(f.render(line, True, color), (x, cy))
        cy += lh
    return pygame.Rect(x, y, max_width, cy - y)


def draw_led(surf, center, radius, color, label=None, label_color=None):
    """A glowing RGB LED."""
    r, g, b = color
    # soft glow
    glow = pygame.Surface((radius * 6, radius * 6), pygame.SRCALPHA)
    for i, a in ((3.0, 22), (2.2, 34), (1.5, 60)):
        pygame.draw.circle(glow, (r, g, b, a), (radius * 3, radius * 3),
                           int(radius * i))
    surf.blit(glow, glow.get_rect(center=center))
    pygame.draw.circle(surf, (40, 44, 52), center, radius + 3)
    pygame.draw.circle(surf, color, center, radius)
    pygame.draw.circle(surf, (255, 255, 255, 60), center, radius, 2)
    if label:
        text(surf, label, center[0], center[1] + radius + 14,
             size=18, color=label_color or config.GREY, align="midtop")


def format_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def draw_timer_bar(surf, remaining, total, solved, needed,
                   mistakes=0, max_mistakes=0):
    """Top-of-screen bomb timer, visible during every puzzle."""
    w = config.SCREEN_WIDTH
    pygame.draw.rect(surf, config.DARK, (0, 0, w, 64))
    pygame.draw.line(surf, config.ACCENT, (0, 64), (w, 64), 2)

    frac = remaining / total if total else 0
    col = config.OK if frac > 0.5 else config.WARN if frac > 0.2 else config.DANGER
    # Pulsing when under two minutes.
    if remaining <= 120:
        pulse = 0.6 + 0.4 * abs((pygame.time.get_ticks() % 1000) / 500 - 1)
        col = tuple(int(c * pulse) for c in config.DANGER)

    text(surf, format_time(remaining), 24, 32, size=40, color=col,
         align="midleft", bold=True, mono=True)
    text(surf, "TIME REMAINING", 24, 8, size=13, color=config.GREY)

    # progress pips
    text(surf, f"MODULE {solved + 1 if solved < needed else needed} / {needed}",
         w // 2, 10, size=14, color=config.GREY, align="midtop")
    pip_w = 26
    total_w = needed * (pip_w + 8)
    sx = w // 2 - total_w // 2
    for i in range(needed):
        c = config.OK if i < solved else (60, 66, 76)
        pygame.draw.rect(surf, c, (sx + i * (pip_w + 8), 34, pip_w, 14),
                         border_radius=4)

    # mistake tally (right side): one X-pip per allowed mistake, lit when used
    if max_mistakes:
        text(surf, "MISTAKES", w - 24, 8, size=13, color=config.GREY,
             align="topright")
        dot_r = 8
        gap = 24
        span = (max_mistakes - 1) * gap
        rx = w - 24 - span
        for i in range(max_mistakes):
            cx = rx + i * gap
            used = i < mistakes
            pygame.draw.circle(surf, config.DANGER if used else (60, 66, 76),
                               (cx, 42), dot_r)
            if used:
                pygame.draw.circle(surf, config.WHITE, (cx, 42), dot_r, 1)


def draw_hardware_panel(surf, hw, encoder_pos=0):
    """Right-hand panel: Player 2's LEDs, buttons, encoder + desktop hints."""
    if not config.SHOW_HARDWARE_PANEL:
        return
    x0 = config.SCREEN_WIDTH - config.PANEL_WIDTH
    pygame.draw.rect(surf, config.PANEL_BG,
                     (x0, 64, config.PANEL_WIDTH, config.SCREEN_HEIGHT - 64))
    pygame.draw.line(surf, (40, 46, 56), (x0, 64), (x0, config.SCREEN_HEIGHT), 2)
    cx = x0 + config.PANEL_WIDTH // 2

    text(surf, "PLAYER 2", cx, 84, size=20, color=config.ACCENT,
         align="midtop", bold=True)
    text(surf, "hardware", cx, 108, size=14, color=config.GREY, align="midtop")

    # Two RGB LEDs
    draw_led(surf, (cx - 60, 170), 26, hw.led_a.color, "LED A")
    draw_led(surf, (cx + 60, 170), 26, hw.led_b.color, "LED B")

    # Four buttons
    text(surf, "BUTTONS", cx, 240, size=13, color=config.GREY, align="midtop")
    bx = x0 + 40
    for i, c in enumerate(config.BTN_ORDER):
        col = config.BTN_COLORS[c]
        cxx = bx + i * 58
        pressed = hw.button_state.get(c, False)
        rad = 22 if pressed else 18
        if pressed:
            pygame.draw.circle(surf, col, (cxx, 288), rad + 4, 3)
        pygame.draw.circle(surf, col if pressed else tuple(int(v * 0.45) for v in col),
                           (cxx, 288), rad)
        key = config.MOCK_BUTTON_KEYS[c].upper() if hw.is_mock else c[0].upper()
        text(surf, key, cxx, 288, size=16, color=config.BLACK,
             align="center", bold=True)

    # Rotary encoder
    text(surf, "ENCODER", cx, 330, size=13, color=config.GREY, align="midtop")
    pygame.draw.circle(surf, (50, 56, 66), (cx, 392), 34)
    pygame.draw.circle(surf, (80, 88, 100), (cx, 392), 34, 2)
    import math
    a = math.radians(encoder_pos * 15 - 90)
    knob = (cx + 24 * math.cos(a), 392 + 24 * math.sin(a))
    pygame.draw.line(surf, config.ACCENT, (cx, 392), knob, 4)
    pygame.draw.circle(surf, config.ACCENT, (int(knob[0]), int(knob[1])), 5)

    if hw.is_mock:
        text(surf, "DESKTOP TEST KEYS", cx, 450, size=12,
             color=config.GREY, align="midtop")
        hints = ["buttons  R  Y  G  B",
                 "encoder  ,  /  .  or wheel"]
        for i, h in enumerate(hints):
            text(surf, h, cx, 470 + i * 20, size=14, color=config.LIGHT,
                 align="midtop", mono=True)
