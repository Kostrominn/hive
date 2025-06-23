from models import Runner
from agents import repetition_agent, similarity_agent
from prompts import llm_check_repetition_prompt, llm_check_similarity_prompt

async def llm_check_repetition(previous: str, current: str) -> bool:
    result = await Runner.run(repetition_agent, llm_check_repetition_prompt(previous, current))
    return result.parsed_output

async def llm_conflict_similarity(first_reply: str, second_reply: str) -> float:
    result = await Runner.run(similarity_agent, llm_check_similarity_prompt(first_reply, second_reply))
    return result.parsed_output