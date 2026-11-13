"""Art for DOOM.SVG: texture/sprite sheets (rasterised at build time) and the vector HUD."""
import pathlib

from level import ENEMIES, ITEMS, TEX

ART = pathlib.Path(__file__).resolve().parent.parent / "build" / "art"

SPRITE_CELLS = [
    "z_walk1", "z_walk2", "z_attack", "z_pain", "z_die1", "z_die2", "z_dead",
    "i_walk1", "i_walk2", "i_attack", "i_pain", "i_die1", "i_die2", "i_dead",
    "medkit", "stimpack", "shells", "barrel1", "barrel2",
]

# ------------------------------------------------------------------ wall textures (64x64 each)
NOISE = """
<filter id="grit" x="0" y="0" width="1" height="1" color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="0.35" numOctaves="3" seed="{seed}" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 {amt} {off}" result="a"/>
  <feComposite in="SourceGraphic" in2="a" operator="in" result="g"/>
  <feFlood flood-color="#000"/><feComposite in2="a" operator="in" result="dark"/>
  <feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="dark"/></feMerge>
</filter>"""


def _grit(fid, seed, amt=0.9, off=-0.25):
    return NOISE.replace('id="grit"', f'id="{fid}"').format(seed=seed, amt=amt, off=off)


WALLS = {
    "tech": """
  <rect width="64" height="64" fill="#8d8571"/>
  <rect y="0" width="64" height="6" fill="#6e6656"/><rect y="58" width="64" height="6" fill="#6e6656"/>
  <rect y="26" width="64" height="12" fill="#5d574a"/><rect y="28" width="64" height="2" fill="#a59d86"/>
  <g fill="#4a453a"><rect x="0" y="6" width="2" height="52"/><rect x="31" y="6" width="2" height="52"/></g>
  <g fill="#b0a890"><rect x="2" y="6" width="1" height="20"/><rect x="33" y="6" width="1" height="20"/><rect x="2" y="38" width="1" height="20"/><rect x="33" y="38" width="1" height="20"/></g>
  <g fill="#3b372e"><circle cx="6" cy="3" r="1"/><circle cx="26" cy="3" r="1"/><circle cx="38" cy="3" r="1"/><circle cx="58" cy="3" r="1"/>
  <circle cx="6" cy="61" r="1"/><circle cx="26" cy="61" r="1"/><circle cx="38" cy="61" r="1"/><circle cx="58" cy="61" r="1"/></g>
  <rect x="12" y="30" width="8" height="4" fill="#3f8f3f"/><rect x="44" y="30" width="8" height="4" fill="#9a2a1a"/>""",
    "brown": """
  <rect width="64" height="64" fill="#6b4a2c"/>
  <g fill="#7d5a37" stroke="#3c2814" stroke-width="1.5">
    <rect x="0" y="0" width="32" height="16"/><rect x="32" y="0" width="32" height="16"/>
    <rect x="-16" y="16" width="32" height="16"/><rect x="16" y="16" width="32" height="16"/><rect x="48" y="16" width="32" height="16"/>
    <rect x="0" y="32" width="32" height="16"/><rect x="32" y="32" width="32" height="16"/>
    <rect x="-16" y="48" width="32" height="16"/><rect x="16" y="48" width="32" height="16"/><rect x="48" y="48" width="32" height="16"/>
  </g>
  <g fill="#94704a"><rect x="2" y="2" width="28" height="2"/><rect x="34" y="2" width="28" height="2"/><rect x="18" y="18" width="28" height="2"/>
  <rect x="2" y="34" width="28" height="2"/><rect x="34" y="34" width="28" height="2"/><rect x="18" y="50" width="28" height="2"/></g>""",
    "stone": """
  <rect width="64" height="64" fill="#6f6f6b"/>
  <g fill="#82827c" stroke="#3f3f3c" stroke-width="1.5">
    <rect x="0" y="0" width="22" height="13"/><rect x="22" y="0" width="26" height="13"/><rect x="48" y="0" width="16" height="13"/>
    <rect x="-6" y="13" width="18" height="17"/><rect x="12" y="13" width="28" height="17"/><rect x="40" y="13" width="30" height="17"/>
    <rect x="0" y="30" width="26" height="15"/><rect x="26" y="30" width="20" height="15"/><rect x="46" y="30" width="18" height="15"/>
    <rect x="-4" y="45" width="24" height="19"/><rect x="20" y="45" width="24" height="19"/><rect x="44" y="45" width="24" height="19"/>
  </g>""",
    "marble": """
  <rect width="64" height="64" fill="#1f3b2a"/>
  <path d="M0 10 C 15 20 20 0 40 12 S 55 30 64 22 M0 40 C 12 30 30 52 44 40 S 60 50 64 46 M20 64 C 25 50 10 40 22 30" fill="none" stroke="#5f8c6a" stroke-width="1.5"/>
  <path d="M8 0 C 12 12 4 20 14 30 M50 0 C 46 16 58 22 52 36" fill="none" stroke="#365c43" stroke-width="2"/>
  <rect x="0" y="0" width="64" height="3" fill="#0e1f15"/><rect x="0" y="61" width="64" height="3" fill="#0e1f15"/>
  <g transform="translate(32 33)"><path d="M-9 -8 L-4 -13 L0 -9 L4 -13 L9 -8 L9 4 L4 10 L-4 10 L-9 4 Z" fill="#2c4f37" stroke="#0e1f15"/>
  <circle cx="-4" cy="-3" r="2" fill="#c33"/><circle cx="4" cy="-3" r="2" fill="#c33"/><path d="M-4 5 L4 5" stroke="#0e1f15" stroke-width="2"/></g>""",
    "door": """
  <rect width="64" height="64" fill="#7a7a80"/>
  <g fill="#5c5c62"><rect x="4" y="0" width="4" height="64"/><rect x="14" y="0" width="4" height="64"/><rect x="46" y="0" width="4" height="64"/><rect x="56" y="0" width="4" height="64"/></g>
  <rect x="30" y="0" width="4" height="64" fill="#2d2d30"/>
  <rect x="22" y="22" width="20" height="20" fill="#9a9aa2" stroke="#3a3a3f" stroke-width="2"/>
  <path d="M22 22 L42 42 M42 22 L22 42" stroke="#3a3a3f" stroke-width="2"/>
  <g><rect x="0" y="0" width="64" height="5" fill="#d8b020"/><path d="M0 5 L5 0 M10 5 L15 0 M20 5 L25 0 M30 5 L35 0 M40 5 L45 0 M50 5 L55 0 M60 5 L65 0" stroke="#111" stroke-width="3"/></g>""",
    "pillar": """
  <rect width="64" height="64" fill="#4f4f55"/>
  <g fill="#6d6d74"><rect x="6" y="0" width="10" height="64"/><rect x="27" y="0" width="10" height="64"/><rect x="48" y="0" width="10" height="64"/></g>
  <g fill="#8b8b93"><rect x="7" y="0" width="2" height="64"/><rect x="28" y="0" width="2" height="64"/><rect x="49" y="0" width="2" height="64"/></g>
  <rect y="0" width="64" height="8" fill="#38383d"/><rect y="56" width="64" height="8" fill="#38383d"/>""",
    "crate": """
  <rect width="64" height="64" fill="#5a4a2a"/>
  <rect x="3" y="3" width="58" height="58" fill="#6e5b33" stroke="#2f2412" stroke-width="3"/>
  <path d="M6 6 L58 58 M58 6 L6 58" stroke="#3f3219" stroke-width="5"/>
  <path d="M6 6 L58 58 M58 6 L6 58" stroke="#8a7444" stroke-width="2"/>
  <rect x="0" y="30" width="64" height="4" fill="#2f2412"/>""",
    "exit": """
  <rect width="64" height="64" fill="#8d8571"/>
  <rect x="14" y="10" width="36" height="44" fill="#4a4a50" stroke="#2a2a2e" stroke-width="2"/>
  <rect x="22" y="18" width="20" height="10" fill="#c22"/><text x="32" y="26.5" font-family="Arial Black, Impact, sans-serif" font-size="8.5" text-anchor="middle" fill="#fff">EXIT</text>
  <rect x="27" y="34" width="10" height="14" fill="#2c2c2c"/><rect x="28" y="35" width="8" height="6" fill="#4c4"/>""",
}


WALL_LEVELS = 8     # light levels baked side by side into the wall atlas (Doom-style colormaps)
SPRITE_LEVELS = 4


def level_brightness(level, levels):
    return 0.16 + 0.84 * level / (levels - 1)


def _with_levels(width, levels, defs, sheet):
    """An atlas holding `sheet` once per light level, each darkened by a colour-matrix filter."""
    dims = "".join(
        f'<filter id="dim{L}" x="0" y="0" width="1" height="1" color-interpolation-filters="sRGB">'
        f'<feColorMatrix type="matrix" values="{b} 0 0 0 0  0 {b} 0 0 0  0 0 {b} 0 0  0 0 0 1 0"/></filter>'
        for L in range(levels) for b in [f"{level_brightness(L, levels):.4f}"]
    )
    uses = "".join(f'<g transform="translate({L * width} 0)" filter="url(#dim{L})"><use href="#sheet"/></g>' for L in range(levels))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width * levels}" height="64" viewBox="0 0 {width * levels} 64">'
            f'<defs>{defs}{dims}<g id="sheet">{sheet}</g></defs>{uses}</svg>')


def write_walls():
    defs = "".join(_grit(f"grit{i}", 3 + i * 7) + f'<clipPath id="cell{i}"><rect width="64" height="64"/></clipPath>' for i in range(len(TEX)))
    sheet = "".join(
        f'<g transform="translate({64 * i} 0)" clip-path="url(#cell{i})"><g filter="url(#grit{i})">{WALLS[name]}</g></g>'
        for i, name in enumerate(TEX)
    )
    ART.mkdir(parents=True, exist_ok=True)
    path = ART / "walls.svg"
    path.write_text(_with_levels(64 * len(TEX), WALL_LEVELS, defs, sheet), encoding="utf-8")
    return path


# ------------------------------------------------------------------ sprites (64x64 cells, floor at y=64)
def _zombie(pose):
    """Former-human: green fatigues, grey skin, rifle. pose in walk1/walk2/attack/pain/die1/die2/dead."""
    if pose == "dead":
        return """<g><ellipse cx="32" cy="61" rx="22" ry="3.5" fill="#5a0a0a"/>
        <path d="M12 60 Q20 54 32 56 Q44 54 52 59 L50 62 L14 62 Z" fill="#3e5a2a"/>
        <circle cx="48" cy="57" r="4" fill="#8f8f80"/><path d="M14 58 L6 60" stroke="#333" stroke-width="2"/></g>"""
    if pose in ("die1", "die2"):
        tilt, squash = (18, 0.85) if pose == "die1" else (32, 0.5)
        return f"""<ellipse cx="32" cy="62" rx="{12 if pose == 'die1' else 18}" ry="2" fill="#6a0c0c"/>
        <g transform="translate(32 64) rotate({tilt}) scale(1 {squash}) translate(-32 -64)">{_zombie_body('pain', blood=True)}</g>"""
    return _zombie_body(pose)


def _zombie_body(pose, blood=False):
    lstep = {"walk1": -3, "walk2": 3}.get(pose, 0)
    skin = "#a09880" if pose != "pain" else "#c08070"
    flash = ""
    gun = '<rect x="36" y="34" width="16" height="3" fill="#2a2a2a"/><rect x="34" y="35" width="5" height="5" fill="#4a3a28"/>'
    if pose == "attack":
        gun = '<rect x="30" y="34" width="22" height="3" fill="#2a2a2a"/><rect x="28" y="35" width="5" height="5" fill="#4a3a28"/>'
        flash = '<path d="M52 35.5 l7 -5 l-2 5 l7 0 l-7 3 l3 5 l-8 -4 z" fill="#ffe14a" stroke="#ff8a00" stroke-width="1"/>'
    return f"""<g>
      <path d="M{25 + lstep} 50 L{23 + lstep} 63 L{28 + lstep} 63 L{30} 50 Z" fill="#2d4220"/>
      <path d="M{34 - lstep} 50 L{36 - lstep} 63 L{41 - lstep} 63 L{39} 50 Z" fill="#2d4220"/>
      <rect x="{22 + lstep}" y="61" width="7" height="3" fill="#1d1d1d"/><rect x="{35 - lstep}" y="61" width="7" height="3" fill="#1d1d1d"/>
      <path d="M23 28 Q32 24 41 28 L42 51 L22 51 Z" fill="#4c6b32"/>
      <path d="M24 30 L40 30 L40 34 L24 34 Z" fill="#3a5226"/>
      <rect x="22" y="44" width="20" height="3" fill="#3b2a1a"/>
      <path d="M22 29 L17 42 L21 44 L25 33 Z" fill="#4c6b32"/><path d="M42 29 L46 38 L40 40 L38 33 Z" fill="#4c6b32"/>
      <rect x="27" y="22" width="10" height="5" fill="{skin}"/>
      <ellipse cx="32" cy="18" rx="6" ry="7" fill="{skin}"/>
      <path d="M26 16 Q32 9 38 16 L38 13 Q32 7 26 13 Z" fill="#3a3324"/>
      <rect x="28.5" y="17" width="2" height="1.6" fill="#600"/><rect x="33.5" y="17" width="2" height="1.6" fill="#600"/>
      <path d="M29.5 22 L34.5 22" stroke="#4a2a20" stroke-width="1"/>
      {'<circle cx="30" cy="38" r="3" fill="#8a0d0d"/><circle cx="35" cy="31" r="2" fill="#8a0d0d"/>' if blood or pose == 'pain' else ''}
      {gun}{flash}
    </g>"""


def _imp(pose):
    if pose == "dead":
        return """<g><ellipse cx="32" cy="61" rx="24" ry="3.5" fill="#5a0a0a"/>
        <path d="M10 61 Q18 52 30 55 Q44 51 54 60 L52 63 L12 63 Z" fill="#7a5233"/>
        <path d="M16 56 l-3 -4 l5 2 M24 54 l-1 -5 l3 4 M40 53 l2 -5 l1 5" stroke="#e8e0c8" stroke-width="1.5" fill="none"/>
        <circle cx="50" cy="58" r="2" fill="#c42"/></g>"""
    if pose in ("die1", "die2"):
        tilt, squash = (-18, 0.85) if pose == "die1" else (-32, 0.5)
        return f"""<ellipse cx="32" cy="62" rx="{12 if pose == 'die1' else 18}" ry="2" fill="#6a0c0c"/>
        <g transform="translate(32 64) rotate({tilt}) scale(1 {squash}) translate(-32 -64)">{_imp_body('pain')}</g>"""
    return _imp_body(pose)


def _imp_body(pose):
    lstep = {"walk1": -3, "walk2": 3}.get(pose, 0)
    hide = "#8a5a36" if pose != "pain" else "#b0704a"
    arms = f"""<path d="M21 30 L13 40 L16 44 L24 35 Z" fill="{hide}"/><path d="M43 30 L51 40 L48 44 L40 35 Z" fill="{hide}"/>
      <path d="M13 40 l-3 3 M14 42 l-2 4 M16 44 l0 4 M51 40 l3 3 M50 42 l2 4 M48 44 l0 4" stroke="#e8e0c8" stroke-width="1"/>"""
    ball = ""
    if pose == "attack":
        arms = f"""<path d="M21 30 L16 14 L21 12 L26 28 Z" fill="{hide}"/><path d="M43 30 L51 40 L48 44 L40 35 Z" fill="{hide}"/>"""
        ball = """<circle cx="18" cy="9" r="7" fill="#ff7a00"/><circle cx="18" cy="9" r="4.5" fill="#ffd23a"/><circle cx="18" cy="9" r="2" fill="#fff6c0"/>"""
    return f"""<g>
      <path d="M{25 + lstep} 47 L{22 + lstep} 63 L{28 + lstep} 63 L30 48 Z" fill="{hide}"/>
      <path d="M{39 - lstep} 47 L{42 - lstep} 63 L{36 - lstep} 63 L34 48 Z" fill="{hide}"/>
      <path d="M{21 + lstep} 63 l3 -2 l2 2 l2 -2 l2 2 Z M{35 - lstep} 63 l3 -2 l2 2 l2 -2 l2 2 Z" fill="#e8e0c8"/>
      <path d="M22 26 Q32 20 42 26 L40 49 L24 49 Z" fill="{hide}"/>
      <path d="M26 30 Q32 28 38 30 L37 44 L27 44 Z" fill="#a8724a"/>
      <g fill="#e8e0c8"><path d="M22 27 l-5 -3 l4 6 Z"/><path d="M42 27 l5 -3 l-4 6 Z"/><path d="M27 34 l-3 1 l3 1 Z"/><path d="M37 34 l3 1 l-3 1 Z"/>
      <path d="M26 40 l-3 1 l3 1 Z"/><path d="M38 40 l3 1 l-3 1 Z"/></g>
      {arms}
      <ellipse cx="32" cy="18" rx="7" ry="7.5" fill="{hide}"/>
      <path d="M25 14 l-3 -5 l5 3 Z M39 14 l3 -5 l-5 3 Z" fill="#e8e0c8"/>
      <path d="M27 16 L31 18 M37 16 L33 18" stroke="#3a2010" stroke-width="1.5"/>
      <circle cx="29" cy="18.5" r="1.6" fill="#ffb000"/><circle cx="35" cy="18.5" r="1.6" fill="#ffb000"/>
      <path d="M28 23 Q32 26 36 23 L35 24.5 Q32 26.5 29 24.5 Z" fill="#2a0a0a"/>
      <path d="M29 23.2 l1 1.4 l1 -1.2 l1 1.4 l1 -1.2 l1 1.4 l1 -1.6" stroke="#e8e0c8" stroke-width="0.6" fill="none"/>
      {ball}
    </g>"""


def _item(kind):
    if kind == "medkit":
        return """<g><rect x="20" y="49" width="24" height="15" rx="1.5" fill="#e6e6e6" stroke="#777"/>
        <rect x="29.5" y="51" width="5" height="11" fill="#d01818"/><rect x="26.5" y="54" width="11" height="5" fill="#d01818"/>
        <rect x="20" y="49" width="24" height="2" fill="#fff"/></g>"""
    if kind == "stimpack":
        return """<g><rect x="26" y="54" width="12" height="10" rx="1" fill="#e6e6e6" stroke="#777"/>
        <rect x="30.5" y="55.5" width="3" height="7" fill="#d01818"/><rect x="28.5" y="57.5" width="7" height="3" fill="#d01818"/></g>"""
    if kind == "shells":
        return """<g><rect x="18" y="50" width="28" height="14" fill="#7a2a14" stroke="#3a1006"/>
        <g fill="#c8a020"><rect x="20" y="46" width="4" height="6"/><rect x="25" y="46" width="4" height="6"/><rect x="30" y="46" width="4" height="6"/><rect x="35" y="46" width="4" height="6"/><rect x="40" y="46" width="4" height="6"/></g>
        <g fill="#b0200c"><rect x="20" y="42" width="4" height="5"/><rect x="25" y="42" width="4" height="5"/><rect x="30" y="42" width="4" height="5"/><rect x="35" y="42" width="4" height="5"/><rect x="40" y="42" width="4" height="5"/></g>
        <rect x="18" y="55" width="28" height="3" fill="#a8401c"/></g>"""
    glow = "#4cff4c" if kind == "barrel1" else "#2bd12b"
    return f"""<g><path d="M21 40 Q32 37 43 40 L44 63 Q32 65 20 63 Z" fill="#5a6a4a" stroke="#2a3020"/>
      <rect x="20" y="45" width="24" height="2" fill="#3c4630"/><rect x="20" y="56" width="24" height="2" fill="#3c4630"/>
      <ellipse cx="32" cy="40" rx="11" ry="2.5" fill="{glow}"/><ellipse cx="32" cy="40" rx="7" ry="1.5" fill="#c8ffc8"/>
      <path d="M26 48 l2 5 l-1 3 M36 47 l-1 4" stroke="#2a3020" fill="none"/></g>"""


def write_sprites():
    cells = []
    for name in SPRITE_CELLS:
        if name.startswith("z_"):
            cells.append(_zombie(name[2:]))
        elif name.startswith("i_"):
            cells.append(_imp(name[2:]))
        else:
            cells.append(_item(name))
    n = len(SPRITE_CELLS)
    defs = "".join(f'<clipPath id="c{i}"><rect width="64" height="64"/></clipPath>' for i in range(n))
    sheet = "".join(f'<g transform="translate({64 * i} 0)" clip-path="url(#c{i})">{body}</g>' for i, body in enumerate(cells))
    ART.mkdir(parents=True, exist_ok=True)
    path = ART / "sprites.svg"
    path.write_text(_with_levels(64 * n, SPRITE_LEVELS, defs, sheet), encoding="utf-8")
    return path


# ------------------------------------------------------------------ vector scene parts
DEFS = """
<linearGradient id="ceil" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3b3b3b"/><stop offset="1" stop-color="#0d0d0d"/></linearGradient>
<linearGradient id="floor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0f0b07"/><stop offset="1" stop-color="#4f3d29"/></linearGradient>
<linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7a7a7a"/><stop offset="0.12" stop-color="#9c9c9c"/><stop offset="1" stop-color="#555"/></linearGradient>
<linearGradient id="steel" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#2a2a2e"/><stop offset="0.45" stop-color="#6a6a72"/><stop offset="0.55" stop-color="#8a8a94"/><stop offset="1" stop-color="#2a2a2e"/></linearGradient>
<linearGradient id="wood" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#3b220f"/><stop offset="0.5" stop-color="#7a4a22"/><stop offset="1" stop-color="#3b220f"/></linearGradient>
<radialGradient id="flash"><stop offset="0" stop-color="#fffbe0"/><stop offset="0.35" stop-color="#ffd84a"/><stop offset="1" stop-color="#ff6a00" stop-opacity="0"/></radialGradient>
<radialGradient id="vignette" cx="0.5" cy="0.45" r="0.75"><stop offset="0.6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.55"/></radialGradient>
<g id="digits"><text class="strip">""" + "".join(f'<tspan x="0" dy="{0 if i == 0 else 20}">{i}</tspan>' for i in range(10)) + """</text></g>
"""

BACKDROP = """<rect width="320" height="84" fill="url(#ceil)"/><rect y="84" width="320" height="84" fill="url(#floor)"/>"""


def weapon_markup():
    return """<g id="xhair" pointer-events="none"><rect x="155" y="83.5" width="3" height="1"/><rect x="162" y="83.5" width="3" height="1"/>
  <rect x="159.5" y="79" width="1" height="3" /><rect x="159.5" y="86" width="1" height="3"/></g>
<g id="gun" pointer-events="none"><g class="gunbob"><g class="gunkick">
  <ellipse class="muzzle" cx="160" cy="96" rx="30" ry="22" fill="url(#flash)"/>
  <path d="M156.5 98 L163.5 98 L169 168 L151 168 Z" fill="url(#steel)"/>
  <path d="M157.5 98 L162.5 98 L162.5 100 L157.5 100 Z" fill="#111"/>
  <path d="M155 112 L165 112 L168 150 L152 150 Z" fill="#1c1c20"/>
  <path d="M153.5 118 L166.5 118 L169.5 146 L150.5 146 Z" fill="url(#wood)"/>
  <g stroke="#2a1608" stroke-width="0.8"><path d="M153 124 L167 124"/><path d="M152.5 129 L167.5 129"/><path d="M152 134 L168 134"/><path d="M151.5 139 L168.5 139"/></g>
  <path d="M146 128 Q144 140 150 147 L153 146 L152 126 Z" fill="#c48c64"/>
  <path d="M174 128 Q176 140 170 147 L167 146 L168 126 Z" fill="#b07a54"/>
  <path d="M147.5 132 L152 132 M147 137 L152 137 M148 142 L152 142" stroke="#8a5a3a" stroke-width="0.8"/>
  <path d="M141 150 L179 150 L186 168 L134 168 Z" fill="#2a2a2e"/>
  <path d="M144 152 L176 152 L181 168 L139 168 Z" fill="#3c3c42"/>
  <rect x="156" y="152" width="8" height="16" fill="url(#steel)"/>
</g></g></g>"""


def number(x, y, var, digits=3, cls="big"):
    """Odometer digits: each digit is a clipped strip of 0-9 translated by -digit * line."""
    out = [f'<g class="num {cls}" style="--v: max(0, var(--{var}))">']
    for k in range(digits):
        dx = x + (digits - 1 - k) * 9.5
        out.append(f'<svg class="dg dg{k}" x="{dx}" y="{y}" width="12" height="15"><use href="#digits" y="13"/></svg>')
    out.append("</g>")
    return "".join(out)


def hud_markup():
    return f"""<g id="hud">
  <rect y="168" width="320" height="32" fill="url(#bar)"/>
  <g fill="#3a3a3a" opacity="0.6"><rect x="0" y="168" width="320" height="1"/><rect x="52" y="170" width="1" height="28"/><rect x="118" y="170" width="1" height="28"/><rect x="146" y="170" width="1" height="28"/><rect x="174" y="170" width="1" height="28"/><rect x="246" y="170" width="1" height="28"/></g>
  {number(10, 172, 'ammo')}
  <text class="lbl" x="27" y="197">AMMO</text>
  {number(58, 172, 'hp')}<text class="pct" x="92" y="185">%</text>
  <text class="lbl" x="85" y="197">HEALTH</text>
  <text class="lbl" x="132" y="182">ARMS</text><text class="arm" x="125" y="194">2</text><text class="arm on" x="134" y="194">3</text>
  <g id="face" transform="translate(160 184)">
    <rect x="-13" y="-15" width="26" height="30" fill="#1a1a1a"/>
    <g class="facebody">
      <path d="M-10 -6 Q-10 -14 0 -14 Q10 -14 10 -6 L9 6 Q6 13 0 13 Q-6 13 -9 6 Z" fill="#c8906a"/>
      <path d="M-10 -6 Q-10 -15 0 -15 Q10 -15 10 -6 L8 -9 Q0 -12 -8 -9 Z" fill="#6b4a2a"/>
      <g class="eyes"><rect x="-6" y="-5" width="4" height="2.5" fill="#fff"/><rect x="2" y="-5" width="4" height="2.5" fill="#fff"/>
        <g class="pupils"><rect x="-4.6" y="-5" width="1.6" height="2.5" fill="#2a3a8a"/><rect x="3.4" y="-5" width="1.6" height="2.5" fill="#2a3a8a"/></g></g>
      <path d="M-7 -7 L-2 -6.5 M2 -6.5 L7 -7" stroke="#4a2a14" stroke-width="1.2"/>
      <path d="M-1 -2 L-2 2 L1 2" stroke="#8a5a3a" fill="none"/>
      <path class="mouth" d="M-4 6 Q0 7.5 4 6" stroke="#5a2a1a" stroke-width="1.4" fill="none"/>
      <path class="ouch" d="M-3.5 7 Q0 3.5 3.5 7 Z" fill="#3a0a0a"/>
      <g class="blood" fill="#9a0c0c"><path d="M-9 -2 l3 1 l-1 5 Z"/><path d="M5 4 l4 -2 l0 5 Z"/><path d="M-3 -12 l4 2 l-5 1 Z"/></g>
    </g>
    <g class="deadface"><path d="M-10 -6 Q-10 -14 0 -14 Q10 -14 10 -6 L9 6 Q6 13 0 13 Q-6 13 -9 6 Z" fill="#8a5a4a"/>
      <path d="M-6 -6 L-2 -2 M-2 -6 L-6 -2 M2 -6 L6 -2 M6 -6 L2 -2" stroke="#300" stroke-width="1.2"/>
      <path d="M-4 6 Q0 3 4 6" stroke="#300" stroke-width="1.4" fill="none"/><path d="M-9 0 Q0 4 9 0 L9 6 Q0 12 -9 6 Z" fill="#900" opacity="0.7"/></g>
  </g>
  {number(186, 172, 'kills', 2)}<text class="pct" x="210" y="185">/{len(ENEMIES)}</text>
  <text class="lbl" x="210" y="197">KILLS</text>
  <g class="joy" transform="translate(283 184)">
    <rect x="-34" y="-14" width="68" height="28" fill="#2a2a2a" opacity="0.5"/>
    <path class="j-fw" d="M0 -12 L5 -6 L-5 -6 Z"/><path class="j-bk" d="M0 12 L5 6 L-5 6 Z"/>
    <path class="j-tl1" d="M-12 0 L-7 -4 L-7 4 Z"/><path class="j-tl2" d="M-24 0 L-19 -4 L-19 4 Z M-30 0 L-25 -4 L-25 4 Z"/>
    <path class="j-tr1" d="M12 0 L7 -4 L7 4 Z"/><path class="j-tr2" d="M24 0 L19 -4 L19 4 Z M30 0 L25 -4 L25 4 Z"/>
    <circle class="j-fire" r="3"/>
  </g>
</g>
<rect id="hurtflash" width="320" height="168" fill="#c00"/>
<rect id="pickflash" width="320" height="168" fill="#ffd040"/>
<rect id="vig" width="320" height="168" fill="url(#vignette)" pointer-events="none"/>
<g id="msgs">{''.join(f'<text class="msg msg{k}" x="4" y="9">{msg}</text>' for k, msg in _messages())}</g>"""


def _messages():
    names = {"medkit": "Picked up a medikit.", "stimpack": "Picked up a stimpack.", "shells": "Picked up a box of shotgun shells."}
    base = len(ENEMIES)
    return [(base + k, names[it.kind]) for k, it in enumerate(ITEMS)]


def overlays_markup():
    # the START button sits in the pad's centre (idle) zone so play begins standing still
    zx = [0, 40, 116, 204, 280, 320]
    zy = [0, 62, 106, 168]
    sx, sy, ox, oy = 0.36, 0.3, 102.4, 120
    grid = "".join(
        f'<rect x="{ox + zx[c] * sx:.1f}" y="{oy + zy[r] * sy:.1f}" width="{(zx[c + 1] - zx[c]) * sx:.1f}" height="{(zy[r + 1] - zy[r]) * sy:.1f}"/>'
        for r in range(3) for c in range(5)
    )
    arrows = {(0, 0): "↖↖", (0, 1): "↖", (0, 2): "↑", (0, 3): "↗", (0, 4): "↗↗",
              (1, 0): "⟲⟲", (1, 1): "⟲", (1, 2): "·", (1, 3): "⟳", (1, 4): "⟳⟳",
              (2, 0): "↙↙", (2, 1): "↙", (2, 2): "↓", (2, 3): "↘", (2, 4): "↘↘"}
    labels = "".join(
        f'<text x="{ox + (zx[c] + zx[c + 1]) / 2 * sx:.1f}" y="{oy + (zy[r] + zy[r + 1]) / 2 * sy + 2.2:.1f}">{a}</text>'
        for (r, c), a in arrows.items()
    )
    return f"""<g id="title" class="overlay">
  <rect width="320" height="200" fill="#000" opacity="0.9"/>
  <text class="logo" x="160" y="48">DOOM</text><text class="logosub" x="160" y="62">.SVG</text>
  <a href="#play"><rect class="btn" x="122" y="72" width="76" height="22" rx="2"/><text class="btntxt" x="160" y="87.5">START</text></a>
  <text class="tag" x="160" y="108">no JavaScript · one SVG · walls raymarched in CSS calc()</text>
  <g class="zones">{grid}</g><g class="zonelbl">{labels}</g>
  <g class="help"><text x="160" y="180">the cursor over the view is your joystick</text>
  <text x="160" y="189">hold the mouse button to fire · walk into doors to open them</text></g>
</g>
<g id="play"/>
<g id="died" class="overlay"><rect width="320" height="200" fill="#400" opacity="0.6"/>
  <text class="logo small" x="160" y="90">YOU DIED</text>
  <a href="?again"><rect class="btn" x="110" y="120" width="100" height="20" rx="2"/><text class="btntxt" x="160" y="134">RESTART</text></a></g>
<g id="won" class="overlay"><rect width="320" height="200" fill="#000" opacity="0.85"/>
  <text class="logo small" x="160" y="56">E1M1 FINISHED</text>
  <text class="stat" x="110" y="90">KILLS</text>{number(196, 80, 'kpct', 3, 'stat')}<text class="statpct" x="232" y="90">%</text>
  <text class="stat" x="110" y="110">ITEMS</text>{number(196, 100, 'ipct', 3, 'stat')}<text class="statpct" x="232" y="110">%</text>
  <text class="stat" x="110" y="130">TIME</text>{number(196, 120, 'secs', 3, 'stat')}<text class="statpct" x="232" y="130">s</text>
  <a href="?again"><rect class="btn" x="110" y="150" width="100" height="20" rx="2"/><text class="btntxt" x="160" y="164">AGAIN</text></a></g>"""


HUD_CSS = """
.strip { font-size: 15px; fill: #c00; stroke: #300; stroke-width: 0.6px; paint-order: stroke; }
.num.stat .strip { fill: #d00; }
.dg use { transform: translateY(calc(mod(round(down, var(--v)), 10) * -20px)); }
.dg1 use { transform: translateY(calc(mod(round(down, var(--v) / 10), 10) * -20px)); }
.dg2 use { transform: translateY(calc(mod(round(down, var(--v) / 100), 10) * -20px)); }
.dg1 { opacity: calc(max(sign(var(--v) - 9.5), 0)); }
.dg2 { opacity: calc(max(sign(var(--v) - 99.5), 0)); }
.lbl { font-size: 7px; fill: #ddd; text-anchor: middle; font-family: Arial, sans-serif; font-weight: bold; }
.pct { font-size: 13px; fill: #c00; stroke: #300; stroke-width: 0.5px; paint-order: stroke; }
.arm { font-size: 9px; fill: #777; } .arm.on { fill: #ff0; }
.joy path, .joy circle { fill: #555; }
#doom:has(.fw:hover) .j-fw, #doom:has(.bk:hover) .j-bk, #doom:has(.tl1:hover) .j-tl1, #doom:has(.tl2:hover) .j-tl2,
#doom:has(.tr1:hover) .j-tr1, #doom:has(.tr2:hover) .j-tr2 { fill: #ffd040; }
.j-fire { fill: if(style(--fire: 1): #f40; else: #555) !important; }
#xhair rect { fill: if(style(--aimed: 1): #ff3020; else: #bbb); opacity: if(style(--aimed: 1): 0.95; else: 0.45); }
.pupils { transform: translateX(calc((mod(round(down, var(--clock) / 1.7), 3) - 1) * 1.6px)); }
.ouch { display: if(style(--hurt: 1): inline; else: none); }
.mouth { display: if(style(--hurt: 1): none; else: inline); }
.blood { opacity: calc(clamp(0, (80 - var(--hp)) / 60, 1)); }
.deadface { display: if(style(--dead: 1): inline; else: none); }
.facebody { display: if(style(--dead: 1): none; else: inline); }
#hurtflash { pointer-events: none; opacity: calc(var(--hurt) * (0.18 + 0.14 * var(--blink)) + var(--dead) * 0.35); }
#pickflash { pointer-events: none; opacity: 0; }
.msg { font-family: Arial, sans-serif; font-size: 7px; fill: #e33; opacity: 0; pointer-events: none; }
@keyframes msgshow { 0%, 85% { opacity: 1; } 100% { opacity: 0; } }
@keyframes pickflash { 0% { opacity: 0.35; } 100% { opacity: 0; } }
.gunbob { transform: translate(calc(var(--moving) * sin(var(--clock) * 7) * 6px), calc(var(--moving) * abs(cos(var(--clock) * 7)) * 5px + 6px)); }
.gunkick { animation: if(style(--fire: 1): gunfire; else: none) 0.9s linear infinite; }
@keyframes gunfire { 0% { transform: translateY(10px); } 12% { transform: translateY(6px); } 40% { transform: translateY(0); } 100% { transform: translateY(0); } }
.muzzle { opacity: 0; animation: if(style(--fire: 1): muzzle; else: none) 0.9s steps(1) infinite; }
@keyframes muzzle { 0% { opacity: 1; } 12% { opacity: 0; } 100% { opacity: 0; } }
.overlay text { text-anchor: middle; }
.logo { font-size: 52px; fill: #b01010; stroke: #ffb000; stroke-width: 1.4px; paint-order: stroke; letter-spacing: 2px; }
.logo.small { font-size: 22px; }
.logosub { font-size: 14px; fill: #ddd; letter-spacing: 6px; }
.tag { font-family: Arial, sans-serif; font-size: 6.5px; fill: #aaa; }
.help text { font-family: Arial, sans-serif; font-size: 7px; fill: #ccc; }
.zones rect { fill: #2a0a0a; stroke: #a33; stroke-width: 0.4px; }
.zonelbl text { font-family: 'Segoe UI Symbol', Arial, sans-serif; font-size: 6.5px; fill: #f0c070; }
.btn { fill: #600; stroke: #f40; cursor: pointer; } a:hover .btn { fill: #900; }
.btntxt { font-size: 12px; fill: #fff; pointer-events: none; }
.stat { font-size: 14px; fill: #c00; text-anchor: start !important; }
.statpct { font-size: 14px; fill: #c00; }
#title { display: inline; } #doom:has(#play:target) #title { display: none; }
#died { display: if(style(--dead: 1): inline; else: none); }
#won { display: if(style(--won: 1) and style(--dead: 0): inline; else: none); }
"""
