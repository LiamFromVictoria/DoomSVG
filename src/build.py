"""Generates doom.svg: a Doom-like FPS that runs on SVG + CSS alone (no script).

Everything that changes over time is a CSS custom property:
  * paused/running CSS animations are integrators (their progress is the state);
  * :hover/:active on invisible control zones decide which integrators run;
  * collision feeds back by hiding control zones (display:none), which moves :hover;
  * walls are sphere-traced per screen column in registered-property calc() chains.
Values only flow down the DOM, so the game is a chain of nested <g> levels L0..L6,
each computing what the levels below need.
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from level import (CRATE, DECOR, DOOR, DOOR_OPEN_TIME, DOOR_SLIDE, DOOR_TRIGGER, ENEMIES, ENEMY_STATS, EXIT,
                   ITEM_KINDS, ITEMS, PILLARS, ROOMS, START, START_AMMO, START_HEALTH, T, TEX, path_keyframes)
import assets
import art
import pvs

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "doom.svg"
ARGS = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)

# ---------------------------------------------------------------- configuration
COLS = int(ARGS.get("cols", 112))   # screen columns (rays); --cols=96 runs faster, --cols=160 looks sharper
GROUP = 8           # columns per cone group
K1 = int(ARGS.get("k1", 12))   # cone-march steps per group (shared by GROUP columns)
K2 = int(ARGS.get("k2", 3))    # secant sphere-tracing steps per column
KL = 6              # line-of-sight march steps per enemy
OVERSHOOT = 0.9     # max extra step beyond the safe sphere step (walls are >= 1 unit thick)
NH = 64             # quantised headings for movement integration (5.6 degree turn steps)
W, VH = 320, 168    # 3D view size in SVG user units
HOR = VH / 2        # horizon
FOC = W / 2         # focal length: 90 degree horizontal FOV
COLW = W / COLS
SPEED = 4.2         # units / s
TURN_SLOW, TURN_FAST = 1.6, 3.6   # rad / s
RADIUS = 0.32       # player collision radius
FIRE_CYCLE = 0.9    # shotgun cycle (s)
GUN_DPS = 55
GUN_RANGE = 16
TEXW = 64           # texels per texture / sprite cell
KEYBIG = 10000000   # sprite sort-key sentinel (keys themselves stay < 1e6)
INF = 100000        # integrator ceiling (s)

GROUPS = COLS // GROUP
assert GROUPS * GROUP == COLS
PVS = pvs.compute()


def num(x):
    if isinstance(x, int):
        return str(x)
    s = f"{x:.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def v(name):
    return f"var(--{name})"


def step(e):
    """1 if e > 0 else 0 (exact integers)."""
    return f"max(sign({e}), 0)"


def sel(c, a, b):
    """c ? a : b for c in {0, 1}; b appears once so nested chains stay linear in size."""
    return f"calc(({c}) * ({a}) + (1 - ({c})) * ({b}))"


def inbox(x, y, box):
    x0, y0, x1, y1 = box
    return step(f"min({x} - {num(x0)}, {num(x1)} - {x}, {y} - {num(y0)}, {num(y1)} - {y})")


def running_if(cond):
    return f"if({cond}: running; else: paused)"


class Registry:
    """@property registrations; registered numbers compute once per element (no token blow-up)."""

    def __init__(self):
        self.props = {}

    def __call__(self, name, syntax="<number>", inherits=True, initial="0"):
        prev = self.props.get(name)
        if prev and prev != (syntax, inherits, initial):
            raise ValueError(f"conflicting registration for --{name}")
        self.props[name] = (syntax, inherits, initial)
        return name

    def css(self):
        return "\n".join(
            f"@property --{n} {{ syntax: '{s}'; inherits: {'true' if i else 'false'}; initial-value: {init}; }}"
            for n, (s, i, init) in self.props.items()
        )


R = Registry()
KEYFRAMES = []


def integrator(prop):
    """A paused-by-default animation whose current value is accumulated running time."""
    R(prop)
    KEYFRAMES.append(f"@keyframes i-{prop} {{ to {{ --{prop}: {INF}; }} }}")
    return f"i-{prop} {INF}s linear forwards"


def decls(d):
    return " ".join(f"--{k}: {val};" for k, val in d.items())


# ---------------------------------------------------------------- the distance field
def sdf_css(X, Y, terms=None):
    """Distance field over the named terms (room names, 'pill', 'crate', 'door'); None = everything."""
    use = lambda name: terms is None or name in terms
    rooms = ", ".join(
        f"min({num((r.x1 - r.x0) / 2)} - abs({X} - {num((r.x0 + r.x1) / 2)}), {num((r.y1 - r.y0) / 2)} - abs({Y} - {num((r.y0 + r.y1) / 2)}))"
        for r in ROOMS if use(r.name)
    )
    p, c, d = PILLARS, CRATE, DOOR
    parts = [f"max({rooms})"]
    if use("pill"):
        parts.append(f"max(abs(abs({X} - {num(p['cx'])}) - {num(p['ox'])}), abs(abs({Y} - {num(p['cy'])}) - {num(p['oy'])})) - {num(p['h'])}")
    if use("crate"):
        parts.append(f"max(abs({X} - {num(c['cx'])}), abs({Y} - {num(c['cy'])})) - {num(c['h'])}")
    if use("door"):
        parts.append(f"max(abs({X} - {num(d['cx'])}) - {num(d['hx'])}, abs({Y} - {num(d['cy'])} - var(--door) * {num(DOOR_SLIDE)}) - {num(d['hy'])})")
    return f"min({', '.join(parts)})" if len(parts) > 1 else f"calc({parts[0]})"


def march(prefix, ox, oy, ux, uy, steps, start="0", terms=None):
    """Secant-accelerated sphere tracing along o + u*s. Emits --{prefix}s{k}, x, y, d; returns final s expr."""
    out = {}
    s = lambda k: f"{prefix}s{k}"
    for k in range(steps + 1):
        for n in ("s", "x", "y", "d"):
            R(f"{prefix}{n}{k}", inherits=False)
        out[s(k)] = start if k == 0 else out.pop("__next")
        out[f"{prefix}x{k}"] = f"calc({ox} + {ux} * {v(s(k))})"
        out[f"{prefix}y{k}"] = f"calc({oy} + {uy} * {v(s(k))})"
        out[f"{prefix}d{k}"] = sdf_css(v(f"{prefix}x{k}"), v(f"{prefix}y{k}"), terms)
        if k == steps:
            break
        dk = v(f"{prefix}d{k}")
        if k == 0:
            out["__next"] = f"calc({v(s(k))} + {dk})"
        else:
            rate = f"max(({v(f'{prefix}d{k-1}')} - {dk}) / max({v(s(k))} - {v(s(k-1))}, 0.0001), 0.02)"
            out["__next"] = f"calc({v(s(k))} + clamp({dk}, {dk} / {rate}, {dk} + {num(OVERSHOOT)}))"
    return out, f"({v(s(steps))} + {v(f'{prefix}d{steps}')})"


# ---------------------------------------------------------------- entity tables
ENEMY_IDS = list(range(len(ENEMIES)))
ITEM_IDS = list(range(len(ENEMIES), len(ENEMIES) + len(ITEMS)))
DECOR_IDS = list(range(ITEM_IDS[-1] + 1, ITEM_IDS[-1] + 1 + len(DECOR)))
ENTITIES = len(ENEMIES) + len(ITEMS) + len(DECOR)
CELL = {name: i for i, name in enumerate(art.SPRITE_CELLS)}
WAKE_BOXES = sorted({e.wake for e in ENEMIES})


def _rooms_at(x, y):
    return {r.name for r in ROOMS if r.x0 <= x <= r.x1 and r.y0 <= y <= r.y1}


# rooms each entity can ever stand in (enemies stay on their patrol loops)
ENTITY_ROOMS = [set().union(*(_rooms_at(x, y) for x, y in e.path)) for e in ENEMIES]
ENTITY_ROOMS += [_rooms_at(it.x, it.y) for it in ITEMS] + [_rooms_at(x, y) for _, x, y in DECOR]

# Declarations that depend on the distance field (or on which entities can be seen) are emitted
# once per PVS zone inside @container style(--zone: z); zone < 0 is the full-level fallback.
ZONED = []


def zoned(selector, fn):
    """fn(terms, ents) -> decls; terms/ents are None for the fallback."""
    ZONED.append((selector, fn))


def zone_css():
    out = []
    for z in [-1] + sorted(PVS):
        terms = None if z < 0 else PVS[z]
        ents = list(range(ENTITIES)) if terms is None else [k for k in range(ENTITIES) if ENTITY_ROOMS[k] & set(terms)]
        cond = "style(--zone < 0)" if z < 0 else f"style(--zone: {z})"
        body = " ".join(f"{sel} {{ {decls(fn(terms, ents))} }}" for sel, fn in ZONED)
        out.append(f"@container {cond} {{ {body} }}")
    return out


def stylesheet():
    css = []
    a0 = math.radians(START[2])
    hstep = 2 * math.pi / NH

    # ---------------- L0: turning + clock
    turns = ["tl1", "tl2", "tr1", "tr2"]
    anims = [integrator("clock")] + [integrator(t) for t in turns]
    R("ang"); R("hd", "<integer>"); R("hdm", "<integer>")
    css.append(
        "#L0 { " + " ".join(f"--ps-{t}: paused;" for t in turns)
        + f" animation: {', '.join(anims)};"
        + f" animation-play-state: running, {', '.join(f'var(--ps-{t})' for t in turns)};"
        + f" --ang: calc({num(a0)} + {num(TURN_SLOW)} * (var(--tl1) - var(--tr1)) + {num(TURN_FAST)} * (var(--tl2) - var(--tr2)));"
        + f" --hd: round(var(--ang) / {num(hstep)}); --hdm: mod(var(--hd), {NH}); }}"
    )
    for t in turns:
        css.append(f"#L0:has(.{t}:hover) {{ --ps-{t}: running; }}")

    # ---------------- L1: movement integrators, one per heading and axis
    for n in ("mv", "mo", "gx", "gy"):
        R(n, "<integer>")
    R("md", "<integer>"); R("px"); R("py"); R("ra")
    anims, states, xs, ys = [], [], [], []
    for j in range(NH):
        th = j * hstep
        anims += [integrator(f"mx{j}"), integrator(f"my{j}")]
        states += [running_if(f"style(--md: {j}) and style(--gx: 1)"), running_if(f"style(--md: {j}) and style(--gy: 1)")]
        if abs(math.cos(th)) > 1e-9:
            xs.append(f"{num(math.cos(th))} * var(--mx{j})")
        if abs(math.sin(th)) > 1e-9:
            ys.append(f"{num(math.sin(th))} * var(--my{j})")
    css.append(
        "#L1 { --mv: 0; --mo: 0; --gx: 0; --gy: 0;"
        f" --md: calc(mod(var(--hdm) + var(--mo), {NH}) + (var(--mv) - 1) * 1000);"
        f" animation: {', '.join(anims)}; animation-play-state: {', '.join(states)};"
        f" --px: calc({num(START[0])} + {num(SPEED)} * ({' + '.join(xs)}));"
        f" --py: calc({num(START[1])} + {num(SPEED)} * ({' + '.join(ys)}));"
        f" --ra: calc(var(--hd) * {num(hstep)}); transition: --ra 0.09s linear; }}"
    )
    css.append("#L1:has(.fw:hover) { --mv: 1; --mo: 0; }")
    css.append(f"#L1:has(.bk:hover) {{ --mv: 1; --mo: {NH // 2}; }}")
    css.append("#L1:has(.gxy:hover) { --gx: 1; --gy: 1; }")
    css.append("#L1:has(.gx:hover) { --gx: 1; }")
    css.append("#L1:has(.gy:hover) { --gy: 1; }")

    # ---------------- L2: player triggers -> wake / pickup / door / exit integrators
    d2, anims, states = {}, [], []
    for b, box in enumerate(WAKE_BOXES):
        R(f"inw{b}", "<integer>")
        d2[f"inw{b}"] = inbox("var(--px)", "var(--py)", box)
        anims.append(integrator(f"w{b}"))
        states.append(running_if(f"style(--inw{b}: 1)"))
    for k, it in zip(ITEM_IDS, ITEMS):
        R(f"nr{k}", "<integer>")
        d2[f"nr{k}"] = step(f"0.7 - hypot(var(--px) - {num(it.x)}, var(--py) - {num(it.y)})")
        anims.append(integrator(f"p{k}"))
        states.append(running_if(f"style(--nr{k}: 1)"))
    R("ndoor", "<integer>"); R("inexit", "<integer>"); R("door")
    d2["ndoor"] = inbox("var(--px)", "var(--py)", DOOR_TRIGGER)
    d2["inexit"] = inbox("var(--px)", "var(--py)", EXIT)
    anims += [integrator("dn"), integrator("ex")]
    states += [running_if("style(--ndoor: 1)"), running_if("style(--inexit: 1)")]
    d2["door"] = f"clamp(0, var(--dn) / {num(DOOR_OPEN_TIME)}, 1)"
    css.append(f"#L2 {{ {decls(d2)} animation: {', '.join(anims)}; animation-play-state: {', '.join(states)}; }}")

    # ---------------- L3: latched flags + patrol copy A (drives AI)
    d3, anims, states = {}, [], []
    for i, e in enumerate(ENEMIES):
        R(f"aw{i}", "<integer>")
        d3[f"aw{i}"] = f"sign(var(--w{WAKE_BOXES.index(e.wake)}))"
    # PVS zone (first room holding the player) * 2 + 1 once the door has started opening
    R("zone", "<integer>")
    room = "-1"
    for ri in reversed(range(len(ROOMS))):
        r = ROOMS[ri]
        room = sel(inbox("var(--px)", "var(--py)", (r.x0, r.y0, r.x1, r.y1)), ri, room)
    d3["zone"] = f"calc({room} * 2 + {step('var(--door) - 0.001')})"
    for k in ITEM_IDS:
        R(f"pk{k}", "<integer>")
        d3[f"pk{k}"] = "sign(var(--p%d))" % k
    R("won", "<integer>")
    d3["won"] = "sign(var(--ex))"
    for i, e in enumerate(ENEMIES):
        frames, total = path_keyframes(e.path)
        for copy in ("a", "b"):
            R(f"e{copy}x{i}"); R(f"e{copy}y{i}")
            body = " ".join(f"{num(f * 100)}% {{ --e{copy}x{i}: {num(x)}; --e{copy}y{i}: {num(y)}; }}" for f, x, y in frames)
            KEYFRAMES.append(f"@keyframes pat{copy}{i} {{ {body} }}")
        anims.append(f"pata{i} {num(total / e.speed)}s linear infinite")
        states.append(running_if(f"style(--aw{i}: 1)"))
    css.append(f"#L3 {{ {decls(d3)} animation: {', '.join(anims)}; animation-play-state: {', '.join(states)}; }}")

    # ---------------- L4: camera, line of sight, targeting, firing, damage to enemies
    d4 = {}
    for n in ("cdx", "cdy"):
        R(n)
    d4["cdx"] = "cos(var(--ra))"
    d4["cdy"] = "sin(var(--ra))"
    for i in ENEMY_IDS:
        for n in ("ll", "lux", "luy", "dep", "lat"):
            R(f"{n}{i}")
        R(f"los{i}", "<integer>"); R(f"tg{i}", "<integer>")
        rx, ry = f"(var(--eax{i}) - var(--px))", f"(var(--eay{i}) - var(--py))"
        d4[f"ll{i}"] = f"max(hypot({rx}, {ry}), 0.001)"
        d4[f"lux{i}"] = f"calc({rx} / var(--ll{i}))"
        d4[f"luy{i}"] = f"calc({ry} / var(--ll{i}))"
        steps, final = march(f"l{i}", "var(--px)", "var(--py)", f"var(--lux{i})", f"var(--luy{i})", KL)
        d4.update({k: val for k, val in steps.items() if not k.startswith(f"l{i}d")})
        zoned("#L4", lambda terms, ents, i=i: {
            k: val for k, val in march(f"l{i}", "var(--px)", "var(--py)", f"var(--lux{i})", f"var(--luy{i})", KL, terms=terms)[0].items()
            if k.startswith(f"l{i}d")})
        d4[f"los{i}"] = step(f"{final} - var(--ll{i}) + 0.45")
        d4[f"dep{i}"] = f"calc({rx} * var(--cdx) + {ry} * var(--cdy))"
        d4[f"lat{i}"] = f"calc({rx} * var(--cdy) - {ry} * var(--cdx))"
        d4[f"tg{i}"] = (f"calc({step(f'var(--dep{i}) - 0.3')} * {step(f'{GUN_RANGE} - var(--dep{i})')}"
                        f" * {step(f'0.42 + 0.06 * var(--dep{i}) - abs(var(--lat{i}))')} * var(--los{i}))")
    R("fire", "<integer>")
    d4["fire"] = "0"
    anims = [integrator("fz")] + [integrator(f"dm{i}") for i in ENEMY_IDS]
    states = [running_if("style(--fire: 1)")] + [running_if(f"style(--fire: 1) and style(--tg{i}: 1)") for i in ENEMY_IDS]
    css.append(f"#L4 {{ {decls(d4)} animation: {', '.join(anims)}; animation-play-state: {', '.join(states)}; }}")
    css.append("#L4:active:has(.am:hover) { --fire: 1; }")

    # ---------------- L5: enemy life, patrol copy B (freezes on death), damage to player
    d5, anims, states = {}, [], []
    for i, e in enumerate(ENEMIES):
        st = ENEMY_STATS[e.kind]
        R(f"al{i}", "<integer>"); R(f"at{i}", "<integer>")
        d5[f"al{i}"] = step(f"{st['hp']} - var(--dm{i}) * {GUN_DPS}")
        d5[f"at{i}"] = (f"calc(var(--al{i}) * var(--aw{i}) * var(--los{i}) * {step(f'{st['range']} - var(--ll{i})')}"
                        f" * {step(f'{st['window']} - mod(var(--clock) + {num(e.phase)}, {st['cycle']})')})")
        frames, total = path_keyframes(e.path)
        anims.append(f"patb{i} {num(total / e.speed)}s linear infinite")
        states.append(running_if(f"style(--aw{i}: 1) and style(--al{i}: 1)"))
    for i in ENEMY_IDS:
        anims.append(integrator(f"hu{i}"))
        states.append(running_if(f"style(--at{i}: 1)"))
    css.append(f"#L5 {{ {decls(d5)} animation: {', '.join(anims)}; animation-play-state: {', '.join(states)}; }}")

    # ---------------- L6: player stats, camera, sprite projection, collision probes
    d6 = {}
    heal = " + ".join(f"{ITEM_KINDS[it.kind].get('health', 0)} * var(--pk{k})" for k, it in zip(ITEM_IDS, ITEMS) if "health" in ITEM_KINDS[it.kind])
    dmg = " + ".join(f"{ENEMY_STATS[e.kind]['dps']} * var(--hu{i})" for i, e in enumerate(ENEMIES))
    ammo = " + ".join(f"{ITEM_KINDS[it.kind]['ammo']} * var(--pk{k})" for k, it in zip(ITEM_IDS, ITEMS) if "ammo" in ITEM_KINDS[it.kind])
    for n in ("hp", "ammo", "shots"):
        R(n)
    for n in ("kills", "dead", "hurt", "okx", "oky", "moving"):
        R(n, "<integer>")
    d6["hp"] = f"min(200, calc({START_HEALTH} + {heal} - ({dmg})))"
    d6["shots"] = f"round(up, var(--fz) / {num(FIRE_CYCLE)})"
    d6["ammo"] = f"calc({START_AMMO} + {ammo} - var(--shots))"
    d6["kills"] = "calc(" + " + ".join(f"(1 - var(--al{i}))" for i in ENEMY_IDS) + ")"
    d6["dead"] = f"calc(1 - {step('var(--hp)')})"
    d6["hurt"] = "sign(" + " + ".join(f"var(--at{i})" for i in ENEMY_IDS) + ")"
    R("aimed", "<integer>")
    d6["aimed"] = "sign(" + " + ".join(f"var(--tg{i}) * var(--al{i})" for i in ENEMY_IDS) + ")"
    d6["moving"] = "calc(var(--mv) * sign(var(--gx) + var(--gy)))"
    # collision: a move along an axis is allowed if it does not bring us closer than RADIUS
    R("mth"); R("pd0"); R("pdx"); R("pdy")
    d6["mth"] = f"calc(var(--md) * {num(hstep)})"
    zoned("#L6", lambda terms, ents: {
        "pd0": sdf_css("var(--px)", "var(--py)", terms),
        "pdx": sdf_css("calc(var(--px) + sign(cos(var(--mth))) * 0.12)", "var(--py)", terms),
        "pdy": sdf_css("var(--px)", "calc(var(--py) + sign(sin(var(--mth))) * 0.12)", terms),
    })
    d6["okx"] = step(f"var(--pdx) - min(var(--pd0), {RADIUS}) + 0.0005")
    d6["oky"] = step(f"var(--pdy) - min(var(--pd0), {RADIUS}) + 0.0005")
    # sprites: per entity screen projection and a packed sort key (depth | screen x | atlas cell)
    R("wk", "<integer>"); R("blink", "<integer>")
    d6["wk"] = "mod(round(down, var(--clock) * 3), 2)"
    d6["blink"] = "mod(round(down, var(--clock) * 6), 2)"
    anims, names = [], []
    for i, e in enumerate(ENEMIES):
        R(f"dt{i}")
        KEYFRAMES.append(f"@keyframes die{i} {{ from {{ --dt{i}: 0; }} to {{ --dt{i}: 1; }} }}")
        names.append(f"if(style(--al{i}: 0): die{i}; else: none)")
    css.append(f"#L6 {{ animation-name: {', '.join(names)}; animation-duration: 0.6s; animation-fill-mode: forwards; animation-timing-function: linear; }}")
    for k in range(ENTITIES):
        for n in ("ex", "ey", "dp", "sx", "hw", "sl", "sr", "sk", "sp"):
            R(f"{n}{k}")
        R(f"cl{k}", "<integer>"); R(f"vs{k}", "<integer>")
        if k in ENEMY_IDS:
            e = ENEMIES[k]
            base = CELL[f"{e.kind[0]}_walk1"]
            walk = f"{base} + var(--wk)"
            attack = sel("var(--blink)", base + 2, base)
            pain = base + 3
            dying = f"{base + 4} + min(2, round(down, var(--dt{k}) * 3))"
            alive_cell = sel(f"var(--tg{k}) * var(--fire)", pain, sel(f"var(--at{k})", attack, sel(f"var(--aw{k})", walk, base)))
            d6[f"cl{k}"] = f"calc({sel(f'var(--al{k})', alive_cell, dying)})"
            d6[f"ex{k}"], d6[f"ey{k}"] = f"var(--ebx{k})", f"var(--eby{k})"
            d6[f"vs{k}"] = "1"
        elif k in ITEM_IDS:
            it = ITEMS[k - ITEM_IDS[0]]
            d6[f"cl{k}"] = str(CELL[it.kind])
            d6[f"ex{k}"], d6[f"ey{k}"] = num(it.x), num(it.y)
            d6[f"vs{k}"] = f"calc(1 - var(--pk{k}))"
        else:
            kind, x, y = DECOR[k - DECOR_IDS[0]]
            d6[f"cl{k}"] = f"calc({CELL['barrel1']} + var(--wk))"
            d6[f"ex{k}"], d6[f"ey{k}"] = num(x), num(y)
            d6[f"vs{k}"] = "1"
        rx, ry = f"(var(--ex{k}) - var(--px))", f"(var(--ey{k}) - var(--py))"
        d6[f"dp{k}"] = f"calc({rx} * var(--cdx) + {ry} * var(--cdy))"
        d6[f"sx{k}"] = f"clamp(-1000, calc({FOC} + {FOC} * ({rx} * var(--cdy) - {ry} * var(--cdx)) / max(var(--dp{k}), 0.01)), 1000)"
        d6[f"hw{k}"] = f"calc({FOC / 2} / max(var(--dp{k}), 0.01))"
        on = f"var(--vs{k}) * {step(f'var(--dp{k}) - 0.25')}"
        d6[f"sl{k}"] = sel(on, f"var(--sx{k}) - var(--hw{k})", "1000000")
        d6[f"sr{k}"] = sel(on, f"var(--sx{k}) + var(--hw{k})", "-1000000")
        # var() hands registered numbers over with ~6 significant digits, so keys stay below 1e6:
        # sort key = depth (1/1000 unit) * 16 + entity id; params = screen x (px) * 32 + atlas cell
        d6[f"sk{k}"] = f"calc(round(min(var(--dp{k}), 59) * 1000) * 16 + {k})"
        d6[f"sp{k}"] = f"calc(round(var(--sx{k}) + 1024) * 32 + var(--cl{k}))"
    R("kpct"); R("ipct"); R("secs")
    d6["kpct"] = f"round(var(--kills) * {num(100 / len(ENEMIES))})"
    d6["ipct"] = "round((" + " + ".join(f"var(--pk{k})" for k in ITEM_IDS) + f") * {num(100 / len(ITEMS))})"
    d6["secs"] = "round(var(--clock) - var(--ex))"
    css.append(f"#L6 {{ {decls(d6)} }}")
    # pickup messages and flash: one-shot animations started when a pickup latch flips
    for k in ITEM_IDS:
        css.append(f".msg{k} {{ animation: if(style(--pk{k}: 1): msgshow; else: none) 2.5s linear forwards; }}")
    flashes = ", ".join(f"if(style(--pk{k}: 1): pickflash; else: none)" for k in ITEM_IDS)
    css.append(f"#pickflash {{ animation-name: {flashes}; animation-duration: 0.5s; animation-fill-mode: forwards; }}")
    return css


def view_css():
    css = []
    # ---------------- cone groups: shared march prefix + per-group sprite candidates
    tau = math.tan(GROUP / COLS) * 1.05
    g = {}
    for n in ("gcx", "grx", "gry", "grl", "gux", "guy"):
        R(n, inherits=False)
    R("gi", "<integer>"); R("gs"); R("k1"); R("k2")
    g["gi"] = "sibling-index()"
    g["gcx"] = f"calc((var(--gi) - 0.5) * {num(2 * GROUP / COLS)} - 1)"
    g["grx"] = "calc(var(--cdx) + var(--cdy) * var(--gcx))"
    g["gry"] = "calc(var(--cdy) - var(--cdx) * var(--gcx))"
    g["grl"] = "calc(1 / hypot(var(--grx), var(--gry)))"
    g["gux"] = "calc(var(--grx) * var(--grl))"
    g["guy"] = "calc(var(--gry) * var(--grl))"
    for k in range(K1 + 1):
        R(f"g{k}", inherits=False)
        if k < K1:
            R(f"gx{k}", inherits=False); R(f"gy{k}", inherits=False)
    g["g0"] = "0"

    for k in range(K1):
        g[f"gx{k}"] = f"calc(var(--px) + var(--gux) * var(--g{k}))"
        g[f"gy{k}"] = f"calc(var(--py) + var(--guy) * var(--g{k}))"
    g["gs"] = f"calc(var(--g{K1}) * 0.98)"
    gx0 = f"(var(--gi) - 1) * {num(GROUP * COLW)}"
    gx1 = f"var(--gi) * {num(GROUP * COLW)}"
    for k in range(ENTITIES):
        R(f"gk{k}", inherits=False)
    for j in (1, 2):
        R(f"sa{j}", "<integer>", inherits=False); R(f"sz{j}"); R(f"sq{j}")
        g[f"sa{j}"] = f"mod(var(--k{j}), 16)"
        g[f"sz{j}"] = f"calc(round(down, var(--k{j}) / 16) / 1000)"

    def group_zoned(terms, ents):
        """Cone steps over the zone's terms; sprite candidates among the zone's visible entities."""
        out = {
            f"g{k+1}": f"calc(var(--g{k}) + max(0, {sdf_css(f'var(--gx{k})', f'var(--gy{k})', terms)} - {num(tau)} * var(--g{k})) / {num(1 + tau)})"
            for k in range(K1)
        }
        if not ents:
            return out | {"k1": str(KEYBIG), "k2": str(KEYBIG), "sq1": "0", "sq2": "0"}
        for k in ents:
            out[f"gk{k}"] = f"calc(var(--sk{k}) + (1 - {step(f'var(--sr{k}) - {gx0}')} * {step(f'{gx1} - var(--sl{k})')}) * {KEYBIG})"
        out["k1"] = "min(" + ", ".join(f"var(--gk{k})" for k in ents) + ", " + str(KEYBIG) + ")"
        out["k2"] = "min(" + ", ".join(f"calc(var(--gk{k}) + {step(f'var(--k1) - var(--gk{k}) + 0.5')} * {KEYBIG})" for k in ents) + ", " + str(KEYBIG) + ")"
        for j in (1, 2):
            out[f"sq{j}"] = "calc(" + " + ".join(f"max(0, 1 - abs(var(--sa{j}) - {k})) * var(--sp{k})" for k in ents) + ")"
        return out

    zoned(".grp", group_zoned)
    css.append(f".grp {{ {decls(g)} }}")

    # ---------------- columns: secant refinement, material, lighting, sprite pick
    c = {}
    for n in ("cx", "rx", "ry", "rl", "ux", "uy", "hx", "hy", "ml"):
        R(n, inherits=False)
    for n in ("t", "tu", "mat", "spd", "spx", "spc", "spv", "cc"):
        R(n)
    R("xf", "<integer>", inherits=False)
    c["cx"] = f"calc(((var(--gi) - 1) * {GROUP} + sibling-index() - 0.5) * {num(2 / COLS)} - 1)"
    c["cc"] = f"calc((var(--cx) + 1) * {FOC})"
    c["rx"] = "calc(var(--cdx) + var(--cdy) * var(--cx))"
    c["ry"] = "calc(var(--cdy) - var(--cdx) * var(--cx))"
    c["rl"] = "calc(1 / hypot(var(--rx), var(--ry)))"
    c["ux"] = "calc(var(--rx) * var(--rl))"
    c["uy"] = "calc(var(--ry) * var(--rl))"
    col_march = lambda terms: march("c", "var(--px)", "var(--py)", "var(--ux)", "var(--uy)", K2, start="var(--gs)", terms=terms)
    steps, final = col_march(None)
    c.update({k: val for k, val in steps.items() if not k.startswith("cd")})
    R("sf", inherits=False)
    c["sf"] = f"max(0.02, calc{final})"
    c["t"] = "max(0.05, calc(var(--sf) * var(--rl)))"
    c["hx"] = "calc(var(--px) + var(--ux) * var(--sf))"
    c["hy"] = "calc(var(--py) + var(--uy) * var(--sf))"
    # walls sit on a 0.5 grid: the hit coordinate closer to a grid line names the face axis
    c["xf"] = step("abs(var(--hy) * 2 - round(var(--hy) * 2)) - abs(var(--hx) * 2 - round(var(--hx) * 2))")
    c["tu"] = "mod(" + sel("var(--xf)", "var(--hy)", "var(--hx)") + ", 1)"
    # material + sector light, packed as mat + light (light < 1). First matching entry wins;
    # each entry names the term whose walls it paints, so a zone only tests what it can see.
    hx, hy = "var(--hx)", "var(--hy)"
    chain = [
        ("door", step(f"min({hy} - 20.05, 21.95 - {hy}, {hx} - 11.95, 13.05 - {hx})"), T["door"] + 0.5),
        ("pill", step(f"min(3.1 - abs({hx} - 3), 2.6 - abs({hy} - 18.5))"), T["pillar"] + 0.75),
        ("crate", step(f"1.05 - max(abs({hx} - 21), abs({hy} - 20))"), T["crate"] + 0.6),
        ("F", step(f"min({hy} - 35.95, 0.55 - abs({hx} - 21))"), T["exit"] + 0.9),
        ("A", step(f"8.05 - {hy}"), T["tech"] + 0.85),
        ("AC", step(f"11.95 - {hy}"), T["brown"] + 0.6),
        ("C", step(f"10.05 - {hx}"), T["stone"] + 0.95),
        ("CD", step(f"15.95 - {hx}"), T["brown"] + 0.5),
        ("F", step(f"{hy} - 29.95"), T["tech"] + 0.8),
        ("EF", step(f"{hy} - 26.05"), T["brown"] + 0.6),
    ]

    def col_zoned(terms, ents):
        out = {k: val for k, val in col_march(terms)[0].items() if k.startswith("cd")}
        expr = num(T["marble"] + 0.7)
        for term, cond, val in reversed(chain):
            if terms is None or term in terms:
                expr = sel(cond, num(val), expr)
        out["ml"] = f"calc({expr})"
        return out

    zoned(".col", col_zoned)
    c["mat"] = "round(down, var(--ml))"
    R("wl", "<integer>"); R("spl", "<integer>")
    light = ("clamp(0.1, calc((var(--ml) - var(--mat)) * (1.3 - var(--t) * 0.06)"
             " * (0.8 + 0.2 * var(--xf))), 1)")
    c["wl"] = f"clamp(0, round(({light} - 0.16) / 0.84 * {art.WALL_LEVELS - 1}), {art.WALL_LEVELS - 1})"
    # sprite: the nearer of the group's two candidates that covers this column in front of the wall
    for n in ("v1", "v2", "spq"):
        R(n, inherits=False)
    for j in (1, 2):
        sx = f"(round(down, var(--sq{j}) / 32) - 1024)"
        c[f"v{j}"] = f"calc({step(f'{FOC / 2} / max(var(--sz{j}), 0.01) - abs(var(--cc) - {sx})')} * {step(f'var(--t) - var(--sz{j})')})"
    c["spv"] = "max(var(--v1), var(--v2))"
    c["spq"] = sel("var(--v1)", "var(--sq1)", "var(--sq2)")
    c["spd"] = f"max(0.05, {sel('var(--v1)', 'var(--sz1)', 'var(--sz2)')})"
    c["spx"] = "calc(round(down, var(--spq) / 32) - 1024)"
    c["spc"] = "mod(var(--spq), 32)"
    c["spl"] = (f"clamp(0, round((clamp(0.1, 0.9 * (1.3 - var(--spd) * 0.06), 1) - 0.16) / 0.84 * {art.SPRITE_LEVELS - 1}),"
                f" {art.SPRITE_LEVELS - 1})")
    css.append(f".col {{ {decls(c)} }}")

    # wall light level and sprite light level pick a pre-darkened copy of the texture in the atlas
    texel = "clamp(0, round(down, var(--tu) * 64), 63)"
    css.append(
        f".wt {{ transform: translate(calc(((var(--wl) * {len(TEX)} + var(--mat)) * {TEXW} + {texel}) * {-COLW:.6f}px),"
        f" calc(({HOR} - {FOC / 2} / var(--t)) * 1px)) scale({num(COLW)}, calc({FOC} / var(--t) / {TEXW})); }}"
    )
    stexel = f"clamp(0, round(down, (var(--cc) - var(--spx)) * var(--spd) / {FOC} * 64 + 32), 63)"
    ncell = len(art.SPRITE_CELLS)
    css.append(
        f".sp {{ opacity: var(--spv); transform: translate(calc(((var(--spl) * {ncell} + var(--spc)) * {TEXW} + {stexel}) * {-COLW:.6f}px),"
        f" calc(({HOR} - {FOC / 2} / var(--spd)) * 1px)) scale({num(COLW)}, calc({FOC} / var(--spd) / {TEXW})); }}"
    )
    return css


def pad_css():
    return [
        "#pad { cursor: crosshair; display: if(style(--dead: 0) and style(--won: 0): inline; else: none); }",
        "#doom:not(:has(#play:target)) #pad { display: none; }",
        ".z rect { fill: transparent; }",
        ".gxy { display: if(style(--okx: 1) and style(--oky: 1): inline; else: none); }",
        ".gx { display: if(style(--okx: 1): inline; else: none); }",
        ".gy { display: if(style(--oky: 1): inline; else: none); }",
        ".am { display: if(style(--ammo > 0): inline; else: none); }",
    ]


def pad_markup():
    """5x3 hover joystick over the view. Moving zones hold collision gates; every gate holds an ammo gate."""
    xs = [0, 40, 116, 204, 280, W]
    ys = [0, 62, 106, VH]
    turn = ["tl2", "tl1", "", "tr1", "tr2"]
    move = ["fw", "", "bk"]
    out = []
    for r in range(3):
        for col in range(5):
            x, y, w, h = xs[col], ys[r], xs[col + 1] - xs[col], ys[r + 1] - ys[r]
            cls = " ".join(c for c in ("z", turn[col], move[r]) if c)
            rect = f'<rect x="{x}" y="{y}" width="{w}" height="{h}"/>'
            gates = ["g0", "gy", "gx", "gxy"] if move[r] else ["g0"]
            inner = "".join(f'<g class="{gname}">{rect}<rect class="am" x="{x}" y="{y}" width="{w}" height="{h}"/></g>' for gname in gates)
            out.append(f'<g class="{cls}">{inner}</g>')
    return '<g id="pad">' + "".join(out) + "</g>"


def columns_markup():
    out = ['<g id="cols">']
    for gi in range(GROUPS):
        out.append('<g class="grp">')
        for ci in range(GROUP):
            x = (gi * GROUP + ci) * COLW
            out.append(
                f'<svg class="col" x="{x:.3f}" y="0" width="{COLW + 0.04:.3f}" height="{VH}">'
                f'<use class="wt" href="#wallatlas"/><use class="sp" href="#spratlas"/></svg>'
            )
        out.append("</g>")
    out.append("</g>")
    return "".join(out)


BASE_CSS = """
svg#doom { user-select: none; -webkit-user-select: none; font-family: Impact, 'Arial Black', sans-serif; }
.col { overflow: hidden; }
image { image-rendering: pixelated; }
"""


def build():
    walls_png = assets.rasterise(art.write_walls(), TEXW * len(TEX) * art.WALL_LEVELS, TEXW)
    sprites_png = assets.rasterise(art.write_sprites(), TEXW * len(art.SPRITE_CELLS) * art.SPRITE_LEVELS, TEXW)
    css = stylesheet() + view_css() + pad_css() + zone_css()
    sheet = "\n".join([R.css(), "\n".join(KEYFRAMES), BASE_CSS, "\n".join(css), art.HUD_CSS])
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" id="doom" viewBox="0 0 {W} 200" width="1280" height="800" preserveAspectRatio="xMidYMid meet">
<title>DOOM.SVG - no script, just CSS</title>
<style><![CDATA[
{sheet}
]]></style>
<defs>
<image id="wallatlas" width="{TEXW * len(TEX) * art.WALL_LEVELS}" height="{TEXW}" preserveAspectRatio="none" href="{assets.data_uri(walls_png)}"/>
<image id="spratlas" width="{TEXW * len(art.SPRITE_CELLS) * art.SPRITE_LEVELS}" height="{TEXW}" preserveAspectRatio="none" href="{assets.data_uri(sprites_png)}"/>
{art.DEFS}
</defs>
<g id="L0"><g id="L1"><g id="L2"><g id="L3"><g id="L4"><g id="L5"><g id="L6">
{art.BACKDROP}
{columns_markup()}
{art.weapon_markup()}
{art.hud_markup()}
{pad_markup()}
{art.overlays_markup()}
</g></g></g></g></g></g></g>
</svg>
"""
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB, {len(R.props)} registered properties)")


if __name__ == "__main__":
    if "--god" in sys.argv:  # test build: enemies deal no damage
        for stats in ENEMY_STATS.values():
            stats["dps"] = 0
        OUT = ROOT / "build" / "doom-god.svg"
    if "out" in ARGS:
        OUT = pathlib.Path(ARGS["out"]).resolve()
    build()
