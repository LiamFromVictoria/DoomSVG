"""Frame-time probe at a few spots along the level route (test-only CDP)."""
import asyncio
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from play import Game  # noqa: E402

FRAMES = """new Promise(r => { let n = 0, t0 = performance.now(), worst = 0, last = t0;
  function f(t) { worst = Math.max(worst, t - last); last = t; n++; if (t - t0 < 2500) requestAnimationFrame(f); else r([n / ((t - t0) / 1000), worst]); }
  requestAnimationFrame(f); })"""


async def measure(g, label):
    m0 = await g.b.metrics()
    fps, worst = await g.b.eval(FRAMES)
    m1 = await g.b.metrics()
    style = (m1["RecalcStyleDuration"] - m0["RecalcStyleDuration"]) / (fps * 2.5) * 1000
    zone = (await g.get("#L6", "--zone"))[0]
    print(f"{label:22} zone={zone:>2} fps={fps:5.1f} worst={worst:6.1f}ms style={style:5.1f}ms", flush=True)


async def main():
    g = await Game().start("#play")
    await g.park()
    await asyncio.sleep(0.5)
    await measure(g, "start room")
    await g.move_to(80, 760)
    await measure(g, "start, cursor on HUD")
    await g.walk(2.6)
    await measure(g, "courtyard entrance")
    await g.move_to(80, 760)
    await measure(g, "entrance, cursor on HUD")
    await g.walk(1.2, "bk")
    await measure(g, "back in corridor")
    await g.hover("tr1", "")
    await measure(g, "corridor turning")
    await g.close()

if __name__ == "__main__":
    asyncio.run(main())
