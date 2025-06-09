from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import async_sessionmaker

from services.reward_service import create_reward, list_rewards
from config import session_maker  # Asegúrate que esto esté correctamente importado

admin_router = Router()

@admin_router.message(Command("recompensas"))
async def show_rewards_menu(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Agregar recompensa", callback_data="add_reward")
    kb.button(text="📋 Ver recompensas", callback_data="list_rewards")
    await message.answer("📦 Gestión de recompensas:", reply_markup=kb.as_markup())

@admin_router.callback_query(F.data == "add_reward")
async def start_add_reward(callback: CallbackQuery):
    await callback.message.answer("🔤 Escribe el nombre de la recompensa:")
    await callback.answer()
    # Aquí deberías continuar con un FSM para completar los pasos

@admin_router.callback_query(F.data == "list_rewards")
async def handle_list_rewards(callback: CallbackQuery):
    async with session_maker() as session:
        rewards = await list_rewards(session)
    if not rewards:
        await callback.message.answer("🚫 No hay recompensas registradas.")
    else:
        text = "\n\n".join(
            [f"🎁 {r.name}\n📝 {r.description or 'Sin descripción'}\n🏅 {r.points_required} puntos" for r in rewards]
        )
        await callback.message.answer(f"📋 Lista de recompensas:\n\n{text}")
    await callback.answer()
