import json
import random

from collections import defaultdict
from typing import List, Dict, Optional

from models import Runner
from llm_api import call_gemini
from agents import chat_agent, chat_speech_agent
from agent_functions import llm_check_repetition

from prompt_builders import select_panelists_with_call_openai, build_full_prompt, build_vote_prompt, build_president_full_prompt_with_history

from chat_managers import RepetitionTracker, ParticipationManager, ReflectionManager, ConflictManager

from prompt_builders import (
    select_panelists_with_call_openai,
    build_full_prompt,
    build_vote_prompt,
    build_president_full_prompt,
    build_distribution_prompt,
)

import logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%m-%d %H:%M',
    handlers=[
        logging.FileHandler("simulation.log", encoding="utf-8"),
        logging.StreamHandler()  # чтобы осталась и печать в консоль
    ],
    force=True
)

# Создаём отдельный логгер для конфликтов
vote_logger = logging.getLogger("vote")
vote_logger.setLevel(logging.INFO)

# Настраиваем обработчик файла
vote_handler = logging.FileHandler("votes.log", encoding="utf-8")
vote_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%m-%d %H:%M'
))

vote_logger.addHandler(vote_handler)
vote_logger.propagate = False 

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
        self.money_pool = 1000
        self.final_distribution = {}
        self.allocation_promises = {}

    def _extract_note_type(self, person) -> Optional[str]:
        notes = self.side_notes.get(person.name, [])
        if any("устал" in note.lower() for note in notes):
            return "fatigue"
        if any("хочу высказаться" in note.lower() or "нужно сказать" in note.lower() for note in notes):
            return "desire"
        return None
    
    def vote_history_context(self):
        block_context = ""
        context = ""
        context += "\n\n📜 История голосований:\n"
        
        for vote_block in self.vote_history:
            round_id = vote_block.get("round")
            block_context = f"\n🕒 Раунд {round_id+1}\n"
            votes = vote_block.get("votes", {})
            vote_counts = defaultdict(int)
            reasons = defaultdict(list)
            individual_votes = []

            for voter, info in votes.items():
                if isinstance(info, dict):
                    candidate = info.get("candidate", "")
                    reason = info.get("reason")
                else:
                    candidate = info
                    reason = ""

                if candidate:
                    vote_counts[candidate] += 1
                    if reason:
                        reasons[candidate].append(reason)
                    reason_str = f' — "{reason}"' if reason else ""
                    
                    individual_votes.append(f"{voter} → {candidate}{reason_str}")

            if individual_votes:
                block_context += "\n🧾 Кто как голосовал:\n"
                block_context += "\n".join(individual_votes)

            if vote_counts:

                block_context += "\n🏅 Итоги:\n"
                block_context += ", ".join(f"{cand} — {cnt}" for cand, cnt in vote_counts.items())
                
                max_votes = max(vote_counts.values())
                leaders = [cand for cand, cnt in vote_counts.items() if cnt == max_votes]
                block_context += f"\nЛидирует: {', '.join(leaders)}"

                reason_lines = []
                for cand in leaders:
                    if reasons.get(cand):
                        unique = list(dict.fromkeys(reasons[cand]))
                context += block_context
        return context, block_context

    def build_context(self, history: List[Dict[str, str]], round_num) -> str:
        context = f"📌 Тема обсуждения: {self.topic}\n\n"
        if history:
            context += "🔨️ Последние реплики. Используй для реакции. Строй СВОЮ точку зрения на ситуацию.\n"
            context += "\n".join([f"{turn['speaker']}: {turn['text']}" for turn in history[-1000:]])
        
        context_vote = ""
        if self.vote_history:
            context_vote, _ = self.vote_history_context()
        context += context_vote
        if self.allocation_promises:
            context += "\n\n💰 Обещания кандидатов:\n"
            for speaker, alloc in self.allocation_promises.items():
                pairs = "; ".join(f"{k}:{v}" for k, v in alloc.items())
                context += f"{speaker}: {pairs}\n"
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

        #prompt = build_president_full_prompt(person, context, history_snippet, conflict_notice, self.topic, own_lines)
        
        recent_messages = [t["text"] for t in self.dialogue[-30:]]
        prompt = await build_president_full_prompt_with_history(person, context, conflict_notice, self.topic, own_lines, recent_messages)
        print('full prompt with history', prompt)
        
        result = await Runner.run(chat_agent, prompt)
        raw_text = extract_text(result)
        parsed = safe_parse_json(raw_text)
        #print('GPT answer', parsed.get("answer", "<нет ответа>"))

        # speech_prompt = build_speech_prompt(person, parsed.get("answer", "").strip(), own_lines, history_snippet)
        # speech_answer = await Runner.run(chat_speech_agent, speech_prompt, call_gemini)
        # print("Gemini semantic change", speech_answer.raw_output)
    
        if parsed:
            reply_text   = parsed.get("answer")
            confidence   = parsed.get("confidence")
            conflict_with = (parsed.get("conflict_with") or "").strip()
            note         = parsed.get("note") or {}
            allocation   = parsed.get("allocation") if isinstance(parsed.get("allocation"), dict) else None
        else:
            reply_text   = raw_text
            conflict_with = ""
            note         = {}
            allocation   = None

        # побочные заметки
        if isinstance(note, dict):
            content = note.get("content", "").strip()
            if content:
                self.side_notes[person.name].append(content)
        
        if allocation:
            self.allocation_promises[person.name] = allocation

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
        # if is_rep:
        #     print(f"🌀 {person.name}: повтор реплики. Ответ не учитывается.")
        #     self.dialogue.append({"speaker": person.name,
        #                           "text": f"(повтор — реплика не принята) {reply_text}"})
        #     return "(реплика пропущена как повтор предыдущих высказываний)"

        # сохраняем нормальную реплику 
        tag = "🔥 (конфликт)" if self.conflict.is_in_active_conflict(person.name) else ""
        self.dialogue.append({"speaker": person.name, "text": f"{tag} {reply_text}".strip()})
        logging.info(f"💬 [{person.name}] reply: {reply_text}")
        logging.info(f"💵 💵 💵[{person.name}] give money to: {allocation}")

        self.repetition.add_text(person.name, reply_text)
        self.participation.update_state(person.name, repetition_score = 0.0 if is_rep else 1.0)
        return reply_text

    #пока не применяем, все высказываются
    async def select_speakers(self, history: List[Dict[str, str]]) -> List:
      selected = []
      for person in random.sample(self.characters, len(self.characters)):
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

    async def conduct_vote(self, history_snippet, round_num, context):
      candidate_names = [p.name for p in self.characters]
      round_result = {}
      for person in self.characters:
          others = [name for name in candidate_names if name != person.name]
          prompt = build_vote_prompt(person, others, history_snippet, context)
          res = await Runner.run(chat_agent, prompt)
          try:
                data = json.loads(res.raw_output)

                candidate = (data.get("answer", "") or "").strip()

                note = data.get("note", {})
                if isinstance(note, dict):
                    reason = note.get("content", "").strip()
                else:
                    reason = str(note).strip()
                

          except json.JSONDecodeError as e:
                logging.warning(f"⚠️ Ошибка JSON: {e} | raw = {res.raw_output}")
                candidate = res.raw_output.split()[0] if res.raw_output else ""
                reason = ""

          if candidate == person.name or candidate not in candidate_names:
              candidate = ""

          entry = {"candidate": candidate}
          if reason:
              entry["reason"] = reason

          round_result[person.name] = entry
      self.vote_history.append({"round": round_num, "votes": round_result})
      _, block_context = self.vote_history_context()
      vote_logger.info(f"Результаты голосования {block_context}")
      print("🗳", round_result)
    
    def get_winner(self) -> Optional[str]:
      if not self.vote_history:
          return None
      last_votes = self.vote_history[-1].get("votes", {})
      counts = defaultdict(int)
      for info in last_votes.values():
          if isinstance(info, dict):
              cand = info.get("candidate")
              if cand:
                  counts[cand] += 1
      if not counts:
          return None
      max_votes = max(counts.values())
      winners = [c for c, v in counts.items() if v == max_votes]
      return winners[0]

    async def ask_distribution(self, president_name: str):
      pres = next((p for p in self.characters if p.name == president_name), None)
      logging.info(f"🏆 Президент: {pres.name if pres else 'не найден'}")
      if not pres:
          return
      context_vote, _ = self.vote_history_context()
      alloc_context = ""
      if self.allocation_promises:
          alloc_context += "\n\n💰 Обещания кандидатов:\n"
          for speaker, alloc in self.allocation_promises.items():
              pairs = "; ".join(f"{k}:{v}" for k, v in alloc.items())
              alloc_context += f"{speaker}: {pairs}\n"
      prompt = build_distribution_prompt(pres, self.money_pool, context_vote + alloc_context)
      res = await Runner.run(chat_agent, prompt)
      logging.info(f"💰 Распределение от {pres.name}: {res.raw_output}")
      raw = extract_text(res)
      parsed = safe_parse_json(raw)
      if parsed and isinstance(parsed.get("distribution"), dict):
          self.final_distribution = parsed
      else:
          self.final_distribution = {"raw": raw}



    async def run_chat(self) -> List[Dict[str, str]]:
      logging.info("📍 Запрашиваем начальные позиции...")
    #   for person in self.characters:
    #       self.initial_positions[person.name] = await self.ask_position(person, phase="before")

      logging.info("📣 Запускаем обсуждение...")
      for round_num in range(self.rounds):
          logging.info(f"\n🔁 Раунд {round_num + 1} из {self.rounds}")
          self.round_num = round_num
          self.conflict.current_round = round_num

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
              context = self.build_context(history, round_num)
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
          history_snippet = "\n".join(f"{t['speaker']}: {t['text']}" for t in self.dialogue[-10:])
          
        #   self.reflection.dialogue = self.dialogue
        #   self.reflection.topic = self.topic
        #   for p in self.characters:
        #       answer = await self.reflection.ask_reflection(p)
        #       self.reflection.log[p.name].append({
        #           "round": self.round_num,
        #           "text": answer,
        #       })

          await self.conduct_vote(history_snippet, round_num, context)
          
      print("📍 Запрашиваем итоговые позиции...")
      for person in self.characters:
          self.final_positions[person.name] = await self.ask_position(person, phase="after")
      
      winner = self.get_winner()
      logging.info(f"🏆 Победитель: {winner}")
      if winner:
          await self.ask_distribution(winner)
      return self.dialogue
    
    
# --- Асинхронный запуск симуляции чата ---
async def run_simulation(topic, people, number_of_people_in_discussion, rounds):
    sim = ChatSimulatorUtils()
    sim.topic = topic
    selected = select_panelists_with_call_openai(topic, people, number_of_people_in_discussion)
    sim.characters = [
        p.model_copy(update={"name": f"Спикер {idx}"})
        for idx, p in enumerate(selected, start=1)
    ]
    logging.info(f"Stating new simulation")
    # 🪵 Логируем соответствие
    for idx, original in enumerate(selected, start=1):
        logging.info(f"🆔 {original.id if hasattr(original, 'id') else '[no id]'} "
                    f"→ Спикер {idx} ({original.gender}, {original.age}, {original.profession})")
    sim.rounds = rounds
    dialogue = await sim.run_chat()

    # result = {
    #     "initial_positions": sim.initial_positions,
    #     "dialogue": dialogue,
    #     "final_positions": sim.final_positions,
    # }
    
    with open("dialogue.json", "w", encoding="utf-8") as f:
        json.dump(dialogue, f, ensure_ascii=False, indent=2)
    with open("votes.json", "w", encoding="utf-8") as f:
        json.dump(sim.vote_history, f, ensure_ascii=False, indent=2)
    
    if sim.final_distribution:
        with open("money_distribution.json", "w", encoding="utf-8") as f:
            json.dump({"president": sim.get_winner(), "distribution": sim.final_distribution}, f, ensure_ascii=False, indent=2)
