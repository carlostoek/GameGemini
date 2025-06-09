from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import Reward

async def create_reward(session: AsyncSession, name: str, description: str, points_required: int) -> Reward:
    reward = Reward(name=name, description=description, points_required=points_required)
    session.add(reward)
    await session.commit()
    await session.refresh(reward)
    return reward

async def list_rewards(session: AsyncSession) -> list[Reward]:
    result = await session.execute(select(Reward))
    return result.scalars().all()
