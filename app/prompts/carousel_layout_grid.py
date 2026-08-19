from __future__ import annotations

"""Carousel layout grid (1080×1350 portrait).

Geometry only — colours and legal footer text come from Brand Space.
- 4:5 portrait LinkedIn/IG carousel
- Top-left headline, mid cards, bottom-right icon, bottom legal reserve
- Outer margins ~8%, logo pocket top-right

All values are ratios of canvas so they scale if export size differs.
"""

from dataclasses import dataclass


# Canonical sample canvas
CAROUSEL_W = 1080
CAROUSEL_H = 1350

# Neutral layout fallbacks only — Brand Space palette overrides at render time.
NAVY = (31, 41, 55)  # #1F2937
BODY_GRAY = (55, 65, 81)  # #374151
ORANGE = (75, 85, 99)  # #4B5563
ICE_BLUE = (243, 244, 246)  # #F3F4F6
CARD_WHITE = (255, 255, 255)
CARD_SHADOW = (209, 213, 219)


@dataclass(frozen=True)
class CarouselLayout:
    """Pixel boxes for one canvas size."""

    width: int
    height: int
    margin_x: int
    margin_top: int
    logo_left: int
    logo_bottom: int
    headline_box: tuple[int, int, int, int]  # x0,y0,x1,y1
    supporting_box: tuple[int, int, int, int]
    cards_box: tuple[int, int, int, int]
    icon_box: tuple[int, int, int, int]
    legal_footer_top: int
    content_wipe: tuple[int, int, int, int]  # wipe AI text, keep icon


def resolve_carousel_layout(width: int = CAROUSEL_W, height: int = CAROUSEL_H) -> CarouselLayout:
    """Compute locked zones for a carousel canvas.

    Sample geometry (1080×1350 reference):
    - Outer margin X: 8% (~86px)
    - Top content start: 7% (~95px) — below logo band
    - Logo pocket: right 24% × top 12% (matches the compositor's wipe)
    - Headline: left content to 78% width, max 2 lines
    - Supporting: under headline
    - Cards column: left 8% → 58% width (leaves icon column)
    - Icon: right 55%→94% × mid 48%→74% (above legal footer)
    - Legal footer: bottom 24% empty then Pillow text from Brand Space
    """
    w = max(int(width), 1)
    h = max(int(height), 1)

    mx = int(w * 0.08)
    mt = int(h * 0.07)
    logo_left = int(w * 0.76)
    logo_bottom = int(h * 0.12)
    legal_footer_top = int(h * 0.76)  # bottom 24%

    # Headline sits under top margin, left of logo pocket
    hl_x0 = mx
    hl_y0 = mt
    hl_x1 = min(int(w * 0.78), logo_left - int(w * 0.02))
    hl_y1 = int(h * 0.20)

    # Supporting under headline
    sup_x0 = mx
    sup_y0 = hl_y1 + int(h * 0.008)
    sup_x1 = hl_x1
    sup_y1 = int(h * 0.28)

    # Cards: left column only — never enter icon or legal footer
    cards_x0 = mx
    cards_y0 = max(sup_y1 + int(h * 0.012), int(h * 0.28))
    cards_x1 = int(w * 0.58)
    cards_y1 = int(h * 0.72)

    # Icon pocket bottom-right above legal footer
    icon_x0 = int(w * 0.55)
    icon_y0 = int(h * 0.48)
    icon_x1 = int(w * 0.94)
    icon_y1 = legal_footer_top - int(h * 0.02)

    # Wipe AI-baked text in headline+cards; keep icon column
    wipe_x0 = int(w * 0.04)
    wipe_y0 = int(h * 0.05)
    wipe_x1 = int(w * 0.60)
    wipe_y1 = legal_footer_top - int(h * 0.01)

    return CarouselLayout(
        width=w,
        height=h,
        margin_x=mx,
        margin_top=mt,
        logo_left=logo_left,
        logo_bottom=logo_bottom,
        headline_box=(hl_x0, hl_y0, hl_x1, hl_y1),
        supporting_box=(sup_x0, sup_y0, sup_x1, sup_y1),
        cards_box=(cards_x0, cards_y0, cards_x1, cards_y1),
        icon_box=(icon_x0, icon_y0, icon_x1, icon_y1),
        legal_footer_top=legal_footer_top,
        content_wipe=(wipe_x0, wipe_y0, wipe_x1, wipe_y1),
    )


def layout_prompt_lock(width: int = CAROUSEL_W, height: int = CAROUSEL_H) -> str:
    """Short lock for image prompts — exact % zones matching resolve_carousel_layout."""
    return (
        f"CANVAS LOCK {width}x{height}. "
        f"Margins 8% all sides. "
        f"TOP-RIGHT 14%x9%: empty (logo later). "
        f"HEADLINE zone: top-left, y 7–20%, width to 78% — COMPLETE Brand Space primary text. "
        f"SUPPORTING: y 20–28%. "
        f"CARDS: left column x 8–58%, y 28–72% — 2 white cards, COMPLETE sentences. "
        f"ICON ONLY: right pocket x 55–94%, y 48–74% — ONE premium clay-3D object. "
        f"BOTTOM 24% (y 76–100%): EMPTY canvas for Brand Space legal footer — no buttons, no text, no icons. "
        f"If CTA button appears ABOVE the legal footer: COMPACT only — width ≤28% canvas, height ≤4.5% canvas, "
        f"2–3 word label, small padding — NEVER a wide accent bar. "
        f"Never clip. Never mid-word cut."
    )
