"""Улучшенный генератор транзакций с нормализацией категорий"""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models import Person, Runner
from .agents import transaction_generation_agent
from .transaction_models import Transaction


class CategoryNormalizer:
    """Нормализует категории трат для аналитики"""
    
    STANDARD_CATEGORIES = {
        'еда': [
            'еда', 'food', 'питание', 'обед', 'завтрак', 'ужин', 'перекус', 
            'напиток', 'кафе', 'ресторан', 'столовая', 'буфет', 'магазин продуктов',
            'горячий напиток', 'холодный напиток', 'сок', 'чай', 'кофе', 'какао',
            'фастфуд', 'доставка еды', 'продукты'
        ],
        'транспорт': [
            'транспорт', 'автобус', 'метро', 'такси', 'бензин', 'парковка', 
            'проезд', 'маршрутка', 'трамвай', 'поезд', 'самолет', 'каршеринг'
        ],
        'развлечения': [
            'развлечения', 'кино', 'театр', 'концерт', 'игры', 'спорт', 
            'хобби', 'клуб', 'бар', 'дискотека', 'боулинг', 'квест'
        ],
        'одежда': [
            'одежда', 'обувь', 'аксессуары', 'косметика', 'парфюм', 
            'украшения', 'сумка', 'очки', 'шляпа', 'перчатки'
        ],
        'здоровье': [
            'здоровье', 'медицина', 'аптека', 'врач', 'лечение', 'витамины',
            'больница', 'стоматолог', 'массаж', 'анализы', 'лекарства'
        ],
        'образование': [
            'образование', 'учёба', 'книги', 'курсы', 'канцелярия', 
            'школа', 'университет', 'репетитор', 'семинар', 'тренинг',
            'распечатка', 'копирование', 'печать', 'канцтовары'
        ],
        'дом': [
            'дом', 'быт', 'уборка', 'ремонт', 'мебель', 'техника',
            'хозяйственные товары', 'бытовая химия', 'посуда', 'текстиль'
        ],
        'подарки': [
            'подарки', 'цветы', 'сувениры', 'праздник', 'день рождения',
            'совместные расходы', 'складываемся', 'сбор денег', 'подарок классу'
        ],
        'коммунальные': [
            'коммунальные', 'свет', 'вода', 'газ', 'интернет', 'телефон',
            'мобильная связь', 'домофон', 'кабельное', 'отопление'
        ],
        'прочее': ['прочее', 'разное', 'другое', 'непонятно']
    }
    
    @classmethod
    def normalize_category(cls, raw_category: str) -> str:
        """Нормализует сырую категорию к стандартной"""
        raw_lower = raw_category.lower()
        
        for standard_cat, keywords in cls.STANDARD_CATEGORIES.items():
            if any(keyword in raw_lower for keyword in keywords):
                return standard_cat
        
        return 'прочее'
    
    @classmethod
    def get_category_rules_for_prompt(cls) -> str:
        """Возвращает правила категорий для промпта"""
        return """
СТРОГО ИСПОЛЬЗУЙ ТОЛЬКО ЭТИ КАТЕГОРИИ:
- еда: любая еда, напитки, рестораны, кафе, продукты
- транспорт: проезд, такси, бензин, парковка, маршрутка
- развлечения: кино, игры, спорт, хобби, клубы
- одежда: одежда, обувь, косметика, аксессуары
- здоровье: медицина, аптека, врач, витамины, лекарства
- образование: учёба, книги, курсы, канцелярия, печать
- дом: быт, уборка, ремонт, мебель, техника, хозтовары
- подарки: подарки, цветы, сувениры, совместные расходы
- коммунальные: свет, вода, газ, интернет, телефон
- прочее: всё остальное

НЕ СОЗДАВАЙ НОВЫЕ КАТЕГОРИИ! Используй только перечисленные выше.
НЕ используй подкатегории типа "еда — перекус", только "еда".
"""


class ImprovedSpendingAnalyzer:
    """Улучшенный анализатор с нормализацией категорий"""
    
    def __init__(self):
        self.normalizer = CategoryNormalizer()
    
    def analyze_spending(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Анализирует траты с нормализованными категориями"""
        
        if not transactions:
            return self._empty_analysis()
        
        # Нормализуем категории
        normalized_transactions = []
        for t in transactions:
            normalized_cat = self.normalizer.normalize_category(t.category)
            normalized_transactions.append({
                'time': t.time,
                'amount': t.amount,
                'place': t.place,
                'items': t.items,
                'category': t.category,  # оригинальная
                'normalized_category': normalized_cat,  # нормализованная
                'why': t.why,
                'mood': t.mood
            })
        
        total_spent = sum(t['amount'] for t in normalized_transactions)
        
        # Анализ по нормализованным категориям
        by_category = {}
        for t in normalized_transactions:
            cat = t['normalized_category']
            if cat not in by_category:
                by_category[cat] = {'amount': 0, 'count': 0, 'items': []}
            by_category[cat]['amount'] += t['amount']
            by_category[cat]['count'] += 1
            by_category[cat]['items'].extend(t['items'])
        
        # Сортируем по сумме
        sorted_categories = sorted(
            by_category.items(), 
            key=lambda x: x[1]['amount'], 
            reverse=True
        )
        
        # Анализ по времени
        time_analysis = self._analyze_by_time(normalized_transactions)
        
        # Анализ по местам
        place_analysis = self._analyze_by_place(normalized_transactions)
        
        # Импульсивные покупки
        impulse_analysis = self._analyze_impulse_purchases(normalized_transactions)
        
        return {
            'total_spent': total_spent,
            'average_transaction': total_spent / len(normalized_transactions),
            'transaction_count': len(normalized_transactions),
            'by_category': {cat: data['amount'] for cat, data in sorted_categories},
            'category_details': dict(sorted_categories),
            'by_time': time_analysis,
            'by_place': place_analysis,
            'impulse_purchases': impulse_analysis,
            'top_category': sorted_categories[0][0] if sorted_categories else None,
            'spending_distribution': self._calculate_distribution(by_category)
        }
    
    def _analyze_by_time(self, transactions: List[Dict]) -> Dict[str, float]:
        """Анализ по времени дня"""
        time_buckets = {
            'утро': 0,      # 6-12
            'день': 0,      # 12-18
            'вечер': 0,     # 18-22
            'ночь': 0       # 22-6
        }
        
        for t in transactions:
            try:
                hour = int(t['time'].split(':')[0])
                if 6 <= hour < 12:
                    time_buckets['утро'] += t['amount']
                elif 12 <= hour < 18:
                    time_buckets['день'] += t['amount']
                elif 18 <= hour < 22:
                    time_buckets['вечер'] += t['amount']
                else:
                    time_buckets['ночь'] += t['amount']
            except (ValueError, IndexError):
                time_buckets['день'] += t['amount']  # По умолчанию - день
        
        return time_buckets
    
    def _analyze_by_place(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Анализ по местам"""
        place_stats = {}
        
        for t in transactions:
            place = t['place']
            if place not in place_stats:
                place_stats[place] = {'amount': 0, 'count': 0}
            place_stats[place]['amount'] += t['amount']
            place_stats[place]['count'] += 1
        
        # Сортируем по сумме
        sorted_places = sorted(
            place_stats.items(),
            key=lambda x: x[1]['amount'],
            reverse=True
        )
        
        return {
            'top_places': dict(sorted_places[:5]),
            'unique_places': len(place_stats),
            'average_per_place': (
                sum(p['amount'] for p in place_stats.values()) / len(place_stats)
                if place_stats else 0
            )
        }
    
    def _analyze_impulse_purchases(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Анализ импульсивных покупок"""
        impulse_keywords = [
            'захотелось', 'настроение', 'порадовать', 'увидел', 'заметил',
            'соблазнился', 'импульс', 'внезапно', 'случайно', 'спонтанно',
            'не удержался', 'привлекло', 'понравилось'
        ]
        
        impulse_purchases = []
        for t in transactions:
            if any(keyword in t['why'].lower() for keyword in impulse_keywords):
                impulse_purchases.append(t)
        
        impulse_total = sum(t['amount'] for t in impulse_purchases)
        total_spent = sum(t['amount'] for t in transactions)
        
        return {
            'count': len(impulse_purchases),
            'total_amount': impulse_total,
            'percentage': (impulse_total / total_spent * 100) if total_spent > 0 else 0,
            'average_impulse': impulse_total / len(impulse_purchases) if impulse_purchases else 0,
            'categories': self._get_impulse_categories(impulse_purchases)
        }
    
    def _get_impulse_categories(self, impulse_purchases: List[Dict]) -> Dict[str, float]:
        """Категории импульсивных покупок"""
        categories = {}
        for t in impulse_purchases:
            cat = t['normalized_category']
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += t['amount']
        return categories
    
    def _calculate_distribution(self, by_category: Dict) -> Dict[str, float]:
        """Рассчитывает процентное распределение по категориям"""
        total = sum(data['amount'] for data in by_category.values())
        if total == 0:
            return {}
        
        return {
            cat: (data['amount'] / total * 100)
            for cat, data in by_category.items()
        }
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Возвращает пустой анализ"""
        return {
            'total_spent': 0,
            'average_transaction': 0,
            'transaction_count': 0,
            'by_category': {},
            'category_details': {},
            'by_time': {'утро': 0, 'день': 0, 'вечер': 0, 'ночь': 0},
            'by_place': {'top_places': {}, 'unique_places': 0, 'average_per_place': 0},
            'impulse_purchases': {'count': 0, 'total_amount': 0, 'percentage': 0},
            'top_category': None,
            'spending_distribution': {}
        }


class TransactionGenerator:
    """Улучшенный генератор транзакций с нормализацией категорий"""
    
    def __init__(self, person: Person):
        self.person = person
        self.daily_budget = self._calculate_daily_budget()
        self.analyzer = ImprovedSpendingAnalyzer()
        
    def _calculate_daily_budget(self) -> float:
        """Рассчитывает примерный дневной бюджет"""
        
        age = self.person.age or 25
        
        # Реалистичные доходы по возрасту
        if age < 18:
            monthly_income = {
                "низкий": 5000,    # карманные деньги
                "средний": 15000,  # подработки
                "высокий": 25000   # активные подработки
            }.get(self.person.income_level, 10000)
        elif age < 25:
            monthly_income = {
                "низкий": 25000,
                "средний": 45000,
                "высокий": 80000
            }.get(self.person.income_level, 40000)
        else:
            monthly_income = {
                "низкий": 35000,
                "средний": 80000,
                "высокий": 250000
            }.get(self.person.income_level, 60000)
        
        # Фиксированные расходы
        if age < 18:
            fixed_ratio = 0.1  # живет с родителями
        elif age < 25:
            fixed_ratio = 0.6  # съемное жилье
        else:
            fixed_ratio = 0.4  # стабильные расходы
            
        disposable = monthly_income * (1 - fixed_ratio)
        daily = disposable / 30
        
        # Корректировка на семью
        if self.person.family_status in ["женат", "замужем"]:
            daily *= 1.2
        if self.person.children and self.person.children > 0:
            daily *= (1 + 0.3 * min(self.person.children, 3))
            
        return daily
    
    async def generate_transactions(
        self,
        day_context: Dict[str, Any],
        social_interactions: List[Any],
        memory: Dict[str, Any]
    ) -> List[Transaction]:
        """Генерирует транзакции с учетом стандартных категорий"""
        
        # Строим улучшенный промпт
        prompt = self._build_improved_transaction_prompt(
            day_context,
            social_interactions,
            memory
        )
        
        # Вызываем LLM
        result = await Runner.run(transaction_generation_agent, prompt)
        
        # Безопасный парсинг JSON
        try:
            transactions_data = json.loads(result.raw_output)
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON транзакций: {e}")
            print(f"Сырой ответ: {result.raw_output}")
            return []
        
        # Преобразуем в модели с валидацией
        transactions = []
        for trans_data in transactions_data.get('transactions', []):
            try:
                # Валидация обязательных полей
                required_fields = ['time', 'amount', 'place', 'items', 'category', 'why', 'mood']
                if not all(field in trans_data for field in required_fields):
                    print(f"❌ Отсутствуют обязательные поля в транзакции: {trans_data}")
                    continue
                
                # Валидация типов данных
                if not isinstance(trans_data['amount'], (int, float)):
                    print(f"❌ Неправильный тип суммы: {trans_data['amount']}")
                    continue
                    
                if not isinstance(trans_data['items'], list):
                    print(f"❌ Товары должны быть списком: {trans_data['items']}")
                    continue
                
                transaction = Transaction(
                    time=str(trans_data['time']),
                    amount=float(trans_data['amount']),
                    place=str(trans_data['place']),
                    items=[str(item) for item in trans_data['items']],
                    category=str(trans_data['category']),
                    why=str(trans_data['why']),
                    mood=str(trans_data['mood']),
                    influenced_by_chat=bool(trans_data.get('influenced_by_chat', False))
                )
                transactions.append(transaction)
                
            except Exception as e:
                print(f"❌ Ошибка при обработке транзакции: {e}")
                print(f"Данные: {trans_data}")
                continue
        
        return transactions
    
    def _build_improved_transaction_prompt(
        self,
        day_context: Dict[str, Any],
        social_interactions: List[Any],
        memory: Dict[str, Any]
    ) -> str:
        """Строит улучшенный промпт с правилами категорий"""
        
        age = self.person.age or 25
        
        # Возрастные особенности трат
        if age < 18:
            spending_psychology = """
ПСИХОЛОГИЯ ТРАТ ПОДРОСТКОВ:
- Ограниченные деньги делают каждую покупку значимой
- Импульсивность высокая - увидел, захотел, купил
- Социальное давление сверстников важно
- Типичные покупки: еда, развлечения, мелкие вещи
- Места: школа, магазины рядом с домом
- Мотивы: голод, скука, желание произвести впечатление
            """
        elif age < 30:
            spending_psychology = """
ПСИХОЛОГИЯ ТРАТ МОЛОДЫХ ВЗРОСЛЫХ:
- Первая финансовая свобода
- Траты на социальную жизнь важны
- Импульсивность средняя
- Онлайн-покупки, подписки, доставка
- Мотивы: карьера, отношения, самовыражение
            """
        else:
            spending_psychology = """
ПСИХОЛОГИЯ ТРАТ ВЗРОСЛЫХ:
- Планирование бюджета, семейная ответственность
- Практичность превышает импульсивность
- Покупки для дома, здоровья, детей
- Мотивы: необходимость, комфорт семьи
            """
        
        # Социальные влияния
        social_context = ""
        if social_interactions:
            social_context = "СОЦИАЛЬНЫЕ ВЗАИМОДЕЙСТВИЯ СЕГОДНЯ:\n"
            for interaction in social_interactions:
                social_context += f"- С {interaction.with_person} ({interaction.context}): {interaction.emotional_impact}\n"
        
        # Недавние траты
        recent_spending = ""
        recent_days = memory.get('recent_days', [])
        if recent_days:
            recent_spending = "НЕДАВНИЕ ТРАТЫ:\n"
            for day in recent_days[-3:]:
                if 'transactions' in day:
                    for trans in day['transactions']:
                        recent_spending += f"- {trans['category']}: {trans['amount']} RUB\n"
        
        # Контекст дня
        day_type = "рабочий" if day_context.get('is_workday', True) else "выходной"
        events = day_context.get('events', ['обычный день'])
        
        # Правила категорий
        category_rules = CategoryNormalizer.get_category_rules_for_prompt()
        
        prompt = f"""Создай ЕСТЕСТВЕННЫЕ покупки для {self.person.name} на {day_type} день.

ПРОФИЛЬ ЧЕЛОВЕКА:
- Имя: {self.person.name}
- Возраст: {age}, {self.person.gender}
- Профессия: {self.person.profession or 'учащийся' if age < 18 else 'не указана'}
- Доход: {self.person.income_level}
- Семья: {self.person.family_status}
- Контекст жизни: {self.person.context}

{spending_psychology}

КОНТЕКСТ СЕГОДНЯШНЕГО ДНЯ:
- День недели: {day_context.get('day_of_week', 'неизвестно')}
- Тип дня: {day_type}
- События: {', '.join(events)}
- Погода: {day_context.get('weather', 'обычная')}

{social_context}

{recent_spending}

ПРИМЕРНЫЙ ДНЕВНОЙ БЮДЖЕТ: {self.daily_budget:.0f} RUB

{category_rules}

ТВОЯ ЗАДАЧА:
Представь себя этим человеком и подумай: что бы ты ЕСТЕСТВЕННО купил в такой день?

ПОДУМАЙ:
1. Какие у тебя потребности в этот день?
2. Как на тебя повлияло общение с людьми?
3. Что подсказывает твой возраст и жизненная ситуация?
4. Какие эмоции могут толкнуть на покупки?
5. Где ты находишься в течение дня?

ПОМНИ:
- Используй ТОЛЬКО указанные категории
- Эмоции влияют на покупки
- Социальные ситуации создают потребности
- Иногда люди экономят, иногда тратят импульсивно

Создай JSON с транзакциями:
{{
  "transactions": [
    {{
      "time": "HH:MM",
      "amount": сумма,
      "place": "конкретное место",
      "items": ["конкретный товар 1", "конкретный товар 2"],
      "category": "ТОЛЬКО из списка выше",
      "why": "внутренняя мотивация - почему именно сейчас купил это",
      "mood": "настроение при покупке",
      "influenced_by_chat": true/false
    }}
  ]
}}

БУДЬ ЕСТЕСТВЕННЫМ! Главное - РЕАЛИЗМ и ПРАВИЛЬНЫЕ КАТЕГОРИИ."""
        
        return prompt
    
    def analyze_spending_patterns(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Анализирует паттерны трат с использованием улучшенного анализатора"""
        return self.analyzer.analyze_spending(transactions)