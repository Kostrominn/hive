from typing import Optional, Union, Type, Any, Dict, List
from pydantic import BaseModel
from llm_api import call_openai
from typing import get_origin, get_args
import json
import inspect

class HistoryEvent(BaseModel):
    """Событие из истории человека"""
    id: int
    life_stage: str
    theme: str
    summary: str
    quote: Optional[str] = None
    emotion: Optional[str] = None
    values: Optional[str] = None
    sociological_note: Optional[str] = None
    type: Optional[str] = None

class Agent:
    def __init__(
        self,
        name: str,
        description: str,
        instructions: str,
        output_type: Optional[Union[Type[BaseModel], Type[List[BaseModel]]]] = None,
    ):
        self.name = name
        self.description = description
        self.instructions = instructions
        self.output_type = output_type

class AgentRunResult:
    def __init__(self, raw_output: str, parsed_output: Optional[BaseModel]):
        self.raw_output = raw_output
        self.parsed_output = parsed_output

    def __repr__(self):
        return f"AgentRunResult(raw_output={repr(self.raw_output)}, parsed_output={repr(self.parsed_output)})"

    def final_output_as(self, model_type: Type[BaseModel]) -> BaseModel:
        if not self.parsed_output:
            raise ValueError("No structured output was parsed.")
        if not isinstance(self.parsed_output, model_type):
            raise TypeError(f"Parsed output is not of type {model_type}")
        return self.parsed_output

    @property
    def final_output(self) -> Any:
        return self.parsed_output or self.raw_output

class Person(BaseModel):
    name: str
    id: str
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
    context: Optional[str] = None  # строка с бытом

    cognitive_frame: Optional[Dict[str, Any]] = None
    rhetorical_manner: Optional[Dict[str, Any]] = None
    trigger_points: Optional[List[str]] = None
    interpretation_biases: Optional[Dict[str, Any]] = None
    meta_self_view: Optional[Dict[str, Any]] = None
    speech_profile: Optional[Dict[str, Any]] = None

    full_history: Optional[List[HistoryEvent]] = None

class Runner:
    @staticmethod
    async def _run_core(agent: Agent, input_text: str, llm_caller) -> AgentRunResult:
        messages = [
            {"role": "system", "content": f"Описание агента: {agent.description}\n\n Описание инструкций агенту: {agent.instructions}"},
            {"role": "user", "content": input_text}
        ]
        if inspect.iscoroutinefunction(llm_caller):
            output_text = await llm_caller(messages)
        else:
            output_text = llm_caller(messages)
        parsed = None

        if output_text.strip().startswith("```json"):
            output_text = output_text.strip()
            output_text = output_text.removeprefix("```json").removesuffix("```").strip()

        try:
            if agent.output_type:
                if agent.output_type == float:
                    parsed = float(output_text)
                elif agent.output_type == int:
                    parsed = int(output_text)
                elif get_origin(agent.output_type) is list:
                    model_cls = get_args(agent.output_type)[0]
                    items = json.loads(output_text)
                    parsed = [model_cls.model_validate(item) for item in items]
                else:
                    parsed = agent.output_type.model_validate_json(output_text)
        except Exception as e:
            print(f"[{agent.name}] ⚠️ Ошибка валидации structured output:\n{e}\n---\n{output_text}")
        return AgentRunResult(raw_output=output_text, parsed_output=parsed)

    @staticmethod
    async def run(agent: Agent, input_text: str, llm_caller=call_openai) -> AgentRunResult:
        return await Runner._run_core(agent, input_text, llm_caller)