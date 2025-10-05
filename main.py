# -*- coding: utf-8 -*-
import os
import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🔑 НАСТРОЙКИ
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8276213136:AAGDPFrlROAdLsw2Bvxp9DteWHT2Pn2R0os")
TEST_MODE = True  # ⬅️ ВКЛЮЧИ ТЕСТОВЫЙ РЕЖИМ!

# 🎮 СОЗДАЕМ БОТА
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🎯 ХРАНИЛИЩЕ ДАННЫХ
waiting_players = {}
active_game = None
night_actions = {}

# 🎯 КЛАСС ИГРЫ
class MafiaGame:
    def __init__(self):
        self.players = {}
        self.phase = "night"
        self.day_number = 1
        self.mafia_target = None
        self.doctor_target = None
        self.sheriff_check = None
        self.votes = {}
    
    def assign_roles(self, players_count):
        roles = []
        if players_count == 1:  # Тестовый режим для одного игрока
            return ["mafia", "sheriff", "doctor", "civilian"]
        elif players_count == 4:
            roles = ["mafia", "sheriff", "doctor", "civilian"]
        elif players_count == 5:
            roles = ["mafia", "sheriff", "doctor", "civilian", "civilian"]
        elif players_count == 6:
            roles = ["mafia", "mafia", "sheriff", "doctor", "civilian", "civilian"]
        else:
            roles = ["mafia", "sheriff", "doctor"] + ["civilian"] * (players_count - 3)
        
        random.shuffle(roles)
        return roles
    
    def get_alive_players_info(self):
        return {uid: info for uid, info in self.players.items() if info["alive"]}
    
    def check_win_condition(self):
        alive_players = self.get_alive_players_info()
        mafia_count = sum(1 for info in alive_players.values() if info["role"] == "mafia")
        civilian_count = len(alive_players) - mafia_count
        
        if mafia_count == 0:
            return "civilians"
        elif mafia_count >= civilian_count:
            return "mafia"
        return None

    async def start_night(self):
        self.phase = "night"
        night_actions.clear()
        
        # Рассылаем ночные действия
        for user_id, player_info in self.get_alive_players_info().items():
            role = player_info["role"]
            
            if role == "mafia":
                await self.send_mafia_action(user_id)
            elif role == "doctor":
                await self.send_doctor_action(user_id)
            elif role == "sheriff":
                await self.send_sheriff_action(user_id)
    
    async def send_mafia_action(self, user_id):
        alive_players = self.get_alive_players_info()
        targets = {uid: info for uid, info in alive_players.items() if info["role"] != "mafia"}
        
        if not targets:
            return
            
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=info["name"], callback_data=f"mafia_kill:{uid}")]
            for uid, info in targets.items()
        ])
        
        try:
            await bot.send_message(
                user_id,
                "🔫 МАФИЯ, ПРОСЫПАЙТЕСЬ!\n\nВыберите игрока для устранения:",
                reply_markup=keyboard
            )
        except:
            pass

    async def send_doctor_action(self, user_id):
        alive_players = self.get_alive_players_info()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=info["name"], callback_data=f"doctor_heal:{uid}")]
            for uid, info in alive_players.items()
        ])
        
        try:
            await bot.send_message(
                user_id,
                "💉 ДОКТОР, ПРОСЫПАЙТЕСЬ!\n\nВыберите игрока для лечения:",
                reply_markup=keyboard
            )
        except:
            pass

    async def send_sheriff_action(self, user_id):
        alive_players = self.get_alive_players_info()
        targets = {uid: info for uid, info in alive_players.items() if uid != user_id}
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=info["name"], callback_data=f"sheriff_check:{uid}")]
            for uid, info in targets.items()
        ])
        
        try:
            await bot.send_message(
                user_id,
                "👮 ШЕРИФ, ПРОСЫПАЙСЯ!\n\nВыберите игрока для проверки:",
                reply_markup=keyboard
            )
        except:
            pass

    async def process_night_actions(self):
        # Обрабатываем действия
        mafia_votes = {}
        doctor_votes = {}
        sheriff_votes = {}
        
        for action in night_actions.values():
            action_type, target_id = action
            if action_type == "mafia_kill":
                mafia_votes[target_id] = mafia_votes.get(target_id, 0) + 1
            elif action_type == "doctor_heal":
                doctor_votes[target_id] = doctor_votes.get(target_id, 0) + 1
            elif action_type == "sheriff_check":
                sheriff_votes[target_id] = sheriff_votes.get(target_id, 0) + 1
        
        # Определяем цели
        self.mafia_target = max(mafia_votes.items(), key=lambda x: x[1])[0] if mafia_votes else None
        self.doctor_target = max(doctor_votes.items(), key=lambda x: x[1])[0] if doctor_votes else None
        self.sheriff_check = max(sheriff_votes.items(), key=lambda x: x[1])[0] if sheriff_votes else None
        
        # Применяем действия
        killed_player = None
        if self.mafia_target and self.mafia_target != self.doctor_target:
            self.players[self.mafia_target]["alive"] = False
            killed_player = self.players[self.mafia_target]["name"]
        
        # Результаты шерифа
        sheriff_result = None
        if self.sheriff_check:
            checked_role = self.players[self.sheriff_check]["role"]
            sheriff_result = "мафия" if checked_role == "mafia" else "мирный житель"
            
            # Сообщаем шерифу результат
            sheriff_user_id = next((uid for uid, info in self.players.items() if info["role"] == "sheriff" and info["alive"]), None)
            if sheriff_user_id:
                try:
                    checked_name = self.players[self.sheriff_check]["name"]
                    await bot.send_message(
                        sheriff_user_id,
                        f"👮 РЕЗУЛЬТАТ ПРОВЕРКИ:\n\nИгрок {checked_name} - {sheriff_result}"
                    )
                except:
                    pass
        
        return killed_player

    async def start_day(self):
        self.phase = "day"
        self.votes.clear()
        
        # Отправляем кнопки для голосования
        for user_id in self.get_alive_players_info().keys():
            await self.send_voting_keyboard(user_id)
    
    async def send_voting_keyboard(self, user_id):
        alive_players = self.get_alive_players_info()
        targets = {uid: info for uid, info in alive_players.items() if uid != user_id}
        
        if not targets:
            return
            
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=info["name"], callback_data=f"vote:{uid}")]
            for uid, info in targets.items()
        ])
        
        try:
            await bot.send_message(
                user_id,
                "🗳️ ГОЛОСОВАНИЕ\n\nВыберите игрока для изгнания:",
                reply_markup=keyboard
            )
        except:
            pass

    async def process_voting(self):
        if not self.votes:
            return None
        
        # Подсчитываем голоса
        vote_count = {}
        for target_id in self.votes.values():
            vote_count[target_id] = vote_count.get(target_id, 0) + 1
        
        # Находим игрока с наибольшим количеством голосов
        max_votes = max(vote_count.values())
        candidates = [target_id for target_id, votes in vote_count.items() if votes == max_votes]
        
        if len(candidates) > 1:
            return None
        
        exiled_id = candidates[0]
        exiled_player = self.players[exiled_id]
        exiled_player["alive"] = False
        
        return exiled_player

# 🎯 КОМАНДА /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 ПРИСОЕДИНИТЬСЯ К ИГРЕ", callback_data="join_game")],
        [InlineKeyboardButton(text="📖 ПРАВИЛА ИГРЫ", callback_data="show_rules")],
        [InlineKeyboardButton(text="👥 ИГРОКИ В ЛОББИ", callback_data="show_players")],
        [InlineKeyboardButton(text="🧪 ТЕСТОВЫЙ РЕЖИМ", callback_data="test_mode")]
    ])
    
    await message.answer(
        "🎮 ДОБРО ПОЖАЛОВАТЬ В МАФИЮ!\n\n"
        "Я буду твоим ведущим в этой захватывающей игре!\n"
        "Выбирай действие:\n\n"
        "🧪 <b>Тестовый режим</b> - можешь тестировать один\n"
        "👥 <b>Обычная игра</b> - нужно 4+ игроков",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# 🎯 ПРИСОЕДИНЕНИЕ К ИГРЕ
@dp.callback_query(F.data == "join_game")
async def join_game(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    
    waiting_players[user_id] = user_name
    players_count = len(waiting_players)
    
    # Обновляем сообщение с новой кнопкой
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 ОБНОВИТЬ СПИСОК ИГРОКОВ", callback_data="show_players")],
        [InlineKeyboardButton(text="📖 ПРАВИЛА ИГРЫ", callback_data="show_rules")],
        [InlineKeyboardButton(text="🚪 ВЫЙТИ ИЗ ЛОББИ", callback_data="leave_lobby")]
    ])
    
    await callback.answer(f"Ты в игре, {user_name}! 🎉")
    await callback.message.edit_text(
        f"✅ ТЫ В ИГРЕ!\n\n"
        f"👥 Игроков в лобби: <b>{players_count}</b>\n"
        f"🎯 Нужно для старта: 4 игрока\n\n"
        f"Ждем остальных... ⏳\n\n"
        f"Админ может запустить игру: /start_game\n"
        f"Или используй тестовый режим!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# 🎯 ВЫХОД ИЗ ЛОББИ
@dp.callback_query(F.data == "leave_lobby")
async def leave_lobby(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    
    if user_id in waiting_players:
        del waiting_players[user_id]
    
    await callback.answer(f"Ты вышел из лобби, {user_name}!")
    
    # Возвращаем к главному меню
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 ПРИСОЕДИНИТЬСЯ К ИГРЕ", callback_data="join_game")],
        [InlineKeyboardButton(text="📖 ПРАВИЛА ИГРЫ", callback_data="show_rules")],
        [InlineKeyboardButton(text="👥 ИГРОКИ В ЛОББИ", callback_data="show_players")],
        [InlineKeyboardButton(text="🧪 ТЕСТОВЫЙ РЕЖИМ", callback_data="test_mode")]
    ])
    
    await callback.message.edit_text(
        "🎮 ДОБРО ПОЖАЛОВАТЬ В МАФИЮ!\n\n"
        "Я буду твоим ведущим в этой захватывающей игре!\n"
        "Выбирай действие:",
        reply_markup=keyboard
    )

# 🎯 ПРАВИЛА ИГРЫ
@dp.callback_query(F.data == "show_rules")
async def show_rules(callback: types.CallbackQuery):
    rules_text = (
        "📖 ПРАВИЛА МАФИИ:\n\n"
        "🎯 ЦЕЛИ:\n"
        "• 🔫 МАФИЯ: убить всех мирных\n"
        "• 👨‍🌾 МИРНЫЕ: найти мафию\n\n"
        "🌙 НОЧЬ:\n"
        "• Мафия выбирает жертву\n"
        "• Доктор лечит игрока\n"
        "• Шериф проверяет игрока\n\n"
        "☀️ ДЕНЬ:\n"
        "• Все обсуждают и голосуют\n"
        "• Изгнанный раскрывает роль\n\n"
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
    
    # Если пользователь в лобби, показываем обновленное сообщение
    if callback.from_user.id in waiting_players:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 ОБНОВИТЬ СПИСОК ИГРОКОВ", callback_data="show_players")],
            [InlineKeyboardButton(text="📖 ПРАВИЛА ИГРЫ", callback_data="show_rules")],
            [InlineKeyboardButton(text="🚪 ВЫЙТИ ИЗ ЛОББИ", callback_data="leave_lobby")]
        ])
        
        await callback.message.edit_text(
            f"✅ ТЫ В ИГРЕ!\n\n"
            f"👥 Игроков в лобби: <b>{total_players}</b>\n"
            f"🎯 Нужно для старта: 4 игрока\n\n"
            f"<b>Список игроков:</b>\n{players_list}\n\n"
            f"Ждем остальных... ⏳",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
    else:
        await callback.answer(f"👥 ИГРОКИ В ЛОББИ:\n\n{players_list}\n\nВсего: {total_players}", show_alert=True)

# 🎯 ТЕСТОВЫЙ РЕЖИМ
@dp.callback_query(F.data == "test_mode")
async def test_mode(callback: types.CallbackQuery):
    global active_game
    
    if active_game:
        await callback.answer("❌ Игра уже идет! Дождитесь окончания.", show_alert=True)
        return
    
    # Создаем тестовых игроков
    test_players = {
        111: {"name": "🔫 Мафия_Тест", "alive": True},
        222: {"name": "👮 Шериф_Тест", "alive": True},
        333: {"name": "💉 Доктор_Тест", "alive": True},
        444: {"name": "👨‍🌾 Мирный_Тест", "alive": True}
    }
    
    # Создаем игру
    active_game = MafiaGame()
    active_game.players = test_players
    
    # Распределяем роли
    roles = ["mafia", "sheriff", "doctor", "civilian"]
    user_ids = list(active_game.players.keys())
    
    for i, user_id in enumerate(user_ids):
        if i < len(roles):
            active_game.players[user_id]["role"] = roles[i]
    
    # Отправляем роли тестовому игроку
    role_info = "\n".join([f"• {info['name']} - {info['role']}" for info in active_game.players.values()])
    
    await callback.message.answer(
        f"🧪 ТЕСТОВЫЙ РЕЖИМ АКТИВИРОВАН!\n\n"
        f"<b>Тестовые игроки:</b>\n{role_info}\n\n"
        f"Ты играешь за ВСЕХ игроков сразу!\n"
        f"Сейчас получишь ночные действия для каждой роли...",
        parse_mode="HTML"
    )
    
    # Запускаем игру
    asyncio.create_task(game_loop())
    
    await callback.answer("Тестовый режим запущен! 🧪")

# 🎯 ЗАПУСК ИГРЫ
@dp.message(Command("start_game"))
async def start_game_command(message: types.Message):
    global active_game
    
    if active_game:
        await message.answer("❌ Игра уже идет! Дождитесь окончания.")
        return
        
    if len(waiting_players) < 4 and not TEST_MODE:
        await message.answer(f"❌ Нужно минимум 4 игрока. Сейчас: {len(waiting_players)}")
        return
    
    # СОЗДАЕМ НОВУЮ ИГРУ
    active_game = MafiaGame()
    
    # ДОБАВЛЯЕМ ИГРОКОВ
    player_list = []
    for user_id, user_name in waiting_players.items():
        active_game.players[user_id] = {
            "name": user_name,
            "role": "",
            "alive": True
        }
        player_list.append(f"• {user_name}")
    
    # РАСПРЕДЕЛЯЕМ РОЛИ
    roles = active_game.assign_roles(len(waiting_players))
    user_ids = list(active_game.players.keys())
    
    for i, user_id in enumerate(user_ids):
        if i < len(roles):
            active_game.players[user_id]["role"] = roles[i]
    
    # ОТПРАВЛЯЕМ РОЛИ
    for user_id, player_info in active_game.players.items():
        role = player_info["role"]
        role_text = {
            "mafia": "🔫 МАФИЯ\nТы должен устранить всех мирных жителей!",
            "sheriff": "👮 ШЕРИФ\nТы должен найти мафию!",
            "doctor": "💉 ДОКТОР\nТы можешь спасти одного игрока за ночь!",
            "civilian": "👨‍🌾 МИРНЫЙ ЖИТЕЛЬ\nНайди мафию и проголосуй против них!"
        }.get(role, "Неизвестная роль")
        
        try:
            await bot.send_message(user_id, f"🎭 ТВОЯ РОЛЬ: {role_text}")
        except:
            pass
    
    waiting_players.clear()
    
    # ЗАПУСКАЕМ ИГРУ
    asyncio.create_task(game_loop())
    
    await message.answer("🎮 Игра началась! Игроки получили роли. Начинается ночь...")

# 🎯 АВТОМАТИЧЕСКИЙ ИГРОВОЙ ЦИКЛ
async def game_loop():
    global active_game
    
    if not active_game:
        return
    
    while active_game:
        # НОЧНАЯ ФАЗА (30 секунд)
        await active_game.start_night()
        await asyncio.sleep(30)
        
        killed_player = await active_game.process_night_actions()
        
        # Оповещаем о результатах ночи
        if killed_player:
            for user_id in active_game.players.keys():
                try:
                    await bot.send_message(user_id, f"🌙 РЕЗУЛЬТАТЫ НОЧИ:\n\n☠️ Жертва мафии: {killed_player}")
                except:
                    pass
        else:
            for user_id in active_game.players.keys():
                try:
                    await bot.send_message(user_id, f"🌙 РЕЗУЛЬТАТЫ НОЧИ:\n\n✅ Этой ночью никто не погиб")
                except:
                    pass
        
        # Проверяем победу
        winner = active_game.check_win_condition()
        if winner:
            await end_game(winner)
            break
        
        # ДНЕВНАЯ ФАЗА (30 секунд)
        await active_game.start_day()
        await asyncio.sleep(30)
        
        exiled_player = await active_game.process_voting()
        
        # Оповещаем о результатах голосования
        if exiled_player:
            role_text = {
                "mafia": "🔫 МАФИЯ",
                "sheriff": "👮 ШЕРИФ", 
                "doctor": "💉 ДОКТОР",
                "civilian": "👨‍🌾 МИРНЫЙ ЖИТЕЛЬ"
            }
            for user_id in active_game.players.keys():
                try:
                    await bot.send_message(
                        user_id,
                        f"⚖️ РЕЗУЛЬТАТ ГОЛОСОВАНИЯ:\n\n"
                        f"Изгнан: {exiled_player['name']}\n"
                        f"Роль: {role_text.get(exiled_player['role'], 'Неизвестно')}"
                    )
                except:
                    pass
        else:
            for user_id in active_game.players.keys():
                try:
                    await bot.send_message(user_id, "🤝 Ничья! Никто не изгнан.")
                except:
                    pass
        
        # Проверяем победу
        winner = active_game.check_win_condition()
        if winner:
            await end_game(winner)
            break
        
        active_game.day_number += 1

async def end_game(winner):
    global active_game
    
    winner_text = "🔫 ПОБЕДА МАФИИ!" if winner == "mafia" else "🎉 ПОБЕДА МИРНЫХ ЖИТЕЛЕЙ!"
    
    role_text = {
        "mafia": "🔫 МАФИЯ",
        "sheriff": "👮 ШЕРИФ",
        "doctor": "💉 ДОКТОР", 
        "civilian": "👨‍🌾 МИРНЫЙ ЖИТЕЛЬ"
    }
    
    # Формируем список игроков и их ролей
    players_info = "\n".join([
        f"• {info['name']} - {role_text.get(info['role'], 'Неизвестно')} {'☠️' if not info['alive'] else '✅'}"
        for info in active_game.players.values()
    ])
    
    # Рассылаем результаты
    for user_id in active_game.players.keys():
        try:
            await bot.send_message(
                user_id,
                f"🎮 ИГРА ОКОНЧЕНА!\n\n"
                f"{winner_text}\n\n"
                f"📊 ИТОГИ:\n{players_info}\n\n"
                f"Спасибо за игру! 🎉\n"
                f"Для новой игры напишите /start"
            )
        except:
            pass
    
    active_game = None

# 🎯 КОМАНДА СТАТУСА
@dp.message(Command("game_status"))
async def game_status_command(message: types.Message):
    if not active_game:
        await message.answer("❌ Сейчас нет активной игры")
        return
    
    alive_players = active_game.get_alive_players_info()
    mafia_count = sum(1 for info in alive_players.values() if info["role"] == "mafia")
    civilian_count = len(alive_players) - mafia_count
    
    status_text = (
        f"🎮 СТАТУС ИГРЫ:\n\n"
        f"📊 Фаза: {'🌙 НОЧЬ' if active_game.phase == 'night' else '☀️ ДЕНЬ'} {active_game.day_number}\n"
        f"👥 Живых игроков: {len(alive_players)}\n"
        f"🔫 Мафия: {mafia_count}\n"
        f"👨‍🌾 Мирные: {civilian_count}\n\n"
        f"🎯 Живые игроки:\n" + "\n".join([f"• {info['name']}" for info in alive_players.values()])
    )
    
    await message.answer(status_text)

# 🎯 КОМАНДА СБРОСА
@dp.message(Command("reset"))
async def reset_command(message: types.Message):
    global active_game, waiting_players
    active_game = None
    waiting_players.clear()
    await message.answer("🔄 Игра сброшена! Можно начинать заново.")

# 🎯 КОМАНДА ПОМОЩИ
@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = (
        "🎮 КОМАНДЫ БОТА МАФИЯ:\n\n"
        "👤 <b>Для игроков:</b>\n"
        "/start - начать игру\n"
        "/help - показать эту справку\n\n"
        "🛠️ <b>Для администратора:</b>\n"
        "/start_game - начать игру (когда 4+ игроков)\n"
        "/game_status - статус текущей игры\n"
        "/reset - сбросить игру\n\n"
        "🎯 <b>Игровой процесс:</b>\n"
        "1. Игроки пишут /start и присоединяются\n"
        "2. Админ пишет /start_game\n"
        "3. Автоматически начинается игра!\n\n"
        "🧪 <b>Тестовый режим:</b>\n"
        "Можешь тестировать один через кнопку 'Тестовый режим'",
        parse_mode="HTML"
    )
    await message.answer(help_text)

# 🎯 НОЧНЫЕ ДЕЙСТВИЯ И ГОЛОСОВАНИЕ (остаются без изменений)
@dp.callback_query(F.data.startswith("mafia_kill:"))
async def mafia_kill(callback: types.CallbackQuery):
    if not active_game or active_game.phase != "night":
        await callback.answer("❌ Сейчас не ночь!", show_alert=True)
        return
    
    target_id = int(callback.data.split(":")[1])
    player_info = active_game.players.get(callback.from_user.id)
    
    if not player_info or player_info["role"] != "mafia" or not player_info["alive"]:
        await callback.answer("❌ Ты не мафия или мертв!", show_alert=True)
        return
    
    night_actions[callback.from_user.id] = ("mafia_kill", target_id)
    target_name = active_game.players[target_id]["name"]
    
    await callback.answer(f"✅ Выбрана жертва: {target_name}", show_alert=False)
    await callback.message.edit_text(f"🔫 Ты выбрал жертву: {target_name}")

@dp.callback_query(F.data.startswith("doctor_heal:"))
async def doctor_heal(callback: types.CallbackQuery):
    if not active_game or active_game.phase != "night":
        await callback.answer("❌ Сейчас не ночь!", show_alert=True)
        return
    
    target_id = int(callback.data.split(":")[1])
    player_info = active_game.players.get(callback.from_user.id)
    
    if not player_info or player_info["role"] != "doctor" or not player_info["alive"]:
        await callback.answer("❌ Ты не доктор или мертв!", show_alert=True)
        return
    
    night_actions[callback.from_user.id] = ("doctor_heal", target_id)
    target_name = active_game.players[target_id]["name"]
    
    await callback.answer(f"💉 Лечишь: {target_name}", show_alert=False)
    await callback.message.edit_text(f"💉 Ты лечишь: {target_name}")

@dp.callback_query(F.data.startswith("sheriff_check:"))
async def sheriff_check(callback: types.CallbackQuery):
    if not active_game or active_game.phase != "night":
        await callback.answer("❌ Сейчас не ночь!", show_alert=True)
        return
    
    target_id = int(callback.data.split(":")[1])
    player_info = active_game.players.get(callback.from_user.id)
    
    if not player_info or player_info["role"] != "sheriff" or not player_info["alive"]:
        await callback.answer("❌ Ты не шериф или мертв!", show_alert=True)
        return
    
    night_actions[callback.from_user.id] = ("sheriff_check", target_id)
    target_name = active_game.players[target_id]["name"]
    
    await callback.answer(f"👮 Проверяешь: {target_name}", show_alert=False)
    await callback.message.edit_text(f"👮 Ты проверяешь: {target_name}")

@dp.callback_query(F.data.startswith("vote:"))
async def vote_player(callback: types.CallbackQuery):
    if not active_game or active_game.phase != "day":
        await callback.answer("❌ Сейчас не день!", show_alert=True)
        return
    
    target_id = int(callback.data.split(":")[1])
    player_info = active_game.players.get(callback.from_user.id)
    
    if not player_info or not player_info["alive"]:
        await callback.answer("❌ Ты мертв и не можешь голосовать!", show_alert=True)
        return
    
    if target_id == callback.from_user.id:
        await callback.answer("❌ Нельзя голосовать за себя!", show_alert=True)
        return
    
    active_game.votes[callback.from_user.id] = target_id
    target_name = active_game.players[target_id]["name"]
    
    await callback.answer(f"🗳️ Голос за: {target_name}", show_alert=False)
    await callback.message.edit_text(f"🗳️ Ты проголосовал за: {target_name}")

# 🚀 ЗАПУСК БОТА
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🎮 Бот Мафия запускается...")
    print("🧪 Тестовый режим: ВКЛЮЧЕН" if TEST_MODE else "Тестовый режим: ВЫКЛЮЧЕН")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
