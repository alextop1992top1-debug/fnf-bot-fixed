import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from core.database import database
from game.engine import game_engine
from game.battle import battle_system
from content.story import get_story_scene, get_available_chapters
import config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class FNFMMOBot:
    def __init__(self):
        self.application = Application.builder().token(config.BOT_TOKEN).build()
        self.setup_handlers()
        self.user_battles = {}  # {user_id: battle_data}
        
    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("play", self.play))
        self.application.add_handler(CommandHandler("profile", self.profile))
        self.application.add_handler(CommandHandler("inventory", self.inventory))
        self.application.add_handler(CommandHandler("achievements", self.achievements))
        self.application.add_handler(CommandHandler("quests", self.quests))
        self.application.add_handler(CommandHandler("battle", self.battle))
        self.application.add_handler(CommandHandler("story", self.story))
        self.application.add_handler(CommandHandler("daily", self.daily))
        
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        player = database.get_player(user.id)
        
        if not player:
            # Создаем нового игрока
            player = database.create_player(user.id, user.username, user.first_name)
            await update.message.reply_text(
                f"🎮 *Добро пожаловать в Friday Night Funkin MMO!*\n\n"
                f"Привет, {user.first_name}! Я твой проводник в мире ритм-баттлов и драматических историй.\n\n"
                f"*Твоё приключение начинается сейчас!* 🎵\n\n"
                f"Используй команды:\n"
                f"/play - Начать игру\n"
                f"/profile - Твой профиль\n"
                f"/story - Продолжить сюжет\n"
                f"/battle - Ритм-баттлы\n"
                f"/quests - Задания\n"
                f"/achievements - Достижения\n"
                f"/inventory - Инвентарь\n"
                f"/daily - Ежедневные задания",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"С возвращением, {player['character_name']}! 🎸\n\n"
                f"Уровень: {player['level']} | Энергия: {player['energy']}/{player['max_energy']}\n"
                f"Деньги: {player['money']} 💰 | Опыт: {player['exp']} ⭐\n\n"
                f"Что будем делать сегодня?",
                reply_markup=self.get_main_menu_keyboard()
            )
    
    async def play(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        player = database.get_player(user.id)
        
        if not player:
            await update.message.reply_text("Сначала зарегистрируйся с помощью /start")
            return
            
        await update.message.reply_text(
            f"🎯 *Главное меню* - {player['character_name']}\n\n"
            f"Выбери действие:",
            reply_markup=self.get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        progress = game_engine.get_player_progress(user.id)
        
        if not progress:
            await update.message.reply_text("Игрок не найден! Используй /start")
            return
            
        player = progress['player']
        stats = player['stats'] or {}
        
        text = (
            f"👤 *Профиль {player['character_name']}*\n\n"
            f"🎯 Уровень: {player['level']}\n"
            f"⭐ Опыт: {player['exp']}\n"
            f"❤️ Здоровье: {player['health']}/{player['max_health']}\n"
            f"⚡ Энергия: {player['energy']}/{player['max_energy']}\n"
            f"💰 Деньги: {player['money']}\n\n"
            f"📊 Навыки:\n"
            f"🎵 Ритм: {player['rhythm']}\n"
            f"💬 Харизма: {player['charisma']}\n"
            f"💪 Сила: {player['strength']}\n\n"
            f"🏆 Статистика:\n"
            f"⚔️ Битв: {stats.get('total_battles', 0)}\n"
            f"✅ Побед: {stats.get('battles_won', 0)}\n"
            f"⭐ Идеально: {stats.get('perfect_scores', 0)}\n"
            f"🔥 Макс комбо: {stats.get('max_combo', 0)}\n"
            f"📜 Квестов: {stats.get('quests_completed', 0)}\n\n"
            f"🎮 Игровое время: {progress['play_time']['total']} минут"
        )
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def story(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        player = database.get_player(user.id)
        
        if not player:
            await update.message.reply_text("Сначала зарегистрируйся с помощью /start")
            return
            
        available_chapters = get_available_chapters(player['level'])
        
        if not available_chapters:
            await update.message.reply_text("Тебе нужно повысить уровень для доступа к новым главам!")
            return
            
        keyboard = []
        for chapter_id in available_chapters:
            scene = get_story_scene(chapter_id, "intro")
            if scene:
                keyboard.append([InlineKeyboardButton(
                    f"📖 {scene['text'][:30]}...", 
                    callback_data=f"story_{chapter_id}_intro"
                )])
        
        await update.message.reply_text(
            "📚 *Выбери главу для продолжения:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def battle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        player = database.get_player(user.id)
        
        if not player:
            await update.message.reply_text("Сначала зарегистрируйся с помощью /start")
            return
            
        available_songs = []
        for song_id, song in battle_system.songs.items():
            if player['level'] >= song['difficulty'] * 2:
                available_songs.append(song_id)
        
        if not available_songs:
            await update.message.reply_text("Тебе нужно повысить уровень для доступа к битвам!")
            return
            
        keyboard = []
        for song_id in available_songs:
            song = battle_system.songs[song_id]
            keyboard.append([InlineKeyboardButton(
                f"🎵 {song['name']} (⚡{song['energy_cost']})",
                callback_data=f"battle_start_{song_id}"
            )])
            
        await update.message.reply_text(
            "🎸 *Выбери песню для битвы:*\n\n"
            "⚡ - стоимость энергии",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def achievements(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        progress = game_engine.get_player_progress(user.id)
        
        if not progress:
            await update.message.reply_text("Игрок не найден!")
            return
            
        achievements = progress['achievements']
        
        text = f"🏆 *Достижения* - {progress['player']['character_name']}\n\n"
        text += f"Завершено: {achievements['completed']}/{achievements['total']} ({achievements['completion_percentage']}%)\n\n"
        
        for achievement in achievements['list'][:10]:  # Показываем первые 10
            status = "✅" if achievement['completed'] else "🔄"
            text += f"{status} *{achievement['achievement_name']}*\n"
            text += f"   {achievement['progress']}/{achievement['target']} - {achievement['achievement_id']}\n\n"
            
        if len(achievements['list']) > 10:
            text += f"... и ещё {len(achievements['list']) - 10} достижений!"
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def quests(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        player = database.get_player(user.id)
        
        if not player:
            await update.message.reply_text("Игрок не найден!")
            return
            
        active_quests = database.get_active_quests(player['id'])
        
        if not active_quests:
            text = "📜 *Активные задания*\n\nНет активных заданий.\nИспользуй /daily для получения ежедневных заданий!"
        else:
            text = "📜 *Активные задания*\n\n"
            for quest in active_quests:
                text += f"🎯 {quest['quest_type'].title()}\n"
                text += f"   {quest['progress']}/{quest['target']} выполнено\n\n"
                
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def daily(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        player = database.get_player(user.id)
        
        if not player:
            await update.message.reply_text("Игрок не найден!")
            return
            
        generated = game_engine.generate_daily_quests(player['id'])
        
        await update.message.reply_text(
            f"📅 *Ежедневные задания обновлены!*\n\n"
            f"Сгенерировано {generated} новых заданий!\n\n"
            f"Используй /quests для просмотра заданий.",
            parse_mode='Markdown'
        )
    
    async def inventory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        progress = game_engine.get_player_progress(user.id)
        
        if not progress:
            await update.message.reply_text("Игрок не найден!")
            return
            
        inventory = progress['inventory']
        
        text = f"🎒 *Инвентарь* - {progress['player']['character_name']}\n\n"
        text += f"Всего предметов: {inventory['total_items']}\n\n"
        
        if inventory['items']:
            for item in inventory['items']:
                text += f"📦 {item['item_name']} x{item['quantity']}\n"
        else:
            text += "Инвентарь пуст!\n"
            
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data.startswith("story_"):
            await self.handle_story_choice(user_id, data, query)
        elif data.startswith("battle_"):
            await self.handle_battle(user_id, data, query)
        elif data.startswith("arrow_"):
            await self.handle_battle_input(user_id, data, query)
            
    async def handle_story_choice(self, user_id, data, query):
        parts = data.split("_")
        chapter = parts[1]
        scene = parts[2]
        
        story_scene = get_story_scene(chapter, scene)
        if not story_scene:
            await query.edit_message_text("Сцена не найдена!")
            return
            
        # Проверяем энергию
        player = database.get_player(user_id)
        energy_cost = story_scene.get('energy_cost', 0)
        
        if player['energy'] < energy_cost:
            await query.edit_message_text(
                f"Недостаточно энергии! Нужно: {energy_cost}, есть: {player['energy']}\n"
                f"Энергия восстанавливается со временем."
            )
            return
            
        # Используем энергию
        if energy_cost > 0:
            database.update_energy(player['id'], player['energy'] - energy_cost)
            
        # Показываем сцену
        text = story_scene['text']
        
        keyboard = []
        if 'choices' in story_scene:
            for choice in story_scene['choices']:
                keyboard.append([InlineKeyboardButton(
                    choice['text'],
                    callback_data=f"story_{chapter}_{choice['action']}"
                )])
                
        if 'battle' in story_scene:
            keyboard.append([InlineKeyboardButton(
                "🎸 Начать битву!",
                callback_data=f"battle_start_{story_scene['battle']}"
            )])
            
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        # Обрабатываем награды за выбор
        if len(parts) > 3 and parts[3] != "intro":
            rewards = game_engine.process_story_choice(player['id'], parts[3], story_scene)
            if rewards['exp'] > 0 or rewards['money'] > 0:
                reward_text = f"\n\n🎁 Награды: +{rewards['exp']} опыта"
                if rewards['money'] > 0:
                    reward_text += f", +{rewards['money']} денег"
                await context.bot.send_message(
                    chat_id=user_id,
                    text=reward_text
                )
    
    async def handle_battle(self, user_id, data, query):
        parts = data.split("_")
        action = parts[1]
        song_id = parts[2] if len(parts) > 2 else None
        
        if action == "start":
            player = database.get_player(user_id)
            song = battle_system.songs.get(song_id)
            
            if not song:
                await query.edit_message_text("Песня не найдена!")
                return
                
            # Проверяем энергию
            if player['energy'] < song['energy_cost']:
                await query.edit_message_text(
                    f"Недостаточно энергии! Нужно: {song['energy_cost']}, есть: {player['energy']}"
                )
                return
                
            # Начинаем битву
            battle_data = battle_system.start_battle(player['id'], song_id)
            self.user_battles[user_id] = battle_data
            
            # Используем энергию
            database.update_energy(player['id'], player['energy'] - song['energy_cost'])
            
            # Показываем интерфейс битвы
            await query.edit_message_text(
                f"🎸 *БИТВА НАЧАЛАСЬ!*\n\n"
                f"Песня: {song['name']}\n"
                f"Нот: {song['notes']}\n"
                f"Сложность: {'⭐' * song['difficulty']}\n\n"
                f"*Готовься к первой ноте!*",
                parse_mode='Markdown',
                reply_markup=self.get_battle_keyboard()
            )
            
    async def handle_battle_input(self, user_id, data, query):
        if user_id not in self.user_battles:
            await query.answer("Битва не начата!")
            return
            
        battle_data = self.user_battles[user_id]
        
        if battle_data['completed']:
            await query.answer("Битва уже завершена!")
            return
            
        # Обрабатываем ввод
        arrow = data.split("_")[1]
        timing_accuracy = "good"  # В реальной игре тут расчет тайминга
        
        battle_data = battle_system.process_note_input(
            battle_data, [arrow], timing_accuracy
        )
        
        self.user_battles[user_id] = battle_data
        
        # Обновляем интерфейс
        current_note = battle_data['current_note']
        total_notes = battle_data['total_notes']
        
        if battle_data['completed']:
            # Завершаем битву
            summary = battle_system.get_battle_summary(battle_data)
            
            # Записываем в БД
            database.record_battle(
                user_id,
                battle_data['song_id'],
                battle_data['score'],
                battle_data['max_combo'],
                battle_data['perfect_hits'],
                battle_data['good_hits'],
                battle_data['bad_hits'],
                battle_data['missed'],
                battle_data['battle_duration']
            )
            
            # Награды
            rewards = game_engine.calculate_battle_rewards(
                user_id,
                battle_data['score'],
                battle_data['max_combo'], 
                battle_data['perfect_hits']
            )
            
            text = (
                f"🎉 *БИТВА ЗАВЕРШЕНА!*\n\n"
                f"Песня: {summary['song_name']}\n"
                f"Счет: {summary['score']}\n"
                f"Точность: {summary['accuracy']}%\n"
                f"Идеально: {summary['perfect_hits']}\n"
                f"Макс комбо: {summary['max_combo']}\n"
                f"Оценка: {summary['grade']}\n\n"
                f"🎁 Награды:\n"
                f"+{rewards['exp']} опыта\n"
                f"+{rewards['money']} денег\n"
            )
            
            if rewards.get('level_up'):
                text += f"🎯 ПОВЫШЕНИЕ УРОВНЯ! Новый уровень: {rewards['level_up']}\n"
                
            await query.edit_message_text(
                text,
                parse_mode='Markdown',
                reply_markup=self.get_main_menu_keyboard()
            )
            
            del self.user_battles[user_id]
            
        else:
            # Показываем следующую ноту
            next_note = battle_data['patterns'][current_note]
            note_text = " ".join(next_note['arrows'])
            
            await query.edit_message_text(
                f"🎸 *БИТВА* - {battle_data['song_name']}\n\n"
                f"Счет: {battle_data['score']}\n"
                f"Комбо: {battle_data['combo']}\n"
                f"Прогресс: {current_note}/{total_notes}\n\n"
                f"*Следующая нота:* {note_text}",
                parse_mode='Markdown',
                reply_markup=self.get_battle_keyboard()
            )
    
    def get_main_menu_keyboard(self):
        keyboard = [
            [InlineKeyboardButton("📖 Сюжет", callback_data="menu_story"),
            InlineKeyboardButton("🎸 Битвы", callback_data="menu_battle")],
            [InlineKeyboardButton("📜 Задания", callback_data="menu_quests"),
            InlineKeyboardButton("🏆 Достижения", callback_data="menu_achievements")],
            [InlineKeyboardButton("🎒 Инвентарь", callback_data="menu_inventory"),
            InlineKeyboardButton("👤 Профиль", callback_data="menu_profile")],
            [InlineKeyboardButton("📅 Ежедневные", callback_data="menu_daily")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_battle_keyboard(self):
        keyboard = [
            [InlineKeyboardButton("←", callback_data="arrow_left"),
             InlineKeyboardButton("→", callback_data="arrow_right")],
            [InlineKeyboardButton("↑", callback_data="arrow_up"),
             InlineKeyboardButton("↓", callback_data="arrow_down")],
            [InlineKeyboardButton("🏃 Сбежать", callback_data="battle_flee")]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def run(self):
        await self.application.run_polling()

# Глобальный экземпляр бота
bot = FNFMMOBot()

# ДОБАВЬ ЭТУ СТРОКУ для совместимости с main.py:
async def run_bot():
    await bot.run()