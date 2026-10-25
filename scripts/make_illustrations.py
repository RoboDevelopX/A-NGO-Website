"""Generate the flat SVG illustrations used as placeholder photos.

Real NGO sites use photographs; a portfolio repo should not ship stock photos it has no
licence for. These scenes are generated from simple shapes so they are small, licence-free
and easy to swap for real photos later (keep the same file names and update the alt text in
app/content.py and app/seed_data.py).

Usage: python -m scripts.make_illustrations
"""

from __future__ import annotations

import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCENES = ROOT / "static" / "img" / "scenes"
PEOPLE = ROOT / "static" / "img" / "people"

TEAL, TEAL_2, TEAL_LIGHT = "#0F5E5A", "#1E7A73", "#E3F0EE"
SAFFRON, TERRACOTTA, SAND, CREAM = "#E89B2D", "#C8553D", "#F3E3C3", "#FBF8F3"
SKY, INK, PLUM, LEAF = "#CFE6EA", "#1F2933", "#6D3B5E", "#3E8E5A"
SKINS = ["#8D5524", "#A0673C", "#C68642", "#6B3E1E", "#B07040"]
CLOTHES = [SAFFRON, TERRACOTTA, TEAL_2, PLUM, "#3B6FB6", LEAF, "#D9A441"]
HAIR = "#2B1B12"

W, H = 800, 600


def svg(width: int, height: int, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" aria-hidden="true">{body}</svg>\n'
    )


def backdrop(sky_top: str, sky_bottom: str, ground: str, gid: str) -> str:
    return (
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{sky_top}"/><stop offset="1" stop-color="{sky_bottom}"/>'
        f'</linearGradient></defs><rect width="{W}" height="{H}" fill="url(#{gid})"/>'
        f'<path d="M0 380 Q 200 320 400 370 T 800 350 V 600 H 0 Z" fill="{TEAL_LIGHT}" opacity=".7"/>'
        f'<path d="M0 420 Q 260 380 520 420 T 800 410 V 600 H 0 Z" fill="{ground}"/>'
    )


def sun(cx: int, cy: int, r: int = 46, colour: str = SAFFRON) -> str:
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{colour}" opacity=".9"/>'


def tree(x: int, y: int, s: float = 1.0) -> str:
    return (
        f'<rect x="{x - 14 * s}" y="{y - 150 * s}" width="{28 * s}" height="{150 * s}" rx="{8 * s}" fill="#7A4E2D"/>'
        f'<circle cx="{x}" cy="{y - 190 * s}" r="{95 * s}" fill="{LEAF}"/>'
        f'<circle cx="{x - 80 * s}" cy="{y - 150 * s}" r="{60 * s}" fill="{LEAF}"/>'
        f'<circle cx="{x + 85 * s}" cy="{y - 155 * s}" r="{65 * s}" fill="#357A4D"/>'
    )


def person(
    x: float,
    y: float,
    s: float,
    skin: str,
    cloth: str,
    *,
    sitting: bool,
    hair: str = "short",
    arms_up: bool = False,
) -> str:
    """A simple figure standing (or sitting) with its feet/base at (x, y)."""
    height = 70 if sitting else 120
    head_r = 16
    top = y - height * s
    body = (
        f'<path d="M{x - 26 * s} {y} Q {x - 30 * s} {top + 30 * s} {x} {top + 18 * s} '
        f'Q {x + 30 * s} {top + 30 * s} {x + 26 * s} {y} Z" fill="{cloth}"/>'
    )
    if sitting:
        body += f'<ellipse cx="{x}" cy="{y}" rx="{40 * s}" ry="{12 * s}" fill="{cloth}"/>'
    else:
        body += (
            f'<rect x="{x - 18 * s}" y="{y - 4 * s}" width="{12 * s}" height="{30 * s}" fill="{INK}"/>'
            f'<rect x="{x + 6 * s}" y="{y - 4 * s}" width="{12 * s}" height="{30 * s}" fill="{INK}"/>'
        )
    if arms_up:
        body += (
            f'<path d="M{x + 18 * s} {top + 40 * s} L {x + 48 * s} {top - 5 * s}" stroke="{skin}" '
            f'stroke-width="{9 * s}" stroke-linecap="round"/>'
        )
    hx, hy, r = x, top, head_r * s
    head = f'<circle cx="{hx}" cy="{hy}" r="{r}" fill="{skin}"/>'
    if hair == "long":
        hair_svg = (
            f'<path d="M{hx - r} {hy + 2 * s} A {r} {r} 0 0 1 {hx + r} {hy + 2 * s} '
            f"L {hx + r} {hy + r * 1.6} L {hx + r * 0.6} {hy + r * 1.6} L {hx + r * 0.7} {hy - r * 0.2} "
            f'L {hx - r * 0.7} {hy - r * 0.2} L {hx - r * 0.6} {hy + r * 1.6} L {hx - r} {hy + r * 1.6} Z" fill="{HAIR}"/>'
        )
    elif hair == "bun":
        hair_svg = (
            f'<path d="M{hx - r} {hy} A {r} {r} 0 0 1 {hx + r} {hy} Z" fill="{HAIR}"/>'
            f'<circle cx="{hx}" cy="{hy - r}" r="{r * 0.45}" fill="{HAIR}"/>'
        )
    else:
        hair_svg = f'<path d="M{hx - r} {hy} A {r} {r} 0 0 1 {hx + r} {hy} Z" fill="{HAIR}"/>'
    return body + head + hair_svg


def book(x: float, y: float, s: float = 1.0, colour: str = TERRACOTTA) -> str:
    return (
        f'<path d="M{x} {y} q {-18 * s} {-8 * s} {-34 * s} {-2 * s} v {22 * s} q {16 * s} {-6 * s} {34 * s} {2 * s} z" fill="{CREAM}" stroke="{colour}" stroke-width="{3 * s}"/>'
        f'<path d="M{x} {y} q {18 * s} {-8 * s} {34 * s} {-2 * s} v {22 * s} q {-16 * s} {-6 * s} {-34 * s} {2 * s} z" fill="{CREAM}" stroke="{colour}" stroke-width="{3 * s}"/>'
    )


def mat(x: int, y: int, w: int, h: int, colour: str = TERRACOTTA) -> str:
    stripes = "".join(
        f'<rect x="{x}" y="{y + i * h / 6}" width="{w}" height="{h / 12}" fill="{CREAM}" opacity=".35"/>'
        for i in range(1, 6)
    )
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{colour}"/>{stripes}'


def children_row(rng: random.Random, xs: list[int], y: int, s: float, with_books: bool) -> str:
    out = ""
    for i, x in enumerate(xs):
        out += person(
            x,
            y,
            s,
            rng.choice(SKINS),
            CLOTHES[i % len(CLOTHES)],
            sitting=True,
            hair="long" if i % 2 else "short",
        )
        if with_books:
            out += book(x, y - 26 * s, 0.8 * s, CLOTHES[(i + 2) % len(CLOTHES)])
    return out


def scene_hero() -> str:
    rng = random.Random(1)
    body = backdrop("#F7E6C4", CREAM, SAND, "g-hero") + sun(640, 140, 60)
    body += (
        '<rect x="80" y="230" width="230" height="200" fill="#E7C9A0"/><path d="M60 240 L195 160 L330 240 Z" fill="'
        + TERRACOTTA
        + '"/>'
    )
    body += '<rect x="170" y="330" width="50" height="100" fill="#7A4E2D"/>'
    body += tree(660, 470, 0.9)
    body += mat(250, 470, 420, 70)
    body += person(200, 520, 1.25, SKINS[2], PLUM, sitting=False, hair="bun")
    body += book(232, 410, 1.2, SAFFRON)
    body += children_row(rng, [310, 400, 490, 580], 520, 1.0, with_books=False)
    return svg(W, H, body)


def scene_reading_circle() -> str:
    rng = random.Random(2)
    body = backdrop(SKY, CREAM, SAND, "g-read") + sun(120, 110)
    body += tree(400, 430, 1.1)
    body += mat(140, 470, 520, 80, TEAL_2)
    body += children_row(rng, [200, 300, 400, 500, 600], 520, 1.0, with_books=True)
    return svg(W, H, body)


def scene_teacher_training() -> str:
    rng = random.Random(3)
    body = f'<rect width="{W}" height="{H}" fill="#F1EADF"/><rect y="440" width="{W}" height="160" fill="#D8C3A5"/>'
    body += '<rect x="120" y="80" width="460" height="250" rx="10" fill="#2F4F46" stroke="#7A4E2D" stroke-width="14"/>'
    for i, (x, w) in enumerate([(160, 120), (300, 90), (420, 110), (160, 200), (390, 140)]):
        y = 140 if i < 3 else 220
        body += f'<path d="M{x} {y} q 20 -25 40 0 t 40 0 t {w - 80} 0" stroke="{CREAM}" stroke-width="6" fill="none" stroke-linecap="round"/>'
    body += person(660, 470, 1.3, SKINS[1], SAFFRON, sitting=False, hair="bun", arms_up=True)
    for i, x in enumerate([170, 290, 410, 530]):
        body += person(
            x,
            560,
            1.1,
            rng.choice(SKINS),
            CLOTHES[(i + 3) % len(CLOTHES)],
            sitting=True,
            hair="long",
        )
    return svg(W, H, body)


def scene_digital_corner() -> str:
    rng = random.Random(4)
    body = f'<rect width="{W}" height="{H}" fill="{TEAL_LIGHT}"/><rect y="430" width="{W}" height="170" fill="#BFD9D4"/>'
    # A window with a view of the fields outside.
    body += '<rect x="540" y="60" width="200" height="160" rx="6" fill="#7A4E2D"/>'
    body += f'<rect x="552" y="72" width="176" height="136" fill="{SKY}"/>'
    body += f'<path d="M552 170 Q 600 140 650 165 T 728 150 V 208 H 552 Z" fill="{LEAF}"/>'
    body += '<rect x="636" y="72" width="8" height="136" fill="#7A4E2D"/><rect x="552" y="136" width="176" height="8" fill="#7A4E2D"/>'
    body += '<rect x="180" y="400" width="440" height="30" rx="6" fill="#7A4E2D"/><rect x="210" y="430" width="20" height="90" fill="#7A4E2D"/><rect x="570" y="430" width="20" height="90" fill="#7A4E2D"/>'
    body += person(280, 400, 1.1, rng.choice(SKINS), SAFFRON, sitting=True, hair="long")
    body += person(
        400, 400, 1.15, rng.choice(SKINS), PLUM, sitting=True, hair="short", arms_up=True
    )
    body += person(520, 400, 1.1, rng.choice(SKINS), TERRACOTTA, sitting=True, hair="long")
    body += (
        '<rect x="340" y="355" width="120" height="80" rx="10" fill="'
        + INK
        + '"/><rect x="350" y="365" width="100" height="60" rx="4" fill="#9BD3CB"/>'
    )
    body += (
        '<circle cx="380" cy="395" r="10" fill="'
        + SAFFRON
        + '"/><rect x="398" y="385" width="40" height="8" rx="4" fill="'
        + CREAM
        + '"/><rect x="398" y="400" width="30" height="8" rx="4" fill="'
        + CREAM
        + '"/>'
    )
    return svg(W, H, body)


def scene_girls_football() -> str:
    rng = random.Random(5)
    body = backdrop("#F4B76A", "#F7DDB0", "#D9B07A", "g-foot") + sun(400, 330, 90, "#F6C66B")
    body += (
        '<rect x="30" y="300" width="12" height="150" fill="'
        + CREAM
        + '"/><rect x="160" y="300" width="12" height="150" fill="'
        + CREAM
        + '"/><rect x="30" y="300" width="142" height="10" fill="'
        + CREAM
        + '"/>'
    )
    for i, x in enumerate([260, 380, 520, 650]):
        body += person(
            x,
            500 + (i % 2) * 20,
            1.05,
            rng.choice(SKINS),
            [TEAL_2, "#3B6FB6"][i % 2],
            sitting=False,
            hair="long",
            arms_up=i == 1,
        )
    body += f'<circle cx="455" cy="530" r="18" fill="{CREAM}" stroke="{INK}" stroke-width="3"/>'
    return svg(W, H, body)


def scene_library_shelf() -> str:
    rng = random.Random(6)
    body = f'<rect width="{W}" height="{H}" fill="#F6EBDD"/><rect y="520" width="{W}" height="80" fill="#D8C3A5"/>'
    body += '<rect x="150" y="60" width="500" height="460" rx="8" fill="#8A5A35"/>'
    for row in range(4):
        y = 80 + row * 110
        body += f'<rect x="165" y="{y + 92}" width="470" height="12" fill="#6E4527"/>'
        x = 175
        while x < 610:
            w = rng.randint(18, 34)
            h = rng.randint(60, 88)
            colour = rng.choice([*CLOTHES, CREAM, TEAL])
            if rng.random() < 0.12 and x < 560:
                body += f'<rect x="{x}" y="{y + 92 - h * 0.9}" width="{h * 0.9}" height="{w}" fill="{colour}" transform="rotate(-12 {x} {y + 92})"/>'
                x += int(h * 0.6)
            else:
                body += f'<rect x="{x}" y="{y + 92 - h}" width="{w}" height="{h}" rx="2" fill="{colour}"/>'
                x += w + 3
    body += person(700, 560, 0.95, SKINS[0], SAFFRON, sitting=False, hair="long")
    return svg(W, H, body)


def scene_parents_meeting() -> str:
    rng = random.Random(7)
    body = backdrop(SKY, "#EAF2EE", SAND, "g-par")
    body += (
        '<rect x="520" y="200" width="220" height="230" fill="#E7C9A0"/><path d="M500 210 L630 140 L760 210 Z" fill="'
        + TERRACOTTA
        + '"/>'
    )
    body += mat(60, 470, 460, 90, PLUM)
    body += person(600, 520, 1.25, SKINS[2], TEAL_2, sitting=False, hair="bun", arms_up=True)
    for i, x in enumerate([120, 220, 320, 420]):
        body += person(
            x,
            530,
            1.15,
            rng.choice(SKINS),
            CLOTHES[(i + 1) % len(CLOTHES)],
            sitting=True,
            hair="bun" if i % 2 else "short",
        )
    return svg(W, H, body)


def avatar(skin: str, cloth: str, bg: str, hair: str, glasses: bool = False) -> str:
    body = f'<circle cx="100" cy="100" r="100" fill="{bg}"/>'
    body += f'<path d="M30 200 Q 35 130 100 128 Q 165 130 170 200 Z" fill="{cloth}"/>'
    body += f'<rect x="88" y="105" width="24" height="28" fill="{skin}"/>'
    if hair == "long":
        body += (
            f'<path d="M58 80 Q 60 30 100 30 Q 140 30 142 80 L 146 140 L 54 140 Z" fill="{HAIR}"/>'
        )
    body += f'<ellipse cx="100" cy="82" rx="36" ry="42" fill="{skin}"/>'
    if hair in ("short", "long"):
        body += f'<path d="M63 78 Q 62 38 100 38 Q 138 38 137 78 Q 120 55 100 58 Q 80 55 63 78 Z" fill="{HAIR}"/>'
    elif hair == "bun":
        body += f'<path d="M63 78 Q 62 38 100 38 Q 138 38 137 78 Q 100 50 63 78 Z" fill="{HAIR}"/><circle cx="100" cy="34" r="16" fill="{HAIR}"/>'
    elif hair == "cap":
        body += f'<path d="M62 70 Q 64 36 100 36 Q 136 36 138 70 Z" fill="{CREAM}"/>'
    if glasses:
        body += f'<g fill="none" stroke="{INK}" stroke-width="3"><circle cx="86" cy="84" r="10"/><circle cx="114" cy="84" r="10"/><path d="M96 84 h8"/></g>'
    body += f'<path d="M88 104 q 12 8 24 0" stroke="{INK}" stroke-width="3" fill="none" stroke-linecap="round"/>'
    body += f'<circle cx="86" cy="84" r="3.5" fill="{INK}"/><circle cx="114" cy="84" r="3.5" fill="{INK}"/>'
    return svg(200, 200, body)


AVATARS = [
    (SKINS[0], TERRACOTTA, "#F7E6C4", "long", False),  # Sunita
    (SKINS[3], SAFFRON, TEAL_LIGHT, "long", False),  # Pooja
    (SKINS[2], "#3B6FB6", "#F7E6C4", "short", True),  # Arjun
    (SKINS[1], PLUM, TEAL_LIGHT, "bun", True),  # Kavita
    (SKINS[3], TEAL_2, "#F7E6C4", "short", False),  # Rahul
    (SKINS[2], SAFFRON, TEAL_LIGHT, "long", True),  # Ananya
    (SKINS[1], INK, "#F7E6C4", "cap", False),  # Imran
]


def main() -> None:
    SCENES.mkdir(parents=True, exist_ok=True)
    PEOPLE.mkdir(parents=True, exist_ok=True)
    scenes = {
        "hero": scene_hero,
        "reading-circle": scene_reading_circle,
        "teacher-training": scene_teacher_training,
        "digital-corner": scene_digital_corner,
        "girls-football": scene_girls_football,
        "library-shelf": scene_library_shelf,
        "parents-meeting": scene_parents_meeting,
    }
    for name, build in scenes.items():
        (SCENES / f"{name}.svg").write_text(build(), encoding="utf-8")
    for i, args in enumerate(AVATARS, start=1):
        (PEOPLE / f"avatar-{i}.svg").write_text(avatar(*args), encoding="utf-8")
    print(f"Wrote {len(scenes)} scenes and {len(AVATARS)} avatars.")


if __name__ == "__main__":
    main()
