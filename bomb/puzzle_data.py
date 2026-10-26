"""Fixed puzzle content shared by the program and the printed manuals.

Anything here that a player must look up in a manual (morse table, Simon
translation, mazes, the navigation map, the logic circuits) is defined ONCE in
this module.  ``tools/generate_manuals.py`` renders the manuals from exactly
these values, so the paper the players hold always matches the bomb.
"""

from __future__ import annotations

import math
import random

# --------------------------------------------------------------------------- #
# Puzzle 2 -- Morse Code
# --------------------------------------------------------------------------- #
MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.",
    "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
    "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
    "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
}

# Words the Morse puzzle can pick (kept short and unambiguous).
MORSE_WORDS = [
    "WIRE", "FUSE", "BOLT", "CODE", "GEAR", "CLIP", "BOMB", "LOCK",
    "COIL", "GRID", "NODE", "VOLT", "FLUX", "RELAY", "TIMER", "SPARK",
]

# --------------------------------------------------------------------------- #
# Puzzle 3 -- Simon with a Twist
# A colour shown on the LED translates to one or more buttons to press.
# --------------------------------------------------------------------------- #
SIMON_RULES = {
    "red": ["blue"],
    "yellow": ["green", "green"],
    "green": ["red"],
    "blue": ["yellow", "yellow"],
}
SIMON_SEQUENCE_LEN = 4   # number of flashed colours per round

# --------------------------------------------------------------------------- #
# Puzzle 4 -- Invisible Maze
# Mazes are generated deterministically from fixed seeds so the program and the
# manual produce byte-identical layouts.
# --------------------------------------------------------------------------- #
MAZE_SEEDS = [11, 23, 42]     # => "Maze 1 / 2 / 3" in the manual
MAZE_W = 7
MAZE_H = 7

# directions: (dx, dy) and the opposite, for carving passages
_DIRS = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
_OPP = {"N": "S", "S": "N", "E": "W", "W": "E"}


def generate_maze(seed: int, w: int = MAZE_W, h: int = MAZE_H) -> dict:
    """Recursive-backtracker maze.  ``cells[y][x]`` is the set of open sides."""
    rng = random.Random(seed)
    cells = [[set() for _ in range(w)] for _ in range(h)]
    visited = [[False] * w for _ in range(h)]
    stack = [(0, 0)]
    visited[0][0] = True
    while stack:
        x, y = stack[-1]
        nbrs = []
        for d, (dx, dy) in _DIRS.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx]:
                nbrs.append((d, nx, ny))
        if not nbrs:
            stack.pop()
            continue
        d, nx, ny = rng.choice(nbrs)
        cells[y][x].add(d)
        cells[ny][nx].add(_OPP[d])
        visited[ny][nx] = True
        stack.append((nx, ny))
    return {"w": w, "h": h, "cells": cells,
            "start": (0, h - 1), "goal": (w - 1, 0)}


def maze_count() -> int:
    return len(MAZE_SEEDS)


def get_maze(index: int) -> dict:
    return generate_maze(MAZE_SEEDS[index % len(MAZE_SEEDS)])


# --------------------------------------------------------------------------- #
# Puzzle 5 -- Navigation
# A route is a start heading plus a list of (turn, miles) steps.  The endpoint
# is computed from the steps, and whichever landmark sits on the endpoint is the
# answer -- so directions, map and answer are consistent by construction.
# --------------------------------------------------------------------------- #
# Compass bearings: 0 = North (up), measured clockwise.
def _bearing_vec(bearing_deg: float) -> tuple[float, float]:
    a = math.radians(bearing_deg)
    return (math.sin(a), -math.cos(a))   # +x East, -y North (screen coords)


ROUTES = [
    {"start_bearing": 0,
     "steps": [("none", 0, 4), ("right", 90, 3), ("left", 45, 2.83)]},
    {"start_bearing": 90,
     "steps": [("none", 0, 5), ("left", 135, 2.83), ("left", 90, 3)]},
    {"start_bearing": 0,
     "steps": [("right", 45, 4.24), ("right", 90, 4.24), ("left", 90, 2)]},
]

NAV_START = (1.5, 11.0)   # start point in map "miles" coordinates


def _route_endpoint(route) -> tuple[float, float]:
    x, y = NAV_START
    bearing = route["start_bearing"]
    for turn, deg, miles in route["steps"]:
        if turn == "right":
            bearing += deg
        elif turn == "left":
            bearing -= deg
        dx, dy = _bearing_vec(bearing)
        x += dx * miles
        y += dy * miles
    return (round(x, 2), round(y, 2))


# Landmark letters placed on the map.  Route endpoints become the "real"
# landmarks; the rest are decoys.  Coordinates are in miles.
_endpoints = [_route_endpoint(r) for r in ROUTES]
NAV_LANDMARKS = {
    "A": _endpoints[0],
    "B": _endpoints[1],
    "C": _endpoints[2],
    "D": (10.8, 6.5),
    "E": (3.5, 2.0),
    "F": (11.5, 3.5),
    "G": (1.8, 4.5),
    "H": (5.5, 8.5),
}
NAV_ANSWERS = ["A", "B", "C"]     # route i -> NAV_ANSWERS[i]
NAV_NAMES = {
    "A": "Old Mill", "B": "Stone Bridge", "C": "Watchtower", "D": "Lake House",
    "E": "Fox Den", "F": "Pine Camp", "G": "Well", "H": "Chapel",
}


def route_instructions(route) -> list[str]:
    """Human-readable turn-by-turn text for a route."""
    out = ["Start at the trailhead, facing "
           + _compass_name(route["start_bearing"]) + "."]
    for turn, deg, miles in route["steps"]:
        if turn == "none":
            out.append(f"Walk {_miles(miles)} straight ahead.")
        else:
            out.append(f"Turn {deg}° to the {turn}, then walk "
                       f"{_miles(miles)}.")
    out.append("Where did you end up?")
    return out


def _miles(m: float) -> str:
    if abs(m - round(m)) < 0.01:
        return f"{int(round(m))} miles"
    return f"{m:.2f} miles"


def _compass_name(bearing: float) -> str:
    names = ["North", "North-East", "East", "South-East",
             "South", "South-West", "West", "North-West"]
    return names[int((bearing % 360) / 45 + 0.5) % 8]


# --------------------------------------------------------------------------- #
# Puzzle 6 -- Turn on the LED (logic gates)
# A circuit is inputs + gates with fixed draw positions (0..1 normalised).
# Node ref is an input name ("i0") or a gate id ("g0").  Output is a gate id.
# --------------------------------------------------------------------------- #
CIRCUITS = [
    {
        "id": "ALPHA",
        "inputs": {"i0": (0.08, 0.25), "i1": (0.08, 0.55), "i2": (0.08, 0.85)},
        "gates": [
            {"id": "g0", "type": "AND", "in": ["i0", "i1"], "pos": (0.42, 0.40)},
            {"id": "g1", "type": "NOT", "in": ["i2"], "pos": (0.42, 0.85)},
            {"id": "g2", "type": "OR", "in": ["g0", "g1"], "pos": (0.74, 0.60)},
        ],
        "output": "g2",
    },
    {
        "id": "BRAVO",
        "inputs": {"i0": (0.08, 0.20), "i1": (0.08, 0.50), "i2": (0.08, 0.80)},
        "gates": [
            {"id": "g0", "type": "XOR", "in": ["i0", "i1"], "pos": (0.42, 0.35)},
            {"id": "g1", "type": "AND", "in": ["i1", "i2"], "pos": (0.42, 0.78)},
            {"id": "g2", "type": "AND", "in": ["g0", "g1"], "pos": (0.74, 0.56)},
        ],
        "output": "g2",
    },
    {
        "id": "CICERO",
        "inputs": {"i0": (0.08, 0.30), "i1": (0.08, 0.70)},
        "gates": [
            {"id": "g0", "type": "NOT", "in": ["i0"], "pos": (0.40, 0.30)},
            {"id": "g1", "type": "XOR", "in": ["g0", "i1"], "pos": (0.72, 0.50)},
        ],
        "output": "g1",
    },
]

_GATE_FN = {
    "AND": lambda a: a[0] and a[1],
    "OR": lambda a: a[0] or a[1],
    "XOR": lambda a: a[0] ^ a[1],
    "NOT": lambda a: 0 if a[0] else 1,
}


def eval_circuit(circuit: dict, input_state: dict) -> dict:
    """Return {node_ref: 0/1} for all inputs and gates."""
    vals = {name: int(bool(input_state.get(name, 0)))
            for name in circuit["inputs"]}
    for g in circuit["gates"]:
        args = [int(bool(vals[ref])) for ref in g["in"]]
        vals[g["id"]] = int(bool(_GATE_FN[g["type"]](args)))
    return vals


def circuit_output(circuit: dict, input_state: dict) -> int:
    return eval_circuit(circuit, input_state)[circuit["output"]]


# --------------------------------------------------------------------------- #
# Puzzle 7 -- Rhythm Lock
# Each rhythm is a list of button colours to replay, in order.
# --------------------------------------------------------------------------- #
RHYTHMS = [
    ["red", "red", "blue", "green"],
    ["green", "yellow", "yellow", "red", "blue"],
    ["blue", "green", "red", "red", "yellow"],
    ["yellow", "blue", "blue", "green"],
]

# Pitch (Hz) for each button colour, used by the tone generator.
BUTTON_TONE = {"red": 294, "yellow": 370, "green": 440, "blue": 587}
