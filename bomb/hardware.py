"""Hardware abstraction for Player 2's controls.

On a real Raspberry Pi this drives two RGB LEDs, four buttons and a rotary
encoder through ``gpiozero``.  On any other machine (no GPIO) it falls back to a
keyboard/mouse *mock* so the whole game is playable and testable on a desktop:

    buttons red/yellow/green/blue  ->  keys  r / y / g / b
    rotary encoder                 ->  mouse wheel, or ',' (CCW) / '.' (CW)

Both backends expose the same tiny interface:

    hw.led_a.set_color((r, g, b))      # 0..255 per channel
    hw.led_b.off()
    hw.button_state["red"]             # bool, held right now
    inputs = hw.poll()                 # edges + encoder delta since last poll
        inputs.button_down  -> list of colours pressed this poll
        inputs.button_up    -> list of colours released this poll
        inputs.encoder_delta-> int, +clockwise / -counter-clockwise
    hw.process_event(event)            # (mock only) feed it pygame events
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from . import config


@dataclass
class Inputs:
    button_down: list = field(default_factory=list)
    button_up: list = field(default_factory=list)
    encoder_delta: int = 0


class _LED:
    """Common LED wrapper; remembers its colour for the on-screen mock panel."""

    def __init__(self, gpio_led=None):
        self._gpio = gpio_led
        self.color = (0, 0, 0)

    def set_color(self, rgb):
        r, g, b = (max(0, min(255, int(c))) for c in rgb)
        self.color = (r, g, b)
        if self._gpio is not None:
            self._gpio.color = (r / 255, g / 255, b / 255)

    def off(self):
        self.set_color((0, 0, 0))


class _BaseHardware:
    is_mock = True

    def __init__(self):
        self.led_a = _LED()
        self.led_b = _LED()
        self.button_state = {c: False for c in config.BTN_ORDER}

    # subclasses implement poll(); mock also implements process_event()
    def poll(self) -> Inputs:
        return Inputs()

    def process_event(self, event):
        pass

    def all_leds_off(self):
        self.led_a.off()
        self.led_b.off()

    def cleanup(self):
        self.all_leds_off()


class MockHardware(_BaseHardware):
    """Desktop backend driven by pygame keyboard/mouse events."""

    is_mock = True

    def __init__(self):
        super().__init__()
        self._key_to_btn = {getattr(pygame, "K_" + k): c
                            for c, k in config.MOCK_BUTTON_KEYS.items()}
        self._pending_down: list[str] = []
        self._pending_up: list[str] = []
        self._enc_delta = 0

    def process_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in self._key_to_btn:
                c = self._key_to_btn[event.key]
                if not self.button_state[c]:
                    self.button_state[c] = True
                    self._pending_down.append(c)
            elif event.key == pygame.K_COMMA:
                self._enc_delta -= 1
            elif event.key == pygame.K_PERIOD:
                self._enc_delta += 1
        elif event.type == pygame.KEYUP:
            if event.key in self._key_to_btn:
                c = self._key_to_btn[event.key]
                if self.button_state[c]:
                    self.button_state[c] = False
                    self._pending_up.append(c)
        elif event.type == pygame.MOUSEWHEEL:
            self._enc_delta += event.y

    def poll(self) -> Inputs:
        inp = Inputs(self._pending_down, self._pending_up, self._enc_delta)
        self._pending_down = []
        self._pending_up = []
        self._enc_delta = 0
        return inp


class PiHardware(_BaseHardware):
    """Raspberry Pi backend using gpiozero."""

    is_mock = False

    def __init__(self):
        from gpiozero import RGBLED, Button, RotaryEncoder

        active_high = not config.LED_COMMON_ANODE
        a, b = config.PINS["led_a"], config.PINS["led_b"]
        self._led_a = RGBLED(a["r"], a["g"], a["b"], active_high=active_high)
        self._led_b = RGBLED(b["r"], b["g"], b["b"], active_high=active_high)

        super().__init__()
        self.led_a = _LED(self._led_a)
        self.led_b = _LED(self._led_b)

        self._buttons = {
            "red": Button(config.PINS["btn_red"], pull_up=True, bounce_time=0.02),
            "yellow": Button(config.PINS["btn_yellow"], pull_up=True, bounce_time=0.02),
            "green": Button(config.PINS["btn_green"], pull_up=True, bounce_time=0.02),
            "blue": Button(config.PINS["btn_blue"], pull_up=True, bounce_time=0.02),
        }
        self._encoder = RotaryEncoder(
            config.PINS["enc_clk"], config.PINS["enc_dt"],
            max_steps=0, wrap=False)
        self._last_steps = self._encoder.steps

    def process_event(self, event):
        pass  # real hardware, nothing to feed

    def poll(self) -> Inputs:
        down, up = [], []
        for c, btn in self._buttons.items():
            pressed = btn.is_pressed
            if pressed and not self.button_state[c]:
                down.append(c)
            elif not pressed and self.button_state[c]:
                up.append(c)
            self.button_state[c] = pressed
        steps = self._encoder.steps
        delta = steps - self._last_steps
        self._last_steps = steps
        return Inputs(down, up, delta)

    def cleanup(self):
        super().cleanup()
        for btn in self._buttons.values():
            btn.close()
        self._encoder.close()
        self._led_a.close()
        self._led_b.close()


def create_hardware(force_mock: bool = False) -> _BaseHardware:
    """Return a PiHardware if gpiozero + real pins are available, else mock."""
    if not force_mock:
        try:
            import gpiozero  # noqa: F401
            # Probe: creating a Device factory fails off-Pi.
            from gpiozero import Device
            Device.ensure_pin_factory()
            return PiHardware()
        except Exception:
            pass
    return MockHardware()
