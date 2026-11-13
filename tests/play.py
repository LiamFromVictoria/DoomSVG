"""Playtest driver for doom.svg (test-only CDP; the game itself has no script).

The SVG is shown at 1280x800, so view units map to pixels x4.
"""
import asyncio
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from cdp import Browser, file_url  # noqa: E402

SCALE = 4
SHOTS = ROOT / "build" / "shots"

# pad zone centres in view units: (turn column, move row)
COLX = {"tl2": 20, "tl1": 78, "": 160, "tr1": 242, "tr2": 300}
ROWY = {"fw": 30, "": 84, "bk": 137}


class Game:
    async def start(self, url_suffix="", path=None):
        self.b = await Browser().start()
        await self.b.viewport(1280, 800)
        await self.b.goto(file_url(path or ROOT / "doom.svg") + url_suffix, settle=1.0)
        self.cursor = (20 * SCALE, 190 * SCALE)
        self.buttons = 0
        SHOTS.mkdir(parents=True, exist_ok=True)
        return self

    async def get(self, el, *props):
        js = ",".join(f"'{p}'" for p in props)
        return await self.b.eval(
            f"(() => {{ const cs = getComputedStyle(document.querySelector('{el}')); return [{js}].map(p => cs.getPropertyValue(p).trim()); }})()"
        )

    async def state(self):
        names = ["--px", "--py", "--ra", "--hp", "--ammo", "--kills", "--okx", "--oky", "--door", "--fire", "--dead", "--won"]
        vals = await self.get("#L6", *names)
        return {n[2:]: float(v) for n, v in zip(names, vals)}

    async def click_at(self, vx, vy):
        x, y = vx * SCALE, vy * SCALE
        await self.b.mouse("mouseMoved", x, y)
        await self.b.mouse("mousePressed", x, y, "left", 1)
        await self.b.mouse("mouseReleased", x, y, "left", 0)
        self.cursor = (x, y)
        await asyncio.sleep(0.3)

    async def move_to(self, x, y):
        self.cursor = (x, y)
        await self.b.mouse("mouseMoved", x, y, "left" if self.buttons else "none", self.buttons)

    async def hover(self, turn="", move=""):
        await self.move_to(COLX[turn] * SCALE, ROWY[move] * SCALE)

    async def park(self):
        """Centre of the view: no movement, no turning (fire still works)."""
        await self.hover("", "")

    async def press(self, down=True):
        """Hold/release the fire button where the cursor currently is."""
        self.buttons = 1 if down else 0
        x, y = self.cursor
        await self.b.mouse("mousePressed" if down else "mouseReleased", x, y, "left", self.buttons)

    async def enemy(self, i):
        x, y, al = await self.get("#L6", f"--ebx{i}", f"--eby{i}", f"--al{i}")
        return float(x), float(y), int(float(al))

    async def aim_at(self, x, y, tol=0.1, budget=6.0):
        """Turn with the slow zones until the heading points at (x, y). Returns the final angle error."""
        loop = asyncio.get_running_loop()
        end = loop.time() + budget
        diff = math.pi
        while loop.time() < end:
            s = await self.state()
            want = math.atan2(y - s["py"], x - s["px"])
            diff = (want - s["ra"] + math.pi) % (2 * math.pi) - math.pi
            if abs(diff) < tol:
                break
            await self.hover("tl1" if diff > 0 else "tr1", "")
            await asyncio.sleep(max(0.03, abs(diff) / 1.6 - 0.02))
            await self.park()
            await asyncio.sleep(0.12)  # let the heading transition settle
        await self.park()
        return diff

    async def walk(self, seconds, move="fw"):
        await self.hover("", move)
        await asyncio.sleep(seconds)
        await self.park()

    async def goto(self, x, y, reach=0.45, budget=20.0):
        """Turn toward (x, y) and walk until within `reach`. Returns final distance."""
        loop = asyncio.get_running_loop()
        end = loop.time() + budget
        while loop.time() < end:
            s = await self.state()
            dist = math.hypot(x - s["px"], y - s["py"])
            if dist < reach or s["dead"]:
                break
            await self.aim_at(x, y, tol=0.07, budget=3)
            await self.walk(max(0.1, dist / 4.2 * 0.85))
        s = await self.state()
        await self.park()
        return math.hypot(x - s["px"], y - s["py"])

    async def shot(self, name):
        await self.b.screenshot(SHOTS / f"{name}.png")

    async def close(self):
        await self.b.close()
