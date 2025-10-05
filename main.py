# -*- coding: utf-8 -*-
import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🔑 НАСТРОЙКИ
BOT_TOKEN = "8276213136:AAGDPFrlROAdLsw2Bvxp9DteWHT2Pn2R0os"

# 🎮 СОЗДАЕМ БОТА
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🎯 ХРАНИЛИЩЕ ДАННЫХ
waiting_players = {}
active_games = {}

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
        "Я бот для игры в Мафию! Присоединяйся к игре и приглашай друзей!",
        reply_markup=keyboard
    )

# 🎯 ПРИСОЕДИНЕНИЕ К ИГРЕ
@dp.callback_query(F.data == "join_game")
async def join_game(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    
    # Добавляем игрока в лобби
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
    if len(waiting_players) < 4:
        await message.answer(f"❌ Нужно минимум 4 игрока. Сейчас: {len(waiting_players)}")
        return
    
    # Создаем уникальный ID для игры
    game_id = message.chat.id
    
    # Создаем игру
    active_games[game_id] = {
        "players": {},
        "phase": "night",
        "day_number": 1
    }
    
    game = active_games[game_id]
    
    # Добавляем игроков в игру
    player_list = []
    for user_id, user_name in waiting_players.items():
        game["players"][user_id] = {
            "name": user_name,
            "role": "",
            "alive": True
        }
        player_list.append(f"• {user_name}")
    
    # Распределяем роли
    roles = []
    players_count = len(waiting_players)
    
    if players_count == 4:
        roles = ["mafia", "sheriff", "doctor", "civilian"]
    elif players_count == 5:
        roles = ["mafia", "sheriff", "doctor", "civilian", "civilian"]
    elif players_count >= 6:
        roles = ["mafia", "mafia", "sheriff", "doctor"] + ["civilian"] * (players_count - 4)
    
    random.shuffle(roles)
    
    # Назначаем роли
    user_ids = list(game["players"].keys())
    for i, user_id in enumerate(user_ids):
        if i < len(roles):
            game["players"][user_id]["role"] = roles[i]
    
    # Отправляем роли игрокам
    role_descriptions = {
        "mafia": "🔫 МАФИЯ\nТы должен устранить всех мирных жителей!",
        "sheriff": "👮 ШЕРИФ\nТы должен найти мафию!",
        "doctor": "💉 ДОКТОР\nТы можешь спасти одного игрока за ночь!",
        "civilian": "👨‍🌾 МИРНЫЙ ЖИТЕЛЬ\nНайди мафию и проголосуй против них!"
    }
    
    for user_id, player_info in game["players"].items():
        role = player_info["role"]
        role_text = role_descriptions.get(role, "Неизвестная роль")
        
        try:
            await bot.send_message(
                user_id,
                f"🎭 ТВОЯ РОЛЬ: {role_text}\n\n"
                f"Игра начинается! Удачи! 🍀"
            )
        except:
            pass  # Если не можем написать игроку
    
    # Оповещаем о начале игры
    players_text = "\n".join(player_list)
    await message.answer(
        f"🎮 ИГРА НАЧАЛАСЬ!\n\n"
        f"👥 Участники ({players_count} игроков):\n{players_text}\n\n"
        f"🌙 НОЧЬ {game['day_number']}\n"
        f"Город засыпает... Просыпается мафия!"
    )
    
    # Очищаем лобби
    waiting_players.clear()

# 🎯 СТАТУС ИГРЫ
@dp.message(Command("game_status"))
async def game_status_command(message: types.Message):
    game_id = message.chat.id
    game = active_games.get(game_id)
    
    if not game:
        await message.answer("❌ Сейчас нет активной игры")
        return
    
    alive_players = [info for info in game["players"].values() if info["alive"]]
    mafia_count = sum(1 for player in alive_players if player["role"] == "mafia")
    civilian_count = len(alive_players) - mafia_count
    
    alive_names = [player["name"] for player in alive_players]
    
    status_text = (
        f"🎮 СТАТУС ИГРЫ:\n\n"
        f"📊 Фаза: {'🌙 НОЧЬ' if game['phase'] == 'night' else '☀️ ДЕНЬ'} {game['day_number']}\n"
        f"👥 Живых игроков: {len(alive_players)}\n"
        f"🔫 Мафия: {mafia_count}\n"
        f"👨‍🌾 Мирные: {civilian_count}\n\n"
        f"🎯 Живые игроки:\n" + "\n".join([f"• {name}" for name in alive_names])
    )
    
    await message.answer(status_text)

# 🎯 ПОМОЩЬ
@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = (
        "🆘 ПОМОЩЬ:\n\n"
        "📋 КОМАНДЫ:\n"
        "• /start - начать работу с ботом\n"
        "• /start_game - начать игру (когда 4+ игроков)\n"
        "• /game_status - статус текущей игры\n"
        "• /help - эта справка\n\n"
        "🎮 КАК ИГРАТЬ:\n"
        "1. Напиши /start\n"
        "2. Нажми 'Присоединиться к игре'\n"
        "3. Жди когда наберется 4+ игроков\n"
        "4. Админ запускает игру: /start_game\n"
        "5. Получи роль в ЛС и играй!"
    )
    await message.answer(help_text)

# 🎯 ЕСЛИ ПРИСЛАЛИ ЛЮБОЕ ДРУГОЕ СООБЩЕНИЕ
@dp.message()
async def other_messages(message: types.Message):
    await message.answer("Напиши /start чтобы начать играть в Мафию! 🎮")

# 🚀 ЗАПУСК БОТА
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🎮 Бот Мафия запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
