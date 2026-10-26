"""Entry point:  python -m bomb  [--mock] [--fullscreen] [--windowed]

Runs the Bomb Diffusal game.  On a Raspberry Pi with gpiozero it drives the real
LEDs / buttons / encoder; on any other machine it uses the on-screen hardware
panel and desktop test keys (see the right-hand panel for the mapping).
"""

from __future__ import annotations

import argparse
import sys

import pygame

from . import audio, config
from .game import Game
from .hardware import create_hardware


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bomb", description="Bomb Diffusal game")
    ap.add_argument("--mock", action="store_true",
                    help="force the desktop keyboard/mouse mock hardware")
    ap.add_argument("--fullscreen", action="store_true",
                    help="run fullscreen (kiosk mode)")
    ap.add_argument("--windowed", action="store_true",
                    help="force a window even if config.FULLSCREEN is set")
    ap.add_argument("--panel", action="store_true",
                    help="show the on-screen Player 2 hardware panel")
    ap.add_argument("--no-panel", action="store_true",
                    help="hide the panel even on the desktop mock (clean fullscreen)")
    args = ap.parse_args(argv)

    audio.pre_init()        # must precede pygame.init() so tones don't crackle
    pygame.init()
    audio.init()

    flags = 0
    if (config.FULLSCREEN or args.fullscreen) and not args.windowed:
        flags = pygame.FULLSCREEN
    screen = pygame.display.set_mode(
        (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), flags)
    pygame.display.set_caption(config.TITLE)
    pygame.mouse.set_visible(True)
    clock = pygame.time.Clock()

    hw = create_hardware(force_mock=args.mock)

    # The on-screen hardware panel is only a stand-in for missing hardware.
    # Default: show it on the desktop mock, hide it on the real Pi (where the
    # physical LEDs/buttons are Player 2's view and the screen is fullscreen).
    if args.panel:
        config.SHOW_HARDWARE_PANEL = True
    elif args.no_panel:
        config.SHOW_HARDWARE_PANEL = False
    else:
        config.SHOW_HARDWARE_PANEL = hw.is_mock

    game = Game(screen, hw)

    running = True
    try:
        while running:
            dt = clock.tick(config.FPS) / 1000.0
            dt = min(dt, 0.1)                    # clamp after a stall
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                hw.process_event(event)
                game.handle_event(event)
            inputs = hw.poll()
            game.update(dt, inputs)
            game.draw()
            pygame.display.flip()
    finally:
        hw.cleanup()
        pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
