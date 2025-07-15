"""Модели данных для симулятора транзакций"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Импортируем базовые модели из основного проекта
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))


class ChatMessage(BaseModel):
    """Одно сообщение в чате"""
    from_person: str = Field(description="Кто отправил")
    text: str = Field(description="Текст сообщения")
    time: Optional[str] = Field(None, description="Время отправки")
    
    
class SocialInteraction(BaseModel):
    """Социальное взаимодействие за день"""
    with_person: str = Field(description="С кем общался")
    context: str = Field(description="Контекст общения (где, когда)")
    chat: List[ChatMessage] = Field(description="Содержание разговора")
    emotional_impact: str = Field(description="Эмоциональный эффект")
    interaction_type: str = Field(default="personal", description="personal/group")


class Transaction(BaseModel):
    """Модель транзакции"""
    time: str = Field(description="Время покупки HH:MM")
    amount: float = Field(description="Сумма")
    place: str = Field(description="Место покупки")
    items: List[str] = Field(description="Список конкретных товаров")
    category: str = Field(description="Категория трат")
    why: str = Field(description="Внутренняя мотивация")
    mood: str = Field(description="Настроение при покупке")
    influenced_by_chat: bool = Field(default=False)
    

class DayContext(BaseModel):
    """Контекст дня"""
    day_of_week: str
    events: List[str] = Field(default_factory=list)
    weather: str = Field(default="обычная")
    is_workday: bool = Field(default=True)
    special_date: Optional[str] = Field(None, description="Праздник или особая дата")


class DailySummary(BaseModel):
    """Итоги дня"""
    total_spent: float
    mood_trajectory: str
    key_moments: List[str]
    new_patterns: Optional[List[str]] = None


class DailyResult(BaseModel):
    """Полный результат симуляции одного дня"""
    date: str
    day_context: DayContext
    social_interactions: List[SocialInteraction]
    transactions: List[Transaction]
    day_summary: DailySummary
    
    
class MemoryContext(BaseModel):
    """Контекст памяти для следующего дня"""
    recent_days: List[Dict[str, Any]] = Field(
        description="Краткая информация о последних днях"
    )
    emotional_state: str = Field(description="Накопленное эмоциональное состояние")
    recent_major_purchases: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Крупные покупки за последние дни"
    )
    social_patterns: Dict[str, int] = Field(
        default_factory=dict,
        description="С кем как часто общался"
    )


class Event(BaseModel):
    """Запланированное событие"""

    day: int = Field(description="День симуляции (0-индекс)")
    type: str = Field(description="Тип события")
    description: Optional[str] = Field(
        default=None,
        description="Дополнительное описание события"
    )


class SimulationConfig(BaseModel):
    """Конфигурация симуляции"""
    target_person_id: str
    start_date: datetime
    days: int = Field(default=30)
    memory_window: int = Field(default=5, description="Дней в памяти")
    daily_budget_multiplier: float = Field(
        default=1.0, 
        description="Множитель дневного бюджета"
    )
    include_weekends: bool = Field(default=True)
    events: Optional[List[Event]] = Field(
        default=None,
        description="Запланированные события"
    )