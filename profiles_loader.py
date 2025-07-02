import os
import pandas as pd
import math
import json
from typing import List
from models import Person, HistoryEvent
from llm_api import call_openai

SCELETON_PATH = "./skeletons"

def fix_nan(value):
    return None if value is None or (isinstance(value, float) and math.isnan(value)) else value

def try_parse_json(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return value

def load_skeleton_history(skeleton_path: str) -> List[HistoryEvent]:
    """Загружает историю из skeleton файла"""
    try:
        df = pd.read_csv(skeleton_path)
        history = []
        for _, row in df.iterrows():
            event = HistoryEvent(
                id=int(row.get("id", 0)),
                life_stage=row.get("life_stage", ""),
                theme=row.get("theme", ""),
                summary=row.get("summary", ""),
                quote=row.get("quote") if pd.notna(row.get("quote")) else None,
                emotion=row.get("emotion") if pd.notna(row.get("emotion")) else None,
                values=row.get("values") if pd.notna(row.get("values")) else None,
                sociological_note=row.get("sociological_note") if pd.notna(row.get("sociological_note")) else None,
                type=row.get("type") if pd.notna(row.get("type")) else None,
            )
            history.append(event)
        return history
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке skeleton: {e}")
        return []

def df_to_people_extended(df: pd.DataFrame, profiles_path: str) -> List[Person]:
    people = []
    for _, row in df.iterrows():
        person_id = str(row["id"]) if pd.notna(row.get("id")) else "Без имени"
            
        # Загружаем историю из skeleton файла
        skeleton_file = None
        for filename in os.listdir(profiles_path):
            if filename.startswith(f"skeleton_{person_id}") and filename.endswith(".csv"):
                skeleton_file = os.path.join(profiles_path, filename)
                break
        
        full_history = []
        if skeleton_file and os.path.exists(skeleton_file):
            print(skeleton_file)
            full_history = load_skeleton_history(skeleton_file)
            print(f"✅ Загружена история для {person_id}: {len(full_history)} событий")
        
        try:
            person = Person(
                name=str(row["id"]) if pd.notna(row.get("id")) else "Без имени",
                id=str(row["id"]) if pd.notna(row.get("id")) else "Без имени",
                gender=row.get("gender") if pd.notna(row.get("gender")) else "Пол не ясен",
                age=int(row["age"]) if pd.notna(row.get("age")) else None,
                birth_year=int(row["birth_year"]) if pd.notna(row.get("birth_year")) else None,
                region=row.get("region") if pd.notna(row.get("region")) else "Регион не ясен",
                city_type=row.get("city_type") if pd.notna(row.get("city_type")) else None,
                education=row.get("education") if pd.notna(row.get("education")) else None,
                profession=row.get("profession") if pd.notna(row.get("profession")) else None,
                employment=row.get("employment") if pd.notna(row.get("employment")) else None,
                income_level=row.get("income_level") if pd.notna(row.get("income_level")) else None,
                family_status=row.get("family_status") if pd.notna(row.get("family_status")) else None,
                children = row["children"] if pd.notna(row.get("children")) else None,
                religion=row.get("religion") if pd.notna(row.get("religion")) else None,
                ideology=row.get("ideology") if pd.notna(row.get("ideology")) else None,
                state_trust=row.get("state_trust") if pd.notna(row.get("state_trust")) else None,
                media_trust=row.get("media_trust") if pd.notna(row.get("media_trust")) else None,
                military_context=row.get("military_context") if pd.notna(row.get("military_context")) else None,
                digital_literacy=row.get("digital_literacy") if pd.notna(row.get("digital_literacy")) else None,
                context=row.get("context") if pd.notna(row.get("context")) else None,
                cognitive_frame=try_parse_json(row.get("cognitive_frame")),
                rhetorical_manner=try_parse_json(row.get("rhetorical_manner")),
                trigger_points=try_parse_json(row.get("trigger_points")),
                interpretation_biases=try_parse_json(row.get("interpretation_biases")),
                meta_self_view=try_parse_json(row.get("meta_self_view")),
                speech_profile=try_parse_json(row.get("speech_profile")),
                full_history=full_history,
            )
            people.append(person)
        except Exception as e:
            print(f"⚠️ Ошибка валидации строки:\n{e}\n---\n{row.to_dict()}\n")
    return people

# def load_people(path: str, limit: int = 10) -> List[Person]:
#     people = []
#     files = sorted([
#         f for f in os.listdir(path)
#         if f.endswith(".csv")
#     ])[:limit]

#     for filename in files:
#         file_path = os.path.join(path, filename)
#         try:
#             df = pd.read_csv(file_path)
#             new_people = df_to_people_extended(df, SCELETON_PATH)
#             people.extend(new_people)
#         except Exception as e:
#             print(f"⚠️ Ошибка при чтении {filename}: {e}")

#     return people

def load_people(
    path: str | None,
    limit: int = 50,
    generate: int = 0,
    llm_caller=call_openai,
) -> List[Person]:
    """Load people either from CSV files or generate via LLM."""
    if generate > 0:
        from character_generator import generate_characters, characters_to_people
        import asyncio

        chars = asyncio.run(generate_characters(generate, llm_caller))
        return characters_to_people(chars)

    if not path:
        raise ValueError("path must be provided when generate=0")
    
    files = sorted([f for f in os.listdir(path) if f.endswith(".csv")])[:limit]
    people = []
    for filename in files:
        file_path = os.path.join(path, filename)
        try:
            df = pd.read_csv(file_path)
            new_people = df_to_people_extended(df, SCELETON_PATH)
            people.extend(new_people)
        except Exception as e:
            print(f"⚠️ Ошибка при чтении {filename}: {e}")

    return people

def save_people_to_file(people: List[Person], filename: str):
    """Сохраняет персонажей в файл"""
    # Конвертируем в DataFrame
    df = pd.DataFrame([p.model_dump() for p in people])
    
    # Сохраняем в CSV
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"💾 Сохранено {len(people)} персонажей в {filename}")
    
    # Дополнительно сохраняем в JSON для полного восстановления
    json_filename = filename.replace('.csv', '.json')
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump([p.model_dump() for p in people], f, ensure_ascii=False, indent=2)
    print(f"💾 Также сохранено в {json_filename}")

def load_people_from_file(filename: str) -> List[Person]:
    """Загружает персонажей из файла"""
    if filename.endswith('.json'):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        people = [Person(**item) for item in data]
    else:
        df = pd.read_csv(filename)
        people = [Person(**row.to_dict()) for _, row in df.iterrows()]
    
    print(f"📂 Загружено {len(people)} персонажей из {filename}")
    return people
