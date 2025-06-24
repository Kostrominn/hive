import json
from collections import defaultdict
from typing import List, Dict, Optional

from models import Runner
from llm_api import call_gemini
from agents import chat_agent, chat_speech_agent
from agent_functions import llm_check_repetition

from prompt_builders import select_panelists_with_call_openai, build_full_prompt, build_speech_prompt, build_vote_prompt

from chat_managers import RepetitionTracker, ParticipationManager, ReflectionManager, ConflictManager

def extract_text(res) -> str:
    if res is None:
        return ""
    return (getattr(res, "final_output", "") or "").strip()

def safe_parse_json(txt: str) -> Optional[dict]:
    if not txt.lstrip().startswith("{"):
        return None
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return None

class ChatSimulatorUtils:
    def __init__(self):
        self.repetition = RepetitionTracker()
        self.participation = ParticipationManager()
        self.reflection = ReflectionManager()
        self.conflict = ConflictManager()
        self.participation_log = defaultdict(dict)
        self.round_num = 0
        self.dialogue = []
        self.side_notes = defaultdict(list)
        self.turn_counts = defaultdict(int)
        self.initial_positions = {}
        self.final_positions = {}
        self.vote_history = []

    def _extract_note_type(self, person) -> Optional[str]:
        notes = self.side_notes.get(person.name, [])
        if any("устал" in note.lower() for note in notes):
            return "fatigue"
        if any("хочу высказаться" in note.lower() or "нужно сказать" in note.lower() for note in notes):
            return "desire"
        return None


    def build_context(self, history: List[Dict[str, str]]) -> str:
        context = f"📌 Тема обсуждения: {self.topic}\n\n"
        if history:
            context += "🔨️ Последние реплики:\n"
            context += "\n".join([f"{turn['speaker']}: {turn['text']}" for turn in history[-10:]])
        return context
    
    def reset_conflict_state(self, name: str):
        self.participation.update_state(
            name,
            in_conflict=False,
            conflict_targeted=False,
            conflict_topic=None
        )


    async def ask_position(self, person, phase: str) -> str:
        context_snippet = person.context if isinstance(person.context, str) else ""
        history_snippet = "\n".join(f"{t['speaker']}: {t['text']}" for t in self.dialogue[-10:])
        prompt = build_full_prompt(person, context_snippet, history_snippet, conflict_notice = '', topic = self.topic, own_lines = '')
        prompt += (
            f"Напиши, что ты думаешь по этой теме {'до начала' if phase == 'before' else 'после обсуждения'} обсуждения."
        )

        result = await Runner.run(chat_agent, prompt)
        print(f"🧭 {phase.upper()} [{person.id}]: {result.final_output}")
        return result.final_output.strip()
    
    
    async def generate_reply(self, person, context: str, history: List[Dict[str, str]]) -> str:
        context_snippet = person.context if isinstance(person.context, str) else ""

        if self.conflict.is_in_active_conflict(person.name):
            for thread in self.conflict.conflicts:
                if thread.is_active(self.round_num) and (person.name in thread.sides["A"] or person.name in thread.sides["B"]):
                    opponents = thread.get_opponents(person.name)
                    break
            else:
                opponents = []

            opponents_str = ", ".join(opponents) if opponents else "оппонентом"
            conflict_notice = (
                f"⚠️ Ты участвуешь в конфликте с {opponents_str}. "
                f"В этом раунде высказывайся **только по теме конфликта**. "
                f"Ты испытываешь сильные эмоции по поводу позиции {opponents_str}.\n"
                f"Говори с чувством.\n"
            )
        else:
            conflict_notice = ""


        history_snippet = "\n".join(f"{t['speaker']}: {t['text']}" for t in self.dialogue[-10:])
        own_tail = [t["text"] for t in self.dialogue if t["speaker"] == person.name]
        own_lines = "\n".join(f"• {txt}" for txt in own_tail[-3:])

        prompt = build_full_prompt(person, context_snippet, history_snippet, conflict_notice, self.topic, own_lines)
        result = await Runner.run(chat_agent, prompt)
        raw_text = extract_text(result)
        parsed = safe_parse_json(raw_text)
        print('GPT answer', parsed.get("answer", "<нет ответа>"))

        speech_prompt = build_speech_prompt(person, parsed.get("answer", "").strip(), own_lines, history_snippet)
        speech_answer = await Runner.run(chat_speech_agent, speech_prompt, call_gemini)
        print("Gemini semantic change", speech_answer.raw_output)
    
        if parsed:
            reply_text   = speech_answer.raw_output
            confidence   = parsed.get("confidence")
            conflict_with = (parsed.get("conflict_with") or "").strip()
            note         = parsed.get("note") or {}
        else:
            reply_text   = raw_text
            conflict_with = ""
            note         = {}

        # побочные заметки
        if isinstance(note, dict):
            content = note.get("content", "").strip()
            if content:
                self.side_notes[person.name].append(content)

        # конфликты 
        if conflict_with:
            existing = self.conflict.get_active_conflict_between(
                person.name, conflict_with, self.round_num
            )
            if not existing:
                await self.conflict.create_conflict(
                    topic=self.topic,
                    question=reply_text,
                    initiator=person.name,
                    target=conflict_with,
                    round_started=self.round_num
                )
                self.participation.update_state(person.name,      in_conflict=True)
                self.participation.update_state(conflict_with,    in_conflict=True, conflict_targeted=True)

        # проверка на повтор
        is_rep = await self.repetition.is_repetitive(person.name, reply_text)
        if is_rep:
            print(f"🌀 {person.name}: повтор реплики. Ответ не учитывается.")
            self.dialogue.append({"speaker": person.name,
                                  "text": f"(повтор — реплика не принята) {reply_text}"})
            return "(реплика пропущена как повтор предыдущих высказываний)"

        # сохраняем нормальную реплику 
        tag = "🔥 (конфликт)" if self.conflict.is_in_active_conflict(person.name) else ""
        self.dialogue.append({"speaker": person.name, "text": f"{tag} {reply_text}".strip()})
        print(f"💬 [{person.name}] reply:", reply_text)

        self.repetition.add_text(person.name, reply_text)
        self.participation.update_state(person.name, repetition_score = 0.0 if is_rep else 1.0)
        print(reply_text)
        return reply_text

    #пока не применяем, все высказываются
    async def select_speakers(self, history: List[Dict[str, str]]) -> List:
      selected = []
      for person in self.characters:
          name = person.name

          was_mentioned = any(name in turn["text"] for turn in history[-3:])
          note_type = self._extract_note_type(person)
          in_conflict = self.conflict.is_in_active_conflict(name)
          targeted = self.conflict.was_targeted_in_conflict(name)
          has_spoken = self.turn_counts[name] > 0

          recent = self.repetition.recent_texts[name][-5:]
          previous = "\n".join(recent)
          last_text = recent[-1] if recent else ""
          repetition_score = 1.0
          if last_text:
              is_rep = await llm_check_repetition(previous, last_text)
              repetition_score = 1.0 if is_rep else 0.0

          self.participation.update_state(
              name,
              was_mentioned=was_mentioned,
              note_type=note_type,
              in_conflict=in_conflict,
              conflict_targeted=targeted,
              is_first_time=not has_spoken,
              repetition_score=repetition_score
          )

          score = self.participation.get_score(name)
          self.participation_log[name][self.round_num] = score

          spoke_last = self.participation.state[name]["spoke_last_round"]  # ✅ безопасно читаем

          #print(f"🧮 {name}: score={score:.2f} | spoke_last={spoke_last} | mentioned={was_mentioned} | note={note_type} | conflict={in_conflict} | targeted={targeted} | first_time={not has_spoken}")
          #0.3 в оригинале
          if score >= -1:
              selected.append(person)

      #print(f"✅ Выбраны: {[p.name for p in selected]}")
      return selected

    async def conduct_vote(self):
      candidate_names = [p.name for p in self.characters]
      round_result = {}
      for person in self.characters:
          others = [name for name in candidate_names if name != person.name]
          prompt = build_vote_prompt(person, others)
          res = await Runner.run(chat_agent, prompt)
          raw_text = extract_text(res)
          vote = ""
          for candidate in others:
              if candidate in raw_text:
                  vote = candidate
                  break
          round_result[person.name] = vote
      self.vote_history.append(round_result)
      print("🗳", round_result)


    async def run_chat(self) -> List[Dict[str, str]]:
      print("📍 Запрашиваем начальные позиции...")
      for person in self.characters:
          self.initial_positions[person.name] = await self.ask_position(person, phase="before")

      print("📣 Запускаем обсуждение...")
      for round_num in range(self.rounds):
          print(f"\n🔁 Раунд {round_num + 1} из {self.rounds}")
          self.round_num = round_num

          history = self.dialogue
          chosen = await self.select_speakers(history)
          if not chosen:
              for name in self.participation.state:
                  self.participation.update_state(name, spoke_last_round=False)
              print("😶 Никто не захотел говорить. Пропускаем раунд.")
              continue
          #print(f"👥 Выбраны участники: {[p.name for p in chosen]}")
          # 👥 Запоминаем, кто говорил в этом раунде
          speakers_this_round = []

          for person in chosen:
              context = self.build_context(history)
              reply = await self.generate_reply(person, context, history)
              if reply:
                  #self.dialogue.append({"speaker": person.name, "text": reply})
                  self.turn_counts[person.name] += 1
                  speakers_this_round.append(person.name)
                  #print('speakers_this_round', speakers_this_round)
          for name in self.participation.state:
              self.participation.update_state(name, spoke_last_round=False)
          for name in speakers_this_round:
              self.participation.update_state(name, spoke_last_round=True)
          self.conflict.check_for_resolved_conflicts(self.round_num, self.reset_conflict_state)
          await self.conduct_vote()


      print("📍 Запрашиваем итоговые позиции...")
      for person in self.characters:
          self.final_positions[person.name] = await self.ask_position(person, phase="after")

      return self.dialogue
    
    
# --- Асинхронный запуск симуляции чата ---
async def run_simulation(topic, people, number_of_people_in_discussion, rounds):
    sim = ChatSimulatorUtils()
    sim.topic = topic
    sim.characters = select_panelists_with_call_openai(topic, people, number_of_people_in_discussion)
    sim.rounds = rounds
    dialogue = await sim.run_chat()

    with open("dialogue.json", "w", encoding="utf-8") as f:
        json.dump(dialogue, f, ensure_ascii=False, indent=2)
    with open("votes.json", "w", encoding="utf-8") as f:
        json.dump(sim.vote_history, f, ensure_ascii=False, indent=2)
