"""Улучшенный анализатор результатов симуляции"""

from typing import List, Dict, Any
from collections import defaultdict

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from models import Person
from .transaction_models import DailyResult, SimulationConfig, Event



class CategoryNormalizer:
    """Нормализует категории для консистентного анализа"""
    
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


class ImprovedSimulationAnalyzer:
    """Улучшенный анализатор симуляции с нормализацией категорий"""
    
    def __init__(self):
        from .advanced_analyzer import AdvancedSimulationAnalyzer as AdvancedAnalyzer
        self.normalizer = CategoryNormalizer()
        # advanced analyzer for extended reports
        self.advanced_analyzer = AdvancedAnalyzer()
    
    def analyze_simulation(
        self,
        daily_results: List[DailyResult],
        person: Person,
        config: SimulationConfig
    ) -> Dict[str, Any]:
        """Полный анализ симуляции"""
        # Используем продвинутый анализатор для получения полной картины
        report = self.advanced_analyzer.generate_comprehensive_report(
            daily_results, person, config
        )

        return {
            "spending_analysis": self._extract_spending_analysis(report),
            "social_analysis": self._extract_social_analysis(report),
            "emotional_analysis": self._extract_emotional_analysis(report, daily_results),
            "behavioral_patterns": report.get("behavioral_analysis", {}),
            "daily_trends": self._extract_daily_trends(daily_results),
            "event_impact": {},
            "insights": self._extract_insights(report),
        }
    
    def _analyze_spending(self, results: List[DailyResult]) -> Dict[str, Any]:
        """Улучшенный анализ трат с нормализацией"""
        
        all_transactions = []
        daily_totals = []
        
        for day in results:
            daily_total = sum(t.amount for t in day.transactions)
            daily_totals.append(daily_total)
            all_transactions.extend(day.transactions)
        
        if not all_transactions:
            return self._empty_spending_analysis()
        
        # Нормализация категорий
        normalized_categories = defaultdict(float)
        category_counts = defaultdict(int)
        original_categories = defaultdict(float)
        
        for t in all_transactions:
            normalized_cat = self.normalizer.normalize_category(t.category)
            normalized_categories[normalized_cat] += t.amount
            category_counts[normalized_cat] += 1
            original_categories[t.category] += t.amount
        
        # Анализ по местам
        by_place = defaultdict(float)
        place_frequency = defaultdict(int)
        
        for t in all_transactions:
            by_place[t.place] += t.amount
            place_frequency[t.place] += 1
        
        # Топ места
        top_places = sorted(by_place.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Анализ по времени
        time_analysis = self._analyze_spending_by_time(all_transactions)
        
        # Импульсивные покупки
        impulse_analysis = self._analyze_impulse_spending(all_transactions)
        
        return {
            "total_spent": sum(daily_totals),
            "daily_average": sum(daily_totals) / len(daily_totals),
            "daily_min": min(daily_totals),
            "daily_max": max(daily_totals),
            "transactions_count": len(all_transactions),
            "by_category": dict(sorted(normalized_categories.items(), 
                                     key=lambda x: x[1], reverse=True)),
            "category_counts": dict(category_counts),
            "category_distribution": self._calculate_category_distribution(normalized_categories),
            "original_categories": dict(original_categories),
            "by_place": dict(top_places),
            "unique_places": len(by_place),
            "place_frequency": dict(place_frequency),
            "by_time": time_analysis,
            "impulse_purchases": impulse_analysis,
            "spending_volatility": self._calculate_spending_volatility(daily_totals),
            "spending_trend": self._analyze_spending_trend(daily_totals)
        }
    
    def _analyze_spending_by_time(self, transactions: List) -> Dict[str, Any]:
        """Анализ трат по времени дня"""
        time_buckets = {
            'утро': 0,      # 6-12
            'день': 0,      # 12-18
            'вечер': 0,     # 18-22
            'ночь': 0       # 22-6
        }
        
        time_counts = {
            'утро': 0,
            'день': 0,
            'вечер': 0,
            'ночь': 0
        }
        
        for t in transactions:
            try:
                hour = int(t.time.split(':')[0])
                if 6 <= hour < 12:
                    time_buckets['утро'] += t.amount
                    time_counts['утро'] += 1
                elif 12 <= hour < 18:
                    time_buckets['день'] += t.amount
                    time_counts['день'] += 1
                elif 18 <= hour < 22:
                    time_buckets['вечер'] += t.amount
                    time_counts['вечер'] += 1
                else:
                    time_buckets['ночь'] += t.amount
                    time_counts['ночь'] += 1
            except (ValueError, IndexError):
                time_buckets['день'] += t.amount
                time_counts['день'] += 1
        
        return {
            'by_amount': time_buckets,
            'by_count': time_counts,
            'peak_spending_time': max(time_buckets.items(), key=lambda x: x[1])[0]
        }
    
    def _analyze_impulse_spending(self, transactions: List) -> Dict[str, Any]:
        """Анализ импульсивных покупок"""
        impulse_keywords = [
            'захотелось', 'настроение', 'порадовать', 'увидел', 'заметил',
            'соблазнился', 'импульс', 'внезапно', 'случайно', 'спонтанно',
            'не удержался', 'привлекло', 'понравилось'
        ]
        
        impulse_transactions = []
        for t in transactions:
            if any(keyword in t.why.lower() for keyword in impulse_keywords):
                impulse_transactions.append(t)
        
        if not impulse_transactions:
            return {
                'count': 0,
                'total_amount': 0,
                'percentage': 0,
                'top_categories': {}
            }
        
        impulse_total = sum(t.amount for t in impulse_transactions)
        total_spent = sum(t.amount for t in transactions)
        
        # Категории импульсивных покупок
        impulse_categories = defaultdict(float)
        for t in impulse_transactions:
            cat = self.normalizer.normalize_category(t.category)
            impulse_categories[cat] += t.amount
        
        return {
            'count': len(impulse_transactions),
            'total_amount': impulse_total,
            'percentage': (impulse_total / total_spent * 100) if total_spent > 0 else 0,
            'average_impulse': impulse_total / len(impulse_transactions),
            'top_categories': dict(sorted(impulse_categories.items(), 
                                        key=lambda x: x[1], reverse=True))
        }
    
    def _calculate_category_distribution(self, categories: Dict[str, float]) -> Dict[str, float]:
        """Процентное распределение по категориям"""
        total = sum(categories.values())
        if total == 0:
            return {}
        
        return {
            cat: (amount / total * 100)
            for cat, amount in categories.items()
        }
    
    def _calculate_spending_volatility(self, daily_totals: List[float]) -> float:
        """Волатильность трат"""
        if len(daily_totals) < 2:
            return 0
        
        mean = sum(daily_totals) / len(daily_totals)
        variance = sum((x - mean) ** 2 for x in daily_totals) / len(daily_totals)
        std_dev = variance ** 0.5
        
        return std_dev / mean if mean > 0 else 0
    
    def _analyze_spending_trend(self, daily_totals: List[float]) -> str:
        """Тренд трат"""
        if len(daily_totals) < 7:
            return "недостаточно данных"
        
        first_half = daily_totals[:len(daily_totals)//2]
        second_half = daily_totals[len(daily_totals)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg * 1.1:
            return "растущий"
        elif second_avg < first_avg * 0.9:
            return "снижающийся"
        else:
            return "стабильный"
    
    def _analyze_social(self, results: List[DailyResult]) -> Dict[str, Any]:
        """Анализ социальных взаимодействий"""
        
        total_interactions = sum(len(day.social_interactions) for day in results)
        
        if total_interactions == 0:
            return {
                'total_interactions': 0,
                'daily_average': 0,
                'unique_contacts': 0,
                'top_contacts': {},
                'interaction_frequency': {}
            }
        
        # Частота контактов
        contact_frequency = defaultdict(int)
        contact_quality = defaultdict(list)
        
        for day in results:
            for interaction in day.social_interactions:
                contact_frequency[interaction.with_person] += 1
                contact_quality[interaction.with_person].append(interaction.emotional_impact)
        
        # Топ контакты
        top_contacts = sorted(contact_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_interactions': total_interactions,
            'daily_average': total_interactions / len(results),
            'unique_contacts': len(contact_frequency),
            'top_contacts': dict(top_contacts),
            'interaction_frequency': dict(contact_frequency),
            'most_frequent_contact': top_contacts[0][0] if top_contacts else None,
            'social_diversity': len(contact_frequency) / total_interactions if total_interactions > 0 else 0
        }
    
    def _analyze_emotions(self, results: List[DailyResult]) -> Dict[str, Any]:
        """Анализ эмоциональных траекторий"""
        
        mood_trajectories = [day.day_summary.mood_trajectory for day in results]
        
        # Простой анализ позитивности
        positive_words = ['радость', 'счастье', 'воодушевление', 'спокойствие', 'удовлетворение', 'гордость']
        negative_words = ['усталость', 'тревога', 'стресс', 'раздражение', 'грусть', 'конфликт']
        
        positive_count = sum(
            1 for trajectory in mood_trajectories 
            if any(word in trajectory.lower() for word in positive_words)
        )
        
        negative_count = sum(
            1 for trajectory in mood_trajectories 
            if any(word in trajectory.lower() for word in negative_words)
        )
        
        return {
            'mood_trajectories': mood_trajectories,
            'positive_days': positive_count,
            'negative_days': negative_count,
            'neutral_days': len(mood_trajectories) - positive_count - negative_count,
            'positivity_ratio': positive_count / len(mood_trajectories) if mood_trajectories else 0,
            'overall_mood': self._determine_overall_mood(positive_count, negative_count, len(mood_trajectories))
        }
    
    def _determine_overall_mood(self, positive: int, negative: int, total: int) -> str:
        """Определяет общее настроение"""
        if positive > negative * 1.5:
            return "преимущественно позитивное"
        elif negative > positive * 1.5:
            return "преимущественно негативное"
        else:
            return "смешанное"
    
    def _analyze_behavioral_patterns(self, results: List[DailyResult]) -> Dict[str, Any]:
        """Анализ поведенческих паттернов"""
        
        weekday_spending = []
        weekend_spending = []
        
        for day in results:
            daily_total = sum(t.amount for t in day.transactions)
            if day.day_context.is_workday:
                weekday_spending.append(daily_total)
            else:
                weekend_spending.append(daily_total)
        
        return {
            'weekday_vs_weekend': {
                'weekday_average': sum(weekday_spending) / len(weekday_spending) if weekday_spending else 0,
                'weekend_average': sum(weekend_spending) / len(weekend_spending) if weekend_spending else 0,
                'weekend_premium': (
                    (sum(weekend_spending) / len(weekend_spending)) - 
                    (sum(weekday_spending) / len(weekday_spending))
                ) if weekday_spending and weekend_spending else 0
            },
            'routine_analysis': self._analyze_routine_patterns(results)
        }
    
    def _analyze_routine_patterns(self, results: List[DailyResult]) -> Dict[str, Any]:
        """Анализ рутинных паттернов"""
        
        # Частые места
        place_days = defaultdict(int)
        for day in results:
            visited_places = set(t.place for t in day.transactions)
            for place in visited_places:
                place_days[place] += 1
        
        routine_places = {
            place: count for place, count in place_days.items() 
            if count > len(results) * 0.3  # появляется в >30% дней
        }
        
        return {
            'routine_places': routine_places,
            'routine_level': len(routine_places) / len(place_days) if place_days else 0
        }
    
    def _analyze_daily_trends(self, results: List[DailyResult]) -> Dict[str, Any]:
        """Анализ трендов по дням"""
        
        daily_data = []
        for day in results:
            daily_data.append({
                'date': day.date,
                'total_spent': sum(t.amount for t in day.transactions),
                'transaction_count': len(day.transactions),
                'social_interactions': len(day.social_interactions),
                'mood_positive': any(word in day.day_summary.mood_trajectory.lower() 
                                   for word in ['радость', 'счастье', 'воодушевление'])
            })
        
        return {
            'daily_data': daily_data,
            'spending_progression': [d['total_spent'] for d in daily_data],
            'social_progression': [d['social_interactions'] for d in daily_data],
            'peak_spending_day': max(daily_data, key=lambda x: x['total_spent']),
            'peak_social_day': max(daily_data, key=lambda x: x['social_interactions'])
        }
    
    def _analyze_event_impact(
        self, 
        results: List[DailyResult], 
        config: SimulationConfig
    ) -> Dict[str, Any]:
        """Анализ влияния событий"""
        
        if not config.events:
            return {'no_events': True}
        
        event_impacts = {}
        
        for event in config.events:
            if isinstance(event, dict):
                event_day = event.get('day', 0)
                event_type = event.get('type', 'unknown')
            else:
                event_day = event.day
                event_type = event.type
            
            if event_day >= len(results):
                continue
            
            # Анализ до и после события
            before_days = results[max(0, event_day-2):event_day]
            after_days = results[event_day+1:min(len(results), event_day+3)]
            
            before_avg = sum(
                sum(t.amount for t in day.transactions) 
                for day in before_days
            ) / len(before_days) if before_days else 0
            
            after_avg = sum(
                sum(t.amount for t in day.transactions) 
                for day in after_days
            ) / len(after_days) if after_days else 0
            
            event_impacts[event_type] = {
                'before_average': before_avg,
                'after_average': after_avg,
                'spending_change': ((after_avg - before_avg) / before_avg * 100) if before_avg > 0 else 0,
                'event_day_spending': sum(t.amount for t in results[event_day].transactions) if event_day < len(results) else 0
            }
        
        return event_impacts
    
    def _generate_insights(self, results: List[DailyResult], person: Person) -> List[str]:
        """Генерирует ключевые инсайты"""
        insights = []
        
        # Анализ трат
        total_spent = sum(sum(t.amount for t in day.transactions) for day in results)
        daily_avg = total_spent / len(results)
        
        if daily_avg < 200:
            insights.append("Экономный режим: низкие ежедневные траты")
        elif daily_avg > 1000:
            insights.append("Высокий уровень трат: может указывать на активный образ жизни")
        
        # Анализ социальности
        total_interactions = sum(len(day.social_interactions) for day in results)
        social_avg = total_interactions / len(results)
        
        if social_avg > 5:
            insights.append("Высокая социальная активность: регулярное общение")
        elif social_avg < 2:
            insights.append("Низкая социальная активность: ограниченное общение")
        
        # Анализ категорий
        all_transactions = []
        for day in results:
            all_transactions.extend(day.transactions)
        
        if all_transactions:
            category_amounts = defaultdict(float)
            for t in all_transactions:
                normalized_cat = self.normalizer.normalize_category(t.category)
                category_amounts[normalized_cat] += t.amount
            
            top_category = max(category_amounts.items(), key=lambda x: x[1])[0]
            insights.append(f"Основная категория трат: {top_category}")
        
        return insights
    
    def _empty_spending_analysis(self) -> Dict[str, Any]:
        """Пустой анализ трат"""
        return {
            "total_spent": 0,
            "daily_average": 0,
            "transactions_count": 0,
            "by_category": {},
            "by_place": {},
            "by_time": {'утро': 0, 'день': 0, 'вечер': 0, 'ночь': 0},
            "impulse_purchases": {'count': 0, 'total_amount': 0, 'percentage': 0}
        }
    
    def generate_summary(self, results: List[DailyResult]) -> Dict[str, Any]:
        """Генерирует итоговую сводку"""
        
        if not results:
            return {
                "total_days": 0,
                "total_spent": 0,
                "daily_average": 0,
                "total_transactions": 0,
                "total_interactions": 0,
                "unique_contacts": 0,
                "overall_mood": "нет данных",
                "key_insights": [],
                "summary": "Данные отсутствуют"
            }
        
        # Основные метрики
        total_spent = sum(sum(t.amount for t in day.transactions) for day in results)
        total_transactions = sum(len(day.transactions) for day in results)
        total_interactions = sum(len(day.social_interactions) for day in results)
        
        # Уникальные контакты
        unique_contacts = set()
        for day in results:
            for interaction in day.social_interactions:
                unique_contacts.add(interaction.with_person)
        
        # Анализ настроения
        emotions = self._analyze_emotions(results)
        
        # Топ категория трат
        all_transactions = []
        for day in results:
            all_transactions.extend(day.transactions)
        
        top_category = None
        if all_transactions:
            category_amounts = defaultdict(float)
            for t in all_transactions:
                normalized_cat = self.normalizer.normalize_category(t.category)
                category_amounts[normalized_cat] += t.amount
            
            if category_amounts:
                top_category = {
                    "category": max(category_amounts.items(), key=lambda x: x[1])[0],
                    "amount": max(category_amounts.values())
                }
        
        # Ключевые инсайты
        key_insights = [
            f"Экономный режим: {total_spent/len(results):.0f} RUB в день",
            f"Высокая социальная активность: {total_interactions/len(results):.1f} взаимодействий/день",
            f"Эмоциональное состояние: {emotions['overall_mood']}",
            f"Основная категория трат: {top_category['category']} ({top_category['amount']:.0f} RUB)" if top_category else "Категории трат не определены",
            f"Широкий круг общения: {len(unique_contacts)} контактов"
        ]
        
        return {
            "total_days": len(results),
            "total_spent": total_spent,
            "daily_average": total_spent / len(results),
            "total_transactions": total_transactions,
            "total_interactions": total_interactions,
            "unique_contacts": len(unique_contacts),
            "overall_mood": emotions['overall_mood'],
            "top_spending_category": top_category,
            "key_insights": key_insights,
            "summary": f"За {len(results)} дней потрачено {total_spent:.0f} RUB (в среднем {total_spent/len(results):.0f} RUB/день). Состоялось {total_interactions} социальных взаимодействий с {len(unique_contacts)} людьми. Эмоциональное состояние: {emotions['overall_mood']}."
        }
    # ----- Методы извлечения данных из продвинутого отчета -----
    def _extract_spending_analysis(self, report: Dict[str, Any]) -> Dict[str, Any]:
        stats = report.get('basic_statistics', {})
        spending = report.get('spending_deep_dive', {})
        categories = spending.get('category_deep_dive', {})
        by_category = {c: d.get('total', 0) for c, d in categories.items()}
        return {
            "total_spent": stats.get('total_spent', 0),
            "daily_average": stats.get('average_daily_spent', 0),
            "daily_min": stats.get('spending_range', {}).get('min', 0),
            "daily_max": stats.get('spending_range', {}).get('max', 0),
            "transactions_count": stats.get('total_transactions', 0),
            "by_category": by_category,
            "category_counts": {c: d.get('frequency', 0) for c, d in categories.items()},
            "category_distribution": spending.get('price_sensitivity_index', 0),
            "by_place": {},
            "unique_places": len(spending.get('place_intelligence', {}).get('place_profiles', {})),
            "by_time": spending.get('spending_velocity', {}).get('spending_by_period', {}),
            "impulse_purchases": spending.get('purchase_frequency', {}).get('impulse_rate', 0),
            "spending_volatility": 0,
            "spending_trend": self._determine_trend(categories),
        }

    def _extract_social_analysis(self, report: Dict[str, Any]) -> Dict[str, Any]:
        stats = report.get('basic_statistics', {})
        social = report.get('social_dynamics', {})
        network = social.get('social_network', {})
        contact_frequency = {p: d.get('interactions', 0) for p, d in network.items()}
        top_contacts = sorted(contact_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        return {
            'total_interactions': stats.get('total_social_interactions', 0),
            'daily_average': stats.get('total_social_interactions', 0) / stats.get('days_analyzed', 1) if stats.get('days_analyzed') else 0,
            'unique_contacts': len(network),
            'top_contacts': dict(top_contacts),
            'interaction_frequency': contact_frequency,
            'most_frequent_contact': top_contacts[0][0] if top_contacts else None,
            'social_diversity': len(network) / stats.get('total_social_interactions', 1) if stats.get('total_social_interactions') else 0,
        }

    def _extract_emotional_analysis(self, report: Dict[str, Any], results: List[DailyResult]) -> Dict[str, Any]:
        mood_trajectories = [day.day_summary.mood_trajectory for day in results]
        pos_words = ['радость', 'счастье', 'воодушевление', 'спокойствие', 'удовлетворение', 'приятно']
        neg_words = ['усталость', 'тревога', 'стресс', 'раздражение', 'грусть', 'конфликт']
        pos = sum(1 for tr in mood_trajectories if any(w in tr.lower() for w in pos_words))
        neg = sum(1 for tr in mood_trajectories if any(w in tr.lower() for w in neg_words))
        return {
            'mood_trajectories': mood_trajectories,
            'positive_days': pos,
            'negative_days': neg,
            'neutral_days': len(mood_trajectories) - pos - neg,
            'positivity_ratio': pos / len(mood_trajectories) if mood_trajectories else 0,
            'overall_mood': self._determine_overall_mood_from_counts(pos, neg, len(mood_trajectories)),
        }

    def _extract_daily_trends(self, results: List[DailyResult]) -> Dict[str, Any]:
        daily_data = []
        for day in results:
            daily_data.append({
                'date': day.date,
                'total_spent': sum(t.amount for t in day.transactions),
                'transaction_count': len(day.transactions),
                'social_interactions': len(day.social_interactions),
                'mood_positive': any(word in day.day_summary.mood_trajectory.lower() for word in ['радость', 'счастье', 'воодушевление']),
            })
        return {
            'daily_data': daily_data,
            'spending_progression': [d['total_spent'] for d in daily_data],
            'social_progression': [d['social_interactions'] for d in daily_data],
            'peak_spending_day': max(daily_data, key=lambda x: x['total_spent']) if daily_data else None,
            'peak_social_day': max(daily_data, key=lambda x: x['social_interactions']) if daily_data else None,
        }

    def _extract_insights(self, report: Dict[str, Any]) -> List[str]:
        insights = []
        for ins in report.get('key_insights', [])[:5]:
            insights.append(f"{ins['insight']}: {ins.get('details', '')}")
        for opp in report.get('advertising_opportunities', {}).get('immediate_opportunities', [])[:2]:
            insights.append(f"Возможность: {opp.get('product', '')} - {opp.get('reasoning', '')}")
        return insights

    def _determine_trend(self, categories: Dict[str, Any]) -> str:
        trends = [d.get('trend') for d in categories.values() if isinstance(d, dict) and 'trend' in d]
        if not trends:
            return 'недостаточно данных'
        growing = sum(1 for t in trends if t == 'растущий')
        declining = sum(1 for t in trends if t == 'снижающийся')
        if growing > declining:
            return 'растущий'
        if declining > growing:
            return 'снижающийся'
        return 'стабильный'
