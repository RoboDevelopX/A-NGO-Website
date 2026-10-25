"""Guard rail for rebrands: text colour pairs must meet WCAG 2.1 AA (4.5:1 for body text)."""

import pytest

from app.config import BRAND


def _luminance(hex_colour: str) -> float:
    hex_colour = hex_colour.lstrip("#")
    channels = [int(hex_colour[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a: str, b: str) -> float:
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


c = BRAND.colors

TEXT_PAIRS = [
    ("body text", c.ink, c.background),
    ("body text on cards", c.ink, c.surface),
    ("muted text", c.muted, c.background),
    ("muted text on tint", c.muted, c.primary_light),
    ("links", c.primary, c.background),
    ("links on tint", c.primary, c.primary_light),
    ("primary button", c.surface, c.primary),
    ("donate button", c.ink, c.accent),
    ("donate button hover", c.ink, c.accent_dark),
    ("footer text", c.primary_light, c.primary_dark),
    ("error text", c.error, c.surface),
    ("success text", c.success, c.surface),
    ("demo banner", c.ink, c.warning_bg),
]


@pytest.mark.parametrize(("name", "fg", "bg"), TEXT_PAIRS, ids=[p[0] for p in TEXT_PAIRS])
def test_text_contrast_meets_wcag_aa(name, fg, bg):
    assert contrast(fg, bg) >= 4.5, f"{name}: {contrast(fg, bg):.2f}:1"


def test_stat_numbers_on_dark_section_meet_large_text_threshold():
    # Stat values are 36px+ bold, so the 3:1 large-text threshold applies.
    assert contrast(c.accent, c.primary_dark) >= 3.0
