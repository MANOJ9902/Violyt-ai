"""Verify 2:3 -> 4:5 letterbox keeps the full poster (no text chopped off)."""
from io import BytesIO

from PIL import Image, ImageDraw

from app.services.image_generation.dalle_service import _resize_to_export


def _canvas(w: int, h: int) -> bytes:
    """Canvas with top and bottom text bands — crop would erase these."""
    img = Image.new("RGB", (w, h), (211, 234, 252))
    d = ImageDraw.Draw(img)
    d.rectangle((40, 8, w - 40, 70), fill=(0, 57, 117))
    d.rectangle((40, h - 70, w - 40, h - 8), fill=(255, 164, 0))
    cx, cy, r = w // 2, h // 2, min(w, h) // 5
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(0, 57, 117))
    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def _count_color(data: bytes, *, pred) -> int:
    img = Image.open(BytesIO(data)).convert("RGB")
    px = img.load()
    hits = 0
    for y in range(0, img.height, 4):
        for x in range(0, img.width, 4):
            if pred(*px[x, y]):
                hits += 1
    return hits


def _is_navy(r, g, b):
    return r < 80 and g < 110 and b > 60


def _is_orange(r, g, b):
    return r > 180 and g < 200 and b < 80


src = _canvas(1024, 1536)
print("source 1024x1536 -> target 1080x1350")

cropped = _resize_to_export(src, 1080, 1350, allow_crop=True)
letterboxed = _resize_to_export(src, 1080, 1350, letterbox=True)
stretched = _resize_to_export(src, 1080, 1350)

src_navy = _count_color(src, pred=_is_navy)
src_orange = _count_color(src, pred=_is_orange)
# After letterbox the content is smaller but both bands must survive.
lb_navy = _count_color(letterboxed, pred=_is_navy)
lb_orange = _count_color(letterboxed, pred=_is_orange)
# Centre-crop removes the edge bands entirely.
cr_navy = _count_color(cropped, pred=_is_navy)
cr_orange = _count_color(cropped, pred=_is_orange)

print(f"  source      navy={src_navy} orange={src_orange}")
print(f"  letterbox   navy={lb_navy} orange={lb_orange}")
print(f"  crop        navy={cr_navy} orange={cr_orange}")

assert Image.open(BytesIO(letterboxed)).size == (1080, 1350)
assert lb_orange > 50, "letterbox must keep the bottom orange takeaway band"
assert lb_navy > 200, "letterbox must keep the top navy headline band"
assert cr_orange < 10, "sanity: centre-crop must erase the bottom band"
# Cropped still has the centre circle (navy) but far less than letterbox+source bands
assert cr_navy < lb_navy, "crop should keep less navy than letterbox (lost headline)"

print("export_letterbox_ok")
