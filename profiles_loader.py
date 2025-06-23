import os
import pandas as pd
import math
import json
from typing import List
from models import Person

def fix_nan(value):
    return None if value is None or (isinstance(value, float) and math.isnan(value)) else value

def try_parse_json(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return value

def df_to_people_extended(df: pd.DataFrame) -> List[Person]:
    people = []
    for _, row in df.iterrows():
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
            )
            people.append(person)
        except Exception as e:
            print(f"⚠️ Ошибка валидации строки:\n{e}\n---\n{row.to_dict()}\n")
    return people

def load_people(path: str, limit: int = 10) -> List[Person]:
    people = []
    files = sorted([
        f for f in os.listdir(path)
        if f.endswith(".csv")
    ])[:limit]

    for filename in files:
        file_path = os.path.join(path, filename)
        try:
            df = pd.read_csv(file_path)
            new_people = df_to_people_extended(df)
            people.extend(new_people)
        except Exception as e:
            print(f"⚠️ Ошибка при чтении {filename}: {e}")

    return people