from models import Agent
from prompts import CHAT_AGENT_INSTRUCTIONS, CHAT_SPEECH_AGENT_INSTRUCTIONS

chat_agent = Agent(
    name="ChatAgent",
    description="Ты — голос человека из России. Все люди вокруг составляют город. Отвечаешь на вопросы так, будто ты — он сам. Твоя задача, чтобы в голосовании за президента за тебя проголосвало как можно больше людей. А за остальных как можно меньше людей.",
    instructions=CHAT_AGENT_INSTRUCTIONS)

chat_speech_agent = Agent(
    name="ChatSpeechAgent",
    description="Ты переделываешь предложения семантически.",
    instructions=CHAT_SPEECH_AGENT_INSTRUCTIONS)

repetition_agent = Agent(
    name="RepetitionCheckAgent",
    description="Определяет, повторяет ли реплика предыдущие мысли.",
    instructions="Ты получаешь несколько предыдущих реплик и новую. Ответь только числом от 0 до 1  является ли новая реплика повтором по смыслу. 1 повтор по смыслу, 0 разные реплики.",
    output_type=float
)

similarity_agent = Agent(
    name="SimilarityAgent",
    description="Оценивает тематическое сходство между двумя репликами.",
    instructions="Ты получаешь два текста. Верни число от 0 до 1, отражающее их сходство по теме. 1 — одно и то же, 0 — всё же разные темы.",
    output_type=float
)
