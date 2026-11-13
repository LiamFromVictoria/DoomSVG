"""End-to-end route: start -> courtyard -> door -> imp hall -> exit. Kills what it can on the way.

Usage: python tests/route.py [god]   ('god' keeps attacking enemies from mattering by checking state only)
"""
import asyncio
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from play import Game  # noqa: E402

WAYPOINTS = [
    ("corridor", 3, 11),
    ("courtyard", 3, 14.5),
    ("east side", 8.5, 21),
    ("door", 11.2, 21),
    ("through door", 15, 21),
    ("imp hall", 18.5, 21),
    ("north E", 21, 24.5),
    ("corridor EF", 21, 29),
    ("exit room", 21, 33),
    ("switch", 21, 35.3),
]


async def fight(g, budget=5.0):
    """Shoot at any awake, alive enemy with line of sight that is close enough."""
    end = time.time() + budget
    while time.time() < end:
        s = await g.state()
        targets = []
        for i in range(6):
            x, y, al = await g.enemy(i)
            los, aw = (await g.get("#L6", f"--los{i}", f"--aw{i}"))
            d = ((x - s["px"]) ** 2 + (y - s["py"]) ** 2) ** 0.5
            if al and float(los) and float(aw) and d < 12:
                targets.append((d, i, x, y))
        if not targets:
            return
        d, i, x, y = min(targets)
        await g.aim_at(x, y, tol=0.08, budget=0.6)
        await g.press(True)
        await asyncio.sleep(0.5)
        await g.press(False)


async def main():
    god = "god" in sys.argv[1:]
    g = await Game().start("#play", path=pathlib.Path(__file__).resolve().parent.parent / "build" / "doom-god.svg" if god else None)
    await g.park()
    await asyncio.sleep(0.3)
    for name, x, y in WAYPOINTS:
        await fight(g)
        dist = await g.goto(x, y)
        s = await g.state()
        print(f"{name:13} -> ({s['px']:.2f},{s['py']:.2f}) miss={dist:.2f} hp={s['hp']:.0f} ammo={s['ammo']:.0f} kills={s['kills']:.0f} door={s['door']:.2f} won={s['won']:.0f} dead={s['dead']:.0f}", flush=True)
        await g.shot(f"route_{name.replace(' ', '_')}")
        if s["dead"] or s["won"]:
            break
    await asyncio.sleep(0.5)
    await g.shot("route_end")
    await g.close()


if __name__ == "__main__":
    asyncio.run(main())
