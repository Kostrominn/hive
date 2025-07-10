"""Генератор транзакций"""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models import Person, Runner
from .agents import transaction_generation_agent
from .prompts import build_transaction_prompt
from .transaction_models import Transaction, DailyResult


class TransactionGenerator:
    """Генерирует транзакции с учетом контекста"""
    
    def __init__(self, person: Person):
        self.person = person
        self.daily_budget = self._calculate_daily_budget()
        
    def _calculate_daily_budget(self) -> float:
        """Рассчитывает примерный дневной бюджет"""
        
        monthly_income = {
            "низкий": 35000,
            "средний": 80000,
            "высокий": 250000
        }.get(self.person.income_level, 60000)
        
        # Фиксированные расходы (аренда, коммуналка) ~ 40%
        fixed = monthly_income * 0.4
        
        # Остается на жизнь
        disposable = monthly_income - fixed
        
        # Дневной бюджет
        daily = disposable / 30
        
        # Корректировка на семью
        if self.person.family_status in ["женат", "замужем"]:
            daily *= 1.3
        if self.person.children and self.person.children > 0:
            daily *= (1 + 0.2 * min(self.person.children, 3))
            
        return daily
    
    async def generate_transactions(
        self,
        day_context: Dict[str, Any],
        social_interactions: List[Any],
        memory: Dict[str, Any]
    ) -> List[Transaction]:
        """Генерирует транзакции дня"""
        
        # Строим промпт
        prompt = build_transaction_prompt(
            self.person,
            day_context,
            [
                {
                    'with_person': si.with_person,
                    'context': si.context,
                    'emotional_impact': si.emotional_impact
                }
                for si in social_interactions
            ],
            memory,
            self.daily_budget
        )
        
        # Вызываем LLM
        result = await Runner.run(transaction_generation_agent, prompt)
        transactions_data = json.loads(result.raw_output)
        
        # Преобразуем в модели
        transactions = []
        for trans_data in transactions_data.get('transactions', []):
            transaction = Transaction(
                time=trans_data['time'],
                amount=trans_data['amount'],
                place=trans_data['place'],
                items=trans_data['items'],
                category=trans_data['category'],
                why=trans_data['why'],
                mood=trans_data['mood']
            )
            transactions.append(transaction)
        
        return transactions
    
    def analyze_spending_patterns(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Анализирует паттерны трат"""
        
        total_spent = sum(t.amount for t in transactions)
        
        # По категориям
        by_category = {}
        for t in transactions:
            if t.category not in by_category:
                by_category[t.category] = 0
            by_category[t.category] += t.amount
        
        # По времени
        morning = sum(t.amount for t in transactions if int(t.time.split(':')[0]) < 12)
        afternoon = sum(t.amount for t in transactions if 12 <= int(t.time.split(':')[0]) < 18)
        evening = sum(t.amount for t in transactions if int(t.time.split(':')[0]) >= 18)
        
        # Импульсивные покупки (простая эвристика)
        impulse_keywords = ['захотелось', 'настроение', 'порадовать', 'увидел']
        impulse_purchases = [
            t for t in transactions 
            if any(kw in t.why.lower() for kw in impulse_keywords)
        ]
        
        return {
            'total_spent': total_spent,
            'by_category': by_category,
            'by_time': {
                'morning': morning,
                'afternoon': afternoon,
                'evening': evening
            },
            'impulse_purchases': len(impulse_purchases),
            'impulse_amount': sum(t.amount for t in impulse_purchases),
            'average_transaction': total_spent / len(transactions) if transactions else 0,
            'budget_utilization': (total_spent / self.daily_budget) * 100
        }