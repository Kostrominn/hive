from typing import List, Optional, Dict, Any, Union
import json
import re
import csv
import glob
import os
import pandas as pd

from models import Agent, Runner, Person, HistoryEvent
from llm_api import call_openai
from pydantic import BaseModel


class CharacterProfile(BaseModel):
    """Profile structure mirroring :class:`Person` fields."""

    name: str
    id: Optional[str] = None
    gender: str
    age: Optional[int] = None
    birth_year: Optional[int] = None
    region: str
    city_type: Optional[str] = None
    education: Optional[str] = None
    profession: Optional[str] = None
    employment: Optional[str] = None
    income_level: Optional[str] = None
    family_status: Optional[str] = None

    children: Optional[Union[int, str]] = None
    religion: Optional[str] = None
    ideology: Optional[str] = None
    state_trust: Optional[str] = None
    media_trust: Optional[str] = None
    military_context: Optional[str] = None
    digital_literacy: Optional[str] = None
    context: Optional[str] = None

    cognitive_frame: Optional[Dict[str, Any]] = None
    rhetorical_manner: Optional[Dict[str, Any]] = None
    trigger_points: Optional[List[str]] = None
    interpretation_biases: Optional[Dict[str, Any]] = None
    meta_self_view: Optional[Dict[str, Any]] = None
    speech_profile: Optional[Dict[str, Any]] = None

    leisure_activity: Optional[str] = None
    weight: Optional[int] = None
    source_agent: Optional[str] = None


def _load_few_shots(n: int = 1, profiles_dir: str = "profiles") -> str:
    """Return JSON examples from existing profile CSV files."""
    files = sorted(glob.glob(os.path.join(profiles_dir, "*.csv")))[:n]
    examples: List[str] = []
    for path in files:
        try:
            with open(path, encoding="utf-8") as f:
                row = next(csv.DictReader(f))
                examples.append(json.dumps(row, ensure_ascii=False))
        except Exception:
            continue
    return "\n".join(examples)

def build_universal_agent(n: int) -> Agent:
    few_shots = _load_few_shots(2)
    instructions = f"""
Ты — UniversalCharacterAgent, создающий репрезентативную модель населения России.
Сгенерируй {n} вымышленных, но реалистичных персонажей, отражающих социально-демографический состав РФ.
Итоговая выборка должна в совокупности напоминать данные Росстата.

🎯 **Основные параметры для {n} персонажей:**

1. **Возраст (точное распределение для {n} человек):**
   - Пенсионеры (60+ лет): {int(n * 0.22)} человек
   - Студенты (18-25 лет): {int(n * 0.12)} человек  
   - Трудоспособное население (25-60 лет): {int(n * 0.60)} человек
   - Подростки/очень пожилые: {n - int(n * 0.94)} человек

2. **Пол:** {n//2} мужчин, {n - n//2} женщин

3. **Регион (для {n} человек):**
   - Москва и СПб: {int(n * 0.13)} человек
   - Областные центры: {int(n * 0.35)} человек
   - Малые города: {int(n * 0.28)} человек
   - Села и деревни: {n - int(n * 0.76)} человек
   - Включи разные регионы: Урал, Сибирь, Юг, Дальний Восток, Кавказ

4. **Доходы:**
   - Низкий: {int(n * 0.30)} человек
   - Средний: {int(n * 0.60)} человек  
   - Высокий: {n - int(n * 0.90)} человек

📋 **Обязательные поля для каждого персонажа:**

**Базовая информация:**
- `name`: Русское имя и фамилия
- `id`: тот же что name
- `gender`: "мужчина" | "женщина"
- `age`: число (без кавычек!)
- `birth_year`: 2025 - age
- `region`: конкретный регион/город РФ
- `city_type`: "мегаполис" | "областной центр" | "малый город" | "село"

**Социально-экономический статус:**
- `education`: "среднее" | "среднее специальное" | "высшее" | "неполное среднее"
- `profession`: конкретная профессия
- `employment`: "работает полный день" | "работает частично" | "безработный" | "на пенсии" | "студент"
- `income_level`: "низкий" | "средний" | "высокий"
- `family_status`: "холост" | "женат" | "разведен" | "вдовец"
- `children`: число или "нет детей"

**Мировоззрение:**
- `religion`: "православие" | "ислам" | "атеист" | "буддизм" | "другое"
- `ideology`: "консервативная" | "умеренная" | "либеральная" | "левые взгляды" | "аполитичный"
- `state_trust`: "высокое" | "среднее" | "низкое" | "критическое"
- `media_trust`: "высокое" | "среднее" | "низкое" | "критическое"
- `military_context`: "поддерживает СВО" | "нейтрально к СВО" | "против СВО" | "сложное отношение"
- `digital_literacy`: "низкая" | "средняя" | "высокая"

**Контекст и психология:**
- `context`: 2-3 предложения о жизненной ситуации, быте, основных проблемах

**Психологические профили (JSON-объекты):**

- `cognitive_frame`: объект с полями:
  {{
    "мир": "как воспринимает реальность",
    "агентность": "уровень веры в личное влияние", 
    "временная_перспектива": "фокус на прошлом/настоящем/будущем",
    "ключевые_понятия": ["3-4", "главных", "ценности"]
  }}

- `rhetorical_manner`: объект с полями:
  {{
    "стиль": "как говорит (прямо/эмоционально/сдержанно)",
    "структура": "как строит речь (хаотично/логично/ассоциативно)",
    "лексика": "словарный запас (простая/литературная/профессиональная)",
    "темп": "быстро/медленно/средне"
  }}

- `trigger_points`: массив строк - что вызывает сильные эмоции
  ["несправедливость", "угроза детям", "коррупция"] - примеры

- `interpretation_biases`: объект - как интерпретирует информацию:
  {{
    "экономика": "через призму личного опыта",
    "политика": "с недоверием к официальным источникам"
  }}

- `meta_self_view`: объект - как видит себя:
  {{
    "роль": "обычный человек/активист/жертва системы",
    "влияние": "могу/не могу влиять на происходящее"
  }}

- `speech_profile`: объект - особенности речи:
  {{
    "темп": "быстрый/средний/медленный",
    "эмоциональность": "высокая/средняя/низкая",
    "паузы": "много/мало",
    "любимые_слова": ["блин", "вообще", "конечно"]
  }}

📖 **Примеры из реальных профилей:**
{few_shots}

⚠️ **КРИТИЧЕСКИ ВАЖНО:**
1. Верни ТОЛЬКО JSON-массив, без markdown блоков ```json
2. Все числовые поля (age, birth_year, children-число) БЕЗ кавычек
3. Делай персонажей реалистичными - учитывай корреляции (село→низкий доход, высшее образование→выше доход)
4. Разнообразие мнений по СВО, власти, будущему страны
5. Психологические профили должны соответствовать социальному статусу
"""
    print(instructions)
    return Agent(
        name="UniversalCharacterAgent",
        description="Агент генерирует набор вымышленных персонажей",
        instructions=instructions,
        output_type=List[CharacterProfile],
    )


def _fix_common_json_errors(raw: str) -> str:
    raw = re.sub(r'"age"\s*:\s*"(\d{1,3})"', r'"age": \1', raw)
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw.removeprefix("```json").removesuffix("```").strip()
    if "]" in raw:
        raw = raw[: raw.rindex("]") + 1]
    return raw


def parse_result_to_characters(result) -> List[CharacterProfile]:
    raw = result.final_output
    if not isinstance(raw, str):
        return raw
    raw = _fix_common_json_errors(raw)
    data = json.loads(raw)
    return [CharacterProfile.model_validate(item) for item in data]


async def generate_characters(count: int, llm_caller=call_openai) -> List[CharacterProfile]:
    agent = build_universal_agent(count)
    result = await Runner.run(agent, " ", llm_caller)
    print(result)
    return parse_result_to_characters(result)


def characters_to_people(chars: List[CharacterProfile]) -> List[Person]:
    """Convert LLM character profiles to Person objects."""
    people: List[Person] = []
    for idx, ch in enumerate(chars):
        person = Person(
            name=ch.name,
            id=ch.id or str(idx),
            gender=ch.gender,
            age=ch.age,
            birth_year=ch.birth_year,
            region=ch.region,
            city_type=ch.city_type,
            education=ch.education,
            profession=ch.profession,
            employment=ch.employment,
            income_level=ch.income_level,
            family_status=ch.family_status,
            children=ch.children,
            religion=ch.religion,
            ideology=ch.ideology,
            state_trust=ch.state_trust,
            media_trust=ch.media_trust,
            military_context=ch.military_context,
            digital_literacy=ch.digital_literacy,
            context=ch.context,
            cognitive_frame=ch.cognitive_frame,
            rhetorical_manner=ch.rhetorical_manner,
            trigger_points=ch.trigger_points,
            interpretation_biases=ch.interpretation_biases,
            meta_self_view=ch.meta_self_view,
            speech_profile=ch.speech_profile,
        )
        people.append(person)
    return people