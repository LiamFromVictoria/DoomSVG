"""Potentially-visible sets: which SDF terms a ray cast from inside each room can ever touch.

Rendering marches with only the current room's terms; omitting a room would turn its open
space solid and omitting an obstacle would hide it, so a term is kept if any sampled ray
passes through that room (dense samples along the ray) or ends on that obstacle, with the
door both closed and open. Results are cached by level geometry.
"""
import hashlib
import json
import math
import pathlib

import level as L

CACHE = pathlib.Path(__file__).resolve().parent.parent / "build" / "cache"
OBSTACLES = ("pill", "crate", "door")


def _terms(x, y, door):
    p, c, d = L.PILLARS, L.CRATE, L.DOOR
    return {
        "pill": max(abs(abs(x - p["cx"]) - p["ox"]), abs(abs(y - p["cy"]) - p["oy"])) - p["h"],
        "crate": max(abs(x - c["cx"]), abs(y - c["cy"])) - c["h"],
        "door": max(abs(x - d["cx"]) - d["hx"], abs(y - d["cy"] - door * L.DOOR_SLIDE) - d["hy"]),
    }


def _sdf(x, y, door):
    return min(max(L.room_inside(r, x, y) for r in L.ROOMS), *_terms(x, y, door).values())


def _cast(x, y, ux, uy, door, seen):
    s = 0.0
    for _ in range(400):
        d = _sdf(x + ux * s, y + uy * s, door)
        if d < 1e-4 or s > 90:
            break
        s += d
    hx, hy = x + ux * s, y + uy * s
    # rooms the ray travels through (dense samples) and the room whose wall it ends on
    t = 0.0
    while t <= s:
        px, py = x + ux * t, y + uy * t
        for r in L.ROOMS:
            if L.room_inside(r, px, py) > -0.02:
                seen.add(r.name)
        t += 0.1
    for r in L.ROOMS:
        if L.room_inside(r, hx, hy) > -0.05:
            seen.add(r.name)
    for name, v in _terms(hx, hy, door).items():
        if v < 0.05:
            seen.add(name)


def compute(step=0.75, rays=240, inset=0.3):
    """{zone: [term names]} with zone = room index * 2 + (door open ? 1 : 0)."""
    key = hashlib.sha256(json.dumps([L.ROOMS, L.PILLARS, L.CRATE, L.DOOR, L.DOOR_SLIDE, step, rays, inset, 2], default=str).encode()).hexdigest()[:16]
    hit = CACHE / f"pvs-{key}.json"
    if hit.exists():
        return {int(k): v for k, v in json.loads(hit.read_text()).items()}
    out = {}
    for ri, room in enumerate(L.ROOMS):
        for opened in (0, 1):
            seen = {room.name}
            nx = max(2, int((room.x1 - room.x0 - 2 * inset) / step) + 1)
            ny = max(2, int((room.y1 - room.y0 - 2 * inset) / step) + 1)
            for i in range(nx):
                for j in range(ny):
                    x = room.x0 + inset + (room.x1 - room.x0 - 2 * inset) * i / (nx - 1)
                    y = room.y0 + inset + (room.y1 - room.y0 - 2 * inset) * j / (ny - 1)
                    if _sdf(x, y, 0) < inset * 0.9:
                        continue
                    for k in range(rays):
                        a = 2 * math.pi * k / rays
                        for door in ((0.0, 0.5, 1.0) if opened else (0.0,)):
                            _cast(x, y, math.cos(a), math.sin(a), door, seen)
            names = [r.name for r in L.ROOMS if r.name in seen] + [o for o in OBSTACLES if o in seen]
            out[ri * 2 + opened] = names
            print(f"pvs {room.name} door={'open' if opened else 'shut'}: {names}")
    CACHE.mkdir(parents=True, exist_ok=True)
    hit.write_text(json.dumps(out))
    return out

if __name__ == "__main__":
    compute()
