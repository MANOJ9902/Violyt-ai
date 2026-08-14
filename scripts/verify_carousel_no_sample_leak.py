"""Carousel slides must not reuse the RBI banknote sample's objects for every brand."""
from app.services.image_generation.carousel_image_prompt import (
    _slide_spec,
    build_carousel_slide_image_prompt,
)

# Objects lifted from the plastic-banknote sample that leaked into every brand.
LEAKED = ("RBI seal", "note in glass", "hourglass", "recycle symbol", "India map",
          "central shield", "shield hub", "orbiting nodes", "PLASTIC emphasised",
          "coins + sprout", "₹ coin")

print("--- layout specs carry no borrowed objects ---")
for n in range(1, 11):
    spec = _slide_spec(n, "")
    blob = f"{spec['composition']} {spec['infographic']}"
    hit = [w for w in LEAKED if w.lower() in blob.lower()]
    assert not hit, f"slide {n} still leaks {hit}"
    print(f"  slide {n:>2} role={spec['role']:<8} ok")

print("\n--- role drives layout, not slide position ---")
assert _slide_spec(7, "cover")["role"] == "cover", "role must win over position"
assert _slide_spec(3, "close")["role"] == "close"
print("  slide 7 tagged cover -> cover layout")
print("  slide 3 tagged close -> close layout")

print("\n--- consecutive detail slides differ ---")
variants = {_slide_spec(n, "detail")["infographic"] for n in range(4, 9)}
assert len(variants) >= 4, f"detail slides repeat: {variants}"
print(f"  {len(variants)} distinct detail layouts across slides 4-8")

print("\n--- two different brands/topics do not share imagery ---")
def slide3(topic: str, headline: str, blocks: list[str]) -> str:
    return build_carousel_slide_image_prompt(
        slide_number=3, total_slides=10, role="overview", headline=headline,
        body="Short supporting line.", story_blocks=blocks, topic=topic,
    )

a = slide3("why India is building airports", "AIRPORT EXPANSION",
           ["148 airports live", "UDAN routes", "Cargo capacity"])
b = slide3("corporate IT reskilling", "SKILLS THAT SCALE",
           ["Cloud certification", "AI fluency", "Retention"])
for p, name in ((a, "airports"), (b, "reskilling")):
    hit = [w for w in LEAKED if w.lower() in p.lower()]
    assert not hit, f"{name} slide leaked {hit}"

assert "148 airports live" in a and "Cloud certification" in b
assert "Cloud certification" not in a and "148 airports live" not in b
print("  airports slide carries only airport labels")
print("  reskilling slide carries only reskilling labels")

assert "NO connector graphs" in a, "graph ban missing"
assert "Every icon depicts its own card's subject" in a or "depicts its own" in a
# The ban itself must not name the borrowed props, or the model may render them.
ban = a.split("ABSOLUTE BANS", 1)[1].split("COLOURS:", 1)[0]
assert not [w for w in LEAKED if w.lower() in ban.lower()], "ban text names the props"
print("\ncarousel_no_sample_leak_ok")
