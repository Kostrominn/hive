from typing import List
from models import Person, HistoryEvent, Agent
from llm_api import call_openai
import json

history_rag_agent = Agent(
    name="HistoryRAGAgent", 
    description="Находит релевантные события из истории для текущего контекста",
    instructions="""
    Ты получаешь:
    1. Тему обсуждения
    2. Последние 3-5 сообщений из диалога  
    3. События из истории человека

    Выбери 2-3 наиболее релевантных события, которые:
    - Объясняют текущую позицию человека
    - Связаны с темой обсуждения
    - Формируют его мировоззрение
    - Вызывают эмоциональный отклик

    Верни JSON: {"selected_events": [1, 5, 12], "reasoning": "краткое объяснение выбора"}
    """,
    output_type=None
)

async def find_relevant_history_llm(
    person: Person,
    topic: str, 
    recent_messages: List[str],
    max_events: int = 10
) -> List[HistoryEvent]:
    """Только LLM подход - никаких keywords"""
    
    if not person.full_history or len(person.full_history) == 0:
        return []
    
    # Формируем компактные данные для LLM
    events_summary = []
    for event in person.full_history:
        compact = {
            "id": event.id,
            "stage": event.life_stage,
            "theme": event.theme, 
            "summary": event.summary[:100],  # обрезаем для экономии токенов
        }
        if event.emotion:
            compact["emotion"] = event.emotion
        if event.values:
            compact["values"] = event.values[:50]
        events_summary.append(compact)
    
    prompt = f"""Ты анализируешь историю человека для политической дискуссии.

Тема дискуссии: {topic}

Недавние сообщения в чате:
{chr(10).join(recent_messages[-5:]) if recent_messages else "Нет сообщений"}

События из жизни человека:
{json.dumps(events_summary[:20], ensure_ascii=False, indent=1)}

ЗАДАЧА: Выбери {max_events} самых релевантных события, которые:
- Объясняют позицию человека по теме дискуссии
- Формируют его мировоззрение 
- Связаны с политикой, властью, справедливостью, деньгами

ВАЖНО: Ответь ТОЛЬКО валидным JSON в формате:
{{"selected_events": [1, 5, 12], "reasoning": "краткое объяснение"}}

Не добавляй никакого другого текста!"""
    
    try:
        result = call_openai([{"role": "user", "content": prompt}])
        data = json.loads(result)
        selected_ids = data.get("selected_events", [])
        
        # Возвращаем полные события по ID
        selected_events = []
        for event_id in selected_ids:
            for event in person.full_history:
                if event.id == event_id:
                    selected_events.append(event)
                    break
        
        return selected_events[:max_events]
        
    except Exception as e:
        print(f"Ошибка LLM-RAG для истории: {e}")
        # Fallback - берем первые несколько событий
        return person.full_history[:max_events]

def format_selected_history(events: List[HistoryEvent]) -> str:
    """Форматируем выбранные события для промпта"""
    if not events:
        return ""
    
    formatted = []
    for event in events:
        event_str = f"📅 {event.life_stage}: {event.summary}"
        if event.emotion:
            event_str += f" (чувствовал: {event.emotion})"
        if event.values:
            event_str += f" (ценности: {event.values})"
        formatted.append(event_str)
    
    return "🧠 Релевантные воспоминания:\n" + "\n".join(formatted)
