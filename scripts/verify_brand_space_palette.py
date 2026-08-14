"""Check Brand Space palette resolution against the real stored Jiraaf spaces."""

from app.prompts.brand_visual_palette import (
    JIRAAF_BG,
    contrast_ratio,
    jiraaf_palette_override_block,
    resolve_jiraaf_palette,
)

CASES = [
    ("Jiraaf 7fe7 (LIVE)", "#003A79", "#FF9E00"),
    ("Jiraaf f8e6", "#003A79", "#FF9D1B"),
    ("Jirraf junk", "#042090", "#0B8E1B"),
    ("jiraaf junk", "#EA1010", "#11D428"),
    ("empty space", "", ""),
]

for name, primary, secondary in CASES:
    out = resolve_jiraaf_palette(primary=primary, secondary=secondary)
    print(f"{name:20} primary={primary or '-':9} -> headline={out['headline']:9} [{out['headline_source']}]")
    print(
        f"{'':20} secondary={secondary or '-':9} -> accent={out['accent']:9} "
        f"[{out['accent_source']}]  contrast_vs_bg={contrast_ratio(secondary, JIRAAF_BG):.2f}"
    )

live = resolve_jiraaf_palette(primary="#003A79", secondary="#FF9E00")
assert live["headline"] == "#003A79", live
assert live["accent"] == "#FF9E00", live
assert live["background"] == JIRAAF_BG, live
assert live["headline_source"] == "brand_space", live

# Red headlines are unreadable on the sky-blue canvas, so they fall back.
junk = resolve_jiraaf_palette(primary="#EA1010", secondary="#11D428")
assert junk["headline_source"] == "locked_default", junk

# An accent indistinguishable from the canvas falls back.
invisible = resolve_jiraaf_palette(primary="#003A79", secondary="#8ACFFB")
assert invisible["accent_source"] == "locked_default", invisible

blank = resolve_jiraaf_palette()
assert blank["headline_source"] == "locked_default", blank
assert blank["accent_source"] == "locked_default", blank

block = jiraaf_palette_override_block(live)
assert "#003A79" in block and JIRAAF_BG in block, block
print("\noverride block:\n" + block)
print("brand_space_palette_ok")
