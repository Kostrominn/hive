"""Промпты для симулятора транзакций"""

from typing import List, Dict, Any
import json

# Импортируем базовые модели
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from models import Person


def build_daily_social_prompt(
    person: Person,
    available_people: List[Dict[str, str]],
    day_context: Dict[str, Any],
    memory: Dict[str, Any]
) -> str:
    """Строит промпт для генерации социальных взаимодействий"""
    
    # Форматируем доступных людей
    people_list = "\n".join([
        f"- {p['name']}: {p['relation']} ({p.get('description', '')})"
        for p in available_people
    ])
    
    # Форматируем память
    memory_str = ""
    if memory.get('recent_days'):
        memory_str = "\nПАМЯТЬ ПОСЛЕДНИХ ДНЕЙ:\n"
        for day in memory['recent_days'][-3:]:  # последние 3 дня
            memory_str += f"- {day['date']}: {day.get('key_interaction', 'обычный день')}\n"
    
    prompt = f"""Сгенерируй социальные взаимодействия для человека на день.

ПРОФИЛЬ:
- Имя: {person.name}
- Возраст: {person.age}, {person.gender}
- Профессия: {person.profession}
- Семья: {person.family_status}, детей: {person.children}
- Характер: {getattr(person, 'meta_self_view', {}) or 'не указан'}

КОНТЕКСТ ДНЯ:
- Дата: {day_context['date']}
- День недели: {day_context['day_of_week']}
- Тип дня: {'рабочий' if day_context.get('is_workday') else 'выходной'}
- События: {', '.join(day_context.get('events', ['обычный день']))}
- Погода: {day_context.get('weather', 'обычная')}

ДОСТУПНЫЕ ЛЮДИ ДЛЯ ОБЩЕНИЯ:
{people_list}

{memory_str}

ЭМОЦИОНАЛЬНОЕ СОСТОЯНИЕ: {memory.get('emotional_state', 'нормальное')}

Создай 2-4 реалистичных взаимодействия для этого дня.
Учти:
- В будни больше общения с коллегами
- Утром обычно семья
- Вечером возможны друзья
- Диалоги должны быть естественными, БЕЗ упоминания покупок

Ответь в формате JSON."""
    
    return prompt


def build_transaction_prompt(
    person: Person,
    day_context: Dict[str, Any],
    social_interactions: List[Dict[str, Any]],
    memory: Dict[str, Any],
    remaining_budget: float
) -> str:
    """Строит промпт для генерации транзакций"""
    
    # Форматируем социальные взаимодействия
    interactions_summary = "\nСОЦИАЛЬНЫЕ ВЗАИМОДЕЙСТВИЯ СЕГОДНЯ:\n"
    for interaction in social_interactions:
        interactions_summary += (
            f"- С {interaction['with_person']} ({interaction['context']}): "
            f"{interaction['emotional_impact']}\n"
        )
    
    # Эмоциональная траектория
    emotions = [i['emotional_impact'] for i in social_interactions]
    mood_flow = " → ".join(emotions) if emotions else "стабильное"
    
    # Крупные покупки из памяти
    recent_purchases = ""
    if memory.get('recent_major_purchases'):
        recent_purchases = "\nКРУПНЫЕ ПОКУПКИ ПОСЛЕДНИХ ДНЕЙ:\n"
        for p in memory['recent_major_purchases']:
            recent_purchases += f"- {p['date']}: {p['items']} за {p['amount']} руб\n"
    
    prompt = f"""Сгенерируй транзакции человека за день.

ПРОФИЛЬ:
- {person.gender}, {person.age} лет, {person.profession}
- Доход: {person.income_level}
- Семья: {person.family_status}
- Регион: {person.region} ({person.city_type})

ФИНАНСЫ:
- Дневной бюджет: около {remaining_budget:.0f} руб
- Уровень цен: {person.city_type}

КОНТЕКСТ ДНЯ:
- {day_context['day_of_week']}, {day_context['date']}
- События: {', '.join(day_context.get('events', ['обычный день']))}

{interactions_summary}

ЭМОЦИОНАЛЬНАЯ ДИНАМИКА: {mood_flow}

{recent_purchases}

Сгенерируй реалистичные покупки этого дня.
ВАЖНО:
- Покупки должны соответствовать профилю и доходу
- Детализируй что именно куплено (список товаров)
- Учитывай эмоциональное состояние
- НЕ превышай разумный дневной бюджет
- Включи как необходимые, так и импульсивные покупки

Ответь в формате JSON."""
    
    return prompt


def build_memory_update_prompt(
    daily_result: Dict[str, Any],
    previous_memory: Dict[str, Any]
) -> str:
    """Строит промпт для обновления памяти"""
    
    prompt = f"""Обнови память на основе прошедшего дня.

ПРОШЕДШИЙ ДЕНЬ:
- Дата: {daily_result['date']}
- Потрачено: {daily_result['day_summary']['total_spent']} руб
- Ключевые моменты: {', '.join(daily_result['day_summary']['key_moments'])}
- Настроение: {daily_result['day_summary']['mood_trajectory']}

ПРЕДЫДУЩАЯ ПАМЯТЬ:
{json.dumps(previous_memory, ensure_ascii=False, indent=2)}

Создай обновленную память, сохранив только важное для будущих дней.
Включи:
- Эмоциональное состояние
- Важные социальные моменты
- Крупные покупки (>1000 руб)
- Новые паттерны поведения

Ответ в формате JSON."""
    
    return prompt


def format_event_context(event_type: str, event_details: Dict[str, Any]) -> str:
    """Форматирует описание события для промпта"""
    
    event_descriptions = {
        "salary": f"Сегодня пришла зарплата: {event_details.get('amount', 'обычная')} руб",
        "promotion": "Сегодня объявили о повышении должности и зарплаты на 40%",
        "birthday": f"Сегодня день рождения {event_details.get('whose', 'персонажа')}",
        "holiday": f"Сегодня праздник: {event_details.get('name', 'выходной день')}",
        "personal": event_details.get('description', 'Произошло личное событие')
    }
    
    return event_descriptions.get(event_type, "")