import asyncio
import sys
from pathlib import Path
import types

openai_stub = types.ModuleType('openai')
class _Dummy: pass
openai_stub.OpenAI = _Dummy
openai_stub.AsyncOpenAI = _Dummy
openai_stub.OpenAIError = Exception
sys.modules['openai'] = openai_stub
sys.modules['requests'] = types.ModuleType('requests')
sys.path.append(str(Path(__file__).resolve().parents[1]))
from chat_managers import ConflictManager


def test_create_conflict_instantiation():
    cm = ConflictManager()

    async def run():
        async def no_conflict(question, threshold=0.8):
            return None
        cm.find_similar_conflict = no_conflict  # type: ignore
        return await cm.create_conflict(
            "Topic", "Question", "Alice", "Bob", 1
        )

    conflict = asyncio.run(run())
    assert conflict is not None
    assert conflict.topic == "Topic"
    assert conflict.question == "Question"
    assert conflict.sides["A"] == {"Alice"}
    assert conflict.sides["B"] == {"Bob"}
