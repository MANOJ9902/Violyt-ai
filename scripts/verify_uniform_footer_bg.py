"""Carousel SEBI footer must NOT paint a separate background band."""
from io import BytesIO

from PIL import Image

from app.services.image_generation.dalle_service import _composite_sebi_footer

BG = (211, 234, 252)  # light sky like the slide
canvas = Image.new("RGB", (1080, 1350), BG)
buf = BytesIO()
canvas.save(buf, format="PNG")

out = _composite_sebi_footer(buf.getvalue(), 1080, 1350)
img = Image.open(BytesIO(out)).convert("RGB")
px = img.load()

def sample_row(y: int) -> list[tuple[int, int, int]]:
    # Far gutters only — centre of the footer row holds grey SEBI glyphs.
    return [px[x, y] for x in (8, 20, 1060, 1072)]

mid = sample_row(600)
bot = sample_row(1320)
print("mid", mid)
print("bot", bot)

def close(a, b, tol=12):
    return all(abs(a[i] - b[i]) <= tol for i in range(3))

for c in mid + bot:
    assert close(c, BG), f"pixel drifted from slide BG: {c} vs {BG}"

# Explicitly: bottom gutters must not be a navy/dark band
assert all(c[2] > 180 for c in bot), bot
assert all(c[0] > 150 for c in bot), bot
print("uniform_bg_ok")
