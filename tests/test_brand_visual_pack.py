from app.services.brand_visual_pack import build_visual_pack


def _jiraaf_like_context() -> dict:
    return {
        "brand_name": "Jiraaf",
        "visual_identity": {
            "brand_color_palette": {
                "primary": "#3D3DBE",
                "secondary": "#FFCBCB",
                "additional": [
                    {"name": "accent", "hex": "#00CB91"},
                    {"name": "secondary", "hex": "#69747A"},
                    {"name": "secondary", "hex": "#FFA400"},
                    {"name": "orange", "hex": "orange"},
                    {"name": "blue", "hex": "blue"},
                    {"name": "grey", "hex": "grey"},
                ],
            },
            "template_intelligence": [
                {
                    "analysis": {
                        "palette": [
                            {"role": "accent", "hex": "#FF6A00", "name": "orange"},
                            {"role": "primary", "hex": "#0B1F4A", "name": "navy"},
                        ]
                    }
                }
            ],
        },
    }


def test_visual_pack_uses_brand_space_roles_not_invented_tints():
    pack = build_visual_pack(
        brand_id="test-brand",
        brand_name="Jiraaf",
        resolved_brand_context=_jiraaf_like_context(),
    )
    assert pack.primary == "#3D3DBE"
    assert pack.secondary == "#FFCBCB"
    assert pack.accent == "#00CB91"
    assert pack.card == "#FFCBCB"
    assert pack.background == "#FFFFFF"
    assert pack.headline == "#3D3DBE"
    lock = pack.palette_lock()
    assert "#3D3DBE" in lock
    assert "#FFCBCB" in lock
    assert "#00CB91" in lock
    # Duplicate secondary / template oranges must not be authorized roles.
    assert "secondary #FFA400" not in lock.lower()
    assert "primary #0B1F4A" not in lock.lower()
    assert "accent #FF6A00" not in lock.lower()
    extras = {str(c.get("hex")).upper() for c in pack.additional}
    assert "#FFA400" not in extras
    assert "#69747A" not in extras
    assert "#0B1F4A" not in extras
    assert "#FF6A00" not in extras


def test_palette_map_assigns_secondary_to_cards():
    pack = build_visual_pack(
        brand_id="test-brand",
        resolved_brand_context=_jiraaf_like_context(),
    )
    mapped = pack.palette_map()
    assert mapped["card"] == "#FFCBCB"
    assert mapped["secondary"] == "#FFCBCB"
    assert mapped["accent"] == "#00CB91"
    assert mapped["background"] == "#FFFFFF"


def test_visual_pack_recognizes_role_based_brand_space_labels():
    pack = build_visual_pack(
        brand_id="test-brand",
        resolved_brand_context={
            "brand_name": "Role Brand",
            "visual_identity": {
                "brand_color_palette": {
                    "additional": [
                        {"name": "Primary Colour", "hex": "#9000FF"},
                        {"name": "Secondary Colour", "hex": "#4BCA0E"},
                        {"name": "Primary Tint", "hex": "#EEE1FA"},
                        {"name": "Supporting Dark", "hex": "#331958"},
                        {"name": "Neutral", "hex": "#000001"},
                    ]
                }
            },
        },
    )
    assert pack.primary == "#9000FF"
    assert pack.secondary == "#4BCA0E"
    assert pack.card == "#EEE1FA"
    assert pack.body == "#331958"
    assert pack.muted == "#331958"


def test_visual_pack_prefers_explicit_role_hint_over_free_text_name():
    """The Brand Space table sends a fixed 'role' plus a free-text colour name (e.g. 'Electric
    Violet'). Explicit role hints must be used instead of trying to guess the role from that name."""
    pack = build_visual_pack(
        brand_id="test-brand",
        resolved_brand_context={
            "brand_name": "Role Hint Brand",
            "visual_identity": {
                "brand_color_palette": {
                    "additional": [
                        {"name": "Deep Violet Ink", "hex": "#331958", "role": "Supporting Dark"},
                        {"name": "Soft Lilac", "hex": "#EEE1FA", "role": "Primary Tint"},
                        {"name": "Almost Black", "hex": "#000001", "role": "Neutral"},
                    ]
                }
            },
        },
    )
    assert pack.card == "#EEE1FA"
    assert pack.body == "#331958"
    assert pack.muted == "#331958"
    names = {entry["name"] for entry in pack.additional}
    assert "Deep Violet Ink" in names
    assert "Soft Lilac" in names


def test_visual_pack_falls_back_to_name_when_role_hint_is_missing():
    """Rows saved before the explicit 'role' field existed keep working via name-based inference."""
    pack = build_visual_pack(
        brand_id="test-brand",
        resolved_brand_context={
            "brand_name": "Legacy Brand",
            "visual_identity": {
                "brand_color_palette": {
                    "additional": [{"name": "Supporting Dark", "hex": "#331958"}],
                }
            },
        },
    )
    assert pack.body == "#331958"
    assert pack.muted == "#331958"
