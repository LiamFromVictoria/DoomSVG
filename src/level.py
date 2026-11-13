"""E1M1-ish level for DOOM.SVG.

World units: 1 unit = wall height. x grows east, y grows north. Open space is the union of
axis-aligned ROOMS; everything else is solid. All wall faces sit on a 0.5 grid so the renderer
can tell x-facing from y-facing walls from the hit point alone.
"""
from dataclasses import dataclass, field
import math


@dataclass(frozen=True)
class Room:
    name: str
    x0: float
    y0: float
    x1: float
    y1: float


# Corridors reach 3 units into the rooms they join: the union-of-boxes distance is a max of
# per-box inside distances, which dips at a junction unless the corridor box already contains
# a full player-width of the room beyond its mouth.
ROOMS = [
    Room("A", 0, 0, 6, 8),          # start room
    Room("AC", 2, 5, 4, 15),        # corridor A -> C
    Room("C", -4, 12, 10, 24),      # pillar courtyard
    Room("CD", 7, 20, 19, 22),      # door corridor C -> E
    Room("E", 16, 14, 26, 26),      # imp hall
    Room("EF", 20, 23, 22, 33),     # corridor E -> F
    Room("F", 17, 30, 25, 36),      # exit room
]

# 2x2 pillar grid in C via domain repetition: centres (3 +- 2.5, 18.5 +- 2), half size 0.5
PILLARS = dict(cx=3, cy=18.5, ox=2.5, oy=2, h=0.5)
# solid crate stack in the middle of E
CRATE = dict(cx=21, cy=20, h=1)
# sliding door across corridor CD; slides north by DOOR_SLIDE units when open
DOOR = dict(cx=12.5, cy=21, hx=0.5, hy=1)
DOOR_SLIDE = 2.2
DOOR_TRIGGER = (10.2, 19.2, 14.8, 22.8)
DOOR_OPEN_TIME = 0.9  # seconds of standing near the door to open it fully

EXIT = (20.2, 34.9, 21.8, 36.1)   # player box that ends the level
EXIT_SWITCH = (21, 36)            # where the switch texture sits on the north wall
START = (3.0, 1.6, 90.0)          # x, y, heading in degrees (90 = north)

# Wall atlas slots (64x64 texels each)
TEX = ["tech", "brown", "stone", "marble", "door", "pillar", "crate", "exit"]
T = {name: i for i, name in enumerate(TEX)}


@dataclass(frozen=True)
class Enemy:
    kind: str                 # "zombie" | "imp"
    path: tuple               # loop of waypoints
    speed: float              # units / second along the path
    wake: tuple               # player box that wakes it (x0, y0, x1, y1)
    phase: float              # attack duty-cycle phase offset (s)


ENEMY_STATS = {
    # hp, attack range, damage per second while in the attack part of the cycle, cycle s, attack window s
    "zombie": dict(hp=20, range=9, dps=10, cycle=2.4, window=0.5),
    "imp": dict(hp=60, range=11, dps=14, cycle=3.0, window=0.7),
}

ENEMIES = [
    Enemy("zombie", ((-2, 14), (-2, 22.5), (8.5, 22.5), (8.5, 14)), 1.3, (-5, 10.5, 11, 25), 0.0),
    Enemy("zombie", ((1.5, 23), (5.5, 23)), 0.9, (-5, 10.5, 11, 25), 1.1),
    Enemy("imp", ((18, 16), (24.5, 16), (24.5, 24.5), (18, 24.5)), 1.6, (13.5, 13, 27, 27), 0.4),
    Enemy("imp", ((25, 18), (25, 25)), 1.0, (13.5, 13, 27, 27), 1.7),
    Enemy("zombie", ((17.2, 23), (17.2, 15)), 1.1, (13.5, 13, 27, 27), 0.9),
    Enemy("imp", ((18.5, 34.5), (23.5, 34.5)), 1.2, (16, 27.5, 26, 37), 0.2),
]

ITEM_KINDS = {"medkit": dict(health=25), "shells": dict(ammo=12), "stimpack": dict(health=10)}


@dataclass(frozen=True)
class Item:
    kind: str
    x: float
    y: float


ITEMS = [
    Item("stimpack", 3, 10),
    Item("shells", -3, 13),
    Item("medkit", 25, 15),
    Item("shells", 17, 25.2),
    Item("medkit", 24, 31),
]

DECOR = [("barrel", 8.8, 12.8), ("barrel", -3.2, 23.2), ("barrel", 16.8, 14.8)]

START_AMMO = 16
START_HEALTH = 100


def room_inside(r, x, y):
    return min((r.x1 - r.x0) / 2 - abs(x - (r.x0 + r.x1) / 2), (r.y1 - r.y0) / 2 - abs(y - (r.y0 + r.y1) / 2))


def sdf(x, y, door_open=0.0):
    """Reference signed distance (Chebyshev boxes); must match the CSS emitted by build.py."""
    rooms = max(room_inside(r, x, y) for r in ROOMS)
    p = PILLARS
    pill = max(abs(abs(x - p["cx"]) - p["ox"]), abs(abs(y - p["cy"]) - p["oy"])) - p["h"]
    c = CRATE
    crate = max(abs(x - c["cx"]), abs(y - c["cy"])) - c["h"]
    d = DOOR
    door = max(abs(x - d["cx"]) - d["hx"], abs(y - d["cy"] - door_open * DOOR_SLIDE) - d["hy"])
    return min(rooms, pill, crate, door)


def path_keyframes(path):
    """Uniform-speed loop: returns [(fraction, x, y)] and total length."""
    pts = list(path) + [path[0]]
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(seg)
    out, acc = [], 0.0
    for i, (x, y) in enumerate(pts):
        out.append((acc / total, x, y))
        if i < len(seg):
            acc += seg[i]
    return out, total
