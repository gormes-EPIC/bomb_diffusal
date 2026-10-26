"""Simple tone synthesis for the Rhythm and Morse puzzles.

Uses only the standard-library ``array`` module (no numpy) to build 16-bit PCM
buffers that pygame.mixer plays.  If no audio device is available (e.g. a
headless test box) every call degrades to a silent no-op.
"""

from __future__ import annotations

import array
import math

import pygame

_READY = False
_CHANNELS = 2
_RATE = 44100
# A large-ish buffer avoids underruns ("crackle") under the 60fps game loop,
# especially on a Raspberry Pi. ~2048 frames ~= 46ms latency at 44.1kHz, which
# is fine for short UI tones.
_BUFFER = 2048
_cache: dict[tuple, "pygame.mixer.Sound"] = {}


def pre_init():
    """Set the mixer parameters BEFORE pygame.init() auto-starts the mixer.

    This must run before pygame.init(); otherwise the mixer comes up with a tiny
    default buffer and the tones crackle. Safe to call even if audio is absent.
    """
    try:
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2,
                              buffer=_BUFFER)
    except Exception:
        pass


def init():
    global _READY, _CHANNELS, _RATE
    try:
        if pygame.mixer.get_init() is None:
            # pre_init() wasn't called (or failed); init directly with a buffer.
            pygame.mixer.init(frequency=44100, size=-16, channels=2,
                              buffer=_BUFFER)
        rate, _size, chans = pygame.mixer.get_init()
        _RATE, _CHANNELS = rate, chans
        _READY = True
    except Exception:
        _READY = False
    return _READY


def tone(freq: float, ms: int = 250, volume: float = 0.35) -> "pygame.mixer.Sound | None":
    """Return a cached Sound for a sine tone, or None if audio is unavailable."""
    if not _READY:
        return None
    key = (round(freq, 1), ms, round(volume, 2), _RATE, _CHANNELS)
    snd = _cache.get(key)
    if snd is not None:
        return snd
    n = int(_RATE * ms / 1000)
    amp = int(volume * 32767)
    attack = max(1, int(n * 0.02))
    release = max(1, int(n * 0.12))
    buf = array.array("h")
    for i in range(n):
        env = 1.0
        if i < attack:
            env = i / attack
        elif i > n - release:
            env = (n - i) / release
        s = int(amp * env * math.sin(2 * math.pi * freq * i / _RATE))
        buf.append(s)
        if _CHANNELS == 2:
            buf.append(s)
    snd = pygame.mixer.Sound(buffer=buf.tobytes())
    _cache[key] = snd
    return snd


def play(freq: float, ms: int = 250, volume: float = 0.35):
    snd = tone(freq, ms, volume)
    if snd is not None:
        snd.play()
