import types
import sys
import asyncio
from pathlib import Path

# stub openai and requests modules before importing project modules
openai_stub = types.ModuleType('openai')
class _Dummy: pass
openai_stub.OpenAI = _Dummy
openai_stub.AsyncOpenAI = _Dummy
openai_stub.OpenAIError = Exception
sys.modules.setdefault('openai', openai_stub)

sys.modules.setdefault('requests', types.ModuleType('requests'))

# ensure project root on path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from models import Person
from chat_simulator import ChatSimulatorUtils

async def run_sim():
    sim = ChatSimulatorUtils()
    sim.topic = 'Topic'
    sim.rounds = 1
    sim.characters = [
        Person(name='Alice', id='1', gender='F', region='RU'),
        Person(name='Bob', id='2', gender='M', region='RU'),
    ]

    async def fake_select(self, history):
        return self.characters
    async def fake_generate(self, person, ctx, history):
        return 'reply'
    async def fake_pos(self, person, phase):
        return 'pos'
    async def fake_reflect(self, person):
        return f'reflect {person.name}'

    import types as _t
    sim.select_speakers = _t.MethodType(fake_select, sim)
    sim.generate_reply = _t.MethodType(fake_generate, sim)
    sim.ask_position = _t.MethodType(fake_pos, sim)
    sim.reflection.ask_reflection = _t.MethodType(fake_reflect, sim.reflection)

    await sim.run_chat()
    return sim.reflection.log

def test_reflection_called():
    log = asyncio.run(run_sim())
    assert log['Alice'][0]['text'] == 'reflect Alice'
    assert log['Bob'][0]['text'] == 'reflect Bob'
