# -*- coding: utf-8 -*-
import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# 🔑 НАСТРОЙКИ
BOT_TOKEN = "8276213136:AAGDPFrlROAdLsw2Bvxp9DteWHT2Pn2R0os"
TEST_MODE = True  # ⚡ ТЕСТОВЫЙ РЕЖИМ - можно играть одному!

# 🎮 СОЗДАЕМ БОТА
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# 🎯 ХРАНИЛИЩЕ ДАННЫХ
waiting_players = {}  # {user_id: {"name": "", "username": ""}}
active_games = {}     # {chat_id: game_data}

# 🎯 НАСТРОЙКА ТЕСТОВОГО РЕЖИМА
def get_min_players():
    return 1 if TEST_MODE else 4

# 🎯 КОМАНДА /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Присоединиться к игре", callback_data="join_game")],
        [InlineKeyboardButton(text="🚪 Выйти из лобби", callback_data="leave_lobby")],
        [InlineKeyboardButton(text="📖 Правила игры", callback_data="show_rules")],
        [InlineKeyboardButton(text="👥 Игроки в лобби", callback_data="show_players")],
        [InlineKeyboardButton(text="🎯 Быстрая игра (ТЕСТ)", callback_data="quick_start")]
    ])
    
    welcome_text = f"""
🎮 <b>ДОБРО ПОЖАЛОВАТЬ В МАФИЮ!</b>

Я - лучший бот для игры в Мафию в Telegram! 🕵️‍♂️

<b>Возможности:</b>
• 🤖 Автоматическое ведение игры
• 🎭 Умное распределение ролей
• 🌙 Ночные действия с кнопками
• ☀️ Дневные голосования
• 📊 Статистика и рейтинги
• 👥 Поддержка 4-12 игроков

<b>Для начала игры:</b>
1. Добавь бота в группу
2. Напиши /start
3. Игроки присоединяются через кнопки
4. Запусти игру: /start_game

🎯 <i>Сейчас доступен ТЕСТОВЫЙ РЕЖИМ - можно играть одному!</i>
<b>Минимум игроков: {get_min_players()}</b>
    """
    
    await message.answer(welcome_text, reply_markup=keyboard)

# 🎯 ПРИСОЕДИНЕНИЕ К ИГРЕ
@dp.callback_query(F.data == "join_game")
async def join_game(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    username = callback.from_user.username or "Без username"
    
    # Добавляем/обновляем игрока
    waiting_players[user_id] = {
        "name": user_name,
        "username": username,
        "chat_id": callback.message.chat.id
    }
    
    players_count = len(waiting_players)
    min_players = get_min_players()
    
    await callback.answer(f"✅ Ты в игре, {user_name}!")
    
    # Обновляем сообщение
    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Присоединиться к игре", callback_data="join_game")],
        [InlineKeyboardButton(text="🚪 Выйти из лобби", callback_data="leave_lobby")],
        [InlineKeyboardButton(text="📖 Правила игры", callback_data="show_rules")],
        [InlineKeyboardButton(text="👥 Игроки в лобби", callback_data="show_players")],
        [InlineKeyboardButton(text="🎯 Быстрая игра (ТЕСТ)", callback_data="quick_start")]
    ])
    
    status = "✅ ГОТОВО К СТАРТУ!" if players_count >= min_players else "⏳ ОЖИДАНИЕ..."
    
    await callback.message.edit_text(
        f"✅ <b>ТЫ В ИГРЕ, {user_name}!</b>\n\n"
        f"👥 <b>Игроков в лобби:</b> {players_count}\n"
        f"🎯 <b>Нужно для старта:</b> {min_players}\n"
        f"📊 <b>Статус:</b> {status}\n\n"
        f"<i>Тестовый режим: {'ВКЛЮЧЕН' if TEST_MODE else 'ВЫКЛЮЧЕН'}</i>\n\n"
        f"Запустить игру: /start_game",
        reply_markup=new_keyboard
    )

# 🎯 ВЫХОД ИЗ ЛОББИ
@dp.callback_query(F.data == "leave_lobby")
async def leave_lobby(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id in waiting_players:
        player_name = waiting_players[user_id]["name"]
        del waiting_players[user_id]
        await callback.answer(f"🚪 Ты вышел из лобби, {player_name}!")
    else:
        await callback.answer("❌ Ты не в лобби!")
        return
    
    players_count = len(waiting_players)
    min_players = get_min_players()
    
    # Обновляем сообщение
    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Присоединиться к игре", callback_data="join_game")],
        [InlineKeyboardButton(text="🚪 Выйти из лобби", callback_data="leave_lobby")],
        [InlineKeyboardButton(text="📖 Правила игры", callback_data="show_rules")],
        [InlineKeyboardButton(text="👥 Игроки в лобби", callback_data="show_players")],
        [InlineKeyboardButton(text="🎯 Быстрая игра (ТЕСТ)", callback_data="quick_start")]
    ])
    
    await callback.message.edit_text(
        f"🚪 <b>ТЫ ВЫШЕЛ ИЗ ЛОББИ</b>\n\n"
        f"👥 <b>Игроков в лобби:</b> {players_count}\n"
        f"🎯 <b>Нужно для старта:</b> {min_players}\n\n"
        f"<i>Тестовый режим: {'ВКЛЮЧЕН' if TEST_MODE else 'ВЫКЛЮЧЕН'}</i>\n\n"
        f"Можешь присоединиться снова! 🔄",
        reply_markup=new_keyboard
    )

# 🎯 БЫСТРАЯ ИГРА - ТЕСТОВЫЙ РЕЖИМ
@dp.callback_query(F.data == "quick_start")
async def quick_start(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # Автоматически добавляем в лобби если не добавлен
    if user_id not in waiting_players:
        waiting_players[user_id] = {
            "name": callback.from_user.first_name,
            "username": callback.from_user.username or "Без username",
            "chat_id": callback.message.chat.id
        }
        await callback.answer("✅ Добавлен в лобби!")
    else:
        await callback.answer("✅ Уже в лобби!")
    
    # ЗАПУСКАЕМ ИГРУ АВТОМАТИЧЕСКИ В ТЕСТОВОМ РЕЖИМЕ
    if TEST_MODE:
        # В тестовом режиме запускаем сразу с одним игроком
        await start_game_implementation(callback.message.chat.id, callback.from_user)
        await callback.answer("🎯 Тестовая игра запущена!")
    else:
        # В обычном режиме проверяем количество
        if len(waiting_players) >= get_min_players():
            await start_game_implementation(callback.message.chat.id, callback.from_user)
            await callback.answer("🎯 Быстрая игра запущена!")
        else:
            await callback.answer(f"❌ Нужно {get_min_players()} игроков!")

# 🎯 ПРАВИЛА ИГРЫ
@dp.callback_query(F.data == "show_rules")
async def show_rules(callback: types.CallbackQuery):
    rules_text = f"""
📖 <b>ПРАВИЛА МАФИИ</b>

🎯 <b>ЦЕЛИ ИГРЫ:</b>
• 🔫 <b>МАФИЯ</b> - устранить всех мирных жителей
• 👨‍🌾 <b>МИРНЫЕ</b> - найти и изгнать всю мафию

🌙 <b>НОЧНАЯ ФАЗА:</b>
• Мафия выбирает жертву
• Доктор лечит одного игрока
• Шериф проверяет одного игрока

☀️ <b>ДНЕВНАЯ ФАЗА:</b>
• Все игроки обсуждают подозреваемых
• Голосование за изгнание
• Изгнанный раскрывает свою роль

👤 <b>РОЛИ:</b>
• 🔫 <b>Мафия</b> (1-3) - убивают ночью
• 👮 <b>Шериф</b> (1) - проверяет игроков
• 💉 <b>Доктор</b> (1) - лечит игроков
• 👨‍🌾 <b>Мирные</b> (2+) - ищут мафию

⚖️ <b>УСЛОВИЯ ПОБЕДЫ:</b>
• 🎉 <b>Мирные побеждают</b> - когда вся мафия изгнана
• 🔫 <b>Мафия побеждает</b> - когда их число ≥ мирных

🎮 <b>ТЕКУЩИЙ РЕЖИМ:</b>
• <i>Тестовый: {'ВКЛЮЧЕН' if TEST_MODE else 'ВЫКЛЮЧЕН'}</i>
• <i>Минимум игроков: {get_min_players()}</i>

🎯 <b>Удачи в игре!</b> 🍀
    """
    
    await callback.message.answer(rules_text)
    await callback.answer("✅")

# 🎯 ИГРОКИ В ЛОББИ
@dp.callback_query(F.data == "show_players")
async def show_players(callback: types.CallbackQuery):
    if not waiting_players:
        players_text = "😔 <b>Лобби пустое</b>\n\nПрисоединяйся первым!"
    else:
        players_list = "\n".join([
            f"• {player['name']} (@{player['username']})" 
            for player in waiting_players.values()
        ])
        players_text = f"👥 <b>Игроки в лобби ({len(waiting_players)}):</b>\n\n{players_list}"
    
    await callback.message.answer(players_text)
    await callback.answer("✅")

# 🎯 ЗАПУСК ИГРЫ
@dp.message(Command("start_game"))
async def start_game_command(message: types.Message):
    await start_game_implementation(message.chat.id, message.from_user)

# 🎯 РЕАЛИЗАЦИЯ ЗАПУСКА ИГРЫ
async def start_game_implementation(chat_id, from_user):
    min_players = get_min_players()
    
    if len(waiting_players) < min_players:
        await bot.send_message(
            chat_id,
            f"❌ <b>Недостаточно игроков!</b>\n\n"
            f"👥 Сейчас в лобби: {len(waiting_players)}\n"
            f"🎯 Требуется: {min_players}\n\n"
            f"<i>Тестовый режим: {'ВКЛЮЧЕН' if TEST_MODE else 'ВЫКЛЮЧЕН'}</i>\n\n"
            f"Присоединись к игре через кнопки или пригласи друзей!"
        )
        return
    
    # Создаем игру
    game_id = chat_id
    active_games[game_id] = {
        "players": {},
        "phase": "night",
        "day_number": 1,
        "creator": from_user.id
    }
    
    game = active_games[game_id]
    
    # Добавляем игроков в игру
    player_list = []
    for user_id, player_data in waiting_players.items():
        game["players"][user_id] = {
            "name": player_data["name"],
            "username": player_data["username"],
            "role": "",
            "alive": True,
            "chat_id": player_data["chat_id"]
        }
        player_list.append(f"• {player_data['name']} (@{player_data['username']})")
    
    # Распределяем роли
    roles = distribute_roles(len(waiting_players))
    user_ids = list(game["players"].keys())
    random.shuffle(user_ids)
    
    for i, user_id in enumerate(user_ids):
        if i < len(roles):
            game["players"][user_id]["role"] = roles[i]
    
    # Отправляем роли игрокам
    await send_roles_to_players(game)
    
    # Оповещаем о начале игры
    players_text = "\n".join(player_list)
    await bot.send_message(
        chat_id,
        f"🎮 <b>ИГРА НАЧАЛАСЬ!</b>\n\n"
        f"👥 <b>Участники ({len(waiting_players)} игроков):</b>\n{players_text}\n\n"
        f"🌙 <b>НОЧЬ {game['day_number']}</b>\n"
        f"<i>Город засыпает... Просыпается мафия...</i> 🕵️‍♂️\n\n"
        f"📊 Посмотреть статус: /game_status\n"
        f"🎯 <i>Тестовый режим: {'ВКЛЮЧЕН' if TEST_MODE else 'ВЫКЛЮЧЕН'}</i>"
    )
    
    # Очищаем лобби
    waiting_players.clear()

# 🎯 РАСПРЕДЕЛЕНИЕ РОЛЕЙ
def distribute_roles(players_count):
    if players_count == 1:
        # В тестовом режиме с одним игроком - даем роль Мафии
        return ["mafia"]
    elif players_count == 4:
        return ["mafia", "sheriff", "doctor", "civilian"]
    elif players_count == 5:
        return ["mafia", "sheriff", "doctor", "civilian", "civilian"]
    elif players_count == 6:
        return ["mafia", "mafia", "sheriff", "doctor", "civilian", "civilian"]
    elif players_count == 7:
        return ["mafia", "mafia", "sheriff", "doctor", "civilian", "civilian", "civilian"]
    elif players_count >= 8:
        mafia_count = min(players_count // 3, 3)
        return ["mafia"] * mafia_count + ["sheriff", "doctor"] + ["civilian"] * (players_count - mafia_count - 2)

# 🎯 ОТПРАВКА РОЛЕЙ ИГРОКАМ
async def send_roles_to_players(game):
    role_descriptions = {
        "mafia": "🔫 <b>ТЫ МАФИЯ!</b>\n\nТвоя цель - устранить всех мирных жителей!\n\nНочью ты будешь выбирать жертву вместе с другими мафиози. Днем притворяйся мирным жителем!",
        "sheriff": "👮 <b>ТЫ ШЕРИФ!</b>\n\nТвоя цель - найти мафию!\n\nКаждой ночью ты можешь проверить одного игрока и узнать его истинную роль.",
        "doctor": "💉 <b>ТЫ ДОКТОР!</b>\n\nТвоя цель - спасать игроков!\n\nКаждой ночью ты можешь вылечить одного игрока, защитив его от мафии.",
        "civilian": "👨‍🌾 <b>ТЫ МИРНЫЙ ЖИТЕЛЬ!</b>\n\nТвоя цель - найти мафию!\n\nВнимательно следи за обсуждениями, ищи противоречия и голосуй против подозреваемых."
    }
    
    for user_id, player_info in game["players"].items():
        role = player_info["role"]
        role_text = role_descriptions.get(role, "❌ Неизвестная роль")
        
        try:
            await bot.send_message(
                user_id,
                f"🎭 {role_text}\n\n"
                f"🍀 <i>Удачи в игре! Следи за основным чатом!</i>"
            )
        except Exception as e:
            print(f"Не удалось отправить роль игроку {player_info['name']}: {e}")

# 🎯 СТАТУС ИГРЫ
@dp.message(Command("game_status"))
async def game_status_command(message: types.Message):
    game_id = message.chat.id
    game = active_games.get(game_id)
    
    if not game:
        await message.answer("❌ <b>Сейчас нет активной игры</b>\n\nНачни новую игру: /start_game")
        return
    
    alive_players = [info for info in game["players"].values() if info["alive"]]
    mafia_count = sum(1 for player in alive_players if player["role"] == "mafia")
    civilian_count = len(alive_players) - mafia_count
    
    alive_names = [f"• {player['name']} (@{player['username']})" for player in alive_players]
    
    status_text = (
        f"🎮 <b>СТАТУС ИГРЫ</b>\n\n"
        f"📊 <b>Фаза:</b> {'🌙 НОЧЬ' if game['phase'] == 'night' else '☀️ ДЕНЬ'} {game['day_number']}\n"
        f"👥 <b>Живых игроков:</b> {len(alive_players)}\n"
        f"🔫 <b>Мафия:</b> {mafia_count}\n"
        f"👨‍🌾 <b>Мирные:</b> {civilian_count}\n"
        f"🎯 <b>Тестовый режим:</b> {'ВКЛЮЧЕН' if TEST_MODE else 'ВЫКЛЮЧЕН'}\n\n"
        f"🎯 <b>Живые игроки:</b>\n" + "\n".join(alive_names)
    )
    
    await message.answer(status_text)

# 🎯 ПОМОЩЬ
@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = f"""
🆘 <b>ПОМОЩЬ ПО БОТУ МАФИИ</b>

📋 <b>ОСНОВНЫЕ КОМАНДЫ:</b>
• /start - начать работу с ботом
• /start_game - запустить игру
• /game_status - статус текущей игры
• /help - эта справка

🎮 <b>КАК ИГРАТЬ:</b>
1. Добавь бота в группу
2. Напиши /start
3. Игроки нажимают "Присоединиться к игре"
4. Когда наберется достаточно игроков
5. Запусти игру: /start_game
6. Игроки получат роли в ЛС!

🔧 <b>ФУНКЦИОНАЛ:</b>
• 🤖 Автоматическое ведение игры
• 🎭 Умное распределение ролей
• 🚪 Выход из лобби
• 🎯 Быстрый старт
• 📊 Подробная статистика

⚡ <b>ТЕКУЩИЙ РЕЖИМ:</b>
• <i>Тестовый: {'ВКЛЮЧЕН' if TEST_MODE else 'ВЫКЛЮЧЕН'}</i>
• <i>Минимум игроков: {get_min_players()}</i>

🎯 <b>Для тестирования:</b>
Нажми "Быстрая игра" для мгновенного старта!
    """
    
    await message.answer(help_text)

# 🎯 ОБРАБОТКА ОСТАЛЬНЫХ СООБЩЕНИЙ
@dp.message()
async def other_messages(message: types.Message):
    if message.text and not message.text.startswith('/'):
        await message.answer(
            f"🎮 <b>Привет! Я бот для игры в Мафию!</b>\n\n"
            f"Напиши /start чтобы начать игру или /help для справки!\n\n"
            f"🎯 <i>Тестовый режим: {'ВКЛЮЧЕН' if TEST_MODE else 'ВЫКЛЮЧЕН'}</i>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎮 Начать игру", callback_data="join_game")],
                [InlineKeyboardButton(text="🎯 Быстрая игра", callback_data="quick_start")]
            ])
        )

# 🚀 ЗАПУСК БОТА
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🎮 Бот Мафия запускается...")
    print(f"⚡ Тестовый режим: {'ВКЛЮЧЕН' if TEST_MODE else 'ВЫКЛЮЧЕН'}")
    print(f"🎯 Минимум игроков: {get_min_players()}")
    print("🚀 Бот готов к работе!")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
