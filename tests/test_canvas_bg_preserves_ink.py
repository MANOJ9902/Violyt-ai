"""Canvas background enforcement must never eat text.

Regression for headline glyphs that came back with Brand-BG holes punched through
them: the background flood fill was seeded inside the header, classified navy
letter strokes as "navy used as page fill", and ran through them.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from app.services.image_generation.dalle_service import (
    _ensure_light_brand_background,
    _flatten_near_brand_canvas,
)

BRAND_BG = "#EEF4FF"
NAVY = (18, 48, 143, 255)
WHITE = (255, 255, 255, 255)
PALE_PLATE = (224, 239, 255, 255)


def _poster() -> Image.Image:
    """Ice page + thick navy headline + navy band with white text."""
    img = Image.new("RGBA", (600, 800), (238, 244, 255, 255))
    d = ImageDraw.Draw(img)
    # Headline: thick navy bars standing in for glyph strokes.
    for i in range(4):
        x = 60 + i * 90
        d.rectangle([x, 70, x + 46, 190], fill=NAVY)
    # Inset navy section band with white text inside it.
    d.rectangle([50, 400, 550, 470], fill=NAVY)
    d.rectangle([180, 425, 420, 445], fill=WHITE)
    return img


def _count(img: Image.Image, colour: tuple[int, int, int]) -> int:
    px = img.convert("RGBA").load()
    w, h = img.size
    n = 0
    for y in range(h):
        for x in range(w):
            if px[x, y][:3] == colour:
                n += 1
    return n


def test_flood_fill_does_not_punch_holes_in_navy_headline() -> None:
    before = _poster()
    navy_before = _count(before, NAVY[:3])
    after = _ensure_light_brand_background(before.copy(), BRAND_BG)
    navy_after = _count(after, NAVY[:3])
    # Headline strokes and the section band must survive intact.
    assert navy_after >= navy_before * 0.99, (navy_before, navy_after)


def test_flood_fill_keeps_inset_navy_band() -> None:
    after = _ensure_light_brand_background(_poster(), BRAND_BG)
    px = after.convert("RGBA").load()
    # Centre of the band (offset from the white text block) is still navy.
    assert px[80, 435][:3] == NAVY[:3]
    assert px[520, 435][:3] == NAVY[:3]


def test_flatten_keeps_white_text_on_a_navy_band() -> None:
    after = _flatten_near_brand_canvas(_poster(), BRAND_BG)
    px = after.convert("RGBA").load()
    # White label inside the navy band must not be bleached to Brand BG.
    assert px[300, 435][:3] == WHITE[:3]


def test_flatten_still_removes_a_nested_pale_plate() -> None:
    img = Image.new("RGBA", (600, 800), (238, 244, 255, 255))
    ImageDraw.Draw(img).rectangle([80, 200, 520, 600], fill=PALE_PLATE)
    after = _flatten_near_brand_canvas(img, BRAND_BG)
    px = after.convert("RGBA").load()
    # The off-brand plate is gone, leaving one Brand Space background.
    assert px[300, 400][:3] == (238, 244, 255)
    assert _count(after, PALE_PLATE[:3]) < 4000


def test_navy_page_background_is_still_rekeyed() -> None:
    """A genuinely navy page (edge to edge) must still be pinned to Brand BG."""
    img = Image.new("RGBA", (400, 400), NAVY)
    after = _ensure_light_brand_background(img, BRAND_BG)
    px = after.convert("RGBA").load()
    assert px[200, 200][:3] == (238, 244, 255)
