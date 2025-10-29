import sqlite3
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class GameDatabase:
    def __init__(self):
        # ИСПОЛЬЗУЕМ ПАМЯТЬ вместо файла для хостинга
        self.conn = sqlite3.connect(':memory:', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.create_default_achievements()
       
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Игроки
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                character_name TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                health INTEGER DEFAULT 100,
                max_health INTEGER DEFAULT 100,
                rhythm INTEGER DEFAULT 50,
                charisma INTEGER DEFAULT 30,
                strength INTEGER DEFAULT 40,
                money INTEGER DEFAULT 100,
                energy INTEGER DEFAULT 100,
                max_energy INTEGER DEFAULT 100,
                last_energy_update DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_active DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Инвентарь
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            )
        ''')
        
        # Прогресс сюжета
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS story_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER UNIQUE NOT NULL,
                chapter INTEGER DEFAULT 1,
                completed_chapters TEXT DEFAULT '[]',
                current_quest TEXT,
                story_flags TEXT DEFAULT '{}',
                pico_relationship INTEGER DEFAULT 0,
                boyfriend_relationship INTEGER DEFAULT 0,
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            )
        ''')
        
        # Активные квесты
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                quest_id TEXT NOT NULL,
                quest_type TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                target INTEGER NOT NULL,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            )
        ''')
        
        # Завершенные квесты
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS completed_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                quest_id TEXT NOT NULL,
                completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                reward_claimed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            )
        ''')
        
        # Достижения
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                achievement_name TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                target INTEGER NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                completed_at DATETIME,
                reward_claimed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            )
        ''')
        
        # Ежедневные задания
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                quest_type TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                target INTEGER NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                date DATE NOT NULL,
                reward_claimed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            )
        ''')
        
        # Статистика
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER UNIQUE NOT NULL,
                total_battles INTEGER DEFAULT 0,
                battles_won INTEGER DEFAULT 0,
                perfect_scores INTEGER DEFAULT 0,
                max_combo INTEGER DEFAULT 0,
                quests_completed INTEGER DEFAULT 0,
                daily_quests_completed INTEGER DEFAULT 0,
                achievements_completed INTEGER DEFAULT 0,
                total_play_time INTEGER DEFAULT 0,
                money_earned INTEGER DEFAULT 0,
                money_spent INTEGER DEFAULT 0,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            )
        ''')
        
        # Баттлы
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS battle_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                song_id TEXT NOT NULL,
                score INTEGER NOT NULL,
                max_combo INTEGER DEFAULT 0,
                perfect_hits INTEGER DEFAULT 0,
                good_hits INTEGER DEFAULT 0,
                bad_hits INTEGER DEFAULT 0,
                missed INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                battle_duration INTEGER DEFAULT 0,
                played_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            )
        ''')
        
        self.conn.commit()
        logger.info("Все таблицы созданы успешно!")
    
    def create_default_achievements(self):
        """Создать достижения по умолчанию для всех игроков"""
        default_achievements = [
            # Story achievements
            {"id": "first_blood", "name": "Первая кровь", "target": 1},
            {"id": "pico_friend", "name": "Друг Пико", "target": 50},
            {"id": "story_master", "name": "Мастер истории", "target": 4},
            
            # Battle achievements  
            {"id": "perfectionist", "name": "Перфекционист", "target": 50},
            {"id": "combo_master", "name": "Мастер комбо", "target": 100},
            {"id": "boss_slayer", "name": "Убийца боссов", "target": 5},
            
            # Collection achievements
            {"id": "note_collector", "name": "Коллекционер нот", "target": 1000},
            {"id": "rich_player", "name": "Богатый игрок", "target": 10000},
            
            # Social achievements
            {"id": "popular", "name": "Популярный", "target": 20},
            {"id": "legendary", "name": "Легендарный", "target": 50}
        ]
        
        cursor = self.conn.cursor()
        
        # Получаем всех игроков
        cursor.execute("SELECT id FROM players")
        players = cursor.fetchall()
        
        for player in players:
            player_id = player[0]
            for achievement in default_achievements:
                # Проверяем, есть ли уже это достижение
                cursor.execute(
                    "SELECT id FROM achievements WHERE player_id = ? AND achievement_id = ?",
                    (player_id, achievement["id"])
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO achievements (player_id, achievement_id, achievement_name, target) VALUES (?, ?, ?, ?)",
                        (player_id, achievement["id"], achievement["name"], achievement["target"])
                    )
        
        self.conn.commit()
    
    def get_player(self, telegram_id):
        """Получить игрока по telegram_id"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM players WHERE telegram_id = ?", (telegram_id,))
        player = cursor.fetchone()
        
        if player:
            # Получаем прогресс сюжета
            cursor.execute("SELECT * FROM story_progress WHERE player_id = ?", (player["id"],))
            story = cursor.fetchone()
            
            # Получаем статистику
            cursor.execute("SELECT * FROM player_stats WHERE player_id = ?", (player["id"],))
            stats = cursor.fetchone()
            
            return {
                **dict(player),
                "story": dict(story) if story else None,
                "stats": dict(stats) if stats else None
            }
        return None
    
    def create_player(self, telegram_id, username, character_name):
        """Создать нового игрока"""
        cursor = self.conn.cursor()
        
        try:
            # Создаем игрока
            cursor.execute('''
                INSERT INTO players (telegram_id, username, character_name) 
                VALUES (?, ?, ?)
            ''', (telegram_id, username, character_name))
            
            player_id = cursor.lastrowid
            
            # Создаем прогресс сюжета
            cursor.execute('''
                INSERT INTO story_progress (player_id) VALUES (?)
            ''', (player_id,))
            
            # Создаем статистику
            cursor.execute('''
                INSERT INTO player_stats (player_id) VALUES (?)
            ''', (player_id,))
            
            # Создаем достижения
            self.create_default_achievements()
            
            # Даем стартовые предметы
            starter_items = [
                ("health_potion", "Зелье здоровья", 3),
                ("energy_drink", "Энергетик", 2),
                ("guitar_pick", "Медиатор", 1)
            ]
            
            for item_id, item_name, quantity in starter_items:
                cursor.execute('''
                    INSERT INTO inventory (player_id, item_id, item_name, quantity)
                    VALUES (?, ?, ?, ?)
                ''', (player_id, item_id, item_name, quantity))
            
            self.conn.commit()
            return self.get_player(telegram_id)
            
        except sqlite3.IntegrityError:
            logger.warning(f"Игрок с telegram_id {telegram_id} уже существует")
            return None
    
    def update_energy(self, player_id, new_energy):
        """Обновить энергию игрока"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE players SET energy = ?, last_energy_update = CURRENT_TIMESTAMP WHERE id = ?",
            (new_energy, player_id)
        )
        self.conn.commit()
    
    def add_experience(self, player_id, exp_amount):
        """Добавить опыт игроку"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE players SET exp = exp + ? WHERE id = ?",
            (exp_amount, player_id)
        )
        self.conn.commit()
        
        # Проверяем повышение уровня
        self.check_level_up(player_id)
    
    def check_level_up(self, player_id):
        """Проверить и обработать повышение уровня"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT level, exp FROM players WHERE id = ?", (player_id,))
        player = cursor.fetchone()
        
        if player:
            current_level = player["level"]
            current_exp = player["exp"]
            
            # Формула для следующего уровня: level^2 * 100
            exp_needed = (current_level ** 2) * 100
            
            if current_exp >= exp_needed:
                new_level = current_level + 1
                cursor.execute(
                    "UPDATE players SET level = ?, max_health = max_health + 10, max_energy = max_energy + 5 WHERE id = ?",
                    (new_level, player_id)
                )
                self.conn.commit()
                return new_level
        
        return None
    
    def add_money(self, player_id, amount):
        """Добавить деньги игроку"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE players SET money = money + ? WHERE id = ?",
            (amount, player_id)
        )
        
        # Обновляем статистику
        if amount > 0:
            cursor.execute(
                "UPDATE player_stats SET money_earned = money_earned + ? WHERE player_id = ?",
                (amount, player_id)
            )
        
        self.conn.commit()
    
    def update_relationship(self, player_id, character, amount):
        """Обновить отношения с персонажем"""
        cursor = self.conn.cursor()
        
        if character == "pico":
            cursor.execute(
                "UPDATE story_progress SET pico_relationship = pico_relationship + ? WHERE player_id = ?",
                (amount, player_id)
            )
        elif character == "boyfriend":
            cursor.execute(
                "UPDATE story_progress SET boyfriend_relationship = boyfriend_relationship + ? WHERE player_id = ?",
                (amount, player_id)
            )
        
        self.conn.commit()
    
    def add_quest(self, player_id, quest_id, quest_type, target):
        """Добавить квест игроку"""
        cursor = self.conn.cursor()
        
        # Проверяем, нет ли уже такого квеста
        cursor.execute(
            "SELECT id FROM active_quests WHERE player_id = ? AND quest_id = ?",
            (player_id, quest_id)
        )
        
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO active_quests (player_id, quest_id, quest_type, target)
                VALUES (?, ?, ?, ?)
            ''', (player_id, quest_id, quest_type, target))
            
            self.conn.commit()
            return True
        return False
    
    def update_quest_progress(self, player_id, quest_type, amount=1):
        """Обновить прогресс квеста"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE active_quests 
            SET progress = progress + ? 
            WHERE player_id = ? AND quest_type = ? AND completed = FALSE
        ''', (amount, player_id, quest_type))
        
        # Проверяем завершение квеста
        cursor.execute('''
            UPDATE active_quests 
            SET completed = TRUE 
            WHERE player_id = ? AND quest_type = ? AND progress >= target AND completed = FALSE
        ''', (player_id, quest_type))
        
        self.conn.commit()
        
        # Возвращаем количество завершенных квестов
        cursor.execute('''
            SELECT COUNT(*) FROM active_quests 
            WHERE player_id = ? AND quest_type = ? AND completed = TRUE
        ''', (player_id, quest_type))
        
        return cursor.fetchone()[0]
    
    def update_achievement_progress(self, player_id, achievement_id, amount=1):
        """Обновить прогресс достижения"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE achievements 
            SET progress = progress + ? 
            WHERE player_id = ? AND achievement_id = ? AND completed = FALSE
        ''', (amount, player_id, achievement_id))
        
        # Проверяем завершение достижения
        cursor.execute('''
            UPDATE achievements 
            SET completed = TRUE, completed_at = CURRENT_TIMESTAMP 
            WHERE player_id = ? AND achievement_id = ? AND progress >= target AND completed = FALSE
        ''', (player_id, achievement_id))
        
        self.conn.commit()
        
        cursor.execute('''
            SELECT completed FROM achievements 
            WHERE player_id = ? AND achievement_id = ?
        ''', (player_id, achievement_id))
        
        result = cursor.fetchone()
        return result["completed"] if result else False
    
    def record_battle(self, player_id, song_id, score, max_combo, perfect_hits, good_hits, bad_hits, missed, duration):
        """Записать результат битвы"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO battle_history 
            (player_id, song_id, score, max_combo, perfect_hits, good_hits, bad_hits, missed, battle_duration, completed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (player_id, song_id, score, max_combo, perfect_hits, good_hits, bad_hits, missed, duration, True))
        
        # Обновляем статистику
        cursor.execute('''
            UPDATE player_stats 
            SET total_battles = total_battles + 1,
                battles_won = battles_won + 1,
                max_combo = CASE WHEN ? > max_combo THEN ? ELSE max_combo END,
                last_activity = CURRENT_TIMESTAMP
            WHERE player_id = ?
        ''', (max_combo, max_combo, player_id))
        
        if perfect_hits >= 10:
            cursor.execute('''
                UPDATE player_stats SET perfect_scores = perfect_scores + 1 WHERE player_id = ?
            ''', (player_id,))
        
        self.conn.commit()
        return cursor.lastrowid

    def get_player_achievements(self, player_id):
        """Получить достижения игрока"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM achievements WHERE player_id = ? ORDER BY completed DESC, progress DESC
        ''', (player_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_active_quests(self, player_id):
        """Получить активные квесты игрока"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM active_quests WHERE player_id = ? AND completed = FALSE
        ''', (player_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_completed_quests(self, player_id):
        """Получить завершенные квесты игрока"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM completed_quests WHERE player_id = ?
        ''', (player_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_inventory(self, player_id):
        """Получить инвентарь игрока"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM inventory WHERE player_id = ? AND quantity > 0 ORDER BY item_name
        ''', (player_id,))
        return [dict(row) for row in cursor.fetchall()]

# Создаем глобальный экземпляр БД
database = GameDatabase()