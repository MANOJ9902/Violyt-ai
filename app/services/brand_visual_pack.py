"""Brand-agnostic visual pack for the LangGraph image pipeline.

Every run is keyed by brand_id. Colors, fonts, legal footer, and mascot come
from BrandSpace.resolved_brand_context (with overview_snapshot as fallback).
No brand-name matching. Palette and assets come only from Brand Space.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.utils.palette_roles import derive_palette_roles, hex_to_rgb, normalize_hex

logger = get_logger(__name__)

_NEUTRAL_PRIMARY = "#1F2937"
_NEUTRAL_SECONDARY = "#4B5563"
_NEUTRAL_BG = "#FFFFFF"
_NEUTRAL_MUTED = "#6B7280"
_NEUTRAL_BODY = "#374151"


def _hex(value: Any, fallback: str = "") -> str:
    return normalize_hex(value) or fallback


def _is_light(hex_color: str) -> bool:
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return True
    return (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) >= 200


def _is_card_wash(hex_color: str) -> bool:
    """True for pale Brand Space secondary washes used as carousel card fills.

    Slightly looser than `_is_light` so sky blues like #A2CDF5 (lum ~199) qualify.
    """
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return False
    return (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) >= 175


_ROLE_NAME_KEYS = {
    "primary": ("primary colour", "primary color", "primary"),
    "secondary": ("secondary colour", "secondary color", "secondary"),
    "accent": ("accent", "highlight", "cta", "button", "button color", "button colour"),
    "background": ("background", "bg", "canvas"),
    "surface": (
        "surface",
        "card",
        "panel",
        "primary tint",
        "secondary tint",
        "tint",
    ),
    "muted": (
        "muted",
        "grey",
        "gray",
        "neutral",
        "body",
        "body text",
        "text body",
        "text body copy",
        "supporting dark",
        "text color",
        "text colour",
    ),
}


def _additional_role_name(name: str) -> str | None:
    """Map an additional-row label to a Brand Space role. Form primary/secondary win."""
    text = (name or "").strip().casefold()
    if not text:
        return None
    if text in {"primary", "primary colour", "primary color"}:
        return "primary"
    if text in {"secondary", "secondary colour", "secondary color"}:
        return "secondary"
    if "primary tint" in text or "secondary tint" in text:
        return "surface"
    if "supporting dark" in text:
        return "muted"
    for role, keys in _ROLE_NAME_KEYS.items():
        if any(key in text for key in keys):
            return role
    return None


def _font_name(typography: Any) -> str:
    if isinstance(typography, str):
        return typography.strip()
    if not isinstance(typography, dict):
        return ""
    for key in ("primary_style", "primary_font", "font_family", "headline_font"):
        val = typography.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    families = typography.get("font_families") or []
    if isinstance(families, list):
        for item in families:
            if isinstance(item, dict) and item.get("name"):
                return str(item["name"]).strip()
            if isinstance(item, str) and item.strip():
                return item.strip()
    hierarchy = typography.get("style_hierarchy") or {}
    if isinstance(hierarchy, dict):
        for val in hierarchy.values():
            if isinstance(val, dict) and val.get("font"):
                return str(val["font"]).strip()
            if isinstance(val, str) and val.strip():
                return val.strip()
    return ""


def _first_legal_text(disclaimers: Any, fmt: str = "") -> tuple[str, str]:
    if not isinstance(disclaimers, list):
        return "", ""
    fmt_l = (fmt or "").strip().lower()
    ranked: list[dict] = []
    for item in disclaimers:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text_template") or item.get("text") or "").strip()
        if not text:
            continue
        applies = item.get("applies_to_formats") or []
        if applies and fmt_l and fmt_l not in {str(x).strip().lower() for x in applies}:
            continue
        ranked.append(item)
    if not ranked:
        for item in disclaimers:
            if isinstance(item, dict) and str(item.get("text_template") or "").strip():
                ranked.append(item)
                break
    if not ranked:
        return "", ""
    chosen = ranked[0]
    return (
        str(chosen.get("text_template") or "").strip(),
        _hex(chosen.get("text_color"), "#68747D"),
    )


def _mascot_path(visual_identity: dict[str, Any], identity: dict[str, Any]) -> str:
    blobs: list[dict] = []
    for key in ("reusable_design_assets", "reusable_assets"):
        items = visual_identity.get(key) or []
        if isinstance(items, list):
            blobs.extend(x for x in items if isinstance(x, dict))
    review = visual_identity.get("reusable_design_asset_review") or {}
    if isinstance(review, dict):
        for key in ("approved",):
            items = review.get(key) or []
            if isinstance(items, list):
                blobs.extend(x for x in items if isinstance(x, dict))
    keywords = ("mascot", "character", "close", "brand character")
    for item in blobs:
        kind = str(item.get("asset_kind") or item.get("review_class") or "").casefold()
        label = str(item.get("label") or "").casefold()
        path = str(item.get("storage_path") or "").strip()
        if not path:
            continue
        hay = f"{kind} {label}"
        if any(k in hay for k in keywords):
            return path
    for item in blobs:
        kind = str(item.get("asset_kind") or "").casefold()
        path = str(item.get("storage_path") or "").strip()
        if path and kind in {"illustration", "character", "mascot"}:
            return path
    for key in ("mascot_storage_path", "close_mascot_path"):
        path = str(identity.get(key) or visual_identity.get(key) or "").strip()
        if path:
            return path
    return ""


def _design_notes(visual_identity: dict[str, Any]) -> str:
    parts: list[str] = []
    ds = visual_identity.get("design_system")
    if isinstance(ds, dict):
        for key in ("summary", "background_style", "layout_style", "icon_style"):
            val = ds.get(key)
            if isinstance(val, str) and val.strip():
                parts.append(val.strip()[:240])
        motifs = ds.get("component_motifs") or visual_identity.get("component_motifs")
        if isinstance(motifs, list) and motifs:
            parts.append("Motifs: " + ", ".join(str(m) for m in motifs[:8]))
    elif isinstance(ds, str) and ds.strip():
        parts.append(ds.strip()[:400])
    mood = visual_identity.get("mood") or visual_identity.get("visual_style")
    if isinstance(mood, str) and mood.strip():
        parts.append(mood.strip()[:200])
    return " | ".join(parts)[:800]


@dataclass
class BrandVisualPack:
    brand_id: str = ""
    brand_name: str = ""
    tenant_id: str = ""
    primary: str = _NEUTRAL_PRIMARY
    secondary: str = _NEUTRAL_SECONDARY
    accent: str = _NEUTRAL_SECONDARY
    background: str = _NEUTRAL_BG
    headline: str = _NEUTRAL_PRIMARY
    body: str = _NEUTRAL_BODY
    muted: str = _NEUTRAL_MUTED
    card: str = "#F3F4F6"
    additional: list[dict] = field(default_factory=list)
    font_primary: str = ""
    legal_footer: str = ""
    legal_color: str = "#68747D"
    mascot_storage_path: str = ""
    logo_position: str = "top-right"
    design_system_summary: str = ""
    source: str = "neutral_fallback"

    @property
    def has_legal(self) -> bool:
        return bool(self.legal_footer.strip())

    @property
    def has_mascot(self) -> bool:
        return bool(self.mascot_storage_path.strip())

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["has_legal"] = self.has_legal
        data["has_mascot"] = self.has_mascot
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> BrandVisualPack:
        if not isinstance(data, dict) or not data:
            return cls()
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})

    def palette_map(self) -> dict[str, str]:
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "background": self.background,
            "headline": self.headline,
            "body": self.body,
            "muted": self.muted,
            "card": self.card,
            "font": self.font_primary,
        }

    def palette_lock(self) -> str:
        font = f" FONT: {self.font_primary}." if self.font_primary else ""
        extras = ""
        if self.additional:
            bits = [
                f"{c.get('name') or c.get('role') or 'extra'} {c.get('hex')}"
                for c in self.additional
                if isinstance(c, dict) and c.get("hex")
            ]
            if bits:
                extras = " Extras: " + ", ".join(bits[:4]) + "."
        return (
            f"BRAND SPACE PALETTE for {self.brand_name or 'this brand'} (AUTHORITATIVE HEX LOCK): "
            f"background={self.background}, headlines/primary={self.primary}, "
            f"secondary/cards={self.secondary}, accent/CTA={self.accent}, "
            f"body={self.body}, cards={self.card}.{extras}{font} "
            "Paint ONLY these exact hexes — including Brand Space ice/sky blues when listed. "
            "FORBIDDEN unless listed above: classic sample navy (#0B2C5F/#003975), "
            "sample orange (#FFA400/#FF8A00), foreign teal/mint/gold, or any OTHER brand palette. "
            "Vector/PDF template swatches NEVER override these Brand Space hexes."
        )

    def image_extra_locks(self, *, fmt: str = "") -> str:
        legal = ""
        if fmt == "carousel" and self.has_legal:
            legal = (
                "Leave the bottom ~20% empty for a composited legal footer. "
                "Do not bake disclaimer text or Learn More buttons into the image.\n"
            )
        elif fmt == "carousel":
            legal = (
                "Leave the bottom ~20% empty Brand Space background. "
                "Do not invent a disclaimer strip or Learn More button.\n"
            )
        else:
            legal = "No regulatory footer strip unless the Brand Space supplied one.\n"
        mascot = ""
        if fmt == "carousel" and self.has_mascot:
            mascot = "On the LAST slide leave the lower-right empty for a composited brand mascot.\n"
        ds = f"Layout notes from Brand Space: {self.design_system_summary}\n" if self.design_system_summary else ""
        return (
            f"\n{self.palette_lock()}\n"
            f"PAGE BACKGROUND (NON-NEGOTIABLE): full-bleed exact {self.background} ONLY. "
            f"NEVER paint primary/navy ({self.primary}) as the page canvas or header band — "
            f"primary is for HEADLINE TEXT only. Cards use {self.secondary}/{self.card}. "
            f"Accent {self.accent} is for CTA/highlights only.\n"
            f"TOP-RIGHT: leave a blank logo pocket; the real logo is composited in post. "
            f"NEVER draw a white box behind any logo. NEVER draw LinkedIn / Instagram / X / "
            f"platform logos, badges, or watermarks anywhere.\n"
            f"{legal}{mascot}{ds}"
            "AUDIENCE: depict the Brand Space persona demographics — not a generic stock crowd.\n"
            "TEXT FIT: every word fully inside the frame — scale font down; never clip mid-word.\n"
        )


def build_visual_pack(
    *,
    brand_id: str,
    brand_name: str = "",
    tenant_id: str = "",
    resolved_brand_context: dict[str, Any] | None = None,
    overview_snapshot: dict[str, Any] | None = None,
    fmt: str = "",
) -> BrandVisualPack:
    context = resolved_brand_context if isinstance(resolved_brand_context, dict) else {}
    snapshot = overview_snapshot if isinstance(overview_snapshot, dict) else {}
    visual = context.get("visual_identity") if isinstance(context.get("visual_identity"), dict) else {}
    if not visual:
        visual = snapshot.get("visual_identity") if isinstance(snapshot.get("visual_identity"), dict) else {}
    identity = context.get("identity") if isinstance(context.get("identity"), dict) else {}
    assets = context.get("brand_assets") if isinstance(context.get("brand_assets"), dict) else {}

    name = (
        str(context.get("brand_name") or identity.get("brand_name") or brand_name or "").strip()
    )
    palette_obj = visual.get("brand_color_palette") if isinstance(visual.get("brand_color_palette"), dict) else {}

    # Form fields on Brand Space win. Do not score leftover PDF/template swatches over them.
    primary = _hex(palette_obj.get("primary"), "")
    secondary = _hex(palette_obj.get("secondary"), "")
    accent = _hex(palette_obj.get("accent"), "")
    background = _hex(palette_obj.get("background"), "")
    surface = _hex(palette_obj.get("surface"), "")
    muted = _hex(palette_obj.get("neutral") or palette_obj.get("muted"), "")

    additional_raw = palette_obj.get("additional") if isinstance(palette_obj.get("additional"), list) else []
    additional: list[dict] = []
    ignored_extra: list[str] = []
    for item in additional_raw:
        if not isinstance(item, dict):
            continue
        hx = _hex(item.get("hex") or item.get("hex_code") or item.get("color"))
        label = str(item.get("name") or "").strip()
        # Optional explicit role hint (e.g. from the Brand Space table's fixed "Role" column such as
        # "Supporting Dark" / "Primary Tint"). Additive: falls back to guessing from the label text so
        # older rows saved before this field existed keep working exactly as before.
        role_hint = str(item.get("role") or "").strip()
        if not hx:
            ignored_extra.append(label or str(item.get("hex") or "invalid"))
            continue
        role = _additional_role_name(role_hint) or _additional_role_name(label)
        if role == "primary" and not primary:
            primary = hx
            additional.append({"name": label or "primary", "hex": hx, "role": "primary"})
        elif role == "secondary" and not secondary:
            secondary = hx
            additional.append({"name": label or "secondary", "hex": hx, "role": "secondary"})
        elif role == "accent" and not accent:
            accent = hx
            additional.append({"name": label or "accent", "hex": hx, "role": "accent"})
        elif role == "background" and not background:
            background = hx
            additional.append({"name": label or "background", "hex": hx, "role": "background"})
        elif role == "surface" and not surface:
            surface = hx
            additional.append({"name": label or "surface", "hex": hx, "role": "surface"})
        elif role == "muted" and not muted:
            muted = hx
            additional.append({"name": label or "muted", "hex": hx, "role": "muted"})
        else:
            # Duplicate primary/secondary PDF swatches stay off the lock.
            # Extra Accent / tint rows can still appear as extras without overriding form roles.
            used = {
                (primary or "").upper(),
                (secondary or "").upper(),
                (accent or "").upper(),
                (background or "").upper(),
                (surface or "").upper(),
                (muted or "").upper(),
            }
            if role in {"primary", "secondary"}:
                ignored_extra.append(f"{label or 'extra'}:{hx}")
            elif hx and hx.upper() not in used:
                additional.append(
                    {
                        "name": label or role_hint or "extra",
                        "hex": hx,
                        "role": role or "extra",
                    }
                )
            else:
                ignored_extra.append(f"{label or 'extra'}:{hx}")

    source = "resolved_brand_context" if (primary or secondary or accent) and context else "neutral_fallback"
    if not primary and snapshot:
        source = "overview_snapshot" if palette_obj else source

    # Gap-fill ONLY from Brand Space palette_entries that already have an explicit role.
    # Never score PDF/template swatches into primary/secondary (cross-brand leak risk).
    if not primary or not secondary or not background or not surface or not muted or not accent:
        roles = derive_palette_roles(visual, allow_template_swatches=False) if visual else {}
        if not primary:
            primary = _hex(roles.get("primary"), "")
        if not secondary:
            secondary = _hex(roles.get("secondary"), "")
        if not accent:
            accent = _hex(roles.get("accent"), "")
        if not background:
            background = _hex(roles.get("background"), "")
        if not surface:
            surface = _hex(roles.get("surface"), "")
        if not muted:
            muted = _hex(roles.get("muted") or roles.get("neutral"), "")

    if not primary:
        primary = _NEUTRAL_PRIMARY
        if source != "overview_snapshot":
            source = "neutral_fallback"
    if not secondary:
        secondary = _NEUTRAL_SECONDARY
    if not accent:
        accent = secondary
    # Canvas default is white when Brand Space did not set a background. Never invent a tint of primary.
    if not background:
        background = _NEUTRAL_BG
    # Card fills: prefer pale Brand Space SECONDARY (sample carousels use secondary as card wash).
    # Primary Tint / surface is a supporting wash — only use it when secondary is not a card wash.
    if secondary and _is_card_wash(secondary) and secondary.upper() != primary.upper():
        card = secondary
    elif surface:
        card = surface
    else:
        card = _NEUTRAL_BG
    headline = primary
    body = muted or _NEUTRAL_BODY
    if not muted:
        muted = _NEUTRAL_MUTED
    if ignored_extra:
        logger.info(
            "brand_visual_pack.ignored_additional",
            brand_id=str(brand_id or ""),
            ignored=ignored_extra[:8],
        )

    typography = visual.get("typography")
    if not typography and isinstance(snapshot.get("visual_identity"), dict):
        typography = snapshot["visual_identity"].get("typography")
    font = _font_name(typography)

    legal_text, legal_color = _first_legal_text(assets.get("legal_disclaimers"), fmt=fmt)
    mascot = _mascot_path(visual, identity)
    logo_pos = str(visual.get("logo_position") or identity.get("logo_position") or "top-right")

    pack = BrandVisualPack(
        brand_id=str(brand_id or ""),
        brand_name=name,
        tenant_id=str(tenant_id or ""),
        primary=primary,
        secondary=secondary,
        accent=accent,
        background=background,
        headline=headline,
        body=body,
        muted=muted,
        card=card,
        additional=additional,
        font_primary=font,
        legal_footer=legal_text,
        legal_color=legal_color or "#68747D",
        mascot_storage_path=mascot,
        logo_position=logo_pos,
        design_system_summary=_design_notes(visual),
        source=source,
    )
    logger.info(
        "brand_visual_pack.built",
        brand_id=pack.brand_id,
        brand_name=pack.brand_name,
        source=pack.source,
        primary=pack.primary,
        secondary=pack.secondary,
        accent=pack.accent,
        card=pack.card,
        background=pack.background,
        has_legal=pack.has_legal,
        has_mascot=pack.has_mascot,
        font=pack.font_primary or "",
    )
    return pack


async def load_brand_visual_pack(brand_id: str, *, fmt: str = "") -> BrandVisualPack:
    """Load the compact visual pack for a Brand Space id."""
    from app.db.session import AsyncSessionLocal
    from app.models.brand import BrandSpace

    if not brand_id:
        return BrandVisualPack()
    try:
        brand_uuid = UUID(str(brand_id))
    except Exception:
        logger.warning("brand_visual_pack.invalid_brand_id", brand_id=str(brand_id)[:80])
        return BrandVisualPack(brand_id=str(brand_id))

    async with AsyncSessionLocal() as session:
        row = await session.get(BrandSpace, brand_uuid)
        if row is None:
            logger.warning("brand_visual_pack.brand_not_found", brand_id=str(brand_id))
            return BrandVisualPack(brand_id=str(brand_id))
        return build_visual_pack(
            brand_id=str(row.id),
            brand_name=str(getattr(row, "name", "") or ""),
            tenant_id=str(getattr(row, "tenant_id", "") or ""),
            resolved_brand_context=getattr(row, "resolved_brand_context", None),
            overview_snapshot=getattr(row, "overview_snapshot", None),
            fmt=fmt,
        )


def visual_pack_from_state(state: dict[str, Any] | None) -> BrandVisualPack:
    if not isinstance(state, dict):
        return BrandVisualPack()
    raw = state.get("visual_pack")
    if isinstance(raw, BrandVisualPack):
        return raw
    if isinstance(raw, dict) and raw:
        return BrandVisualPack.from_dict(raw)
    return BrandVisualPack(
        brand_id=str(state.get("brand_id") or ""),
        brand_name=str(state.get("brand_name") or ""),
        tenant_id=str(state.get("tenant_id") or ""),
    )
