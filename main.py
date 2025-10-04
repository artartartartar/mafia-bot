import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🔑 НАСТРОЙКИ
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8276213136:AAGDPFrlROAdLsw2Bvxp9DteWHT2Pn2R0os")

# 🎮 СОЗДАЕМ БОТА
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🎯 ХРАНИЛИЩЕ ДАННЫХ
waiting_players = {}
active_game = None
night_actions = {}

# 🎯 КЛАСС ИГРЫ (упрощенная версия для примера)
class MafiaGame:
    def __init__(self):
        self.players = {}
        self.phase = "night"
        self.day_number = 1
    
    def assign_roles(self, players_count):
        if players_count == 4:
            return ["mafia", "sheriff", "doctor", "civilian"]
        elif players_count == 5:
            return ["mafia", "sheriff", "doctor", "civilian", "civilian"]
        else:
            return ["mafia", "sheriff", "doctor"] + ["civilian"] * (players_count - 3)

# 🎯 КОМАНДА /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 ПРИСОЕДИНИТЬСЯ К ИГРЕ", callback_data="join_game")],
        [InlineKeyboardButton(text="📖 ПРАВИЛА ИГРЫ", callback_data="show_rules")],
        [InlineKeyboardButton(text="👥 ИГРОКИ В ЛОББИ", callback_data="show_players")]
    ])
    
    await message.answer(
        "🎮 ДОБРО ПОЖАЛОВАТЬ В МАФИЮ!\n\n"
        "Я буду твоим ведущим в этой захватывающей игре!\n"
        "Выбирай действие:",
        reply_markup=keyboard
    )

# 🎯 ПРИСОЕДИНЕНИЕ К ИГРЕ
@dp.callback_query(F.data == "join_game")
async def join_game(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    
    waiting_players[user_id] = user_name
    players_count = len(waiting_players)
    
    await callback.answer(f"Ты в игре, {user_name}! 🎉")
    await callback.message.edit_text(
        f"✅ ТЫ В ИГРЕ!\n\n"
        f"👥 Игроков в лобби: {players_count}\n"
        f"🎯 Нужно для старта: 4 игрока\n\n"
        f"Ждем остальных... ⏳"
    )

# 🎯 ПРАВИЛА ИГРЫ
@dp.callback_query(F.data == "show_rules")
async def show_rules(callback: types.CallbackQuery):
    rules_text = (
        "📖 ПРАВИЛА МАФИИ:\n\n"
        "🎯 ЦЕЛИ:\n"
        "• 🔫 МАФИЯ: убить всех мирных\n"
        "• 👨‍🌾 МИРНЫЕ: найти мафию\n\n"
        "🌙 НОЧЬ: Мафия выбирает жертву\n"
        "☀️ ДЕНЬ: Все голосуют за изгнание\n\n"
        "⚖️ УСЛОВИЯ ПОБЕДЫ:\n"
        "• Мафия побеждает когда их >= мирных\n"
        "• Мирные побеждают когда мафия мертва"
    )
    await callback.answer(rules_text, show_alert=True)

# 🎯 ИГРОКИ В ЛОББИ
@dp.callback_query(F.data == "show_players")
async def show_players(callback: types.CallbackQuery):
    if not waiting_players:
        players_list = "Пока никого нет 😔"
    else:
        players_list = "\n".join([f"• {name}" for name in waiting_players.values()])
    
    total_players = len(waiting_players)
    await callback.answer(f"👥 ИГРОКИ В ЛОББИ:\n\n{players_list}\n\nВсего: {total_players}", show_alert=True)

# 🎯 ЗАПУСК ИГРЫ
@dp.message(Command("start_game"))
async def start_game_command(message: types.Message):
    global active_game
    
    if len(waiting_players) < 4:
        await message.answer(f"❌ Нужно минимум 4 игрока. Сейчас: {len(waiting_players)}")
        return
    
    active_game = MafiaGame()
    
    # Добавляем игроков
    for user_id, user_name in waiting_players.items():
        active_game.players[user_id] = {"name": user_name, "alive": True}
    
    # Распределяем роли
    roles = active_game.assign_roles(len(waiting_players))
    user_ids = list(active_game.players.keys())
    
    for i, user_id in enumerate(user_ids):
        if i < len(roles):
            active_game.players[user_id]["role"] = roles[i]
    
    # Отправляем роли
    for user_id, player_info in active_game.players.items():
        role = player_info["role"]
        role_text = {
            "mafia": "🔫 МАФИЯ",
            "sheriff": "👮 ШЕРИФ", 
            "doctor": "💉 ДОКТОР",
            "civilian": "👨‍🌾 МИРНЫЙ ЖИТЕЛЬ"
        }.get(role, "Неизвестная роль")
        
        try:
            await bot.send_message(user_id, f"🎭 ТВОЯ РОЛЬ: {role_text}")
        except:
            pass
    
    waiting_players.clear()
    await message.answer("🎮 Игра началась! Игроки получили роли в ЛС.")

# 🚀 ЗАПУСК БОТА
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🚀 Бот Мафия запускается на Railway...")
    print(f"🔑 Токен: {'установлен' if BOT_TOKEN else 'не найден'}")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        # Перезапуск через 10 секунд
        await asyncio.sleep(10)
        await main()

if __name__ == "__main__":
    asyncio.run(main())
