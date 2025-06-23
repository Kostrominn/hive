import types
import sys
import asyncio
import pytest

# Stub openai module before importing project modules
openai_stub = types.ModuleType("openai")
class OpenAIError(Exception):
    pass
class OpenAI:
    def __init__(self, api_key=None):
        pass
class AsyncOpenAI(OpenAI):
    pass
openai_stub.OpenAI = OpenAI
openai_stub.AsyncOpenAI = AsyncOpenAI
openai_stub.OpenAIError = OpenAIError
sys.modules.setdefault("openai", openai_stub)

# Stub requests module to avoid dependency during import
requests_stub = types.ModuleType("requests")
def _dummy_post(*args, **kwargs):
    class Resp:
        status_code = 200
        text = ""
        def json(self):
            return {}
    return Resp()
requests_stub.post = _dummy_post
sys.modules.setdefault("requests", requests_stub)

import chat_managers

# Patch llm_conflict_similarity to avoid network calls
async def _fake_similarity(a, b):
    return 0.0
chat_managers.llm_conflict_similarity = _fake_similarity

from chat_managers import ConflictManager, ConflictThread

def test_create_conflict():
    manager = ConflictManager()
    thread = asyncio.run(manager.create_conflict(
        "Test Topic",
        "Is this a test question?",
        "Alice",
        "Bob",
        0,
    ))
    assert isinstance(thread, ConflictThread)
    assert "Alice" in thread.sides["A"]
    assert "Bob" in thread.sides["B"]
