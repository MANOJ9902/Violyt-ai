"""Inspect skush user and brand visibility on production."""
from __future__ import annotations

import asyncio
import json

from sqlalchemy import select

from app.core.security import hash_password, verify_password
from app.db.session import AsyncSessionLocal
from app.models.brand import BrandSpace
from app.models.tenant import User, UserRole


async def main() -> None:
    email = "skush@indosakura.com"
    password = "DemoPass123!"
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
        if not user:
            print("USER_NOT_FOUND")
            return
        print("user_id", user.id)
        print("email", user.email)
        print("tenant_id", user.tenant_id)
        print("is_active", user.is_active)
        print("password_ok", verify_password(password, user.hashed_password or ""))

        roles = (
            await session.execute(select(UserRole).where(UserRole.user_id == user.id))
        ).scalars().all()
        print("roles", [(r.role_code, getattr(r, "tenant_id", None)) for r in roles])

        brands = (
            await session.execute(
                select(BrandSpace).where(BrandSpace.tenant_id == user.tenant_id)
            )
        ).scalars().all()
        print(f"tenant_brands_count={len(brands)}")
        for b in brands[:20]:
            print(" brand", b.id, "|", b.name, "|", b.slug, "| active=", getattr(b, "is_active", None))

        jiraaf = [b for b in brands if (b.slug or "").lower() == "jiraaf" or "jiraaf" in (b.name or "").lower()]
        print("jiraaf_brands", len(jiraaf))
        for b in jiraaf:
            print(" jiraaf", b.id, b.name, b.slug)


if __name__ == "__main__":
    asyncio.run(main())
