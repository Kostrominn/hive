import asyncio
from profiles_loader import load_people_from_file, save_people_to_file
from chat_simulator import run_simulation

path = "./profiles"

def main():
    people = load_people_from_file('synthetic_people_50.json')
    number_of_people_in_discussion = 3
    number_of_rounds_in_discussion = 3
    topic = f"Вы находитесь в одном городе. В городе {number_of_people_in_discussion} людей и среди вас выбирают президента. Президент определяется голосованием из {number_of_rounds_in_discussion} раундов. Вы хотите им стать!"
    
    try:
        asyncio.run(run_simulation(topic, people, number_of_people_in_discussion, number_of_rounds_in_discussion))
    except Exception as e:
        print(f"Ошибка при запуске симуляции: {e}")

if __name__ == "__main__":
    main()