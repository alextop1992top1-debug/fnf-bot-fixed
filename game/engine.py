import sqlite3
import json
import random
from datetime import datetime, timedelta
from core.database import database

class GameEngine:
    def __init__(self):
        self.db = database
        self.energy_cooldown = 5  # минут на 1 энергию
        
    def calculate_play_time(self, player_id):
        """Рассчитать игровое время"""
        player = self.db.get_player(player_id)
        if player and player.get('stats'):
            base_time = 180 + 60  # 3+1 часа основного контента
            endgame_minutes = player['stats'].get('total_play_time', 0)
            return {
                "main_story": 180,
                "side_quests": 60, 
                "endgame": endgame_minutes,
                "total": base_time + endgame_minutes
            }
        return {"main_story": 0, "side_quests": 0, "endgame": 0, "total": 0}
    
    def generate_daily_quests(self, player_id):
        """Генерация ежедневных заданий"""
        today = datetime.now().date()
        
        daily_quests = [
            {
                "quest_id": f"daily_battle_{today}",
                "quest_type": "battle",
                "target": random.randint(5, 10),
                "description": "Победить в ритм-баттлах"
            },
            {
                "quest_id": f"daily_social_{today}", 
                "quest_type": "social",
                "target": random.randint(3, 6),
                "description": "Пообщаться с персонажами"
            },
            {
                "quest_id": f"daily_explore_{today}",
                "quest_type": "exploration", 
                "target": random.randint(4, 8),
                "description": "Посетить локации"
            },
            {
                "quest_id": f"daily_collect_{today}",
                "quest_type": "collection",
                "target": random.randint(10, 20), 
                "description": "Собрать музыкальные ноты"
            },
            {
                "quest_id": f"daily_skill_{today}",
                "quest_type": "skill",
                "target": random.randint(1, 3),
                "description": "Улучшить навыки"
            }
        ]
        
        created_count = 0
        for quest in daily_quests:
            if self.db.add_quest(player_id, quest["quest_id"], quest["quest_type"], quest["target"]):
                created_count += 1
                
        return created_count
    
    def check_energy(self, player_id):
        """Проверка и восстановление энергии"""
        player_data = self.db.get_player(player_id)
        if not player_data:
            return 0
            
        player = player_data
        current_energy = player['energy']
        max_energy = player['max_energy']
        
        if current_energy >= max_energy:
            return current_energy
            
        # Восстанавливаем энергию со временем
        last_update = datetime.fromisoformat(player['last_energy_update'])
        time_diff = datetime.now() - last_update
        energy_gain = int(time_diff.total_seconds() // (self.energy_cooldown * 60))
        
        if energy_gain > 0:
            new_energy = min(max_energy, current_energy + energy_gain)
            self.db.update_energy(player_id, new_energy)
            return new_energy
            
        return current_energy
    
    def use_energy(self, player_id, amount):
        """Использовать энергию"""
        current_energy = self.check_energy(player_id)
        
        if current_energy >= amount:
            new_energy = current_energy - amount
            self.db.update_energy(player_id, new_energy)
            return True
        return False
    
    def calculate_battle_rewards(self, player_id, score, max_combo, perfect_hits):
        """Рассчитать награды за битву"""
        base_exp = 50
        base_money = 25
        
        # Бонусы за performance
        exp_bonus = (score // 1000) + (max_combo // 10) + (perfect_hits * 2)
        money_bonus = (score // 2000) + (max_combo // 20) + (perfect_hits * 1)
        
        total_exp = base_exp + exp_bonus
        total_money = base_money + money_bonus
        
        # Добавляем награды
        self.db.add_experience(player_id, total_exp)
        self.db.add_money(player_id, total_money)
        
        # Обновляем достижения
        self.db.update_achievement_progress(player_id, "first_blood")
        self.db.update_achievement_progress(player_id, "perfectionist", perfect_hits)
        self.db.update_achievement_progress(player_id, "combo_master", max_combo)
        
        # Обновляем прогресс квестов
        self.db.update_quest_progress(player_id, "battle")
        self.db.update_quest_progress(player_id, "collection", perfect_hits)
        
        return {
            "exp": total_exp,
            "money": total_money,
            "level_up": self.db.check_level_up(player_id)
        }
    
    def process_story_choice(self, player_id, choice, chapter_data):
        """Обработать выбор в сюжете"""
        rewards = {
            "exp": 0,
            "money": 0,
            "relationship": 0,
            "unlocks": []
        }
        
        # Награды за выбор
        if choice == "ask_pico_past":
            rewards["exp"] = 25
            rewards["relationship"] = 10
            self.db.update_relationship(player_id, "pico", 10)
            
        elif choice == "help_pico":
            rewards["exp"] = 50
            rewards["money"] = 100
            rewards["relationship"] = 15
            self.db.update_relationship(player_id, "pico", 15)
            self.db.update_relationship(player_id, "boyfriend", 5)
            
        elif choice == "challenge_battle":
            rewards["exp"] = 75
            rewards["relationship"] = 20
            self.db.update_relationship(player_id, "pico", 20)
            
        # Добавляем награды
        if rewards["exp"] > 0:
            self.db.add_experience(player_id, rewards["exp"])
            
        if rewards["money"] > 0:
            self.db.add_money(player_id, rewards["money"])
            
        # Обновляем достижения
        self.db.update_achievement_progress(player_id, "pico_friend", rewards["relationship"])
        self.db.update_quest_progress(player_id, "social")
        
        return rewards
    
    def get_player_progress(self, player_id):
        """Получить полный прогресс игрока"""
        player_data = self.db.get_player(player_id)
        if not player_data:
            return None
            
        achievements = self.db.get_player_achievements(player_id)
        active_quests = self.db.get_active_quests(player_id)
        completed_quests = self.db.get_completed_quests(player_id)
        inventory = self.db.get_inventory(player_id)
        
        completed_achievements = [a for a in achievements if a['completed']]
        completion_percentage = (len(completed_achievements) / len(achievements)) * 100 if achievements else 0
        
        return {
            "player": player_data,
            "achievements": {
                "total": len(achievements),
                "completed": len(completed_achievements),
                "completion_percentage": round(completion_percentage, 1),
                "list": achievements
            },
            "quests": {
                "active": active_quests,
                "completed": len(completed_quests),
                "active_count": len(active_quests)
            },
            "inventory": {
                "items": inventory,
                "total_items": sum(item['quantity'] for item in inventory)
            },
            "play_time": self.calculate_play_time(player_id)
        }

# Глобальный экземпляр движка
game_engine = GameEngine()