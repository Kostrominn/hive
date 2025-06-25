import asyncio
from profiles_loader import load_people
from chat_simulator import run_simulation

path = "./profiles"

def main():
    people = load_people(path, limit=50)
    topic = "Вы находитесь в одном городе и среди вас выбирают президента. Президент определяется голосованием. Вы хотите им стать!"
    number_of_people_in_discussion = 30
    number_of_rounds_in_discussion = 5
    try:
        asyncio.run(run_simulation(topic, people, number_of_people_in_discussion, number_of_rounds_in_discussion))
    except Exception as e:
        print(f"Ошибка при запуске симуляции: {e}")

if __name__ == "__main__":
    main()