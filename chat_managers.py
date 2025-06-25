from collections import defaultdict
from typing import List, Dict, Optional
from agent_functions import llm_check_repetition, llm_conflict_similarity
from prompt_builders import build_full_prompt
from agents import chat_agent
from models import Runner

class ConflictThread:
    def __init__(self, topic: str, question: str, initiator: str, target: str, round_started: int):
        self.topic = topic
        self.question = question
        self.sides = defaultdict(set)
        self.round_started = round_started
        self.resolved = False
        self.history = []
        # Automatically add the initiating parties to their respective sides
        self.add_to_side(initiator, "A")
        self.add_to_side(target, "B")

    def add_to_side(self, person: str, side: str):
        if person not in self.sides[side]:
            print(f"👥 {person} присоединился к стороне {side} в конфликте: {self.topic}")
        self.sides[side].add(person)

    def is_active(self, round_num: int) -> bool:
        return not self.resolved and round_num - self.round_started <= 5

    def get_opponents(self, name: str) -> List[str]:
        if name in self.sides["A"]:
            return list(self.sides["B"])
        elif name in self.sides["B"]:
            return list(self.sides["A"])
        return []

class ConflictManager:
    def __init__(self):
        self.conflicts: List[ConflictThread] = []
        self.current_round: int = 0
    
    def is_in_active_conflict(self, name: str) -> bool:
        return any(
            name in thread.sides["A"] or name in thread.sides["B"]
            for thread in self.conflicts if thread.is_active(self.current_round)
        )

    def was_targeted_in_conflict(self, name: str) -> bool:
        return any(
            name in thread.sides["B"]
            for thread in self.conflicts
            if thread.is_active(self.current_round)
        )

    def must_speak_due_to_conflict(self, name: str) -> bool:
        return self.is_in_active_conflict(name)

    async def find_similar_conflict(self, new_question: str, threshold: float = 0.8) -> Optional[ConflictThread]:
        for conflict in self.conflicts:
            if not conflict.resolved:
                similarity = await llm_conflict_similarity(new_question, conflict.question)
                if similarity > threshold:
                    return conflict
        return None

    async def create_conflict(self, topic: str, question: str, initiator: str, target: str, round_started: int) -> Optional[ConflictThread]:
        existing = await self.find_similar_conflict(question)
        if existing:
            print(f"🚫 Конфликт слишком похож на уже активный: {existing.question}")
            return None

        new_conflict = ConflictThread(topic, question, initiator, target, round_started)
        self.conflicts.append(new_conflict)
        print(f"🔥 Новый конфликт: {topic} между {initiator} и {target}")
        return new_conflict

    def check_for_resolved_conflicts(self, round_num: int, reset_callback):
        for conflict in self.conflicts:
            if not conflict.resolved and not conflict.is_active(round_num):
                conflict.resolved = True
                print(f"🧯 Конфликт завершён: {conflict.topic} между {list(conflict.sides['A'])} и {list(conflict.sides['B'])}")
                for name in conflict.sides["A"] | conflict.sides["B"]:
                    reset_callback(name)

    def get_active_conflict_between(self, person1: str, person2: str, round_num: int) -> Optional[ConflictThread]:
        for conflict in self.conflicts:
            if conflict.is_active(round_num):
                side_A = conflict.sides["A"]
                side_B = conflict.sides["B"]
                if (person1 in side_A and person2 in side_B) or (person1 in side_B and person2 in side_A):
                    return conflict
        return None
    

class RepetitionTracker:
    def __init__(self):
        self.recent_texts: Dict[str, List[str]] = defaultdict(list)

    def add_text(self, person: str, text: str):
        self.recent_texts[person].append(text)

    async def is_repetitive(self, person: str, new_text: str) -> bool:
        full_context = "\n".join(self.recent_texts[person][-5:])
        score = await llm_check_repetition(full_context, new_text)
        return score >= 0.9

class ParticipationManager:
    def __init__(self):
        self.state: Dict[str, Dict] = defaultdict(lambda: {
            "spoke_last_round": False,
            "note_type": None,
            "was_mentioned": False,
            "in_conflict": False,
            "conflict_targeted": False,
            "is_first_time": True,
            "repetition_score": 1.0,
            "conflict_topic": None
        })

    def update_state(self, name: str, **kwargs):
        self.state[name].update(kwargs)

    def get_score(self, name: str) -> float:
        s = self.state[name]
        score = 0.0
        if s["in_conflict"]:
            return 1.0
        if not s["spoke_last_round"]:
            score += 0.3
        if s["was_mentioned"]:
            score += 0.7
        if s["note_type"] == "desire":
            score += 0.6
        if s["note_type"] == "fatigue":
            score -= 0.8
        if s["in_conflict"]:
            score += 0.5
        if s["conflict_targeted"]:
            score += 0.6
        if s["is_first_time"]:
            score += 0.8
        return min(max(score, 0.0), 1.0)

class ReflectionManager:
    def __init__(self):
        self.log: Dict[str, List[Dict]] = defaultdict(list)

    def record_reflection(self, name: str, round_num: int, changed: bool, summary: str, influenced_by: Optional[str]):
        self.log[name].append({
            "round": round_num,
            "changed": changed,
            "summary": summary,
            "influenced_by": influenced_by
        })

    def get_latest(self, name: str) -> Optional[Dict]:
        return self.log[name][-1] if self.log[name] else None
    
    async def ask_reflection(self, person) -> str:
        context_snippet = person.context if isinstance(person.context, str) else ""

        history_snippet = "\n".join(f"{t['speaker']}: {t['text']}" for t in self.dialogue[-10:])

        prompt = build_full_prompt(person, context_snippet, history_snippet, conflict_notice = '', topic = self.topic, own_lines = '')
        prompt += (
            f"Что ты понял(а) за последние раунды обсуждения? Изменилась ли твоя точка зрения? Кто повлиял на тебя?\n"
            f"Ответь коротко и по существу."
        )
        result = await Runner.run(chat_agent, prompt)
        print(f"🔎 REFLECTION [{person.name}]: {result.final_output}")
        return result.final_output.strip()