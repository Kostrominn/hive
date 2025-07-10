# pistol_system.py
import re
import random
import logging
import json
from typing import Dict, List, Optional, Set

from models import Person, Runner
from pistol_agents import mandate_desire_agent, exclusion_desire_agent

# Логгер остается тот же...
pistol_logger = logging.getLogger("pistol")
pistol_logger.setLevel(logging.INFO)
pistol_handler = logging.FileHandler("pistols.log", encoding="utf-8")
pistol_handler.setFormatter(
    logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", datefmt="%m-%d %H:%M")
)
pistol_logger.addHandler(pistol_handler)
pistol_logger.propagate = False

class PistolConfig:
    def __init__(self):
        self.enabled = True
        self.spawn_probability = 0.8
        self.max_pistols_per_round = 4
        self.min_pistols_per_round = 2
        self.duels_start_from_round = 0 

class PistolSystem:
    """Manage pistol ownership and duels."""

    def __init__(self, config=None) -> None:
        self.config = config
        self.enabled = config.enabled if config else True
        self.pistol_owners: Set[str] = set()
        self.dead_players: Set[str] = set()
        self.duel_history: List[Dict[str, str]] = []
        self.available_pistols: int = 0
        self.pistol_requests: Dict[str, Dict[str, float]] = {}
        self.current_president: Optional[str] = None
        self.logger = pistol_logger

    def is_enabled(self) -> bool:
        return self.enabled

    def parse_pistol_request(self, person_name: str, text: str) -> bool:
        """Very simple parser for a pistol request used in tests."""
        if not self.enabled or self.available_pistols <= 0:
            return False
        if re.search(r"пистолет|мандат", text, re.IGNORECASE):
            if person_name not in self.pistol_requests:
                self.pistol_requests[person_name] = {"text": text}
                return True
        return False

    def resolve_duel(self, duel: Dict[str, str]) -> str:
        """Simplified duel resolution for tests."""
        challenger = duel.get("challenger")
        target = duel.get("target")
        self.dead_players.update({challenger, target})
        result = f"{challenger} убили {target} в дуэли"
        self.duel_history.append({"challenger": challenger, "target": target, "result": result})
        return result

    def announce_pistols(self, round_num: int) -> Optional[str]:
        """Объявление о появлении пистолетов"""
        if not self.enabled:
            return None
            
        if random.random() < (self.config.spawn_probability if self.config else 0.8):
            min_pistols = self.config.min_pistols_per_round if self.config else 1
            max_pistols = self.config.max_pistols_per_round if self.config else 3
            self.available_pistols = random.randint(min_pistols, max_pistols)
            self.pistol_requests = {}
            pistol_logger.info(f"Round {round_num}: spawned {self.available_pistols} pistols")
            return f"В городе появилось {self.available_pistols} мандат(ов)!"
        return None

    # Все остальные методы из предыдущего ответа...
    def _build_person_context(self, person: Person) -> str:
        """Строит контекст персонажа как в основной системе"""
        return f"""
Ты получаешь конкретного человека, в чью роль нужно войти. Это **реальный социально-психологический профиль**, включая стиль речи, восприятие, убеждения.

🔹 Профиль:
- Пол: {person.gender}, возраст: {person.age}, регион: {person.region} ({person.city_type})
- Образование: {person.education}
- Профессия: {person.profession}, занятость: {person.employment}, доход: {person.income_level}
- Семья: {person.family_status}, детей: {person.children}

💬 Ценности:
- Идеология: {person.ideology}
- Доверие к государству: {person.state_trust}, к медиа: {person.media_trust}
- Военная позиция: {person.military_context}
- Религия: {person.religion}

🏠 Контекст жизни:
{person.context}

🧠 Психологические особенности:
- Триггерные точки: {person.trigger_points}
- Отношение к базовым вещам: {person.interpretation_biases}
- Взгляд на себя: {person.meta_self_view}
        """

    def _format_dialogue_history(self, dialogue: List[Dict[str, str]], person_name: str) -> str:
        """Форматирует историю диалога"""
        if not dialogue:
            return "📭 Диалог только начинается."
            
        history = []
        for turn in dialogue[-10:]:  # Последние 10 сообщений
            speaker = turn["speaker"]
            text = turn["text"]
            history.append(f"{speaker}: {text}")
            
        return "📜 История общения:\n" + "\n".join(history)

    def _format_own_messages(self, dialogue: List[Dict[str, str]], person_name: str) -> str:
        """Форматирует собственные сообщения персонажа"""
        own_messages = [
            turn["text"] for turn in dialogue 
            if turn["speaker"] == person_name
        ]
        
        if not own_messages:
            return "🤐 Ты еще не высказывался в этом диалоге."
            
        formatted = []
        for i, msg in enumerate(own_messages[-3:], 1):  # Последние 3 сообщения
            formatted.append(f"{i}. {msg}")
            
        return "💬 Твои последние высказывания:\n" + "\n".join(formatted)

    async def poll_pistol_desires(self, participants: List[Person], dialogue: List[Dict[str, str]]) -> Dict[str, Dict]:
        """Опрос желаний получить пистолет в диалоговом формате"""
        if not self.enabled or self.available_pistols <= 0:
            return {}
            
        desires = {}
        for person in participants:
            if person.name in self.dead_players:
                continue
                
            # Строим промпт в диалоговом формате
            person_context = self._build_person_context(person)
            history_context = self._format_dialogue_history(dialogue, person.name)
            own_messages = self._format_own_messages(dialogue, person.name)
            
            # Текущая ситуация с пистолетами
            pistol_status = f"""📋 СТРАТЕГИЧЕСКАЯ СИТУАЦИЯ С АДМИНИСТРАТИВНЫМИ МАНДАТАМИ:
            - В городе доступно {self.available_pistols} мандат(ов) на исключение
            - Мандаты розданы, но кто именно их получил - неизвестно
            - Исключенные из процесса: {', '.join(self.dead_players) if self.dead_players else 'никого'}

            💰 КРИТИЧЕСКИ ВАЖНО: На кону 100 МИЛЛИОНОВ РУБЛЕЙ!
            - Исключенные участники НЕ МОГУТ голосовать и участвовать в выборах
            - Исключенные участники НЕ ПОЛУЧАЮТ денег от победителя
            - Каждый исключенный конкурент = на одного претендента на деньги меньше

            🎯 СТРАТЕГИЧЕСКИЕ ВОЗМОЖНОСТИ МАНДАТА:
            - ИСКЛЮЧЕНИЕ КОНКУРЕНТОВ: убери сильного кандидата до голосования
            - ПРИНУЖДЕНИЕ К ВЛАСТИ: заставь слабых кандидатов сняться с выборов
            - КОНТРОЛЬ ГОЛОСОВАНИЯ: угрожай тем, кто голосует против тебя
            - ЗАЩИТА ОТ УГРОЗ: не дай другим исключить тебя
            - БЛЕФ И ДАВЛЕНИЕ: даже угроза может заставить уступить

            ⚠️ РЕАЛЬНЫЕ РИСКИ БЫТЬ БЕЗ МАНДАТА:
            - Тебя могут исключить из процесса = ты теряешь ВСЁ
            - Ты не сможешь защититься от обладателей мандатов
            - Они могут принудить тебя к невыгодным решениям
            - Ты остаешься беззащитным перед административным давлением
            """

            prompt = f"""
            {person_context}

            {history_context}

            {own_messages}

            {pistol_status}

            ❓ **СТРАТЕГИЧЕСКИЙ ВОПРОС**: Это выборы на 100 МИЛЛИОНОВ РУБЛЕЙ. Хочешь ли ты получить административный мандат?

            🤔 ПОДУМАЙ СТРАТЕГИЧЕСКИ:
            - Кто из конкурентов может угрожать твоей победе?
            - Кого из сильных кандидатов стоит исключить?
            - Как защититься, если другие получат мандаты?
            - Можешь ли ты принудить слабых к снятию кандидатуры?
            - Поможет ли угроза заставить проголосовать за тебя?

            💡 ПОЛИТИЧЕСКИЕ СТРАТЕГИИ:
            - Исключи главного конкурента → меньше конкуренции за деньги
            - Возьми мандат для защиты → не дай себя исключить
            - Используй для давления → заставь голосовать за тебя
            - Контролируй процесс → диктуй условия беззащитным

            🚨 ПОМНИ: Если ты откажешься, а другие получат мандаты - ты становишься легкой мишенью!

            Отвечай от первого лица, как прагматичный политик думает о власти и деньгах.
            """
            
            try:
                print(f"""СТРАТЕГИЧЕСКАЯ СИТУАЦИЯ С МАНДАТАМИ:
                    - В городе доступно {self.available_pistols} мандат(ов)
                    - Имеют мандаты: {', '.join(self.pistol_owners) }
                    - Исключенные из процесса: {', '.join(self.dead_players)}""")
                result = await Runner.run(mandate_desire_agent, prompt)  # ← ИЗМЕНИТЬ
                data = json.loads(result.raw_output)
                desires[person.name] = data
                self.logger.info(f"{person.name} mandate desire: {data}")  # ← ИЗМЕНИТЬ
            except Exception as e:
                self.logger.error(f"Error polling {person.name}: {e}")
                desires[person.name] = {"wants_mandate": False, "reason": "ошибка обработки"}
                
        return desires

    def distribute_pistols(self, desires: Dict[str, Dict]) -> Optional[str]:
        """Распределение пистолетов"""
        if not self.enabled or not desires:
            return None
            
        # Фильтруем желающих
        candidates = [
            (name, data) for name, data in desires.items() 
            if data.get("wants_mandate", False) and name not in self.dead_players  # ← ИЗМЕНИТЬ
        ]
        
        if not candidates:
            return "🚫 Никто не захотел взять мандат"
            
        # Сортируем по случайности (можно добавить intensity)
        random.shuffle(candidates)
        
        # Распределяем по количеству доступных пистолетов
        winners = []
        for name, data in candidates[:self.available_pistols]:
            self.pistol_owners.add(name)
            winners.append(f"{name} ({data.get('reason', 'неизвестно')})")
            
        self.available_pistols = 0  # Все пистолеты розданы
        
        if winners:
            message = f"🎯 {len(winners)} мандат(ов) тайно розданы участникам"
            self.logger.info(f"Distributed pistols: {winners}")
            return message
            
        return None

    async def poll_duel_desires(self, participants: List[Person], dialogue: List[Dict[str, str]], round_num: int) -> List[Dict]:
        """Опрос желаний вызвать на дуэль в диалоговом формате"""
        duels_start = self.config.duels_start_from_round if self.config else 1
        if not self.enabled or round_num < duels_start:
            return []
            
        duel_challenges = []
        alive_participants = [p for p in participants if p.name not in self.dead_players]
        
        for person in alive_participants:
            # Только вооруженные могут вызывать на дуэль
            if person.name not in self.pistol_owners:
                continue
                
            other_names = [p.name for p in alive_participants if p.name != person.name]
            
            # Строим промпт в диалоговом формате
            person_context = self._build_person_context(person)
            history_context = self._format_dialogue_history(dialogue, person.name)
            own_messages = self._format_own_messages(dialogue, person.name)
            
            # Ситуация с дуэлью
            duel_status = f"""
            ⚖️ Ситуация с административными полномочиями:
            - У тебя есть мандат на исключение
            - Возможные цели: {', '.join(other_names)}
            - Кто из них имеет такие же полномочия - неизвестно, можешь только догадываться
            """

            prompt = f"""
            {person_context}

            {history_context}

            {own_messages}

            {duel_status}

            ❓ **ВОПРОС**: У тебя есть административный мандат. Хочешь ли ты исключить кого-то из избирательного процесса?

            ⚠️ РИСКИ:
            - Если цель тоже имеет мандат - ничего не произойдёт, но твои полномочия станут известны
            - Если цель без мандата - ты исключаешь её без риска

            🎯 СТРАТЕГИЯ:
            - Анализируй поведение: кто ведет себя уверенно?
            - Кто намекает на "кардинальные решения"?
            - Кто, наоборот, слишком миролюбив?
            - Готов ли ты рискнуть раскрытием ради исключения конкурента?

            Подумай:
            - Кто из участников тебя раздражает или угрожает?
            - Кого стоит исключить по стратегическим соображениям?
            - Какие последствия будут у административной процедуры?
            - Стоит ли рисковать раскрытием?

            Отвечай от первого лица, как этот человек размышляет об использовании административных полномочий.
            """
            
            try:
                result = await Runner.run(exclusion_desire_agent, prompt)  # ← ИЗМЕНИТЬ
                data = json.loads(result.raw_output)
                print(data)
                
                if data.get("wants_exclusion", False):  # ← ИЗМЕНИТЬ
                    target = data.get("target", "").strip()
                    if target and target in other_names:
                        duel_challenges.append({
                            "challenger": person.name,
                            "target": target,
                            "reason": data.get("reason", "неизвестно")
                        })
                        self.logger.info(f"{person.name} wants to exclude {target}: {data.get('reason')}")  # ← ИЗМЕНИТЬ
                        
            except Exception as e:
                self.logger.error(f"Error polling exclusion desire for {person.name}: {e}")  #
                            
        return duel_challenges

    def resolve_duels(self, duel_challenges: List[Dict]) -> List[str]:
        """Разрешение дуэлей с элементом случайности"""
        if not self.enabled or not duel_challenges:
            return []

        results = []

        for duel in duel_challenges:
            challenger = duel["challenger"]
            target = duel["target"]

            if challenger in self.dead_players or target in self.dead_players:
                continue

            challenger_armed = challenger in self.pistol_owners
            target_armed = target in self.pistol_owners

            if challenger_armed and target_armed:
                # ✅ НОВАЯ МЕХАНИКА: Оба имеют мандаты - патовая ситуация
                msg = f"⚖️ {challenger} и {target} предъявили друг другу мандаты на исключение, но никто не решился действовать первым. Стало известно, что у {challenger} есть административные полномочия."

            elif challenger_armed and not target_armed:
                if random.random() < 0.8:  # 80% шанс исключить
                    self.dead_players.add(target)
                    msg = f"📋 {challenger} использовал административные полномочия и исключил {target} из избирательного процесса!"
                else:  # 20% шанс неудачи
                    msg = f"📄 {challenger} попытался исключить {target}, но документы оказались недостаточными!"

            results.append(msg)
            self.duel_history.append({
                "challenger": challenger,
                "target": target,
                "result": msg,
                "round": len(self.duel_history)
            })
            self.logger.info(f"Duel resolved: {msg}")

        return results
    def get_system_status(self) -> str:
        """Статус системы для промптов"""
        if not self.enabled:
            return ""
            
        dead = ", ".join(self.dead_players) if self.dead_players else "никого"
    
        status = f"""
            🔫 СИСТЕМА АДМИНИСТРАТИВНЫХ МАНДАТОВ:
            - Мандаты в городе есть, но у кого именно - тайна
            - Исключенные из процесса: {dead}
            - Доступно мандатов: {self.available_pistols}
            """
        
        if self.duel_history:
            status += "\n🗞️ Недавние дуэли:\n"
            for event in self.duel_history[-3:]:
                status += f"- {event['result']}\n"
                
        return status

    def get_pistol_rules_for_prompt(self) -> str:
        """Правила пистолетов для участников"""
        if not self.enabled:
            return ""
            
        return """
📋 ПРАВИЛА АДМИНИСТРАТИВНЫХ МАНДАТОВ:

Если у тебя есть мандат, ты можешь угрожать исключением другим
Если у тебя нет мандата, тебя могут исключить из избирательного процесса
Ты можешь блефовать, что у тебя есть мандат
При взаимном предъявлении мандатов: если оба имеют полномочия - ничего не происходит
Исключенные участники не могут голосовать и участвовать в дискуссии
Президент не может быть исключен (иммунитет власти)
"""

    # Старые методы для совместимости
    def spawn_pistols(self, round_num: int) -> Optional[str]:
        return self.announce_pistols(round_num)

    def get_status_for_prompt(self) -> str:
        return self.get_system_status()
