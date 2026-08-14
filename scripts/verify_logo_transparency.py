"""Logo pad must disappear — no white rectangle behind the wordmark."""
from io import BytesIO

from PIL import Image, ImageDraw

from app.services.image_generation.dalle_service import _make_background_transparent


def _logo_on_white_plate() -> bytes:
    """Simulate a Brand Space logo shipped on an opaque white rectangle."""
    img = Image.new("RGBA", (400, 160), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)
    # Orange mark
    d.ellipse((30, 40, 110, 120), fill=(255, 164, 0, 255))
    # Navy wordmark block
    d.rectangle((140, 55, 360, 105), fill=(0, 57, 117, 255))
    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


raw = Image.open(BytesIO(_logo_on_white_plate()))
cleared = _make_background_transparent(raw)
px = cleared.load()
w, h = cleared.size

white_opaque = 0
ink = 0
for y in range(h):
    for x in range(w):
        r, g, b, a = px[x, y]
        if a == 0:
            continue
        if r > 240 and g > 240 and b > 240:
            white_opaque += 1
        else:
            ink += 1

print(f"size={w}x{h} ink={ink} white_opaque={white_opaque}")
assert ink > 200, "brand ink must survive"
assert white_opaque < 40, f"white plate still present ({white_opaque} px)"
# Tight crop should have removed most of the plate area
assert w * h < 400 * 160 * 0.7, "should tight-crop away empty pad"
print("logo_transparency_ok")
