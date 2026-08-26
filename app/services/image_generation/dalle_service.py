from __future__ import annotations

"""DALL-E / gpt-image-1 image generation service with brand logo overlay.

After generating the base image, the service optionally composites the brand
logo onto the image using PIL.  This is the only reliable way to embed an
exact brand logo — AI models cannot accurately render arbitrary logos.
"""

import base64
import re
from io import BytesIO
from urllib.request import urlopen
from uuid import UUID, uuid4

from openai import AsyncOpenAI
from PIL import Image

from app.core.config import get_settings
from app.core.logging import get_logger
from app.integrations.object_storage import get_object_storage
from app.utils.palette_roles import normalize_hex

logger = get_logger(__name__)

# Keep Brand Space logo compact in top-right (full lockup OK — do NOT strip logo text).
# Transparent BG only; smaller footprint so headlines stay clear.
_LOGO_MAX_WIDTH_RATIO = 0.11
# Minimum logo short-side in pixels (prevents tiny, unreadable logos).
_LOGO_MIN_PX = 48
# Padding from the canvas edge when placing the logo (in pixels).
_LOGO_EDGE_PADDING = 14
# Logo background fill color (used only for solid-background logos without transparency).
_LOGO_BG_COLOR = (255, 255, 255, 0)  # transparent
def _rgba(hex_color: str) -> tuple[int, int, int, int]:
    h = (normalize_hex(hex_color) or "#FFFFFF").lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


_LEGAL_FOOTER_COLOR = (104, 116, 125, 255)
_DEFAULT_CANVAS_BG = "#FFFFFF"


def _flatten_rgba_to_brand_bg(img: Image.Image, bg_hex: str = _DEFAULT_CANVAS_BG) -> Image.Image:
    """Flatten any transparency onto the Brand Space background colour."""
    rgba = img.convert("RGBA")
    bg = Image.new("RGBA", rgba.size, _rgba(bg_hex or _DEFAULT_CANVAS_BG))
    bg.alpha_composite(rgba)
    return bg


def _colour_dist(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    return abs(c1[0] - c2[0]) + abs(c1[1] - c2[1]) + abs(c1[2] - c2[2])


def _split_fused_card_band(
    img: Image.Image,
    bg_hex: str = _DEFAULT_CANVAS_BG,
    *,
    columns: int = 4,
) -> Image.Image:
    """Punch Brand BG gutters through a fused full-width card slab.

    Landscape static often paints one medium-blue rectangle behind all cards,
    which reads as a second page colour. Restoring ice in the side margins and
    between columns makes four separate cards on ONE background.
    """
    rgba = img.convert("RGBA")
    w, h = rgba.size
    if h >= 800 or w < 400:
        return rgba
    br, bgc, bb, _ = _rgba(bg_hex or _DEFAULT_CANVAS_BG)
    brand = (br, bgc, bb, 255)
    px = rgba.load()
    side = max(int(w * 0.06), 48)
    gutter = max(int(w * 0.022), 22)
    inner = max(0, w - side * 2 - gutter * (columns - 1))
    card_w = inner // columns
    y0 = int(h * 0.28)
    y1 = int(h * 0.84)

    def _is_slab(r: int, g: int, b: int) -> bool:
        lum = (r + g + b) / 3
        sat = max(r, g, b) - min(r, g, b)
        # Medium cool fill (card/secondary) — not navy ink, not orange, not ice.
        if lum < 120 or lum > 225:
            return False
        if b < r + 18:
            return False
        if sat < 35:
            return False
        if r > 180 and g < 170 and b < 120:
            return False
        return True

    gutters: list[tuple[int, int]] = [(0, side), (w - side, w)]
    x = side + card_w
    for _ in range(columns - 1):
        gutters.append((x, min(w, x + gutter)))
        x += gutter + card_w

    changed = 0
    for y in range(y0, y1):
        for x0, x1 in gutters:
            for x in range(max(0, x0), min(w, x1)):
                r, g, b, a = px[x, y]
                if _is_slab(r, g, b):
                    px[x, y] = brand
                    changed += 1
    if changed:
        logger.info("dalle.fused_card_band_split", rekeyed=changed, canvas=f"{w}x{h}")
    return rgba


def _flatten_near_brand_canvas(img: Image.Image, bg_hex: str = _DEFAULT_CANVAS_BG) -> Image.Image:
    """Rekey nested ice/white page plates to exact Brand BG.

    LinkedIn static often paints a second pale-blue rectangle (e.g. 224,239,255)
    on top of Brand BG (235,243,252). That offset is too small for the navy/white
    flood-fill, then the CTA wipe (exact Brand BG) makes two backgrounds obvious.

    Pale pixels are only rekeyed when they belong to a light region wide enough to
    be a plate: the fill starts from pixels sitting well inside a light field and
    spreads through pale neighbours only. Ink is never a candidate, so white text
    on a navy band and highlights inside headline glyphs survive — flattening those
    globally is what bleached the band text and specked the headline.
    """
    rgba = img.convert("RGBA")
    w, h = rgba.size
    br, bg_, bb_, _ = _rgba(bg_hex or _DEFAULT_CANVAS_BG)
    brand = (br, bg_, bb_)
    px = rgba.load()
    changed = 0

    # Pixels that could belong to an off-brand pale plate.
    cand = bytearray(w * h)
    for y in range(h):
        row = y * w
        for x in range(w):
            r, g, b, _a = px[x, y]
            dist = _colour_dist((r, g, b), brand)
            if dist < 8:
                if dist:
                    px[x, y] = (br, bg_, bb_, 255)
                    changed += 1
                continue
            lum = (r + g + b) / 3
            sat = max(r, g, b) - min(r, g, b)
            if (lum > 205 and sat < 58 and dist < 56) or (lum > 242 and sat < 22):
                cand[row + x] = 1

    # A plate spans hundreds of pixels; a glyph stroke is tens. Reach must exceed
    # the thickest text stroke, or bold white band labels read as a pale plate.
    reach = max(6, min(w, h) // 45)
    stack: list[int] = []
    seen = bytearray(w * h)
    for y in range(reach, h - reach):
        row = y * w
        for x in range(reach, w - reach):
            i = row + x
            if not cand[i] or seen[i]:
                continue
            if (
                cand[i - reach]
                and cand[i + reach]
                and cand[i - reach * w]
                and cand[i + reach * w]
            ):
                seen[i] = 1
                stack.append(i)

    while stack:
        i = stack.pop()
        x, y = i % w, i // w
        px[x, y] = (br, bg_, bb_, 255)
        changed += 1
        for j in (i - 1, i + 1, i - w, i + w):
            if 0 <= j < w * h and cand[j] and not seen[j]:
                # Stay on the same row for horizontal steps.
                if j in (i - 1, i + 1) and j // w != y:
                    continue
                seen[j] = 1
                stack.append(j)

    if changed:
        logger.info("dalle.nested_plate_flattened", rekeyed=changed, bg=bg_hex, size=f"{w}x{h}")
    return rgba


def _ensure_light_brand_background(img: Image.Image, bg_hex: str = _DEFAULT_CANVAS_BG) -> Image.Image:
    """Pin the page canvas to Brand Space background without eating ink.

    Only background-SIZED regions reachable from a background seed are rekeyed:

    1) A thin outer edge is always pinned so every slide shares one canvas frame.
    2) Wrong page fills (near-black, navy-as-page, harsh white) are flood-filled
       only from the canvas EDGE, because a real page background touches the edge.
       An inset navy section band and a navy headline never do, so both survive.
    3) Nested pale "second page" plates are flood-filled from interior seeds, using
       a pale-only predicate so a navy glyph can never seed a fill.

    Each region is committed only if it is background-sized. Seeding inside the
    header used to let the fill run through connected navy letter strokes and punch
    Brand BG holes straight through the headline, so size is the hard guard.
    """
    rgba = img.convert("RGBA")
    w, h = rgba.size
    if w < 8 or h < 8:
        return rgba

    br, bg_, bb_, _ba = _rgba(bg_hex or _DEFAULT_CANVAS_BG)
    brand_bg = (br, bg_, bb_)
    px = rgba.load()

    # Always pin outer edge so every slide shares the same Brand Space canvas frame.
    edge = max(2, min(w, h) // 90)
    for y in range(h):
        for x in range(w):
            if x < edge or y < edge or x >= w - edge or y >= h - edge:
                px[x, y] = (br, bg_, bb_, 255)

    edge_seeds = [
        (edge + 2, edge + 2),
        (w // 2, edge + 2),
        (w - edge - 3, edge + 2),
        (edge + 2, h // 2),
        (w - edge - 3, h // 2),
        (edge + 2, h - edge - 3),
        (w // 2, h - edge - 3),
        (w - edge - 3, h - edge - 3),
        (w // 4, edge + 2),
        (3 * w // 4, edge + 2),
        (edge + 2, h // 4),
        (w - edge - 3, h // 4),
    ]

    def _is_wrong_page_fill(r: int, g: int, b: int) -> bool:
        lum = (r + g + b) / 3
        sat = max(r, g, b) - min(r, g, b)
        if _colour_dist((r, g, b), brand_bg) < 48:
            return False
        # Near-black plate
        if lum < 48 and abs(r - g) < 22 and abs(g - b) < 22:
            return True
        # Navy / primary used as the page itself (only ever reached from the edge)
        if b > r + 22 and b > g + 10 and 28 < lum < 130 and sat < 150:
            return True
        # Harsh pure white / cream page when Brand BG is ice (not logo ink)
        if lum > 242 and sat < 18 and _colour_dist((r, g, b), brand_bg) > 35:
            return True
        # Nested pale page panel (second background) — cool light plate != Brand BG.
        if lum > 200 and sat < 72 and b >= g - 8 and _colour_dist((r, g, b), brand_bg) > 28:
            return True
        return False

    def _is_pale_plate(r: int, g: int, b: int) -> bool:
        """Interior seeds may only ever start on a washed-out light plate."""
        lum = (r + g + b) / 3
        sat = max(r, g, b) - min(r, g, b)
        if _colour_dist((r, g, b), brand_bg) < 28:
            return False
        return lum > 200 and sat < 72 and b >= g - 8

    # Interior pale panel: Brand BG rim + washed centre (the "two backgrounds" bug).
    interior_seeds = [
        (w // 2, h // 3),
        (w // 3, h // 3),
        (2 * w // 3, h // 3),
        (w // 2, h // 4),
        (w // 4, h // 2),
        (3 * w // 4, h // 2),
    ]

    wrong_edges = sum(1 for x, y in edge_seeds if _is_wrong_page_fill(*px[x, y][:3]))
    pale_interior = sum(1 for x, y in interior_seeds if _is_pale_plate(*px[x, y][:3]))
    if wrong_edges == 0 and pale_interior < 2:
        return rgba

    visited = [[False] * w for _ in range(h)]
    # A glyph stroke or icon is orders of magnitude smaller than a page region.
    min_area = max(600, int(w * h * 0.015))
    changed = 0
    kept = 0

    def _fill_region(seed: tuple[int, int], predicate) -> int:
        sx, sy = seed
        if not (0 <= sx < w and 0 <= sy < h) or visited[sy][sx]:
            return 0
        sr, sg, sb, _sa = px[sx, sy]
        if not predicate(sr, sg, sb):
            visited[sy][sx] = True
            return 0
        region: list[tuple[int, int]] = []
        stack = [(sx, sy)]
        visited[sy][sx] = True
        while stack:
            x, y = stack.pop()
            region.append((x, y))
            r, g, b, _a = px[x, y]
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx]:
                    nr, ng, nb, _na = px[nx, ny]
                    if predicate(nr, ng, nb) and _colour_dist((r, g, b), (nr, ng, nb)) < 55:
                        visited[ny][nx] = True
                        stack.append((nx, ny))
        if len(region) < min_area:
            return 0
        for x, y in region:
            px[x, y] = (br, bg_, bb_, 255)
        return len(region)

    for seed in edge_seeds:
        filled = _fill_region(seed, _is_wrong_page_fill)
        changed += filled
        kept += 1 if filled else 0
    if pale_interior >= 2:
        for seed in interior_seeds:
            filled = _fill_region(seed, _is_pale_plate)
            changed += filled
            kept += 1 if filled else 0

    logger.info(
        "dalle.canvas_bg_enforced",
        wrong_edges=wrong_edges,
        pale_interior=pale_interior,
        regions=kept,
        rekeyed=changed,
        bg=bg_hex,
        size=f"{w}x{h}",
    )
    return rgba


def _wipe_platform_chrome(
    base_img: Image.Image,
    canvas_width: int,
    canvas_height: int,
    *,
    fill_hex: str,
) -> Image.Image:
    """Remove AI-hallucinated LinkedIn / social platform marks from the top band."""
    from PIL import ImageDraw

    fill = _rgba(fill_hex or _DEFAULT_CANVAS_BG)
    # Top-center strip where LinkedIn "in" badges commonly appear.
    top_h = max(26, int(canvas_height * 0.07))
    left = int(canvas_width * 0.22)
    right = int(canvas_width * 0.78)
    ImageDraw.Draw(base_img).rectangle((left, 0, right, top_h), fill=fill)
    # Thin full-width hairline only (platform chrome at the very edge).
    ImageDraw.Draw(base_img).rectangle(
        (0, 0, canvas_width, max(8, int(canvas_height * 0.015))),
        fill=fill,
    )
    return base_img


def _scrub_top_right_white_plates(
    base_img: Image.Image,
    canvas_width: int,
    canvas_height: int,
    *,
    fill_hex: str,
) -> Image.Image:
    """Remove AI-baked white logo plates in the top-right before compositing."""
    br, bg_, bb_, _ = _rgba(fill_hex or _DEFAULT_CANVAS_BG)
    px = base_img.load()
    x0 = int(canvas_width * 0.68)
    y1 = int(canvas_height * 0.18)
    for y in range(0, y1):
        for x in range(x0, canvas_width):
            r, g, b, a = px[x, y]
            lum = (r + g + b) / 3
            # White / near-white / cream plates only — keep navy/orange ink.
            if lum > 225 and abs(r - g) < 28 and abs(g - b) < 28:
                px[x, y] = (br, bg_, bb_, 255)
            elif r > 235 and g > 235 and b > 230:
                px[x, y] = (br, bg_, bb_, 255)
    return base_img


def _scrub_logo_pocket_plates(
    base_img: Image.Image,
    *,
    logo_x: int,
    logo_y: int,
    logo_w: int,
    logo_h: int,
    canvas_width: int,
    canvas_height: int,
    fill_hex: str,
    logo_mask: Image.Image | None = None,
) -> Image.Image:
    """After paste, kill leftover white/cream plates in the logo pocket (not logo ink)."""
    br, bg_, bb_, _ = _rgba(fill_hex or _DEFAULT_CANVAS_BG)
    px = base_img.load()
    pad = 12
    x0 = max(0, logo_x - pad)
    y0 = max(0, logo_y - pad)
    x1 = min(canvas_width, logo_x + logo_w + pad)
    y1 = min(canvas_height, logo_y + logo_h + pad)
    mask_px = logo_mask.load() if logo_mask is not None else None
    for y in range(y0, y1):
        for x in range(x0, x1):
            if mask_px is not None:
                mx = x - logo_x
                my = y - logo_y
                if 0 <= mx < logo_w and 0 <= my < logo_h and mask_px[mx, my][3] > 40:
                    continue  # keep logo ink
            r, g, b, a = px[x, y]
            if _is_logo_pad_rgb(r, g, b, jpeg_mode=True):
                px[x, y] = (br, bg_, bb_, 255)
            elif (r + g + b) / 3 > 220 and abs(r - g) < 24 and abs(g - b) < 24:
                px[x, y] = (br, bg_, bb_, 255)
    return base_img


def _is_logo_pad_rgb(r: int, g: int, b: int, *, jpeg_mode: bool = False) -> bool:
    """True for colours that are logo padding, never brand ink.

    JPG logos compress white pads into dirty off-whites — use a looser threshold
    so the white rectangle does not survive on ice-blue slides.
    """
    lum = (r + g + b) / 3
    white_cut = 215 if jpeg_mode else 230
    soft_cut = 200 if jpeg_mode else 218
    # Pure / near-white and cream pads (the white box behind JPG logos with white pads).
    if r > white_cut and g > white_cut and b > white_cut:
        return True
    if r > soft_cut and g > soft_cut and b > soft_cut - 8 and lum > soft_cut:
        return True
    if r > 210 and g > 210 and b > 200 and lum > 212:
        return True
    # Soft ice / sky pads used as logo canvases.
    if b > 205 and g > 195 and r > 185 and b >= g >= r - 15 and lum > 200:
        return True
    if b > 215 and 110 < r < 195 and 165 < g < 235 and b > g > r:
        return True
    # Flat gray / black plates.
    if abs(r - g) < 16 and abs(g - b) < 16 and (lum < 40 or 95 < lum < 190):
        return True
    return False


def _make_background_transparent(img: Image.Image) -> Image.Image:
    """Key out solid logo padding and tight-crop to the real mark.

    Brand Space logos often ship as JPG/PNG with an opaque white rectangle. That
    rectangle was surviving composite and showing as a white box on every slide.
    Prefer PNG uploads; for JPG, use wider pad keying for JPEG compression noise.
    """
    # Detect whether the source had a real alpha channel before convert.
    src_mode = (img.mode or "").upper()
    # Palette / JPEG logos ship with opaque white pads — use looser keying.
    jpeg_mode = src_mode in ("RGB", "L", "CMYK", "P") and "A" not in src_mode
    img = img.convert("RGBA")
    w, h = img.size
    if w <= 2 or h <= 2:
        return img

    px = img.load()
    near_tol = 42 if jpeg_mode else 28

    def _near(c1: tuple[int, int, int], c2: tuple[int, int, int], tol: int) -> bool:
        return (
            abs(c1[0] - c2[0]) <= tol
            and abs(c1[1] - c2[1]) <= tol
            and abs(c1[2] - c2[2]) <= tol
        )

    def _is_brand_ink(r: int, g: int, b: int) -> bool:
        return (
            (r > 170 and g < 165 and b < 90)  # orange
            or (b > 70 and r < 90 and g < 120)  # navy
            or (r < 95 and g < 95 and b < 95)  # dark wordmark
        )

    # Pass 1 — flood-fill from each corner through matching pad colour.
    visited = [[False] * w for _ in range(h)]
    stack: list[tuple[int, int]] = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    # Also seed mid-edge + inset corners — JPG pads are often inset 1–2 px.
    stack.extend(
        [
            (w // 2, 0),
            (w // 2, h - 1),
            (0, h // 2),
            (w - 1, h // 2),
            (2, 2),
            (w - 3, 2),
            (2, h - 3),
            (w - 3, h - 3),
        ]
    )
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
            continue
        r, g, b, a = px[x, y]
        if a == 0 or not _is_logo_pad_rgb(r, g, b, jpeg_mode=jpeg_mode):
            visited[y][x] = True
            continue
        visited[y][x] = True
        px[x, y] = (r, g, b, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx]:
                nr, ng, nb, na = px[nx, ny]
                if (
                    na
                    and _near((r, g, b), (nr, ng, nb), near_tol)
                    and _is_logo_pad_rgb(nr, ng, nb, jpeg_mode=jpeg_mode)
                ):
                    stack.append((nx, ny))

    # Pass 2 — any leftover near-white / cream / ice plate that is not brand ink.
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if _is_logo_pad_rgb(r, g, b, jpeg_mode=jpeg_mode) and not _is_brand_ink(r, g, b):
                px[x, y] = (r, g, b, 0)
            # Extra soft plate kill — pale gray/ice frames behind lockups.
            elif (
                not _is_brand_ink(r, g, b)
                and (r + g + b) / 3 > 210
                and abs(r - g) < 22
                and abs(g - b) < 22
            ):
                px[x, y] = (r, g, b, 0)

    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    return img


def _is_logo_wordmark_ink(r: int, g: int, b: int, a: int) -> bool:
    """Dark / navy pixels that form brand-name text in lockup logos (e.g. JIRAAF)."""
    if a < 24:
        return False
    # Vivid orange / brand glyph — never treat as wordmark.
    if r > 160 and g < 170 and b < 110 and (r - b) > 50:
        return False
    mx = max(r, g, b)
    mn = min(r, g, b)
    lum = (r + g + b) / 3
    # Navy wordmark: blue-dominant mid/dark ink (Jiraaf #0D3A85-ish).
    if b >= r + 15 and b >= g and lum < 120 and b < 190:
        return True
    # Charcoal / near-black text.
    if mx < 95 and (mx - mn) < 45:
        return True
    # Low-sat dark slate text.
    if lum < 100 and (mx - mn) < 55:
        return True
    return False


def _is_logo_icon_ink(r: int, g: int, b: int, a: int) -> bool:
    """Saturated brand-mark pixels (icon/glyph), not the wordmark text."""
    if a < 24:
        return False
    if _is_logo_wordmark_ink(r, g, b, a):
        return False
    # Orange / vivid brand marks (Jiraaf giraffe glyph).
    if r > 160 and g < 175 and b < 120 and (r - b) > 45:
        return True
    mx = max(r, g, b)
    mn = min(r, g, b)
    sat = mx - mn
    return sat >= 45 and mx >= 110


def _extract_logo_icon_only(logo_img: Image.Image) -> Image.Image:
    """Prefer the icon/glyph — strip Brand Space wordmark text (e.g. 'JIRAAF').

    Many Brand Space uploads are square lockups: orange icon + navy brand name.
    Compositing the full lockup puts readable brand text on every slide.
    """
    img = logo_img.convert("RGBA")
    w, h = img.size
    if w < 16 or h < 16:
        return img

    px = img.load()
    icon_cols = [0] * w
    icon_count = 0
    word_count = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if _is_logo_wordmark_ink(r, g, b, a):
                word_count += 1
            elif _is_logo_icon_ink(r, g, b, a):
                icon_cols[x] += 1
                icon_count += 1

    # Nothing to strip — keep as-is (already icon-only or monochrome mark).
    if icon_count < 40 or word_count < max(40, int(icon_count * 0.15)):
        return img

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if _is_logo_wordmark_ink(r, g, b, a):
                px[x, y] = (r, g, b, 0)

    bbox = img.getbbox()
    if not bbox:
        return logo_img.convert("RGBA")

    min_icon = max(2, h // 40)
    right = bbox[2]
    for x in range(w - 1, -1, -1):
        if icon_cols[x] >= min_icon:
            right = x + 1
            break
    left = bbox[0]
    for x in range(w):
        if icon_cols[x] >= min_icon:
            left = x
            break
    top, bottom = bbox[1], bbox[3]
    crop_w = max(1, right - left)
    crop_h = max(1, bottom - top)
    if crop_w > int(crop_h * 1.35):
        right = min(w, left + int(crop_h * 1.15))
    cropped = img.crop((left, top, max(left + 1, right), bottom))
    return cropped if cropped.getbbox() else logo_img.convert("RGBA")


def _sample_corner_fill(base_img: Image.Image, canvas_width: int, canvas_height: int) -> tuple[int, int, int, int]:
    """Pick a fill color from just outside the small logo wipe zone (matches background)."""
    px = base_img.load()
    # Sample left of the compact logo corner so we don't pull headline colors.
    xs = [
        max(0, int(canvas_width * 0.88)),
        max(0, int(canvas_width * 0.90)),
        max(0, int(canvas_width * 0.92)),
    ]
    y = min(16, canvas_height - 1)
    samples = [px[x, y][:3] for x in xs]
    r = int(sum(s[0] for s in samples) / len(samples))
    g = int(sum(s[1] for s in samples) / len(samples))
    b = int(sum(s[2] for s in samples) / len(samples))
    return (r, g, b, 255)


def _wipe_top_right_corner(
    base_img: Image.Image,
    canvas_width: int,
    canvas_height: int,
    *,
    width_ratio: float = 0.22,
    height_ratio: float = 0.12,
    fill_hex: str | None = None,
) -> Image.Image:
    """Remove AI-hallucinated logos / 'Brand Logo' placeholders before compositing.

    Pocket sized to fit the Brand Space logo composite without eating the headline.
    Prefer Brand Space background fill so the wipe never leaves a white patch.
    """
    from PIL import ImageDraw

    wipe_w = min(int(canvas_width * width_ratio), canvas_width)
    wipe_h = min(int(canvas_height * height_ratio), canvas_height)
    wipe_box = (canvas_width - wipe_w, 0, canvas_width, wipe_h)
    if fill_hex:
        fill = _rgba(fill_hex)
    else:
        fill = _sample_corner_fill(base_img, canvas_width, canvas_height)
    ImageDraw.Draw(base_img).rectangle(wipe_box, fill=fill)
    return base_img


def _composite_logo(
    base_bytes: bytes,
    logo_bytes: bytes,
    logo_zone_instruction: str | None,
    canvas_width: int,
    canvas_height: int,
    *,
    canvas_bg_hex: str = _DEFAULT_CANVAS_BG,
) -> bytes:
    """Wipe top-right pocket with Brand BG, then paste the Brand Space logo AS-IS.

    - Keep the full uploaded logo (icon + wordmark if present in the asset).
    - Key out opaque white/cream logo plates so no white box shows on ice-blue slides.
    - Never invent extra brand-name watermarks — only the Brand Space logo asset.
    """
    base_img = Image.open(BytesIO(base_bytes)).convert("RGBA")
    logo_raw = Image.open(BytesIO(logo_bytes))
    # Remove solid white/cream plate — keep logo ink (icon AND wordmark) intact.
    logo_img = _make_background_transparent(logo_raw).convert("RGBA")
    # Tight crop to real ink only (no empty pad).
    content_box = logo_img.getbbox()
    if content_box:
        logo_img = logo_img.crop(content_box)

    # Compact size — less space, headlines stay clear of the pocket.
    max_logo_w = max(int(canvas_width * _LOGO_MAX_WIDTH_RATIO), _LOGO_MIN_PX)
    max_logo_h = max(int(canvas_height * 0.055), _LOGO_MIN_PX)
    logo_w, logo_h = logo_img.size
    scale = min(max_logo_w / max(logo_w, 1), max_logo_h / max(logo_h, 1), 1.0)
    new_w = max(int(logo_w * scale), 1)
    new_h = max(int(logo_h * scale), 1)
    if new_h > max_logo_h:
        shrink = max_logo_h / new_h
        new_w = max(int(new_w * shrink), 1)
        new_h = max_logo_h
    logo_img = logo_img.resize((new_w, new_h), Image.LANCZOS)
    logo_w, logo_h = logo_img.size

    pad = _LOGO_EDGE_PADDING
    x = canvas_width - logo_w - pad
    y = pad

    bg_hex = canvas_bg_hex or _DEFAULT_CANVAS_BG
    # Kill LinkedIn / platform chrome before logo paste.
    base_img = _wipe_platform_chrome(base_img, canvas_width, canvas_height, fill_hex=bg_hex)
    # Kill AI-baked white logo rectangles in the top-right pocket.
    base_img = _scrub_top_right_white_plates(
        base_img, canvas_width, canvas_height, fill_hex=bg_hex
    )
    # Wipe AI-drawn fake logos / white plates with Brand Space background (never white).
    wipe_w = max(0.22, min(0.36, (logo_w + 5 * pad) / max(canvas_width, 1)))
    wipe_h = max(0.11, min(0.18, (logo_h + 5 * pad) / max(canvas_height, 1)))
    base_img = _wipe_top_right_corner(
        base_img,
        canvas_width,
        canvas_height,
        width_ratio=wipe_w,
        height_ratio=wipe_h,
        fill_hex=bg_hex,
    )
    # Clear any leftover white plate in pocket, then paste transparent logo.
    base_img = _scrub_logo_pocket_plates(
        base_img,
        logo_x=x,
        logo_y=y,
        logo_w=logo_w,
        logo_h=logo_h,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        fill_hex=bg_hex,
        logo_mask=None,
    )
    base_img.paste(logo_img, (x, y), logo_img)
    base_img = _scrub_logo_pocket_plates(
        base_img,
        logo_x=x,
        logo_y=y,
        logo_w=logo_w,
        logo_h=logo_h,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        fill_hex=bg_hex,
        logo_mask=logo_img,
    )

    out = BytesIO()
    fixed = _ensure_light_brand_background(base_img, bg_hex)
    fixed = _flatten_near_brand_canvas(fixed, bg_hex)
    _flatten_rgba_to_brand_bg(fixed, bg_hex).convert("RGB").save(
        out, format="PNG", optimize=False
    )
    return out.getvalue()


def _load_footer_font(size: int):
    """Prefer a clean sans on Windows/macOS; fall back to PIL default."""
    from PIL import ImageFont

    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_footer_lines(text: str, font, max_width: int, draw) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _composite_legal_footer(
    base_bytes: bytes,
    canvas_width: int,
    canvas_height: int,
    footer_text: str | None = None,
    *,
    carousel_sample_chrome: bool = False,
    legal_color_hex: str = "",
    canvas_bg_hex: str = _DEFAULT_CANVAS_BG,
) -> bytes:
    """Paint Brand Space legal footer as text only — same background as the slide.

    Never paint a separate footer rectangle — that reads as a second background
    band. Legal copy sits on the existing pixels.
    """
    from PIL import ImageDraw

    text = (footer_text or "").strip()
    if not text:
        return base_bytes

    base_img = Image.open(BytesIO(base_bytes)).convert("RGBA")
    draw = ImageDraw.Draw(base_img)

    # Legacy navy chrome is disabled for product carousels. Keeping the branch
    # unreachable unless explicitly requested, so we never reintroduce a band.
    if carousel_sample_chrome:
        logger.warning("dalle.legal_navy_chrome_ignored", reason="uniform_slide_bg_required")

    font_size = max(11, min(14, int(canvas_width * 0.012)))
    font = _load_footer_font(font_size)
    side_pad = max(16, int(canvas_width * 0.035))
    max_text_w = canvas_width - side_pad * 2
    lines = _wrap_footer_lines(text, font, max_text_w, draw)
    line_gap = max(2, int(font_size * 0.28))
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(max(bbox[3] - bbox[1], font_size))
    text_block_h = sum(line_heights) + line_gap * max(len(lines) - 1, 0)
    band_pad_y = max(8, int(canvas_height * 0.008))
    max_band = int(canvas_height * 0.12)
    if text_block_h + band_pad_y * 2 > max_band:
        font_size = max(10, font_size - 2)
        font = _load_footer_font(font_size)
        lines = _wrap_footer_lines(text, font, max_text_w, draw)
        line_heights = [
            max(
                draw.textbbox((0, 0), l, font=font)[3]
                - draw.textbbox((0, 0), l, font=font)[1],
                font_size,
            )
            for l in lines
        ]
        text_block_h = sum(line_heights) + line_gap * max(len(lines) - 1, 0)

    # NO filled rectangle — text floats on the slide's own background.
    y = canvas_height - band_pad_y - text_block_h
    y = max(int(canvas_height * 0.88), y)
    # Legal footer is LEFT-aligned small muted text from Brand Space.
    footer_fill = _rgba(legal_color_hex) if legal_color_hex else _LEGAL_FOOTER_COLOR
    for i, line in enumerate(lines):
        draw.text((side_pad, y), line, font=font, fill=footer_fill)
        y += line_heights[i] + line_gap

    out = BytesIO()
    # Flatten only — do not recolour the footer zone to a different fill.
    _flatten_rgba_to_brand_bg(base_img, canvas_bg_hex).convert("RGB").save(
        out, format="PNG", optimize=False
    )
    return out.getvalue()


def _edge_pad_color(img: Image.Image) -> tuple[int, int, int]:
    """Sample near-edge pixels so letterbox pads blend into the artwork."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    samples: list[tuple[int, int, int]] = []
    px = rgb.load()
    for y in (max(0, h // 20), h // 2, min(h - 1, (19 * h) // 20)):
        for x in (0, 1, max(0, w - 2), max(0, w - 1)):
            samples.append(px[x, y])
    if not samples:
        return (211, 234, 252)  # data-story sky mid
    r = sum(c[0] for c in samples) // len(samples)
    g = sum(c[1] for c in samples) // len(samples)
    b = sum(c[2] for c in samples) // len(samples)
    return (r, g, b)


def _letterbox_to_size(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Fit the full image inside the target canvas; pad with edge-matched colour.

    Never crops. Used for 2:3 API canvases exporting to 4:5 so headline/footer
    text cannot be sliced off the way centre-crop did.
    """
    src_w, src_h = img.size
    scale = min(target_w / src_w, target_h / src_h)
    new_w = max(1, int(round(src_w * scale)))
    new_h = max(1, int(round(src_h * scale)))
    fitted = img.resize((new_w, new_h), Image.LANCZOS)
    pad = _edge_pad_color(fitted)
    canvas = Image.new("RGB", (target_w, target_h), pad)
    if fitted.mode == "RGBA":
        canvas.paste(fitted, ((target_w - new_w) // 2, (target_h - new_h) // 2), fitted)
    else:
        canvas.paste(fitted, ((target_w - new_w) // 2, (target_h - new_h) // 2))
    logger.info(
        "dalle.letterboxed_to_aspect",
        source=f"{src_w}x{src_h}",
        fitted=f"{new_w}x{new_h}",
        target=f"{target_w}x{target_h}",
        pad_rgb=pad,
    )
    return canvas


def _resize_to_export(
    image_bytes: bytes,
    target_w: int,
    target_h: int,
    *,
    allow_crop: bool = False,
    letterbox: bool = False,
    canvas_bg_hex: str = _DEFAULT_CANVAS_BG,
) -> bytes:
    """Fit the API canvas to the exact export size.

    Default is a stretch (keeps one seamless field). For portrait posters,
    pass letterbox=True so 2:3 -> 4:5 never chops the headline or takeaway —
    centre-crop was cutting ~8% off the top and bottom and amputating text.
    allow_crop is retained for callers but is no longer used for portrait posters.
    """
    img = _ensure_light_brand_background(
        Image.open(BytesIO(image_bytes)), canvas_bg_hex or _DEFAULT_CANVAS_BG
    )
    src_w, src_h = img.size
    if src_w <= 0 or src_h <= 0 or target_w <= 0 or target_h <= 0:
        return image_bytes
    if (src_w, src_h) == (target_w, target_h):
        out = BytesIO()
        _flatten_rgba_to_brand_bg(img, canvas_bg_hex).convert("RGB").save(
            out, format="PNG", optimize=False
        )
        return out.getvalue()

    if letterbox:
        # Pad with Brand BG so side/top bars match the brand canvas, not a sampled tint.
        src_w, src_h = img.size
        scale = min(target_w / src_w, target_h / src_h)
        new_w = max(1, int(round(src_w * scale)))
        new_h = max(1, int(round(src_h * scale)))
        fitted = img.resize((new_w, new_h), Image.LANCZOS)
        pad = _rgba(canvas_bg_hex or _DEFAULT_CANVAS_BG)[:3]
        canvas = Image.new("RGB", (target_w, target_h), pad)
        if fitted.mode == "RGBA":
            canvas.paste(fitted, ((target_w - new_w) // 2, (target_h - new_h) // 2), fitted)
        else:
            canvas.paste(fitted, ((target_w - new_w) // 2, (target_h - new_h) // 2))
        logger.info(
            "dalle.letterboxed_to_aspect",
            source=f"{src_w}x{src_h}",
            fitted=f"{new_w}x{new_h}",
            target=f"{target_w}x{target_h}",
            pad_rgb=pad,
        )
        out = BytesIO()
        canvas.save(out, format="PNG", optimize=False)
        return out.getvalue()

    if allow_crop:
        src_aspect = src_w / src_h
        target_aspect = target_w / target_h
        if abs(src_aspect - target_aspect) / target_aspect > 0.02:
            if src_aspect > target_aspect:
                crop_w = max(1, int(round(src_h * target_aspect)))
                left = (src_w - crop_w) // 2
                img = img.crop((left, 0, left + crop_w, src_h))
            else:
                crop_h = max(1, int(round(src_w / target_aspect)))
                top = (src_h - crop_h) // 2
                img = img.crop((0, top, src_w, top + crop_h))
            logger.info(
                "dalle.cropped_to_aspect",
                source=f"{src_w}x{src_h}",
                cropped=f"{img.size[0]}x{img.size[1]}",
                target=f"{target_w}x{target_h}",
            )

    img = img.resize((target_w, target_h), Image.LANCZOS)
    out = BytesIO()
    _flatten_rgba_to_brand_bg(img, canvas_bg_hex).convert("RGB").save(
        out, format="PNG", optimize=False
    )
    return out.getvalue()


def _composite_close_mascot(
    base_bytes: bytes,
    canvas_width: int,
    canvas_height: int,
    mascot_bytes: bytes,
    *,
    canvas_bg_hex: str = _DEFAULT_CANVAS_BG,
) -> bytes:
    """Paste a Brand Space mascot on the carousel last slide."""
    base_img = Image.open(BytesIO(base_bytes)).convert("RGBA")
    mascot_raw = Image.open(BytesIO(mascot_bytes))
    mascot = _make_background_transparent(mascot_raw).convert("RGBA")
    box = mascot.getbbox()
    if box:
        mascot = mascot.crop(box)

    max_h = max(int(canvas_height * 0.52), 180)
    max_w = max(int(canvas_width * 0.48), 160)
    mw, mh = mascot.size
    scale = min(max_w / max(mw, 1), max_h / max(mh, 1), 1.0)
    new_w = max(int(mw * scale), 1)
    new_h = max(int(mh * scale), 1)
    mascot = mascot.resize((new_w, new_h), Image.LANCZOS)

    margin_x = max(int(canvas_width * 0.04), 16)
    footer_top = int(canvas_height * 0.87)
    x = canvas_width - new_w - margin_x
    y = footer_top - new_h - max(int(canvas_height * 0.02), 8)
    y = max(int(canvas_height * 0.28), y)

    base_img.paste(mascot, (x, y), mascot)
    out = BytesIO()
    _flatten_rgba_to_brand_bg(base_img, canvas_bg_hex).convert("RGB").save(out, format="PNG", optimize=False)
    logger.info(
        "dalle.close_mascot_composited",
        size=f"{new_w}x{new_h}",
        pos=f"{x},{y}",
        canvas=f"{canvas_width}x{canvas_height}",
    )
    return out.getvalue()


def _load_cta_font(size: int):
    from PIL import ImageFont

    for path in (
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ):
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _composite_infographic_cta(
    base_bytes: bytes,
    *,
    cta_text: str,
    accent_hex: str,
    canvas_bg_hex: str = _DEFAULT_CANVAS_BG,
) -> bytes:
    """Wipe bottom band and paint a fully-visible CTA pill with letter-perfect text.

    Image models routinely crop the baked CTA and invent typos. Compositing after
    generation keeps spelling and safe margins deterministic.

    Also removes AI-baked ghost CTAs (partial orange strips) that survive a shallow wipe.
    """
    from PIL import ImageDraw, ImageFont

    label = re.sub(r"\s+", " ", (cta_text or "EXPLORE MORE").strip()).upper()
    if not label:
        label = "EXPLORE MORE"
    # Keep the pill compact so it never wraps.
    label = " ".join(label.split()[:3])

    base_img = Image.open(BytesIO(base_bytes)).convert("RGBA")
    # Flatten nested ice plates first so the footer wipe does not leave a second BG.
    base_img = _flatten_near_brand_canvas(base_img, canvas_bg_hex)
    w, h = base_img.size
    # Footer reserve for the composited pill — keep shallow so cards stay intact.
    band_h = max(int(h * 0.13), 84)
    wipe_top = max(0, h - band_h)
    bg = _rgba(canvas_bg_hex)
    accent = _rgba(accent_hex or "#FF9E02")
    ar, ag, ab = accent[:3]

    draw = ImageDraw.Draw(base_img)
    # Full-width Brand BG wipe of the footer zone only.
    draw.rectangle((0, wipe_top, w, h), fill=bg)

    # Center-only scrub for AI-baked ghost CTA strips sitting ABOVE the footer
    # (thin orange bars / partial pills) — do not wipe the side cards.
    px = base_img.load()
    ghost_top = max(0, wipe_top - max(28, int(h * 0.06)))
    cx0, cx1 = int(w * 0.28), int(w * 0.72)
    for y in range(ghost_top, wipe_top):
        for x in range(cx0, cx1):
            r, g, b, a = px[x, y]
            if r > 180 and g < 190 and b < 120 and r > b + 40:
                px[x, y] = bg
            elif r > 245 and g > 245 and b > 245:
                # white CTA glyph fragments sitting on an orange remnant
                left = px[max(cx0, x - 2), y][:3]
                right = px[min(cx1 - 1, x + 2), y][:3]
                if (left[0] > 180 and left[2] < 120) or (right[0] > 180 and right[2] < 120):
                    px[x, y] = bg

    # Compact pill that always fits with clear air under it.
    font_size = max(18, min(26, int(h * 0.034)))
    font = _load_cta_font(font_size)
    text_bbox = draw.textbbox((0, 0), label, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    pad_x = max(22, int(w * 0.028))
    pad_y = max(9, int(h * 0.012))
    max_pill_w = int(w * (0.32 if h < 800 else 0.40))
    pill_w = min(max_pill_w, text_w + pad_x * 2)
    pill_h = text_h + pad_y * 2
    # Hard floor: keep >= 5% of canvas (min 18px) empty under the pill.
    bottom_gap = max(int(h * 0.05), 18)
    pill_x = (w - pill_w) // 2
    pill_y = h - pill_h - bottom_gap
    if pill_y < wipe_top + 6:
        font_size = max(16, font_size - 3)
        font = _load_cta_font(font_size)
        text_bbox = draw.textbbox((0, 0), label, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        pill_w = min(max_pill_w, text_w + pad_x * 2)
        pill_h = text_h + pad_y * 2
        pill_x = (w - pill_w) // 2
        pill_y = h - pill_h - bottom_gap
    pill_y = max(wipe_top + 4, pill_y)
    if pill_y + pill_h > h - 10:
        pill_y = h - pill_h - 10

    radius = pill_h // 2
    draw.rounded_rectangle(
        (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h),
        radius=radius,
        fill=(ar, ag, ab, 255),
    )
    tx = pill_x + (pill_w - text_w) // 2
    ty = pill_y + (pill_h - text_h) // 2 - max(1, text_bbox[1] // 4)
    draw.text((tx, ty), label, fill=(255, 255, 255, 255), font=font)

    out = BytesIO()
    _flatten_rgba_to_brand_bg(base_img, canvas_bg_hex).convert("RGB").save(
        out, format="PNG", optimize=False
    )
    logger.info(
        "dalle.cta_composited",
        cta=label,
        accent=accent_hex,
        band_h=band_h,
        pill=(pill_x, pill_y, pill_w, pill_h),
        bottom_gap=h - (pill_y + pill_h),
        canvas=f"{w}x{h}",
    )
    return out.getvalue()


def apply_brand_image_overlays(
    image_bytes: bytes,
    *,
    storage,
    logo_storage_path: str | None = None,
    logo_zone_instruction: str | None = None,
    composite_legal_footer: bool = False,
    wipe_reserved_corner: bool = False,
    composite_close_mascot: bool = False,
    legal_footer_text: str = "",
    close_mascot_storage_path: str = "",
    canvas_bg_hex: str = _DEFAULT_CANVAS_BG,
    composite_cta_text: str = "",
    cta_accent_hex: str = "",
    legal_color_hex: str = "",
    composite_sebi_footer: bool | None = None,
    composite_jiraaf_close_mascot: bool | None = None,
) -> bytes:
    """Apply brand overlays.

    Accept both the current neutral flags and legacy Jiraaf-specific flag names so
    mixed deploys do not crash during the DALL·E -> SDXL fallback path.
    """
    if composite_sebi_footer is not None:
        composite_legal_footer = composite_legal_footer or composite_sebi_footer
    if composite_jiraaf_close_mascot is not None:
        composite_close_mascot = composite_close_mascot or composite_jiraaf_close_mascot
    bg_hex = canvas_bg_hex or _DEFAULT_CANVAS_BG
    # Always strip platform chrome + enforce Brand Space canvas before/without logo.
    try:
        base_img = Image.open(BytesIO(image_bytes)).convert("RGBA")
        real_w, real_h = base_img.size
        wiped = _wipe_platform_chrome(base_img, real_w, real_h, fill_hex=bg_hex)
        if wipe_reserved_corner and not logo_storage_path:
            wiped = _wipe_top_right_corner(
                wiped,
                real_w,
                real_h,
                width_ratio=0.26,
                height_ratio=0.13,
                fill_hex=bg_hex,
            )
        wiped = _ensure_light_brand_background(wiped, bg_hex)
        wiped = _flatten_near_brand_canvas(wiped, bg_hex)
        out = BytesIO()
        _flatten_rgba_to_brand_bg(wiped, bg_hex).convert("RGB").save(out, format="PNG", optimize=False)
        image_bytes = out.getvalue()
        logger.info("dalle.canvas_prepped", canvas=f"{real_w}x{real_h}", bg=bg_hex)
    except Exception as wipe_exc:
        logger.warning("dalle.canvas_prep_failed", error=str(wipe_exc)[:200])

    if logo_storage_path:
        try:
            logo_bytes = storage.read_bytes(logo_storage_path)
            if logo_bytes:
                base_img = Image.open(BytesIO(image_bytes))
                real_w, real_h = base_img.size
                image_bytes = _composite_logo(
                    base_bytes=image_bytes,
                    logo_bytes=logo_bytes,
                    logo_zone_instruction=logo_zone_instruction,
                    canvas_width=real_w,
                    canvas_height=real_h,
                    canvas_bg_hex=canvas_bg_hex or _DEFAULT_CANVAS_BG,
                )
                logger.info(
                    "dalle.logo_composited",
                    logo_path=logo_storage_path,
                    zone="top-right",
                    canvas=f"{real_w}x{real_h}",
                )
            else:
                logger.warning("dalle.logo_empty_bytes", logo_path=logo_storage_path)
        except Exception as logo_exc:
            logger.warning(
                "dalle.logo_composite_failed",
                logo_path=logo_storage_path,
                error=str(logo_exc)[:300],
            )

    if composite_close_mascot and close_mascot_storage_path:
        try:
            mascot_bytes = storage.read_bytes(close_mascot_storage_path)
            if mascot_bytes:
                base_img = Image.open(BytesIO(image_bytes))
                real_w, real_h = base_img.size
                image_bytes = _composite_close_mascot(
                    image_bytes, real_w, real_h, mascot_bytes, canvas_bg_hex=canvas_bg_hex
                )
            else:
                logger.warning("dalle.close_mascot_empty", path=close_mascot_storage_path)
        except Exception as mascot_exc:
            logger.warning("dalle.close_mascot_failed", error=str(mascot_exc)[:300])

    if composite_legal_footer and (legal_footer_text or "").strip():
        try:
            base_img = Image.open(BytesIO(image_bytes))
            real_w, real_h = base_img.size
            image_bytes = _composite_legal_footer(
                base_bytes=image_bytes,
                canvas_width=real_w,
                canvas_height=real_h,
                footer_text=legal_footer_text,
                legal_color_hex=legal_color_hex,
                canvas_bg_hex=bg_hex,
            )
            logger.info("dalle.legal_footer_composited", canvas=f"{real_w}x{real_h}")
        except Exception as footer_exc:
            logger.warning("dalle.legal_footer_failed", error=str(footer_exc)[:300])

    if (composite_cta_text or "").strip():
        # Never fall back to a literal accent: painting one brand's orange onto
        # another brand's canvas is exactly the palette leak we must avoid.
        if not (cta_accent_hex or "").strip():
            logger.warning("dalle.cta_skipped_no_brand_accent")
        else:
            try:
                image_bytes = _composite_infographic_cta(
                    image_bytes,
                    cta_text=composite_cta_text,
                    accent_hex=cta_accent_hex,
                    canvas_bg_hex=bg_hex,
                )
            except Exception as cta_exc:
                logger.warning("dalle.cta_composite_failed", error=str(cta_exc)[:300])

    return image_bytes


class DalleService:
    """Async OpenAI Image Generation service (gpt-image-1 or dall-e-3) with brand logo overlay."""

    def __init__(self, api_key: str | None = None) -> None:
        self.settings = get_settings()
        self.api_key = api_key or self.settings.openai_api_key
        self.image_timeout_s = float(
            getattr(self.settings, "image_generation_timeout_seconds", 180) or 180
        )
        self.image_quality = str(
            getattr(self.settings, "image_quality", "medium") or "medium"
        ).strip().lower()
        self.client = (
            AsyncOpenAI(api_key=self.api_key, timeout=self.image_timeout_s)
            if self.api_key
            else None
        )
        self.storage = get_object_storage()
        self.model = getattr(self.settings, "image_model", "gpt-image-1") or "gpt-image-1"

    async def generate_and_save(
        self,
        tenant_id: str | UUID,
        brand_space_id: str | UUID,
        prompt: str,
        size: str = "1024x1024",
        logo_storage_path: str | None = None,
        logo_zone_instruction: str | None = None,
        composite_legal_footer: bool = False,
        wipe_reserved_corner: bool = False,
        quality: str | None = None,
        letterbox_to_aspect: bool = False,
        composite_close_mascot: bool = False,
        legal_footer_text: str = "",
        close_mascot_storage_path: str = "",
        canvas_bg_hex: str = _DEFAULT_CANVAS_BG,
        composite_cta_text: str = "",
        cta_accent_hex: str = "",
        legal_color_hex: str = "",
    ) -> str:
        """Call gpt-image-1, optionally composite the brand logo, save, and return URL path.

        Args:
            tenant_id: Tenant UUID.
            brand_space_id: Brand space UUID.
            prompt: The fully-expanded art direction prompt.
            size: Requested canvas size (e.g. "1200x627").
            logo_storage_path: Optional filesystem path to the brand logo asset.
                If provided, the logo will be composited onto the generated image.
            logo_zone_instruction: Free-text description of logo placement
                (e.g. "bottom-right corner, 40px margin").
            composite_legal_footer: When True, paint Brand Space legal footer via Pillow.
                Pass True for carousel slides only — static/infographic must stay False.
            composite_close_mascot: Carousel LAST slide only — paste Brand Space mascot.
        """
        if not self.client:
            logger.error("dalle.client_not_configured")
            raise ValueError("OpenAI API key not configured for DALL-E")

        # Target export size (product size). API only supports 3 aspect buckets — we resize after.
        export_w, export_h = map(int, size.split("x")) if size and "x" in size else (1024, 1024)
        is_gpt_image = "gpt-image" in self.model
        square_size = "1024x1024"
        landscape_size = "1536x1024" if is_gpt_image else "1792x1024"
        portrait_size = "1024x1536" if is_gpt_image else "1024x1792"

        dalle_size = square_size
        if export_w > export_h:
            dalle_size = landscape_size
        elif export_w < export_h:
            dalle_size = portrait_size

        logger.info(
            "dalle.generate_start",
            model=self.model,
            export_size=f"{export_w}x{export_h}",
            api_size=dalle_size,
            prompt_len=len(prompt),
            has_logo=bool(logo_storage_path),
            has_client=bool(self.client),
            timeout_s=self.image_timeout_s,
        )

        # ── Call gpt-image-1 ─────────────────────────────────────────────────────
        import asyncio

        # gpt-image-1 accepts 32k prompt chars; dall-e-3 hard-fails past 4k. The old
        # flat 6k clip silently amputated the tail of banded/dense prompts, which is
        # where the brand-colour and no-cutoff rules live.
        prompt_cap = 32000 if is_gpt_image else 4000
        try:
            kwargs: dict = {
                "model": self.model,
                "prompt": prompt[:prompt_cap],
                "size": dalle_size,
                "n": 1,
            }
            if is_gpt_image:
                default_q = self.image_quality if self.image_quality in ("low", "medium", "high") else "medium"
                q = (quality or default_q).strip().lower()
                if q not in ("low", "medium", "high"):
                    q = default_q
                kwargs["quality"] = q
            else:
                kwargs["quality"] = "hd" if self.image_quality == "high" else "standard"
            logger.info(
                "dalle.generate_params",
                model=self.model,
                size=dalle_size,
                quality=kwargs.get("quality"),
                timeout_s=self.image_timeout_s,
            )
            response = await asyncio.wait_for(
                self.client.images.generate(**kwargs),
                timeout=self.image_timeout_s,
            )
        except asyncio.TimeoutError as e:
            logger.error("dalle.generate_timeout", timeout_s=self.image_timeout_s, model=self.model)
            raise TimeoutError(
                f"Image generation timed out after {self.image_timeout_s:.0f}s "
                f"(model={self.model}). Try IMAGE_QUALITY=medium."
            ) from e
        except Exception as e:
            logger.error(
                "dalle.generate_failed",
                error_type=type(e).__name__,
                error_msg=str(e)[:500],
                prompt_snippet=prompt[:200],
            )
            raise

        data = response.data
        if not data:
            raise RuntimeError("DALL-E response did not contain image data")

        image_url = getattr(data[0], "url", None)
        b64_json = getattr(data[0], "b64_json", None)

        if b64_json:
            logger.info("dalle.decode_base64", b64_len=len(b64_json))
            image_bytes = base64.b64decode(b64_json)
        elif image_url:
            logger.info("dalle.download_start", url=image_url[:60])
            loop = asyncio.get_running_loop()

            def _download() -> bytes:
                with urlopen(image_url, timeout=60) as resp:
                    return resp.read()

            image_bytes = await loop.run_in_executor(None, _download)
        else:
            raise RuntimeError(
                f"Image response did not include url or b64_json (model={self.model})"
            )

        # Resize API canvas → exact export size (Instagram/LinkedIn/X).
        # Portrait explain uses letterbox=True (caller). Landscape LinkedIn static
        # STRETCHES — letterbox side-pads look like a second background. CTA is
        # Pillow-composited after resize so squash no longer clips the button.
        try:
            use_letterbox = bool(letterbox_to_aspect)
            image_bytes = _resize_to_export(
                image_bytes,
                export_w,
                export_h,
                letterbox=use_letterbox,
                canvas_bg_hex=canvas_bg_hex,
            )
            logger.info(
                "dalle.resized_to_export",
                export=f"{export_w}x{export_h}",
                letterboxed=use_letterbox,
            )
        except Exception as resize_exc:
            logger.warning("dalle.resize_failed", error=str(resize_exc)[:200])

        # Strip AI logos / composite brand logo / close mascot / legal footer
        image_bytes = apply_brand_image_overlays(
            image_bytes,
            storage=self.storage,
            logo_storage_path=logo_storage_path,
            logo_zone_instruction=logo_zone_instruction,
            composite_legal_footer=composite_legal_footer,
            wipe_reserved_corner=wipe_reserved_corner,
            composite_close_mascot=composite_close_mascot,
            legal_footer_text=legal_footer_text,
            close_mascot_storage_path=close_mascot_storage_path,
            canvas_bg_hex=canvas_bg_hex,
            composite_cta_text=composite_cta_text,
            cta_accent_hex=cta_accent_hex,
            legal_color_hex=legal_color_hex,
        )

        # ── Save final image to object storage ───────────────────────────────────
        filename = f"dalle-{uuid4().hex[:8]}.png"
        stored = self.storage.save_bytes(
            tenant_id=UUID(str(tenant_id)),
            brand_space_id=UUID(str(brand_space_id)),
            category="generated",
            filename=filename,
            content=image_bytes,
        )

        logger.info("dalle.save_complete", storage_path=stored.storage_path)

        # Build the final public URL mapping to /storage static path
        return f"/storage/{stored.storage_path}"
