# DOOM.SVG

A playable, Doom-flavoured first-person shooter that is **one SVG file with no JavaScript**.
Every wall is raymarched by CSS `calc()`. All game state lives in CSS animations, and all input comes from `:hover` and `:active`.

Open `doom.svg` in a current Chromium browser (built and tested against Chrome 157). It relies on
`@property`, `if()`, `sibling-index()`, container style queries with range syntax, CSS trig/`round()`/`mod()`
and `:has()`, so Firefox and Safari will not run it.

## Playing

| Where the cursor is (over the 3D view) | What happens |
| --- | --- |
| top band | walk forward |
| bottom band | walk backward |
| left / right thirds | turn (outer edge turns faster) |
| centre | stand still |
| mouse button held anywhere on the view | fire the shotgun (needs shells) |

The view is a joystick: rest the cursor in a zone, don't click it. The joystick widget in the status bar shows the zone you are in.
Doors open while you stand next to them. The level (an E1M1 homage) ends at the EXIT switch in the far room.
Pickups: stimpack, medikits and shell boxes. Enemies: former humans and imps, awake once you enter their area.
**RESTART**/**AGAIN** reloads the file.

## How it works

The game runs with no script, so values can only flow *down* the DOM. The SVG is a chain of nested `<g>`
levels (`#L0` … `#L6`), and each level computes what the levels below it need:

| level | holds |
| --- | --- |
| L0 | clock + turning integrators → heading |
| L1 | 2×64 movement integrators (one per heading per axis) → position |
| L2 | proximity triggers → wake / pickup / door / exit integrators |
| L3 | latched flags, PVS zone, enemy patrol copy A |
| L4 | camera, per-enemy line-of-sight marches, aim cone, fire + damage integrators |
| L5 | enemy alive flags, patrol copy B (stops on death), damage-to-player integrators |
| L6 | health/ammo/kills, sprite projection, collision probes, everything you see |

* **Integrators.** A registered custom property animated from 0 to 100000 over 100000 s with a `linear`
  timing function is a stopwatch, and pausing the animation keeps its value. `animation-play-state` is switched by
  `:has(.zone:hover)` or by `if(style(--flag: 1): running; else: paused)` on a value inherited from a level
  above. Position is `start + speed · Σ cos/sin(heading) · time-walked-in-that-heading`.
* **Collision without feedback loops.** CSS cannot feed a value back up the tree, but the browser's hit-testing can.
  Each movement zone holds stacked rectangles for "x allowed", "y allowed" and "both". If a probe of the distance
  field says a move would bring you within 0.32 units of a wall, the matching rectangle gets `display:none`. Chrome
  then re-hit-tests the still cursor on the next frame, `:hover` falls through to a rectangle that allows less
  movement, and that axis's integrators pause. You slide along walls. Ammo uses the same trick: the fire rectangle
  vanishes at 0 shells.
* **Raymarching.** The level is a signed distance field (union of axis-aligned rooms, a domain-repeated pillar grid,
  a crate and a sliding door), written once as a CSS expression. The 112 columns form 14 groups of 8:
  * each group cone-marches 12 steps along its centre ray, which shares the empty-space prefix;
  * each column then runs 3 secant-accelerated sphere-tracing steps from where its group stopped;
  * `sibling-index()` gives each column its ray, so one generic rule drives all of them.
* **PVS.** At build time, rays are sampled from every room to find which rooms and obstacles can be seen. In-game,
  `@container style(--zone: N)` swaps in a smaller distance field for the room you are in (start room: 4 terms
  instead of 10).
* **Sprites.** Each entity gets a packed sort key, `depth·1000·16 + id`. `var()` passes registered numbers along at
  about 6 significant digits, so every packed value stays under 10⁶. Each group picks its two nearest overlapping
  entities with `min()`, and each column shows the front one if it is nearer than the wall.
* **Textures and light.** The art is authored as SVG, rasterised to PNG atlases at build time, and embedded as data URIs.
  Every texture is baked at 8 light levels (sprites at 4), Doom-colormap style. A column picks its texel and light
  level purely through the `transform` of a `<use>` inside a 1-column-wide nested `<svg>`.
* **One-shot effects.** Death frames, pickup messages and flashes start when
  `animation-name: if(style(--flag: 1): anim; else: none)` flips.

## Building

```
pip install websockets          # the build drives headless Chrome over CDP to rasterise the SVG art
python src/build.py             # -> doom.svg
python src/build.py --cols=96   # faster; --cols=160 sharper; --k1/--k2 change march steps
python src/build.py --god       # -> build/doom-god.svg, enemies do no damage (for tests)
```

`src/level.py` holds the map, enemies and items, and `src/art.py` holds all art and the HUD. `src/pvs.py` computes the
visibility sets (cached in `build/cache`, about 2 minutes on first run).

## Tests

The tests drive Chrome over CDP and read computed styles. That is test-only script; the game has none.

```
python tests/route.py god       # bot plays start -> door -> exit, screenshots in build/shots
python tests/perf.py            # fps / style-recalc time at a few spots
python tests/accuracy.py        # per-column wall depth vs an exact Python march
```

## Limits

* About 23–32 fps on the dev machine at 112 columns. The cost is Blink's `calc()` evaluation (~0.25–0.45 µs per
  math node per frame).
* Turning moves in 5.6° steps (smoothed by a transition), because movement is integrated per quantised heading.
* Enemies follow fixed patrol loops in their rooms and always face you. They attack in bursts while they can see you.
* A shot hits every live enemy in the aim cone, so corpses never block shots.
* No sound, no keyboard (CSS cannot see keys without a focused form control).
