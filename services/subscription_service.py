import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import SubscriptionToken


class SubscriptionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_token(self, duration_hours: int = 24) -> SubscriptionToken:
        token_str = uuid.uuid4().hex
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=duration_hours)
        token = SubscriptionToken(token=token_str, expires_at=expires_at)
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def get_token(self, token: str) -> SubscriptionToken | None:
        return await self.session.get(SubscriptionToken, token)

    async def is_valid(self, token: str) -> bool:
        token_obj = await self.get_token(token)
        if not token_obj:
            return False
        return token_obj.expires_at > datetime.datetime.utcnow()
