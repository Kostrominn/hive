import asyncio
from profiles_loader import load_people
from chat_simulator import run_simulation

path = "./profiles"

def main():
    people = load_people(path, limit=50)
    topic = "Расскажите, как вы относитесь к идее удалённой работы: подходит ли это вам, людям в вашем окружении, что вы в этом видите — плюсы, минусы??"
    number_of_people_in_discussion = 5
    number_of_rounds_in_discussion = 5
    try:
        asyncio.run(run_simulation(topic, people, number_of_people_in_discussion, number_of_rounds_in_discussion))
    except Exception as e:
        print(f"Ошибка при запуске симуляции: {e}")

if __name__ == "__main__":
    main()