"""
Скрипт для запуска симулятора жизни
Поддерживает как веб-интерфейс, так и консольный режим
"""

import argparse
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# Импортируем необходимые модули
import sys
# Добавляем родительскую папку (на уровень выше) в путь поиска
sys.path.append(str(Path(__file__).parent.parent))

from models import Person
from uuid import uuid4
from transaction_simulator.life_simulator import LifeTransactionSimulator
from transaction_simulator.transaction_models import SimulationConfig
from transaction_simulator.report_generator import ReportGenerator
from life_simulator_ui import app

def run_web_interface():
    """Запускает веб-интерфейс"""
    print("🚀 Запускаем веб-интерфейс...")
    print("📍 Откройте в браузере: http://localhost:5001")
    print("🛑 Для остановки нажмите Ctrl+C")
    app.run(debug=False, port=5001, host="0.0.0.0")

async def run_console_simulation(args):
    """Запускает симуляцию в консольном режиме"""
    # Создаем персону
    person = Person(
        id=str(uuid4()),
        name=args.name,
        age=args.age,
        gender=args.gender,
        profession=args.profession,
        income_level=args.income,
        family_status=args.family,
        children=args.children,
        region=args.region,
        city_type=args.city_type,
    )
    
    print(f"\n👤 Персонаж: {person.name}, {person.age} лет, {person.profession}")
    print(f"📍 Локация: {person.city_type} {person.region}")
    print(f"💰 Доход: {person.income_level}")
    print(f"👨‍👩‍👧‍👦 Семья: {person.family_status}, детей: {person.children}")
    print(f"\n⏳ Симулируем {args.days} дней...\n")
    
    # Создаем конфигурацию
    start_date = datetime.now() - timedelta(days=args.days-1)
    config = SimulationConfig(
        target_person_id=person.id,
        start_date=start_date,
        days=args.days,
        memory_window=5
    )
    
    # Подготовка callback для лайв-вывода
    def progress(event_type, data):
        if event_type == "environment":
            print("\n🔹 Социальное окружение:")
            for p in data.get("close_circle", []):
                print(f"  - {p['name']} ({p['relation']}, {p.get('age', '?')} лет)")
            for p in data.get("extended_circle", []):
                print(f"  - {p['name']} ({p['relation']}, {p.get('age', '?')} лет)")
        elif event_type == "day_result":
            from transaction_simulator.transaction_models import DailyResult
            result = data if isinstance(data, DailyResult) else DailyResult(**data)

            print(f"\n{'='*60}")
            print(f"📅 {result.date} ({result.day_context.day_of_week})")
            print(f"💰 Потрачено: {result.day_summary.total_spent} руб")
            print(f"😊 Настроение: {result.day_summary.mood_trajectory[:100]}...")

            print(f"\n👥 Социальные взаимодействия ({len(result.social_interactions)}):")
            for si in result.social_interactions:
                print(f"  - {si.with_person}: {si.context} ({si.emotional_impact})")
                if args.show_chats:
                    for msg in si.chat[:3]:
                        print(f"    💬 {msg.from_person}: {msg.text}")

            print(f"\n🛒 Покупки ({len(result.transactions)}):")
            for t in result.transactions:
                print(f"  - {t.time} {t.place}: {', '.join(t.items[:3])} - {t.amount} руб ({t.category})")

    # Запускаем симуляцию
    simulator = LifeTransactionSimulator(config, [person])
    simulation_result = await simulator.run_simulation(progress_callback=progress)

    # Извлекаем результаты
    results = simulation_result['daily_results']
    
    # Генерируем отчет
    if args.report:
        print(f"\n{'='*60}")
        print("📋 ДЕТАЛЬНЫЙ ОТЧЕТ")
        print('='*60)
        report_gen = ReportGenerator(person)
        
        # Конвертируем словари обратно в объекты для генератора отчета
        daily_results_objects = []
        for result_dict in results:
            from transaction_simulator.transaction_models import DailyResult
            daily_results_objects.append(DailyResult(**result_dict))
        
        report = report_gen.generate_detailed_report(daily_results_objects)
        print(report)
    
    # Сохраняем результаты
    if args.output:
        output_data = {
            'person': {
                'name': person.name,
                'age': person.age,
                'gender': person.gender,
                'profession': person.profession,
                'income_level': person.income_level,
                'family_status': person.family_status,
                'children': person.children,
                'region': person.region,
                'city_type': person.city_type
            },
            'simulation_date': datetime.now().isoformat(),
            'days_simulated': args.days,
            'results': results,  # Уже в формате словарей
            'analysis': simulation_result.get('analysis', {})  # Добавляем анализ если есть
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Результаты сохранены в {args.output}")

def main():
    parser = argparse.ArgumentParser(
        description='Симулятор жизни человека',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

1. Запустить веб-интерфейс (рекомендуется):
   python run_simulator.py --web

2. Консольная симуляция с параметрами по умолчанию:
   python run_simulator.py

3. Симуляция подростка:
   python run_simulator.py --name "Маша" --age 16 --gender "женщина" --profession "школьница"

4. Симуляция с отчетом и сохранением:
   python run_simulator.py --days 7 --report --output results.json

5. Подробная симуляция с чатами:
   python run_simulator.py --show-chats --report
"""
    )
    
    # Режим работы
    parser.add_argument('--web', action='store_true', 
                       help='Запустить веб-интерфейс (рекомендуется)')
    
    # Параметры персонажа
    parser.add_argument('--name', default='Александр Петров',
                       help='Имя персонажа')
    parser.add_argument('--age', type=int, default=28,
                       help='Возраст (14-80)')
    parser.add_argument('--gender', choices=['мужчина', 'женщина'], 
                       default='мужчина', help='Пол')
    parser.add_argument('--profession', default='менеджер',
                       help='Профессия')
    parser.add_argument('--income', choices=['низкий', 'средний', 'высокий'],
                       default='средний', help='Уровень дохода')
    parser.add_argument('--family', default='не женат',
                       help='Семейное положение')
    parser.add_argument('--children', type=int, default=0,
                       help='Количество детей')
    parser.add_argument('--region', default='Москва',
                       help='Регион проживания')
    parser.add_argument('--city-type', 
                       choices=['село', 'малый город', 'средний город', 
                               'крупный город', 'мегаполис'],
                       default='мегаполис', help='Тип населенного пункта')
    parser.add_argument('--interests', default='',
                       help='Интересы через запятую')
    parser.add_argument('--traits', default='',
                       help='Черты характера через запятую')
    
    # Параметры симуляции
    parser.add_argument('--days', type=int, default=3,
                       help='Количество дней для симуляции (1-30)')
    parser.add_argument('--show-chats', action='store_true',
                       help='Показывать диалоги')
    parser.add_argument('--report', action='store_true',
                       help='Генерировать детальный отчет')
    parser.add_argument('--output', help='Файл для сохранения результатов')
    
    args = parser.parse_args()
    
    if args.web:
        run_web_interface()
    else:
        # Запускаем консольную симуляцию
        asyncio.run(run_console_simulation(args))

if __name__ == '__main__':
    main()