from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Reward, User
import logging

logger = logging.getLogger(__name__)

class RewardService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_rewards(self) -> list[Reward]:
        stmt = select(Reward).where(Reward.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_reward_by_id(self, reward_id: int) -> Reward | None:
        return await self.session.get(Reward, reward_id)

    async def purchase_reward(self, user_id: int, reward_id: int) -> tuple[bool, str]:
        user = await self.session.get(User, user_id)
        reward = await self.session.get(Reward, reward_id)

        if not user:
            logger.warning(f"Purchase attempt by non-existent user {user_id}.")
            return False, "Usuario no encontrado. Por favor, inicia con /start."
        if not reward or not reward.is_active:
            logger.warning(f"Purchase attempt for inactive or non-existent reward {reward_id}.")
            return False, "Recompensa no disponible."
        if reward.stock != -1 and reward.stock <= 0:
            logger.warning(f"Purchase attempt for out-of-stock reward {reward_id}.")
            return False, "Recompensa agotada."
        if user.points < reward.cost:
            logger.info(f"User {user_id} attempted to buy {reward.name} but has insufficient points ({user.points}/{reward.cost}).")
            return False, f"No tienes suficientes puntos. Necesitas {reward.cost - user.points} puntos más."

        user.points -= reward.cost
        if reward.stock != -1:
            reward.stock -= 1

        # Lógica adicional para entregar la recompensa (ej. notificar al admin, enviar un código, etc.)
        # For now, just log it. A real system would integrate with an external reward fulfillment.
        logger.info(f"User {user_id} successfully purchased reward {reward.name} (ID: {reward_id}) for {reward.cost} points.")

        await self.session.commit()
        await self.session.refresh(user)
        await self.session.refresh(reward) # Refresh reward to show updated stock
        return True, "Compra exitosa. ¡Disfruta tu recompensa!"

    async def create_reward(self, name: str, description: str, cost: int, stock: int = -1) -> Reward:
        new_reward = Reward(name=name, description=description, cost=cost, stock=stock)
        self.session.add(new_reward)
        await self.session.commit()
        await self.session.refresh(new_reward)
        logger.info(f"New reward '{name}' created by admin.")
        return new_reward

    async def toggle_reward_status(self, reward_id: int, status: bool) -> bool:
        reward = await self.session.get(Reward, reward_id)
        if reward:
            reward.is_active = status
            await self.session.commit()
            logger.info(f"Reward '{reward.name}' status set to {status}.")
            return True
        logger.warning(f"Failed to toggle status for reward {reward_id}. Not found.")
        return False
