"""Точка входа для запуска симуляции"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
import sys

# Добавляем путь к основному проекту
sys.path.append(str(Path(__file__).parent.parent))

from profiles_loader import load_people
from transaction_simulator.transaction_models import SimulationConfig
from transaction_simulator.life_simulator import LifeTransactionSimulator


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transaction_simulation.log'),
        logging.StreamHandler()
    ]
)


async def main():
    """Основная функция запуска"""
    
    # Загружаем людей
    print("Loading people profiles...")
    people = load_people("../profiles", limit=20)
    print(f"Loaded {len(people)} people")
    
    # Выбираем целевого человека
    # Можно выбрать по критериям или взять первого
    target_person = people[2]
    
    print(f"\nTarget person: {target_person.name}")
    print(f"Age: {target_person.age}, Profession: {target_person.profession}")
    print(f"Income: {target_person.income_level}, Family: {target_person.family_status}")
    
    # Конфигурация симуляции
    config = SimulationConfig(
        target_person_id=target_person.id,
        start_date=datetime(2024, 1, 1),
        days=5,
        memory_window=5,
        events=[
            #{"day": 2, "type": "день зарплаты"},
            #{"day": 5, "type": "повышение"},
            {"day": 3, "type": "день зарплаты"}
        ]
    )
    
    # Создаем и запускаем симулятор
    print(f"\nStarting simulation for {config.days} days...")
    simulator = LifeTransactionSimulator(config, people)
    
    results = await simulator.run_simulation()
    
    # Сохраняем результаты
    output_file = f"simulation_{target_person.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    simulator.save_results(output_file)
    
    # Выводим УЛУЧШЕННУЮ статистику
    print("\n" + "="*50)
    print("УЛУЧШЕННАЯ АНАЛИТИКА СИМУЛЯЦИИ")
    print("="*50)
    
    analysis = results['analysis']
    spending = analysis['spending_analysis']
    social = analysis['social_analysis']
    emotions = analysis['emotional_analysis']
    patterns = analysis['behavioral_patterns']
    
    print(f"\n📊 ФИНАНСЫ:")
    print(f"Общие траты: {spending['total_spent']:,.0f} RUB")
    print(f"Средний день: {spending['daily_average']:,.0f} RUB")
    print(f"Диапазон: {spending['daily_min']:,.0f} - {spending['daily_max']:,.0f} RUB")
    print(f"Транзакций: {spending['transactions_count']}")
    print(f"Волатильность: {spending['spending_volatility']:.2f}")
    print(f"Тренд: {spending['spending_trend']}")
    
    print(f"\n📈 КАТЕГОРИИ ТРАТ:")
    for category, amount in list(spending['by_category'].items())[:5]:
        percentage = spending['category_distribution'][category]
        print(f"  {category}: {amount:,.0f} RUB ({percentage:.1f}%)")
    
    print(f"\n⏰ ТРАТЫ ПО ВРЕМЕНИ:")
    time_data = spending['by_time']['by_amount']
    for time_period, amount in time_data.items():
        print(f"  {time_period}: {amount:,.0f} RUB")
    print(f"Пик трат: {spending['by_time']['peak_spending_time']}")
    
    print(f"\n🛒 ИМПУЛЬСИВНЫЕ ПОКУПКИ:")
    impulse = spending['impulse_purchases']
    print(f"Количество: {impulse['count']}")
    print(f"Сумма: {impulse['total_amount']:,.0f} RUB ({impulse['percentage']:.1f}%)")
    
    print(f"\n👥 СОЦИАЛЬНАЯ АКТИВНОСТЬ:")
    print(f"Всего взаимодействий: {social['total_interactions']}")
    print(f"В среднем в день: {social['daily_average']:.1f}")
    print(f"Уникальных контактов: {social['unique_contacts']}")
    print(f"Самый частый контакт: {social['most_frequent_contact']}")
    
    print(f"\n😊 ЭМОЦИОНАЛЬНОЕ СОСТОЯНИЕ:")
    print(f"Позитивных дней: {emotions['positive_days']}")
    print(f"Негативных дней: {emotions['negative_days']}")
    print(f"Нейтральных дней: {emotions['neutral_days']}")
    print(f"Общее настроение: {emotions['overall_mood']}")
    
    print(f"\n🔄 ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ:")
    weekday_weekend = patterns['weekday_vs_weekend']
    print(f"Средний будний день: {weekday_weekend['weekday_average']:,.0f} RUB")
    print(f"Средний выходной: {weekday_weekend['weekend_average']:,.0f} RUB")
    if weekday_weekend['weekend_premium'] > 0:
        print(f"Премия выходного дня: +{weekday_weekend['weekend_premium']:,.0f} RUB")
    
    print(f"\n💡 КЛЮЧЕВЫЕ ИНСАЙТЫ:")
    insights = analysis['insights']
    for insight in insights:
        print(f"  • {insight}")
    
    # Показываем топ места
    print(f"\n🏪 ТОП МЕСТА:")
    for place, amount in list(spending['by_place'].items())[:5]:
        frequency = spending['place_frequency'][place]
        print(f"  {place}: {amount:,.0f} RUB ({frequency} визитов)")
    
    print(f"\nРезультаты сохранены в: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())