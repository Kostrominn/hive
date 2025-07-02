import os
import openai
import requests
from openai import OpenAI, AsyncOpenAI
from typing import List, Dict

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = "AIzaSyBhEZ6y1lUvUkzcZnCKzqdMLWbmWf9F-Zs"

os.environ['HTTP_PROXY'] = 'http://Pgt8x0:LW7zMg@163.198.133.232:8000'     # если нужен http-прокси
os.environ['HTTPS_PROXY'] = 'http://Pgt8x0:LW7zMg@163.198.133.232:8000' 

#Open AI call

def call_openai(messages, model="o3", temperature=0.1, presence_penalty=0.6):
    client = OpenAI(api_key=OPENAI_API_KEY)
    #print(f"Calling OpenAI with model: {model}, temperature: {temperature}, presence_penalty: {presence_penalty}")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            #temperature=temperature,
            #presence_penalty=presence_penalty,
            timeout=600,
        )
        return response.choices[0].message.content
    except openai.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        return f"<OpenAI API error: {e}>"
    except Exception as e:
        print(f"Unexpected error: {e}")
        return f"<Unexpected error: {e}>"

async def call_openai_async(messages, model="gpt-4.1", temperature=0.3):
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content

# Gemini call
def call_gemini(messages: List[Dict[str, str]], need_json_decode=False, temperature: float = 0.3):
    URL_GEMINI = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    HEADERS = {
        "Content-Type": "application/json",
    }
    PROXIES = {
        "http": os.environ.get("HTTP_PROXY"),
        "https": os.environ.get("HTTPS_PROXY"),
    }
    system_prompt = ""
    gemini_messages = []
    for i in range(len(messages)):
        if messages[i]["role"] == "assistant":
            system_prompt = messages[i]["content"]
        elif messages[i]["role"] == "user":
            gemini_messages.append(
                {
                    "role": "user",
                    "parts": [{"text": messages[i]["content"]}]
                }
            )
    data = {
        "system_instruction": {
            "parts": {
                "text": system_prompt
            }
        },
        "generationConfig": {
            "temperature": temperature,
        },
        "contents": gemini_messages
    }
    if need_json_decode:
        data["generationConfig"]["response_mime_type"] = "application/json"
    response = requests.post(url=URL_GEMINI, headers=HEADERS, json=data, proxies=PROXIES)
    response = response.json()
    try:
        response = {"choices": [{"message": {"content": response["candidates"][0]["content"]["parts"][0]["text"]}}]}
    except:
        return  gemini_messages
    return response["choices"][0]["message"]["content"]