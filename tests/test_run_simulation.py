import asyncio
import builtins
import io
import types
import sys

# Stub openai and requests modules before importing project modules
openai_stub = types.ModuleType('openai')
openai_stub.OpenAI = object
openai_stub.AsyncOpenAI = object
openai_stub.OpenAIError = Exception
sys.modules.setdefault('openai', openai_stub)
requests_stub = types.ModuleType('requests')
requests_stub.post = lambda *a, **k: types.SimpleNamespace(status_code=200, json=lambda: {})
sys.modules.setdefault('requests', requests_stub)

import chat_simulator
from chat_simulator import ChatSimulatorUtils

class DummyPerson:
    def __init__(self, name):
        self.name = name
        self.id = name

async def fake_run_chat(self):
    self.initial_positions = {'A': 'start A'}
    self.final_positions = {'A': 'end A'}
    self.dialogue = [{'speaker': 'A', 'text': 'hi'}]
    return self.dialogue

def fake_select_panelists(topic, people, number):
    return [DummyPerson('A')]

def test_run_simulation_returns_log(monkeypatch):
    monkeypatch.setattr(chat_simulator, 'select_panelists_with_call_openai', fake_select_panelists)
    monkeypatch.setattr(ChatSimulatorUtils, 'run_chat', fake_run_chat, raising=False)
    # patch open to avoid file IO
    monkeypatch.setattr(builtins, 'open', lambda *a, **k: io.StringIO(), raising=False)
    result = asyncio.run(chat_simulator.run_simulation('t', [], 1, 1))
    assert result['initial_positions'] == {'A': 'start A'}
    assert result['dialogue'] == [{'speaker': 'A', 'text': 'hi'}]
    assert result['final_positions'] == {'A': 'end A'}
