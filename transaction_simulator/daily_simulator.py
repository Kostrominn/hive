"""Симулятор одного дня"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models import Person, Runner
from .transaction_models import DailyResult, DayContext, DailySummary, Event
from .social_manager import SocialInteractionManager, SocialEnvironment
from .transaction_generator import TransactionGenerator
from .agents import emotion_analyzer_agent
from .prompts import format_event_context


class DailyLifeSimulator:
    """Симулирует один день жизни персонажа"""
    
    def __init__(
        self, 
        person: Person, 
        social_environment: SocialEnvironment
    ):
        self.person = person
        self.social_environment = social_environment
        self.social_manager = SocialInteractionManager(person, social_environment)
        self.transaction_generator = TransactionGenerator(person)
        
    async def simulate_day(
        self,
        date: datetime,
        memory_context: Dict[str, Any],
        special_event: Optional[Event] = None
    ) -> DailyResult:
        """Полная симуляция одного дня"""
        
        # 1. Определяем контекст дня
        day_context = self._build_day_context(date, special_event)
        
        # Добавляем дату в контекст для всех промптов
        day_context_dict = day_context.dict()
        day_context_dict['date'] = date.strftime("%Y-%m-%d")
        
        # 2. Генерируем социальные взаимодействия
        social_interactions = await self.social_manager.generate_daily_interactions(
            day_context_dict,
            memory_context
        )
        
        # 3. Анализируем эмоциональную траекторию
        mood_trajectory = await self._analyze_mood_trajectory(social_interactions)
        
        # 4. Генерируем транзакции с учетом всего контекста
        transactions = await self.transaction_generator.generate_transactions(
            day_context_dict,  # используем тот же расширенный словарь
            social_interactions,
            memory_context
        )
    
        
        # 5. Анализируем день
        spending_analysis = self.transaction_generator.analyze_spending_patterns(
            transactions
        )
        
        # 6. Формируем итоги дня
        day_summary = DailySummary(
            total_spent=spending_analysis['total_spent'],
            mood_trajectory=mood_trajectory,
            key_moments=self._extract_key_moments(social_interactions, transactions),
            new_patterns=self._detect_new_patterns(transactions, memory_context)
        )
        
        # 7. Собираем полный результат
        return DailyResult(
            date=date.strftime("%Y-%m-%d"),
            day_context=day_context,
            social_interactions=social_interactions,
            transactions=transactions,
            day_summary=day_summary
        )
    
    def _build_day_context(
        self,
        date: datetime,
        special_event: Optional[Event]
    ) -> DayContext:
        """Строит контекст дня"""
        
        day_names = ["понедельник", "вторник", "среда", "четверг", 
                     "пятница", "суббота", "воскресенье"]
        
        day_of_week = day_names[date.weekday()]
        is_workday = date.weekday() < 5
        
        events = []
        if special_event:
            events.append(
                format_event_context(special_event.type, special_event.dict())
                or special_event.type
            )
        
        # Определяем стандартные события
        if date.day == 25:  # примерно зарплата
            events.append("день зарплаты")
        
        # Праздники (упрощенно)
        if date.month == 1 and date.day == 1:
            events.append("Новый год")
        elif date.month == 3 and date.day == 8:
            events.append("8 марта")
        
        # Погода (упрощенно по сезону)
        season_weather = {
            12: "холодно, снег",
            1: "холодно, снег", 
            2: "холодно",
            3: "прохладно",
            4: "тепло",
            5: "тепло",
            6: "жарко",
            7: "жарко",
            8: "жарко",
            9: "тепло",
            10: "прохладно",
            11: "холодно"
        }
        
        weather = season_weather.get(date.month, "обычная")
        
        return DayContext(
            day_of_week=day_of_week,
            events=events if events else ["обычный день"],
            weather=weather,
            is_workday=is_workday
        )
    
    async def _analyze_mood_trajectory(self, interactions) -> str:
        """Анализирует эмоциональную динамику дня"""
        
        if not interactions:
            return "день прошёл спокойно"
        
        # Вариант 1: Простая генерация без LLM
        # return generate_simple_mood_description(interactions)
        
        # Вариант 2: Улучшенный промпт для LLM
        impacts = [i.emotional_impact for i in interactions]
        
        prompt = f"""Опиши простыми словами как менялось настроение за день.

    Что произошло:
    {' → '.join(impacts)}

    Ответь ОДНИМ простым предложением без литературных красот.
    Например: "Утром был сонный, на работе взбодрился, к вечеру устал"
    Или: "Весь день было хорошее настроение"
    Или: "Начал нервно, но постепенно успокоился"

    Говори как обычный человек, НЕ как писатель."""
        
        result = await Runner.run(emotion_analyzer_agent, prompt)
        return result.raw_output.strip()
    
    def _extract_key_moments(self, interactions, transactions) -> List[str]:
        """Извлекает ключевые моменты дня"""
        
        moments = []
        
        # Важные разговоры
        for interaction in interactions:
            if any(word in interaction.emotional_impact.lower() 
                   for word in ['конфликт', 'радость', 'тревога', 'воодушевление']):
                moments.append(f"разговор с {interaction.with_person}")
        
        # Крупные покупки
        major_purchases = [t for t in transactions if t.amount > 2000]
        for purchase in major_purchases:
            moments.append(f"покупка: {', '.join(purchase.items[:2])}")
        
        # Новые места
        common_places = ['магазин', 'кафе', 'аптека', 'метро']
        new_places = [
            t.place for t in transactions 
            if not any(common in t.place.lower() for common in common_places)
        ]
        for place in new_places[:1]:  # максимум 1
            moments.append(f"посещение: {place}")
        
        return moments[:3]  # максимум 3 момента
    
    def _detect_new_patterns(
        self, 
        transactions, 
        memory_context: Dict[str, Any]
    ) -> Optional[List[str]]:
        """Определяет новые паттерны поведения"""
        
        new_patterns = []
        
        # Проверяем новые категории
        past_categories = set()
        for day in memory_context.get('recent_days', []):
            for trans in day.get('transactions', []):
                past_categories.add(trans.get('category'))
        
        current_categories = {t.category for t in transactions}
        new_categories = current_categories - past_categories
        
        for cat in new_categories:
            new_patterns.append(f"новая категория трат: {cat}")
        
        # Проверяем необычно высокие траты
        current_total = sum(t.amount for t in transactions)
        past_average = memory_context.get('average_daily_spending', 0)
        
        if past_average > 0 and current_total > past_average * 1.5:
            new_patterns.append("повышенный уровень трат")
        
        return new_patterns if new_patterns else None