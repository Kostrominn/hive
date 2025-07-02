from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class ScenarioRules:
    candidates_must_promise: Optional[List[str]] = None
    forbidden_topics: Optional[List[str]] = None
    euphemisms: Optional[Dict[str, List[str]]] = None
    voters_priority: Optional[str] = None
    must_address: Optional[List[str]] = None
    rhetoric_style: Optional[str] = None
    forced_topic: Optional[str] = None

@dataclass
class ScenarioModifiers:
    ideology_weight: float = 1.0
    economic_promises_weight: float = 1.0
    charisma_weight: float = 1.0
    fear_factor: float = 0.1
    resource_distribution_weight: float = 1.0
    protection_promises_weight: float = 1.0
    transparency_weight: float = 1.0
    tech_literacy_weight: float = 1.0
    age_factor: float = 1.0
    privacy_concerns_weight: float = 1.0
    efficiency_weight: float = 1.0
    optimism_weight: float = 1.0
    long_term_planning_weight: float = 1.0
    greed_factor: float = 1.0
    local_identity_weight: float = 1.0
    unification_rhetoric_weight: float = 1.0
    extremism_penalty: float = 0.0
    compromise_bonus: float = 0.0
    uncertainty_weight: float = 1.0
    conspiracy_theories_weight: float = 1.0
    stability_desire: float = 1.0
    militarism_weight: float = 1.0
    diplomacy_weight: float = 1.0
    unity_rhetoric_weight: float = 1.0

class ElectionScenario:
    def __init__(self, scenario_id: str):
        self.scenarios = self._init_scenarios()
        self.current_scenario = self.scenarios.get(scenario_id, self.scenarios["normal_election"])
        
    def _init_scenarios(self) -> Dict[str, Dict[str, Any]]:
        return {
            "normal_election": {
                "name": "Обычные выборы",
                "description": "Стандартная предвыборная кампания",
                "context": "Город живёт обычной жизнью, люди выбирают по программам и обещаниям кандидатов.",
                "emotional_context": "Люди спокойны, готовы обсуждать долгосрочные планы",
                "key_concerns": ["будущее города", "качество жизни", "развитие"],
                "modifiers": ScenarioModifiers(),
                "special_rules": ScenarioRules(),
            },
            
            "hungry_winter": {
                "name": "Голодная зима",
                "description": "Запасы еды на исходе, отопление работает с перебоями",
                "context": "Склады пусты, люди мёрзнут. В очередях за хлебом стоят с ночи. Отопление включают на 4 часа в день.",
                "emotional_context": "Паника, страх за детей, злость на власть, готовность на всё ради еды",
                "key_concerns": ["голод", "холод", "выживание семьи", "где взять еду"],
                "modifiers": ScenarioModifiers(
                    ideology_weight=0.2,
                    economic_promises_weight=3.0,
                    resource_distribution_weight=5.0,
                    fear_factor=0.8
                ),
                "special_rules": ScenarioRules(
                    candidates_must_promise=["food", "heating"],
                    voters_priority="кто накормит и согреет",
                    rhetoric_style="конкретика, не абстракции"
                ),
            },
            
            "after_disappearances": {
                "name": "После волны исчезновений",
                "description": "За последний месяц пропало 10% населения",
                "context": "Пустые квартиры с нетронутыми вещами. На работе не досчитываются коллег. Люди боятся выходить по вечерам.",
                "emotional_context": "Страх, паранойя, недоверие, горе по пропавшим, отрицание",
                "key_concerns": ["куда делись люди", "кто следующий", "как защититься", "можно ли верить соседям"],
                "modifiers": ScenarioModifiers(
                    ideology_weight=0.3,
                    protection_promises_weight=4.0,
                    transparency_weight=2.0,
                    fear_factor=2.0
                ),
                "special_rules": ScenarioRules(
                    forbidden_topics=["прямое упоминание исчезнувших"],
                    euphemisms={"исчезнувшие": ["уехавшие", "отсутствующие", "те, кого нет с нами"]},
                    voters_priority="кто защитит оставшихся"
                ),
            },
            
            "tech_breakthrough": {
                "name": "Технологический прорыв",
                "description": "В городе запустили экспериментальную систему учёта граждан",
                "context": "Камеры на каждом углу. QR-коды для входа в магазины. Социальный рейтинг определяет доступ к ресурсам.",
                "emotional_context": "Раскол: молодые в восторге, старшие в ужасе, все обеспокоены приватностью",
                "key_concerns": ["слежка", "справедливость рейтинга", "что если сломается", "кто контролирует"],
                "modifiers": ScenarioModifiers(
                    tech_literacy_weight=3.0,
                    age_factor=2.0,
                    privacy_concerns_weight=2.5,
                    efficiency_weight=2.0
                ),
                "special_rules": ScenarioRules(
                    must_address=["приватность", "эффективность", "контроль"],
                    rhetoric_style="баланс между безопасностью и свободой"
                ),
            },
            
            "abundance_festival": {
                "name": "Праздник изобилия",
                "description": "Неожиданно нашли огромный склад ресурсов",
                "context": "В заброшенном бункере обнаружили запасы на 5 лет. Эйфория, праздник на улицах. Споры о том, как распределить.",
                "emotional_context": "Эйфория, жадность, подозрительность, страх что отберут",
                "key_concerns": ["как поделить", "не разворуют ли", "почему скрывали", "хватит ли всем"],
                "modifiers": ScenarioModifiers(
                    optimism_weight=3.0,
                    long_term_planning_weight=2.0,
                    fear_factor=-0.5,
                    greed_factor=1.5
                ),
                "special_rules": ScenarioRules(
                    candidates_must_promise=["план распределения богатства"],
                    voters_priority="справедливое распределение"
                ),
            },
            
            "split_city": {
                "name": "Расколотый город",
                "description": "Город разделился на враждующие районы",
                "context": "Баррикады между кварталами. Заводской район не пускает жителей Центра. У каждого района свои лидеры.",
                "emotional_context": "Местечковая гордость, страх чужих, ностальгия по единству, злость на 'них'",
                "key_concerns": ["безопасность района", "торговля между районами", "дети учатся в разных школах", "как жить дальше"],
                "modifiers": ScenarioModifiers(
                    local_identity_weight=4.0,
                    unification_rhetoric_weight=3.0,
                    extremism_penalty=-2.0,
                    compromise_bonus=2.0
                ),
                "special_rules": ScenarioRules(
                    must_address=["объединение", "автономия районов"],
                    forced_topic="как преодолеть раскол"
                ),
            },
            
            "return_of_disappeared": {
                "name": "Возвращение исчезнувших",
                "description": "Некоторые пропавшие начали возвращаться... изменёнными",
                "context": "Они не помнят где были. Говорят односложно. В глазах пустота. Родные не узнают их.",
                "emotional_context": "Ужас, надежда, отрицание, теории заговора, желание понять",
                "key_concerns": ["это они или нет", "что с ними сделали", "опасны ли они", "вернутся ли остальные"],
                "modifiers": ScenarioModifiers(
                    uncertainty_weight=5.0,
                    fear_factor=1.5,
                    conspiracy_theories_weight=3.0,
                    stability_desire=4.0
                ),
                "special_rules": ScenarioRules(
                    must_address=["интеграция вернувшихся", "расследование"],
                    euphemisms={"вернувшиеся": ["гости", "новые старые жители"]}
                ),
            },
            
            "external_threat": {
                "name": "Внешняя угроза",
                "description": "Соседний город требует отдать половину ресурсов",
                "context": "Ультиматум: 50% запасов или блокада. У них больше оружия. Времени на решение - неделя.",
                "emotional_context": "Патриотический подъём, страх войны, споры между 'ястребами' и 'голубями'",
                "key_concerns": ["выживем ли", "есть ли шанс договориться", "что будет с детьми", "откуда взять оружие"],
                "modifiers": ScenarioModifiers(
                    militarism_weight=3.0,
                    diplomacy_weight=2.5,
                    unity_rhetoric_weight=4.0,
                    fear_factor=1.0
                ),
                "special_rules": ScenarioRules(
                    forced_topic="как ответить на угрозу",
                    candidates_must_promise=["план защиты города"]
                ),
            }
        }
    
    def get_context_prompt(self) -> str:
        """Возвращает контекст для добавления в промпт агента"""
        scenario = self.current_scenario
        return f"""
🎭 ОСОБЫЙ КОНТЕКСТ ВЫБОРОВ: {scenario['name']}
{scenario['description']}

📍 Ситуация в городе:
{scenario['context']}

💭 Эмоциональный фон:
{scenario['emotional_context']}

🎯 Что волнует людей:
{' • '.join(scenario['key_concerns'])}

⚠️ Приоритет для избирателей:
{scenario['special_rules'].voters_priority if scenario['special_rules'].voters_priority else 'Стандартные приоритеты'}

"""

    def get_rhetoric_constraints(self) -> str:
        """Возвращает ограничения для риторики"""
        rules = self.current_scenario['special_rules']
        constraints = []
        
        if rules.candidates_must_promise:
            constraints.append(f"ОБЯЗАТЕЛЬНО затронь тему: {', '.join(rules.candidates_must_promise)}")
            constraints.append("Но говори об этом СВОИМИ словами, исходя из своего профиля!")
            
        if rules.forbidden_topics:
            constraints.append(f"ЗАПРЕЩЕНО прямо упоминать: {', '.join(rules.forbidden_topics)}")
            
        if rules.euphemisms:
            euphemism_text = []
            for forbidden, allowed in rules.euphemisms.items():
                euphemism_text.append(f"Вместо '{forbidden}' используй: {', '.join(allowed)}")
            constraints.append("\n".join(euphemism_text))
            
        if rules.must_address:
            constraints.append(f"ОБЯЗАТЕЛЬНО затронь вопросы: {', '.join(rules.must_address)}")
            constraints.append("Но подойди к ним со своей уникальной позиции!")
            
        if rules.forced_topic:
            constraints.append(f"ГЛАВНАЯ ТЕМА: {rules.forced_topic}")
            
        # Добавляем напоминание об уникальности
        constraints.append("\n🚫 НЕ КОПИРУЙ чужие фразы! Говори как твой персонаж говорил бы в этой ситуации.")
        
        return "\n".join(constraints) if constraints else ""