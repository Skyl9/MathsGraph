from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import User, PasswordResetToken, UserSession


class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_username_or_email(self, username: str, email: str):
        query = select(User).where((User.username == username) | (User.email == email))
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_user_by_username(self, username: str):
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_user_by_email(self, email: str):
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def add_user(self, user: User):
        self.db.add(user)
        await self.db.flush()
        return user

    async def get_user_by_id(self, user_id: int):
        return await self.db.get(User, user_id)

    async def add_session(self, session: UserSession):
        self.db.add(session)
        await self.db.flush()

    async def add_reset_token(self, reset_token: PasswordResetToken):
        self.db.add(reset_token)
        await self.db.flush()

    async def get_valid_reset_token(self, token: str):
        query = select(PasswordResetToken).where(PasswordResetToken.token == token, PasswordResetToken.used.is_(False))
        result = await self.db.execute(query)
        return result.scalars().first()

    async def flush(self):
        await self.db.flush()
