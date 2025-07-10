"""Главный симулятор периода жизни"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models import Person
from .transaction_models import SimulationConfig, MemoryContext, DailyResult
from .social_manager import SocialEnvironment
from .daily_simulator import DailyLifeSimulator
from .analyzer import ImprovedSimulationAnalyzer 


logger = logging.getLogger(__name__)


class LifeTransactionSimulator:
    """Симулятор жизни с транзакциями на заданный период"""
    
    def __init__(self, config: SimulationConfig, all_people: List[Person]):
        self.config = config
        self.all_people = all_people
        
        # Находим целевого персонажа
        self.person = next(
            (p for p in all_people if p.id == config.target_person_id),
            None
        )
        if not self.person:
            raise ValueError(f"Person {config.target_person_id} not found")
        
        # Инициализируем компоненты
        self.social_environment = SocialEnvironment(self.person)
        self.daily_simulator = DailyLifeSimulator(
            self.person, 
            self.social_environment
        )
        self.analyzer = ImprovedSimulationAnalyzer()
        
        # Результаты
        self.daily_results: List[DailyResult] = []
        self.memory = MemoryContext(
            recent_days=[],
            emotional_state="нормальное",
            recent_major_purchases=[],
            social_patterns={}
        )
    
    def _get_basic_person_profile(self) -> Dict[str, Any]:
        """Возвращает базовый профиль персонажа без объемных данных"""
        
        return {
            "name": self.person.name,
            "id": self.person.id,
            "gender": self.person.gender,
            "age": self.person.age,
            "birth_year": self.person.birth_year,
            "region": self.person.region,
            "city_type": self.person.city_type,
            "education": self.person.education,
            "profession": self.person.profession,
            "employment": self.person.employment,
            "income_level": self.person.income_level,
            "family_status": self.person.family_status,
            "children": self.person.children,
            "religion": self.person.religion,
            "ideology": self.person.ideology,
            "state_trust": self.person.state_trust,
            "media_trust": self.person.media_trust,
            "military_context": self.person.military_context,
            "digital_literacy": self.person.digital_literacy,
            "context": self.person.context,
            # Исключаем объемные поля:
            # - full_history (может быть очень большим)
            # - cognitive_frame (сложные вложенные структуры)
            # - rhetorical_manner
            # - trigger_points
            # - interpretation_biases
            # - meta_self_view
            # - speech_profile
        }
    
    async def run_simulation(self) -> Dict[str, Any]:
        """Запускает полную симуляцию"""
        
        logger.info(f"Starting simulation for {self.person.name}")
        logger.info(f"Period: {self.config.days} days from {self.config.start_date}")
        
        # 1. Генерируем начальное социальное окружение
        logger.info("Generating social environment...")
        await self.social_environment.generate_initial_environment()
        
        # 2. Симулируем каждый день
        current_date = self.config.start_date
        
        for day_num in range(self.config.days):
            logger.info(f"\nSimulating day {day_num + 1}/{self.config.days}")
            
            # Проверяем события
            special_event = self._check_for_event(day_num)
            if special_event:
                logger.info(f"Special event: {special_event}")
                
                # Возможно добавляем нового человека
                if special_event in ["повышение", "новая работа"]:
                    new_person = await self.social_environment.add_new_person(
                        context=f"В связи с {special_event}",
                        event_type=special_event
                    )
                    logger.info(f"New person added: {new_person['name']}")
            
            # Симулируем день
            daily_result = await self.daily_simulator.simulate_day(
                current_date,
                self.memory.dict(),
                special_event
            )
            
            self.daily_results.append(daily_result)
            
            # Обновляем память
            self._update_memory(daily_result)
            
            # Выводим краткую информацию
            logger.info(
                f"Day {current_date.strftime('%Y-%m-%d')}: "
                f"Spent {daily_result.day_summary.total_spent:.0f} RUB, "
                f"Mood: {daily_result.day_summary.mood_trajectory}"
            )
            
            current_date += timedelta(days=1)
        
        # 3. Анализируем результаты (этот код остается без изменений)
        logger.info("\nAnalyzing results...")
        analysis = self.analyzer.analyze_simulation(
            self.daily_results,
            self.person,
            self.config
        )
        
        return {
            "person": self.person.dict(),
            "config": self.config.dict(),
            "social_environment": {
                "close_circle": self.social_environment.close_circle,
                "extended_circle": self.social_environment.extended_circle
            },
            "daily_results": [r.dict() for r in self.daily_results],
            "analysis": analysis  # Теперь содержит улучшенную аналитику
        }
    
    def _check_for_event(self, day_num: int) -> Optional[str]:
        """Проверяет, есть ли событие в этот день"""
        
        if not self.config.events:
            return None
        
        for event in self.config.events:
            if event.get('day') == day_num:
                return event.get('type')
        
        return None
    
    def _update_memory(self, daily_result: DailyResult):
        """Обновляет память на основе прошедшего дня"""
        
        # Добавляем день в память
        day_summary = {
            "date": daily_result.date,
            "total_spent": daily_result.day_summary.total_spent,
            "key_interaction": (
                daily_result.social_interactions[0].with_person 
                if daily_result.social_interactions else "один"
            ),
            "mood": daily_result.day_summary.mood_trajectory,
            "transactions": [
                {
                    "category": t.category,
                    "amount": t.amount,
                    "items": t.items[:2]  # первые 2 товара
                }
                for t in daily_result.transactions
            ]
        }
        
        self.memory.recent_days.append(day_summary)
        
        # Оставляем только последние N дней
        if len(self.memory.recent_days) > self.config.memory_window:
            self.memory.recent_days.pop(0)
        
        # Обновляем эмоциональное состояние
        self.memory.emotional_state = daily_result.day_summary.mood_trajectory
        
        # Обновляем крупные покупки
        major_purchases = [
            {
                "date": daily_result.date,
                "amount": t.amount,
                "items": t.items,
                "place": t.place
            }
            for t in daily_result.transactions
            if t.amount > 2000
        ]
        
        self.memory.recent_major_purchases.extend(major_purchases)
        self.memory.recent_major_purchases = self.memory.recent_major_purchases[-5:]
        
        # Обновляем социальные паттерны
        for interaction in daily_result.social_interactions:
            person_name = interaction.with_person
            if person_name not in self.memory.social_patterns:
                self.memory.social_patterns[person_name] = 0
            self.memory.social_patterns[person_name] += 1
    
    def save_results(self, filename: str):
        """Сохраняет результаты с улучшенной аналитикой"""
        
        results = {
            "metadata": {
                "simulation_date": datetime.now().isoformat(),
                "person_name": self.person.name,
                "person_id": self.person.id,
                "days_simulated": self.config.days
            },
            "config": self.config.dict(),
            "person_profile": self._get_basic_person_profile(),
            "social_environment": {
                "close_circle": self.social_environment.close_circle,
                "extended_circle": self.social_environment.extended_circle
            },
            "daily_results": [r.dict() for r in self.daily_results],
            "summary": self.analyzer.generate_summary(self.daily_results)  # Улучшенная сводка
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Results saved to {filename}")