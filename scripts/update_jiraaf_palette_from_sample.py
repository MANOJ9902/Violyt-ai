"""Persist Jiraaf Brand Space palette into visual_identity (UI source of truth)."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from copy import deepcopy
from uuid import UUID

sys.path.insert(0, r"C:\Users\Lenovo\ai10\Violyt-ai")
os.chdir(r"C:\Users\Lenovo\ai10\Violyt-ai")

BRAND_ID = UUID("1eeb4475-24ca-41dd-8cad-80bb50e0ca74")

# User-provided sample graphic roles → Brand Space form fields (not image hardcodes).
PALETTE = {
    "primary": "#0D3A85",
    "primary_name": "Deep Navy Blue",
    "secondary": "#A2CDF5",
    "secondary_name": "Pale Sky Blue",
    "accent": "#FF9E02",
    "background": "#EBF3FC",
    "additional": [
        {"name": "Vivid Amber Orange", "hex": "#FF9E02", "role": "Accent"},
        {"name": "Soft Gradient Ice Blue", "hex": "#EBF3FC", "role": "Background"},
        {"name": "Dark Slate Charcoal", "hex": "#1F2937", "role": "Supporting Dark"},
        {"name": "Soft Light Peach", "hex": "#FFEED6", "role": "Primary Tint"},
        {"name": "Marigold Orange", "hex": "#F9A000", "role": "Secondary Tint"},
        {"name": "Golden Orange", "hex": "#FAAA24", "role": "Accent"},
    ],
}


async def main() -> None:
    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models.brand import BrandConfigurationSection, BrandSpace
    from app.services.brand import BrandSpaceService
    from app.services.brand_visual_pack import load_brand_visual_pack

    async with AsyncSessionLocal() as session:
        brand = await session.get(BrandSpace, BRAND_ID)
        if not brand:
            raise SystemExit(f"brand not found: {BRAND_ID}")

        result = await session.execute(
            select(BrandConfigurationSection)
            .where(
                BrandConfigurationSection.brand_space_id == BRAND_ID,
                BrandConfigurationSection.section_code == "visual_identity",
                BrandConfigurationSection.is_current.is_(True),
            )
            .order_by(BrandConfigurationSection.version.desc())
        )
        section = result.scalars().first()
        payload = deepcopy(section.payload) if section and isinstance(section.payload, dict) else {}
        payload["brand_color_palette"] = dict(PALETTE)

        if section:
            section.payload = payload
            section.completion_percent = 100
        else:
            session.add(
                BrandConfigurationSection(
                    brand_space_id=BRAND_ID,
                    tenant_id=brand.tenant_id,
                    section_code="visual_identity",
                    payload=payload,
                    completion_percent=100,
                    version=1,
                    is_current=True,
                )
            )
        await session.commit()

        service = BrandSpaceService(session)
        await service.refresh_context(BRAND_ID)
        await session.commit()
        brand_name = brand.name

    pack = await load_brand_visual_pack(str(BRAND_ID))
    print(
        json.dumps(
            {
                "brand": brand_name,
                "primary": pack.primary,
                "secondary": pack.secondary,
                "accent": pack.accent,
                "background": pack.background,
                "headline": pack.headline,
                "body": pack.body,
                "muted": pack.muted,
                "card": pack.card,
                "additional": pack.additional,
                "source": pack.source,
                "lock": pack.palette_lock(),
            },
            indent=2,
        )
    )


asyncio.run(main())
