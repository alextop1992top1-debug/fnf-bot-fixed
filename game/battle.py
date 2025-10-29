import random
import time
from datetime import datetime

class RhythmBattleSystem:
    def __init__(self):
        self.songs = {
            "tutorial": {
                "name": "🎵 Обучение ритму",
                "notes": 30,
                "difficulty": 1,
                "duration": 1,
                "energy_cost": 10
            },
            "pico_theme": {
                "name": "🎸 Тема Пико", 
                "notes": 80,
                "difficulty": 3,
                "duration": 3,
                "energy_cost": 20
            },
            "boyfriend_song": {
                "name": "🎤 Песня Бойфренда",
                "notes": 120, 
                "difficulty": 4,
                "duration": 5,
                "energy_cost": 30
            },
            "final_boss": {
                "name": "🔥 Финальный босс",
                "notes": 200,
                "difficulty": 5, 
                "duration": 8,
                "energy_cost": 50
            }
        }
        
        self.arrows = ['←', '→', '↑', '↓']
        
    def start_battle(self, player_id, song_id):
        """Начать битву"""
        if song_id not in self.songs:
            return None
            
        song = self.songs[song_id]
        patterns = self.generate_note_patterns(song['notes'], song['difficulty'])
        
        battle_data = {
            'song_id': song_id,
            'song_name': song['name'],
            'total_notes': song['notes'],
            'notes_hit': 0,
            'perfect_hits': 0,
            'good_hits': 0,
            'bad_hits': 0,
            'missed': 0,
            'combo': 0,
            'max_combo': 0,
            'score': 0,
            'patterns': patterns,
            'current_note': 0,
            'start_time': datetime.now(),
            'completed': False,
            'energy_cost': song['energy_cost']
        }
        
        return battle_data
    
    def generate_note_patterns(self, note_count, difficulty):
        """Генерация паттернов нот"""
        patterns = []
        
        for i in range(note_count):
            if difficulty == 1:
                # Легко: только одиночные ноты
                pattern = [random.choice(self.arrows)]
            elif difficulty == 2:
                # Средне: 80% одиночные, 20% двойные
                if random.random() < 0.2:
                    pattern = random.sample(self.arrows, 2)
                else:
                    pattern = [random.choice(self.arrows)]
            elif difficulty == 3:
                # Сложно: 60% одиночные, 30% двойные, 10% тройные
                rand = random.random()
                if rand < 0.1:
                    pattern = random.sample(self.arrows, 3)
                elif rand < 0.4:
                    pattern = random.sample(self.arrows, 2)
                else:
                    pattern = [random.choice(self.arrows)]
            elif difficulty >= 4:
                # Очень сложно: сложные паттерны
                pattern_length = random.randint(1, min(4, difficulty))
                pattern = [random.choice(self.arrows) for _ in range(pattern_length)]
            
            patterns.append({
                'id': i,
                'arrows': pattern,
                'timing': i * 0.8,  # Нота каждые 0.8 секунд
                'hit': None,
                'score': 0
            })
        
        return patterns
    
    def process_note_input(self, battle_data, player_input, timing_accuracy):
        """Обработать ввод ноты игроком"""
        if battle_data['current_note'] >= battle_data['total_notes']:
            return battle_data
            
        current_note = battle_data['patterns'][battle_data['current_note']]
        
        # Проверяем правильность ввода
        if set(player_input) == set(current_note['arrows']):
            if timing_accuracy == 'perfect':
                score = 100
                battle_data['perfect_hits'] += 1
                battle_data['combo'] += 1
            elif timing_accuracy == 'good':
                score = 50  
                battle_data['good_hits'] += 1
                battle_data['combo'] += 1
            else:  # bad
                score = 10
                battle_data['bad_hits'] += 1
                battle_data['combo'] = 0
        else:
            score = 0
            battle_data['missed'] += 1
            battle_data['combo'] = 0
        
        # Обновляем статистику
        battle_data['score'] += score * battle_data['combo']
        battle_data['notes_hit'] += 1
        battle_data['max_combo'] = max(battle_data['max_combo'], battle_data['combo'])
        battle_data['current_note'] += 1
        
        # Проверяем завершение битвы
        if battle_data['current_note'] >= battle_data['total_notes']:
            battle_data['completed'] = True
            battle_data['end_time'] = datetime.now()
            duration = (battle_data['end_time'] - battle_data['start_time']).total_seconds()
            battle_data['battle_duration'] = duration
            
        return battle_data
    
    def calculate_timing_accuracy(self, timing_difference):
        """Рассчитать точность тайминга"""
        if timing_difference <= 0.1:
            return 'perfect'
        elif timing_difference <= 0.3:
            return 'good'
        else:
            return 'bad'
    
    def get_battle_summary(self, battle_data):
        """Получить статистику битвы"""
        if not battle_data['completed']:
            return None
            
        accuracy = (battle_data['notes_hit'] / battle_data['total_notes']) * 100
        perfect_percentage = (battle_data['perfect_hits'] / battle_data['total_notes']) * 100
        
        grade = "F"
        if accuracy >= 90:
            grade = "S" if perfect_percentage >= 80 else "A"
        elif accuracy >= 80:
            grade = "B" 
        elif accuracy >= 70:
            grade = "C"
        elif accuracy >= 60:
            grade = "D"
            
        return {
            'song_name': battle_data['song_name'],
            'total_notes': battle_data['total_notes'],
            'notes_hit': battle_data['notes_hit'],
            'perfect_hits': battle_data['perfect_hits'],
            'good_hits': battle_data['good_hits'],
            'bad_hits': battle_data['bad_hits'],
            'missed': battle_data['missed'],
            'max_combo': battle_data['max_combo'],
            'score': battle_data['score'],
            'accuracy': round(accuracy, 1),
            'perfect_percentage': round(perfect_percentage, 1),
            'grade': grade,
            'duration': round(battle_data['battle_duration'], 1)
        }

# Глобальный экземпляр системы боев
battle_system = RhythmBattleSystem()