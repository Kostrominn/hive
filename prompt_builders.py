import json
from typing import Dict, Any, List
from models import Person, Agent
from llm_api import call_openai
import re

from prompts import build_cognitive_frame_summary_system_message, build_cognitive_frame_summary_few_shot
from prompts import build_llm_prompt_for_speech_profile_prompt, build_speech_template_prompt
from prompts import build_speech_prompt_prompt, build_full_prompt_prompt, build_president_prompt_prompt
from prompts import analyse_dialogue_prompt, build_selection_prompt_prompt, build_vote_prompt_prompt, build_distribution_prompt_prompt

from history_analyzer import find_relevant_history_llm, format_selected_history

def clean(name: str) -> str:
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'\s*-\s*', ' - ', name)
    return name

def _safe_json_loads(text: str) -> Dict:
    try:
        return json.loads(text)
    except Exception:
        return {}

def analyse_dialogue(history_snippet: str, me: str) -> (List[Dict[str, str]], str):
    raw = call_openai(analyse_dialogue_prompt(history_snippet, me)) or ""
    if not isinstance(raw, str):
        raw = getattr(raw, "final_output", "") or ""
    data = _safe_json_loads(raw)
    reactions = [
        r for r in data.get("reactions", [])
        if isinstance(r, dict)
           and isinstance(r.get("to"), str)
           and r.get("mode") in {"agree", "disagree", "ignore"}
    ]
    new_point = data.get("new_point", "") if isinstance(data.get("new_point", ""), str) else ""
    return reactions, new_point

def person_short_card(p: Person) -> str:
    fields = [
        f"gender={p.gender}",
        f"age={p.age or 'n/a'}",
        f"region={p.region}",
        f"profession={p.profession or 'n/a'}",
        f"ideology={p.ideology or 'n/a'}",
        f"rhetoric={p.rhetorical_manner or 'n/a'}",
        f"triggers={p.trigger_points or 'n/a'}",
        f"context={p.context or 'n/a'}",
    ]
    return f"id={p.id}; " + "; ".join(fields)



def select_panelists_with_call_openai(topic: str, people: List[Person], number_of_people: int) -> List[Person]:
    """
    Выбирает количество людей, указанное в ``number_of_people``, для участия в дискуссии.
    """
    prompt = build_selection_prompt(topic, people, number_of_people)
    print(prompt)
    print('*'*50)
    raw_json = call_openai([{"role": "user", "content": prompt}])
    print("Полученный raw_json:")
    print(f"Тип: {type(raw_json)}")
    print(f"Длина: {len(raw_json) if raw_json else 'None/Empty'}")
    print(f"Содержимое: '{raw_json}'")
    print("="*50)
    data = json.loads(raw_json)
    
    print("Причина выбора:", data.get("reason", ""))
    ids = data.get("selection", [])
    print(ids)
    if not isinstance(ids, list):
        raise ValueError("selection must be a list")
    if len(ids) != number_of_people:
        raise ValueError(f"LLM вернуло {len(ids)} ID вместо {number_of_people}: {ids}")

    id_to_person = {p.id.strip(): p for p in people}
    norm_person = {clean(k): v for k, v in id_to_person.items()}

    try:
        selected = [
            norm_person[clean(i)]
            for i in ids
            if clean(i) in norm_person
        ]
    except KeyError as miss:
        raise KeyError(f"ID {miss} нет в списке кандидатов")

    return selected

def build_cognitive_frame_summary(cognitive_frame: Dict[str, Any]) -> str:
    user_message = json.dumps({"Когнитивная рамка": cognitive_frame}, ensure_ascii=False, indent=2)
    messages = (
        [{"role": "system", "content": build_cognitive_frame_summary_system_message}]
        + build_cognitive_frame_summary_few_shot
        + [{"role": "user", "content": user_message}]
    )
    return call_openai(messages)

def build_llm_prompt_for_speech_profile(rhetorical_manner: Dict[str, Any]) -> str:
    return call_openai(build_llm_prompt_for_speech_profile_prompt(rhetorical_manner))

def build_speech_template(person: Person) -> str:
    return call_openai(build_speech_template_prompt(person))

def render_reactions(rc: List[Dict[str, str]]) -> str:
    if not rc:
        return "- прямых обращений нет; можешь сам выбрать, к кому подойти."
    mapping = {"agree": "кратко согласись", "disagree": "кратко возрази", "ignore": "можешь игнорировать"}
    return "\n".join(f"- **{r['to']}** — {mapping[r['mode']]}" for r in rc)

def build_full_prompt(person: Person, context_snippet: str, history_snippet: str, conflict_notice: str, topic: str, own_lines: str) -> str:
    reactions, new_pt = analyse_dialogue(
        history_snippet=history_snippet, me=person.name
    )
    reactions_block = render_reactions(reactions)
    new_point_line  = new_pt if new_pt else "Придумай свежий аспект сам."
    prompt = build_full_prompt_prompt(
    person,
    context_snippet,
    conflict_notice,
    topic,
    own_lines,
    reactions_block,
    new_point_line
)
    prompt += f"\n🧠 Когнитивная рамка:\n{build_cognitive_frame_summary(person.cognitive_frame)}\n"
    prompt += f"\nВ качестве структуры фразы, используй шаблон {build_speech_template(person)}, НО если все твои реплики из одного и того же шаблона, выбери другой шаблон.\n"
    
    return prompt


def build_president_full_prompt(person: Person, context: str, history_snippet: str, conflict_notice: str, topic: str, own_lines: str) -> str:
    reactions, new_pt = analyse_dialogue(
        history_snippet=history_snippet, me=person.name
    )
    reactions_block = render_reactions(reactions)
    new_point_line  = new_pt if new_pt else "Придумай свежий аспект сам."
    prompt = build_president_prompt_prompt(
    person,
    context,
    conflict_notice,
    topic,
    own_lines,
    reactions_block,
    new_point_line
)
    prompt += f"\n🧠 Когнитивная рамка:\n{build_cognitive_frame_summary(person.cognitive_frame)}\n"
    prompt += f"\nВ качестве структуры фразы, используй шаблон {build_speech_template(person)}, НО если все твои реплики из одного и того же шаблона, выбери другой шаблон.\n"
    
    return prompt

def build_speech_prompt(person: Person, answer: str, own_lines: str, history_sinppet: str) -> str:
    speech_profile = build_llm_prompt_for_speech_profile(person.speech_profile)
    prompt = build_speech_prompt_prompt(person, answer, own_lines, history_sinppet, speech_profile)
    prompt += f"\n🧠 Когнитивная рамка:\n{build_cognitive_frame_summary(person.cognitive_frame)}\n"
    print(prompt)
    return prompt

def build_selection_prompt(topic: str, people: List[Person], number_of_people: int) -> str:
    header = f"Тема дискуссии: {topic}\n\nСписок кандидатов:"
    body_lines = [
        f"{idx+1}) id={p.id}: {person_short_card(p)}"
        for idx, p in enumerate(people)
    ]
    body = "\n".join(body_lines)

    return f"{build_selection_prompt_prompt(number_of_people)}\n\n{header}\n{body}\n\nОтвет:"

def build_vote_prompt(person: Person, candidates: List[str], history_snippet: str, context) -> str:
    candidate_str = ", ".join(candidates)
    print('candidate_str', candidate_str)
    return build_vote_prompt_prompt(person, candidate_str, history_snippet, context)

def build_distribution_prompt(person: Person, money: int, resources, context: str) -> str:
    return build_distribution_prompt_prompt(person, money, resources, context)

async def build_full_prompt_with_history(person: Person, context_snippet: str, history_snippet: str, 
                                       conflict_notice: str, topic: str, own_lines: str, 
                                       recent_messages: List[str]) -> str:
    
    # RAG по истории через LLM
    relevant_events = await find_relevant_history_llm(person, topic, recent_messages, max_events=25)
    
    # Существующий промпт + история
    base_prompt = build_full_prompt_prompt(person, context_snippet, conflict_notice, topic, own_lines, 
                                         "", "Придумай свежий аспект сам.")
    
    # Добавляем релевантную историю
    if relevant_events:
        history_context = format_selected_history(relevant_events)
        base_prompt += f"\n{history_context}\n"
        base_prompt += "💡 Используй эти воспоминания для обоснования своей позиции, если они подходят к теме.\n"
    
    return base_prompt

async def build_president_full_prompt_with_history(person: Person, context: str, conflict_notice: str, 
                                                 topic: str, own_lines: str, recent_messages: List[str]) -> str:
    
    # RAG по истории
    relevant_events = await find_relevant_history_llm(person, topic, recent_messages, max_events=10)

    # Существующий промпт
    base_prompt = build_president_prompt_prompt(person, context, conflict_notice, topic, own_lines,
                                              "", "Придумай свежий аспект сам.")
    
    # Добавляем историю
    if relevant_events:
        history_context = format_selected_history(relevant_events)
        base_prompt += f"\n{history_context}\n"
        base_prompt += "🎯 Можешь опираться на данные воспоминания в аргументации.\n"
    
    return base_prompt
