"""Check/fix kush user credentials on production."""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.user import User


async def main() -> None:
    emails = ["skush@indosakura.com", "owner@violyt.ai", "kushals1992003@gmail.com"]
    async with AsyncSessionLocal() as session:
        for email in emails:
            row = (
                await session.execute(select(User).where(User.email == email))
            ).scalar_one_or_none()
            if not row:
                print(email, "NOT_FOUND")
                continue
            print(
                email,
                "id=", row.id,
                "active=", getattr(row, "is_active", None),
                "tenant=", getattr(row, "tenant_id", None),
            )


if __name__ == "__main__":
    asyncio.run(main())
