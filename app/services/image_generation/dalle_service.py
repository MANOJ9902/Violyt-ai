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

# Keep logo clearly visible in top-right (samples show readable wordmark).
# Logo ~14% of canvas width — keeps wordmark readable without covering the headline.
_LOGO_MAX_WIDTH_RATIO = 0.14
# Minimum logo short-side in pixels (prevents tiny, unreadable logos).
_LOGO_MIN_PX = 72
# Padding from the canvas edge when placing the logo (in pixels).
_LOGO_EDGE_PADDING = 18
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


def _ensure_light_brand_background(img: Image.Image, bg_hex: str = _DEFAULT_CANVAS_BG) -> Image.Image:
    """If AI returned a near-black canvas, rekey dark background to Brand Space bg."""
    rgba = img.convert("RGBA")
    w, h = rgba.size
    if w < 8 or h < 8:
        return rgba

    px = rgba.load()
    sample_pts = [
        (2, 2),
        (w // 2, 2),
        (w - 3, 2),
        (2, h // 2),
        (w - 3, h // 2),
        (2, h - 3),
        (w // 2, h - 3),
        (w - 3, h - 3),
    ]
    dark = 0
    for x, y in sample_pts:
        r, g, b, _a = px[x, y]
        if (r + g + b) / 3 < 45:
            dark += 1
    if dark < 5:
        return rgba

    # Rekey near-black background pixels to brand ice-blue (preserve colored content)
    datas = list(rgba.getdata())
    out = []
    br, bg_, bb_, ba_ = _rgba(bg_hex or _DEFAULT_CANVAS_BG)
    for r, g, b, a in datas:
        if (r + g + b) / 3 < 38 and abs(r - g) < 18 and abs(g - b) < 18:
            out.append((br, bg_, bb_, 255))
        else:
            out.append((r, g, b, a))
    rgba.putdata(out)
    logger.info("dalle.black_bg_rekeyed", dark_corners=dark, size=f"{w}x{h}")
    return rgba


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
    jpeg_mode = src_mode in ("RGB", "L", "CMYK") and "A" not in src_mode
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

    # Pass 2 — any leftover near-white plate that is not brand ink.
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if _is_logo_pad_rgb(r, g, b, jpeg_mode=jpeg_mode) and not _is_brand_ink(r, g, b):
                px[x, y] = (r, g, b, 0)

    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    return img


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
    width_ratio: float = 0.18,
    height_ratio: float = 0.11,
) -> Image.Image:
    """Remove AI-hallucinated logos / 'Brand Logo' placeholders before compositing.

    Pocket sized to fit the Brand Space logo composite without eating the headline.
    """
    from PIL import ImageDraw

    wipe_w = min(int(canvas_width * width_ratio), canvas_width)
    wipe_h = min(int(canvas_height * height_ratio), canvas_height)
    wipe_box = (canvas_width - wipe_w, 0, canvas_width, wipe_h)
    fill = _sample_corner_fill(base_img, canvas_width, canvas_height)
    ImageDraw.Draw(base_img).rectangle(wipe_box, fill=fill)
    return base_img


def _composite_logo(
    base_bytes: bytes,
    logo_bytes: bytes,
    logo_zone_instruction: str | None,
    canvas_width: int,
    canvas_height: int,
) -> bytes:
    """Wipe a small top-right pocket, then paste the Brand Space logo AS-IS (icon + wordmark OK)."""
    base_img = Image.open(BytesIO(base_bytes)).convert("RGBA")
    logo_raw = Image.open(BytesIO(logo_bytes))
    logo_img = _make_background_transparent(logo_raw).convert("RGBA")
    # Tight crop again after any residual alpha fringe
    content_box = logo_img.getbbox()
    if content_box:
        logo_img = logo_img.crop(content_box)

    max_logo_w = max(int(canvas_width * _LOGO_MAX_WIDTH_RATIO), _LOGO_MIN_PX)
    max_logo_h = max(int(canvas_height * 0.065), _LOGO_MIN_PX)
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
    # Clear AI-drawn fake logos / placeholders. The pocket is derived from the placed
    # logo so a wide wordmark can never land on top of un-wiped artwork.
    base_img = _wipe_top_right_corner(
        base_img,
        canvas_width,
        canvas_height,
        width_ratio=max(0.18, (logo_w + 2 * pad) / max(canvas_width, 1)),
        height_ratio=max(0.11, (logo_h + 2 * pad) / max(canvas_height, 1)),
    )
    base_img.paste(logo_img, (x, y), logo_img)

    out = BytesIO()
    fixed = _ensure_light_brand_background(base_img)
    _flatten_rgba_to_brand_bg(fixed).convert("RGB").save(out, format="PNG", optimize=False)
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
    for i, line in enumerate(lines):
        draw.text((side_pad, y), line, font=font, fill=_LEGAL_FOOTER_COLOR)
        y += line_heights[i] + line_gap

    out = BytesIO()
    # Flatten only — do not recolour the footer zone to a different fill.
    _flatten_rgba_to_brand_bg(base_img).convert("RGB").save(out, format="PNG", optimize=False)
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
) -> bytes:
    """Fit the API canvas to the exact export size.

    Default is a stretch (keeps one seamless field). For portrait posters,
    pass letterbox=True so 2:3 -> 4:5 never chops the headline or takeaway —
    centre-crop was cutting ~8% off the top and bottom and amputating text.
    allow_crop is retained for callers but is no longer used for portrait posters.
    """
    img = _ensure_light_brand_background(Image.open(BytesIO(image_bytes)))
    src_w, src_h = img.size
    if src_w <= 0 or src_h <= 0 or target_w <= 0 or target_h <= 0:
        return image_bytes
    if (src_w, src_h) == (target_w, target_h):
        out = BytesIO()
        _flatten_rgba_to_brand_bg(img).convert("RGB").save(out, format="PNG", optimize=False)
        return out.getvalue()

    if letterbox:
        canvas = _letterbox_to_size(img, target_w, target_h)
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
    _flatten_rgba_to_brand_bg(img).convert("RGB").save(out, format="PNG", optimize=False)
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
    if wipe_reserved_corner and not logo_storage_path:
        try:
            base_img = Image.open(BytesIO(image_bytes))
            real_w, real_h = base_img.size
            wiped = _wipe_top_right_corner(base_img.convert("RGBA"), real_w, real_h)
            out = BytesIO()
            _flatten_rgba_to_brand_bg(wiped, canvas_bg_hex).convert("RGB").save(out, format="PNG", optimize=False)
            image_bytes = out.getvalue()
            logger.info("dalle.corner_wiped", canvas=f"{real_w}x{real_h}")
        except Exception as wipe_exc:
            logger.warning("dalle.corner_wipe_failed", error=str(wipe_exc)[:200])

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
            )
            logger.info("dalle.legal_footer_composited", canvas=f"{real_w}x{real_h}")
        except Exception as footer_exc:
            logger.warning("dalle.legal_footer_failed", error=str(footer_exc)[:300])

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

        try:
            kwargs: dict = {
                "model": self.model,
                "prompt": prompt[:6000],
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

        # Resize API canvas → exact export size (Instagram/LinkedIn/X)
        try:
            image_bytes = _resize_to_export(
                image_bytes,
                export_w,
                export_h,
                letterbox=letterbox_to_aspect,
            )
            logger.info(
                "dalle.resized_to_export",
                export=f"{export_w}x{export_h}",
                letterboxed=letterbox_to_aspect,
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
