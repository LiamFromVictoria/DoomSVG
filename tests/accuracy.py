"""Wall-depth accuracy of the CSS raymarcher vs an exact Python march (test-only CDP).

Poses are forced by overriding --px/--py/--ra inline on #L1; every column's --t is compared
with the reference perpendicular distance, reported as wall half-height error in view pixels.
Usage: python tests/accuracy.py [path/to/build.svg]
"""
import asyncio
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import level  # noqa: E402
from play import Game  # noqa: E402

POSES = [(3, 2, 90), (3, 6, 45), (3, 13.5, 70), (3, 18.5, 0), (8, 21, 10), (-2, 22, 300), (8.5, 14, 135), (5, 23, 200)]


def reference(px, py, ang, cx):
    dx, dy = math.cos(ang), math.sin(ang)
    rx, ry = dx + dy * cx, dy - dx * cx
    rl = 1 / math.hypot(rx, ry)
    ux, uy = rx * rl, ry * rl
    s = 0.0
    for _ in range(4000):
        d = level.sdf(px + ux * s, py + uy * s)
        if d < 1e-5:
            break
        s += d
    return s * rl


async def main():
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "doom.svg"
    g = await Game().start("#play", path=path)
    await g.park()
    errs = []
    for px, py, deg in POSES:
        ang = math.radians(deg)
        await g.b.eval(f"(() => {{ const s = document.getElementById('L1').style; s.setProperty('--px', '{px}'); s.setProperty('--py', '{py}'); s.setProperty('--ra', '{ang}'); }})()")
        await asyncio.sleep(0.35)
        ts = await g.b.eval("[...document.querySelectorAll('.col')].map(e => parseFloat(getComputedStyle(e).getPropertyValue('--t')))")
        cols = len(ts)
        for i, t in enumerate(ts):
            cx = (i + 0.5) * 2 / cols - 1
            r = reference(px, py, ang, cx)
            errs.append((abs(80 / t - 80 / r), (px, py, deg, i, round(t, 3), round(r, 3))))
    errs.sort()
    e = [x[0] for x in errs]
    print(f"{path.name}: half-height error px  median={e[len(e) // 2]:.2f}  p90={e[int(len(e) * 0.9)]:.2f}  p99={e[int(len(e) * 0.99)]:.2f}  max={e[-1]:.2f}")
    print("  worst:", [x[1] for x in errs[-3:]])
    await g.close()


if __name__ == "__main__":
    asyncio.run(main())
