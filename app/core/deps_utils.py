from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


async def get_user_from_payload(payload: dict, db: AsyncSession):
    email = payload.get("sub")
    if not email:
        return None
    email_return = select(User).where(User.email == email)
    return await db.scalar(email_return)
