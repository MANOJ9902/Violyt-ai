from __future__ import annotations

"""Official Cognixia brand DNA — sourced from Website Colors.pdf + Website Font Style.pdf."""

# Website Colors.pdf
COGNIXIA_PRIMARY_BLUE = "#0952A9"
COGNIXIA_DEEP_NAVY = "#00387A"
COGNIXIA_TEXT_DARK = "#151224"
COGNIXIA_BODY_GRAY = "#707070"
COGNIXIA_CARD_BG = "#F3F9FF"
COGNIXIA_ACCENT_TEAL = "#74ADBA"
COGNIXIA_WHITE = "#FFFFFF"

# Website Font Style.pdf
COGNIXIA_FONT_FAMILY = "Outfit"
COGNIXIA_TAGLINE = "Confident digital change"
COGNIXIA_WEBSITE = "www.cognixia.com"

COGNIXIA_VOICE_LOCK = """
COGNIXIA VOICE (official):
- B2B digital talent + organization transformation — CTOs, CDOs, CHROs, STEM talent.
- Tone: confident, clear, educational, future-ready — NOT retail finance, NOT bond/FD language.
- Signature line when relevant: "Confident digital change."
- Themes: upskilling, reskilling, digital transformation, technology + talent together.
"""

COGNIXIA_TYPOGRAPHY_LOCK = f"""
COGNIXIA TYPOGRAPHY (Website Font Style.pdf):
- Font family: {COGNIXIA_FONT_FAMILY} (Google Font) — clean modern sans-serif.
- Headlines: bold {COGNIXIA_FONT_FAMILY}, dark {COGNIXIA_TEXT_DARK} or deep navy {COGNIXIA_DEEP_NAVY}.
- Body copy: {COGNIXIA_FONT_FAMILY} regular, color {COGNIXIA_BODY_GRAY}.
- Card headings: {COGNIXIA_FONT_FAMILY} semi-bold on card background {COGNIXIA_CARD_BG}.
- CTA buttons: {COGNIXIA_PRIMARY_BLUE} background, white {COGNIXIA_WHITE} label text, rounded pill.
"""

COGNIXIA_VISUAL_LOCK = f"""
COGNIXIA VISUAL SYSTEM (official Website Colors):
- Canvas background: {COGNIXIA_WHITE} or soft card tint {COGNIXIA_CARD_BG} — NEVER Jiraaf ice-blue #E8F0F8.
- Primary brand blue: {COGNIXIA_PRIMARY_BLUE} (headlines, icons, CTA fills).
- Deep navy: {COGNIXIA_DEEP_NAVY} (emphasis headings, dark panels).
- Body text: {COGNIXIA_BODY_GRAY} on white; dark text {COGNIXIA_TEXT_DARK} on light cards.
- Accent / card gradient teal: {COGNIXIA_ACCENT_TEAL} (borders, icon glow, connector lines).
- Cards: rounded white or {COGNIXIA_CARD_BG} panels with subtle shadow; optional teal gradient accent strip.
- Icons: premium 3D tech icons (cloud, blockchain, AI, network, learning) — blue→teal gradient like Cognixia logo.
- Layout: clean corporate education — hub + connected nodes OR stacked fact cards; spacious margins.
- Logo: tiny top-right pocket only (composited later) — never bake "Cognixia" wordmark in AI image.
- FORBIDDEN: Jiraaf navy #003975, orange #FFA400, ice-blue backgrounds, finance/wallet/rupee icons, SEBI footer.
{COGNIXIA_TYPOGRAPHY_LOCK}
"""


def is_cognixia_brand(brand_name: str | None) -> bool:
    name = (brand_name or "").casefold()
    return "cognixia" in name or "cognia" in name


def cognixia_default_palette() -> dict[str, str]:
    return {
        "primary": COGNIXIA_PRIMARY_BLUE,
        "secondary": COGNIXIA_ACCENT_TEAL,
        "text_dark": COGNIXIA_TEXT_DARK,
        "body_gray": COGNIXIA_BODY_GRAY,
        "card_bg": COGNIXIA_CARD_BG,
        "deep_navy": COGNIXIA_DEEP_NAVY,
        "white": COGNIXIA_WHITE,
        "font_family": COGNIXIA_FONT_FAMILY,
    }


def cognixia_color_behavior(
    *,
    primary_color: str = "",
    secondary_color: str = "",
) -> str:
    palette = cognixia_default_palette()
    primary = primary_color or palette["primary"]
    secondary = secondary_color or palette["secondary"]
    return (
        f"Cognixia official palette: background {palette['white']}/{palette['card_bg']}, "
        f"primary {primary}, deep navy {palette['deep_navy']}, accent teal {secondary}, "
        f"body text {palette['body_gray']}, headline text {palette['text_dark']}, "
        f"font {palette['font_family']}. {COGNIXIA_VISUAL_LOCK}"
    )


def cognixia_carousel_palette_line(
    *,
    primary_color: str = "",
    secondary_color: str = "",
) -> str:
    palette = cognixia_default_palette()
    return (
        f"BG {palette['white']} or {palette['card_bg']}; "
        f"primary {primary_color or palette['primary']}; "
        f"deep navy {palette['deep_navy']}; "
        f"accent teal {secondary_color or palette['secondary']}; "
        f"body {palette['body_gray']}; CTA {palette['primary']} on white text; font {palette['font_family']}"
    )
