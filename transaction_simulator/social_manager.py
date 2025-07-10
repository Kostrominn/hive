"""Управление социальными взаимодействиями - естественный подход"""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models import Person, Runner, Agent
from .agents import daily_social_agent, group_chat_agent
from .prompts import build_daily_social_prompt
from .transaction_models import SocialInteraction, ChatMessage


# Агент для генерации социального окружения
social_circle_generator = Agent(
    name="SocialCircleGenerator",
    description="Генерирует реалистичное социальное окружение для человека",
    instructions="""Создай реалистичное социальное окружение для человека.

На основе профиля определи:
1. Кто входит в его близкий круг (семья, лучшие друзья)
2. Кто в расширенном круге (коллеги, знакомые)
3. Характер отношений с каждым
4. Частоту общения

Учитывай:
- Семейное положение (есть ли супруг, дети, родители)
- Профессию (коллеги по работе)
- Возраст и интересы (друзья)
- Регион проживания

Формат ответа - JSON:
{
  "close_circle": [
    {
      "id": "spouse_1",
      "name": "Елена",
      "relation": "жена",
      "age": 32,
      "description": "работает учителем, заботливая",
      "communication_frequency": "ежедневно",
      "relationship_quality": "близкие, теплые"
    }
  ],
  "extended_circle": [
    {
      "id": "colleague_1", 
      "name": "Андрей",
      "relation": "коллега",
      "age": 35,
      "description": "энергичный, любит спорт",
      "communication_frequency": "в рабочие дни",
      "relationship_quality": "приятельские"
    }
  ],
  "potential_new_contacts": [
    "сосед по дому",
    "родители одноклассников ребенка",
    "люди из спортзала"
  ]
}"""
)


class SocialEnvironment:
    """Социальное окружение персонажа"""
    
    def __init__(self, target_person: Person):
        self.target = target_person
        self.close_circle = []
        self.extended_circle = []
        self.all_contacts = {}
        self.interaction_history = []
        
    async def generate_initial_environment(self):
        """Генерирует начальное социальное окружение через LLM"""
        
        prompt = f"""Создай социальное окружение для человека:

ПРОФИЛЬ:
- Имя: {self.target.name}
- Возраст: {self.target.age}, {self.target.gender}
- Профессия: {self.target.profession}
- Семья: {self.target.family_status}, детей: {self.target.children}
- Регион: {self.target.region} ({self.target.city_type})
- Доход: {self.target.income_level}

КОНТЕКСТ ЖИЗНИ:
{self.target.context}

Создай реалистичное окружение с конкретными людьми."""
        
        result = await Runner.run(social_circle_generator, prompt)
        social_data = json.loads(result.raw_output)
        
        self.close_circle = social_data.get('close_circle', [])
        self.extended_circle = social_data.get('extended_circle', [])
        
        # Индексируем всех людей
        for person in self.close_circle + self.extended_circle:
            self.all_contacts[person['id']] = person
    
    def get_all_available_people(self) -> List[Dict[str, Any]]:
        """Возвращает всех людей из окружения для выбора LLM"""
        return self.close_circle + self.extended_circle
    
    def update_relationship_quality(self, person_id: str, interaction_summary: str):
        """Обновляет качество отношений после взаимодействия"""
        self.interaction_history.append({
            'person_id': person_id,
            'summary': interaction_summary,
            'timestamp': datetime.now()
        })

    async def add_new_person(self, context: str, event_type: str) -> Dict[str, Any]:
        """Добавляет нового человека в окружение"""
        
        prompt = f"""Добавь нового человека в социальное окружение в связи с событием "{event_type}".

Контекст: {context}

Профиль целевого человека:
- Возраст: {self.target.age}
- Профессия: {self.target.profession}
- Семья: {self.target.family_status}
- Регион: {self.target.region}

Создай одного нового человека в формате:
{{
  "id": "new_person_1",
  "name": "Имя",
  "relation": "отношение",
  "age": возраст,
  "description": "описание",
  "communication_frequency": "частота",
  "relationship_quality": "качество отношений"
}}"""
        
        result = await Runner.run(social_circle_generator, prompt)
        new_person_data = json.loads(result.raw_output)
        
        # Добавляем в расширенный круг
        self.extended_circle.append(new_person_data)
        self.all_contacts[new_person_data['id']] = new_person_data
        
        return new_person_data


class SocialInteractionManager:
    """Менеджер социальных взаимодействий - естественный подход"""
    
    def __init__(self, target_person: Person, social_environment: SocialEnvironment):
        self.target = target_person
        self.environment = social_environment
        
    async def generate_daily_interactions(
        self,
        day_context: Dict[str, Any],
        memory: Dict[str, Any]
    ) -> List[SocialInteraction]:
        """Генерирует взаимодействия на день через LLM без искусственных ограничений"""
        
        all_available_people = self.environment.get_all_available_people()
        
        if not all_available_people:
            return []
        
        # Просто передаем всех людей LLM и позволяем ей самой решать
        prompt = self._build_comprehensive_social_prompt(
            all_available_people,
            day_context,
            memory
        )
        
        result = await Runner.run(daily_social_agent, prompt)
        
        # Безопасный парсинг JSON
        try:
            interactions_data = json.loads(result.raw_output)
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            print(f"Сырой ответ: {result.raw_output}")
            return []
        
        # Преобразуем в модели с валидацией
        interactions = []
        for int_data in interactions_data.get('interactions', []):
            try:
                # Валидация данных взаимодействия
                if not isinstance(int_data, dict):
                    print(f"❌ Взаимодействие не является словарем: {int_data}")
                    continue
                    
                if 'with_person' not in int_data or 'context' not in int_data:
                    print(f"❌ Отсутствуют обязательные поля: {int_data}")
                    continue
                
                # Безопасный парсинг чата
                chat_messages = []
                chat_data = int_data.get('chat', [])
                
                if isinstance(chat_data, list):
                    for msg in chat_data:
                        if isinstance(msg, dict) and 'from' in msg and 'text' in msg:
                            chat_messages.append(ChatMessage(
                                from_person=msg['from'],
                                text=msg['text']
                            ))
                        elif isinstance(msg, dict) and 'from_person' in msg and 'text' in msg:
                            # Альтернативный формат
                            chat_messages.append(ChatMessage(
                                from_person=msg['from_person'],
                                text=msg['text']
                            ))
                        else:
                            print(f"❌ Неправильный формат сообщения: {msg}")
                            continue
                else:
                    print(f"❌ Чат не является списком: {chat_data}")
                
                interaction = SocialInteraction(
                    with_person=int_data['with_person'],
                    context=int_data['context'],
                    chat=chat_messages,
                    emotional_impact=int_data.get('emotional_impact', 'нейтральное')
                )
                interactions.append(interaction)
                
                # Обновляем историю отношений
                person_id = self._find_person_id(int_data['with_person'])
                if person_id:
                    self.environment.update_relationship_quality(
                        person_id,
                        int_data.get('emotional_impact', '')
                    )
                    
            except Exception as e:
                print(f"❌ Ошибка при обработке взаимодействия: {e}")
                print(f"Данные: {int_data}")
                continue
        
        return interactions
    
    def _build_comprehensive_social_prompt(
    self,
    all_people: List[Dict[str, Any]],
    day_context: Dict[str, Any],
    memory: Dict[str, Any]
) -> str:
        """Строит детализированный промпт с учётом всех данных о персонаже"""
        
        age = self.target.age or 25
        
        # Извлекаем данные о речевом профиле
        rhetorical_manner = getattr(self.target, 'rhetorical_manner', {}) or {}
        speech_profile = getattr(self.target, 'speech_profile', {}) or {}
        trigger_points = getattr(self.target, 'trigger_points', []) or []
        interpretation_biases = getattr(self.target, 'interpretation_biases', {}) or {}
        meta_self_view = getattr(self.target, 'meta_self_view', {}) or {}
        
        # Формируем речевые характеристики
        speech_characteristics = []
        
        # Манера речи
        if rhetorical_manner:
            speech_characteristics.append(f"Манера речи: {rhetorical_manner}")
        
        # Речевая маска
        if speech_profile:
            speech_characteristics.append(f"Речевой профиль: {speech_profile}")
        
        # Триггерные точки
        triggers_text = ""
        if trigger_points:
            triggers_text = f"""
    ТРИГГЕРНЫЕ ТОЧКИ (избегай или используй осторожно):
    {chr(10).join([f"- {trigger}" for trigger in trigger_points])}
    """
        
        # Психологические особенности
        psychology_text = ""
        if interpretation_biases:
            psychology_text += f"""
    ОСОБЕННОСТИ МЫШЛЕНИЯ:
    {chr(10).join([f"- {key}: {value}" for key, value in interpretation_biases.items()])}
    """
        
        if meta_self_view:
            psychology_text += f"""
    САМОВОСПРИЯТИЕ:
    {chr(10).join([f"- {key}: {value}" for key, value in meta_self_view.items()])}
    """
        
        # Определяем речевой стиль по образованию
        education_level = self.target.education or "среднее"
        
        if "начальное" in education_level.lower() or "неполное" in education_level.lower():
            speech_style = "простая разговорная речь, много сленга, короткие фразы"
            speech_examples = ["Чё как дела?", "Да нормально", "Заебись!", "Хреново"]
        elif "среднее" in education_level.lower() and "специальное" not in education_level.lower():
            speech_style = "обычная разговорная речь, умеренный сленг"
            speech_examples = ["Как дела?", "Да нормально всё", "Классно!", "Блин"]
        elif "среднее специальное" in education_level.lower() or "техникум" in education_level.lower():
            speech_style = "профессиональная речь, меньше сленга, конкретность"
            speech_examples = ["По работе как дела?", "Смену отработал", "Нормально", "Достало"]
        elif "высшее" in education_level.lower():
            speech_style = "литературная речь, развернутые предложения, вежливость"
            speech_examples = ["Как дела на работе?", "В целом неплохо", "Прекрасно", "Сожалею"]
        elif "кандидат" in education_level.lower() or "доктор" in education_level.lower():
            speech_style = "книжная речь, сложные конструкции, формальность"
            speech_examples = ["Как обстоят дела?", "Есть результаты", "Весьма интересно"]
        else:
            speech_style = "обычная разговорная речь"
            speech_examples = ["Как дела?", "Нормально", "Хорошо"]
        
        # Учитываем идеологию и ценности
        ideology_influence = ""
        if self.target.ideology:
            ideology_influence = f"""
    ИДЕОЛОГИЧЕСКИЕ ОСОБЕННОСТИ: {self.target.ideology}
    - Может влиять на темы разговоров и оценки событий
    - Формирует отношение к политике, обществу, работе
    """
        
        # Учитываем доверие к институтам
        trust_context = ""
        if self.target.state_trust or self.target.media_trust:
            trust_context = f"""
    ОТНОШЕНИЕ К ИНСТИТУТАМ:
    - Доверие к государству: {self.target.state_trust or 'не указано'}
    - Доверие к медиа: {self.target.media_trust or 'не указано'}
    - Может влиять на отношение к новостям, властям, официальной информации
    """
        
        # Учитываем военный контекст
        military_context = ""
        if self.target.military_context:
            military_context = f"""
    ВОЕННЫЙ КОНТЕКСТ: {self.target.military_context}
    - Может влиять на отношение к армии, войне, службе
    - Формирует специфическую лексику и взгляды
    """
        
        # Семейный контекст
        family_context = ""
        if self.target.family_status != "не женат" and self.target.family_status != "не замужем":
            family_context = f"""
    СЕМЕЙНЫЙ СТАТУС: {self.target.family_status}
    - Детей: {self.target.children or 0}
    - Влияет на темы разговоров, приоритеты, лексику
    - Семейные люди говорят о доме, детях, бытовых вопросах
    """
        
        # Профессиональный контекст
        profession_context = ""
        if self.target.profession:
            profession_context = f"""
    ПРОФЕССИОНАЛЬНЫЙ КОНТЕКСТ:
    - Профессия: {self.target.profession}
    - Занятость: {self.target.employment or 'не указано'}
    - Доход: {self.target.income_level or 'не указан'}
    - Влияет на лексику, темы разговоров, график общения
    """
        
        # Региональные особенности
        regional_context = ""
        if self.target.region:
            regional_context = f"""
    РЕГИОНАЛЬНЫЕ ОСОБЕННОСТИ:
    - Регион: {self.target.region}
    - Тип места: {self.target.city_type or 'не указан'}
    - Может влиять на диалектные особенности, менталитет
    """
        
        # Религиозный контекст
        religion_context = ""
        if self.target.religion:
            religion_context = f"""
    РЕЛИГИОЗНЫЙ КОНТЕКСТ: {self.target.religion}
    - Может влиять на лексику, темы разговоров, оценки
    - Формирует отношение к праздникам, традициям, морали
    """
        
        prompt = f"""Создай ГЛУБОКО ПЕРСОНАЛИЗИРОВАННЫЕ социальные взаимодействия для {self.target.name}.

    📊 ПОЛНЫЙ ПРОФИЛЬ ПЕРСОНАЖА:
    - Имя: {self.target.name}
    - Возраст: {age}, {self.target.gender}
    - Образование: {self.target.education or 'не указано'}
    - Профессия: {self.target.profession or 'не указана'}
    - Семья: {self.target.family_status}, детей: {self.target.children or 0}
    - Регион: {self.target.region} ({self.target.city_type or 'не указан'})

    🎭 РЕЧЕВЫЕ ХАРАКТЕРИСТИКИ:
    Базовый стиль: {speech_style}
    Примеры фраз: {', '.join(speech_examples)}
    {chr(10).join(speech_characteristics) if speech_characteristics else ""}

    {triggers_text}

    {psychology_text}

    {ideology_influence}

    {trust_context}

    {military_context}

    {family_context}

    {profession_context}

    {regional_context}

    {religion_context}

    🏠 КОНТЕКСТ ЖИЗНИ:
    {self.target.context}

    📅 СЕГОДНЯШНИЙ ДЕНЬ:
    - День недели: {day_context.get('day_of_week', 'неизвестно')}
    - Погода: {day_context.get('weather', 'обычная')}
    - События: {', '.join(day_context.get('events', ['обычный день']))}

    👥 ДОСТУПНЫЕ ЛЮДИ:
    {chr(10).join([
        f"- {p['name']} ({p['relation']}, {p.get('age', '?')} лет) - {p.get('description', 'нет описания')}"
        for p in all_people
    ])}

    📖 НЕДАВНИЕ ВЗАИМОДЕЙСТВИЯ:
    {chr(10).join([
        f"- {day['date']}: общался с {day.get('key_interaction', 'никем особенным')}"
        for day in memory.get('recent_days', [])[-3:]
    ]) if memory.get('recent_days') else "Нет данных"}

    🎯 ЗАДАЧА:
    Создай взаимодействия, которые ИДЕАЛЬНО отражают личность {self.target.name}:

    1. ИСПОЛЬЗУЙ ВСЕ ДАННЫЕ О ПЕРСОНАЖЕ:
    - Речевой стиль должен соответствовать образованию и профессии
    - Темы разговоров должны отражать интересы и ценности
    - Реакции должны учитывать триггерные точки
    - Манера общения должна соответствовать самовосприятию

    2. УЧИТЫВАЙ ПСИХОЛОГИЮ:
    - Как этот человек РЕАЛЬНО отвечает на вопросы?
    - Что его волнует, раздражает, радует?
    - Как его идеология влияет на оценки?
    - Как семейный статус влияет на приоритеты?

    3. ДЕЛАЙ ДИАЛОГИ ЖИВЫМИ:
    - Не все взаимодействия позитивные
    - Люди устают, раздражаются, отвлекаются
    - Учитывай настроение и обстоятельства
    - Покажи уникальность каждого персонажа

    4. EMOTIONAL_IMPACT - ПРОСТО И ЧЕСТНО:
    - "нормально поговорили"
    - "слегка раздражает"
    - "поддержал"
    - "как обычно"
    - "приятно"
    - "напряжно"

    СОЗДАЙ JSON:
    {{
    "interactions": [
        {{
        "with_person": "Имя",
        "context": "детальный контекст: где, когда, почему, обстоятельства",
        "chat": [
            {{"from": "Имя", "text": "реплика, отражающая характер говорящего"}},
            {{"from": "{self.target.name}", "text": "ответ, ИДЕАЛЬНО соответствующий профилю {self.target.name}"}},
            {{"from": "Имя", "text": "продолжение диалога"}},
            {{"from": "{self.target.name}", "text": "реакция {self.target.name} с учётом всех его особенностей"}}
        ],
        "emotional_impact": "простое описание"
        }}
    ]
    }}

    ПОМНИ: Каждый диалог должен быть УНИКАЛЬНЫМ отражением личности {self.target.name}!
    Используй ВСЕ данные о нём для создания максимально реалистичных взаимодействий."""

        return prompt
    
    def _find_person_id(self, name: str) -> Optional[str]:
        """Находит ID человека по имени"""
        for person_id, person_data in self.environment.all_contacts.items():
            if person_data['name'] == name:
                return person_id
        return None