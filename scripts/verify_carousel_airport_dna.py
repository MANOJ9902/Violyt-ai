"""Carousel must match airport PDF DNA: clean cards, no connector graphs, no navy footer bake."""
from app.services.image_generation.carousel_image_prompt import (
    _slide_spec,
    build_brand_carousel_slide_image_prompt,
    build_carousel_slide_image_prompt,
)
from app.services.image_generation.dalle_service import _composite_sebi_footer
from io import BytesIO
from PIL import Image

LEAKED = (
    "RBI seal", "note in glass", "hourglass", "recycle symbol", "India map",
    "central shield", "shield hub", "orbiting nodes", "PLASTIC emphasised",
    "coins + sprout", "connected flow", "connector lines", "hub-and-spoke",
)

print("--- layout specs: no borrowed props / no connector graphs ---")
for n in range(1, 11):
    spec = _slide_spec(n, "")
    blob = f"{spec['composition']} {spec['infographic']}".lower()
    hit = [w for w in LEAKED if w.lower() in blob]
    assert not hit, f"slide {n} still leaks {hit}"
    print(f"  slide {n:>2} role={spec['role']:<8} ok")

print("\n--- Jiraaf prompt bans graphs + navy footer bake ---")
p = build_carousel_slide_image_prompt(
    slide_number=2, total_slides=6, role="overview",
    headline="India is betting big on airports",
    body="This isn't just about building a few new terminals.",
    story_blocks=[
        "Operational airports increased from 74 to 165",
        "Over 1.4 lakh crore invested",
        "25 greenfield airports approved",
    ],
    topic="india airports",
)
assert "STACKED CARDS" in p or "stacked" in p.casefold()
assert "NO connector graphs" in p
assert "dark footer bar" in p.casefold() or "LIGHT grey SEBI" in p
assert "Claymorphic" in p or "clay" in p.casefold()
# Ban text must not summon old props by naming them.
assert "orbiting" not in p.casefold()
assert "plastic" not in p.casefold()
print("  jiraaf clean dna ok")

print("\n--- other brand cannot inherit Jiraaf colours ---")
other = build_brand_carousel_slide_image_prompt(
    slide_number=2, total_slides=5, role="detail",
    headline="Skills that scale",
    story_blocks=["Cloud certification", "AI fluency"],
    brand_name="Acme Learning",
    primary_color="#0B3D91",
    secondary_color="#00A3E0",
)
assert "NEVER Jiraaf" in other or "NOT JIRAAF" in other
assert "#87CEFA" in other or "#E8F0F8" in other  # banned explicitly
assert "NO connector graphs" in other or "NO connector" in other
print("  cross-brand lock ok")

print("\n--- SEBI footer default is LIGHT (not navy bar) ---")
canvas = Image.new("RGB", (1080, 1350), (135, 206, 250))
buf = BytesIO(); canvas.save(buf, format="PNG")
out = _composite_sebi_footer(buf.getvalue(), 1080, 1350)
img = Image.open(BytesIO(out)).convert("RGB")
# Sample the footer band — must NOT be navy (~0,57,117)
px = img.load()
ys = [1320, 1335, 1345]
samples = [px[540, y] for y in ys]
avg_b = sum(s[2] for s in samples) / len(samples)
avg_r = sum(s[0] for s in samples) / len(samples)
print(f"  footer samples={samples}")
# Light sky footer: blue channel high, red not navy-dark
assert avg_b > 150 and avg_r > 80, f"footer still looks navy: {samples}"
print("  light footer ok")

print("\ncarousel_airport_dna_ok")
