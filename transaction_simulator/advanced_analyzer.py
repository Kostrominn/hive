from typing import List, Dict, Any
from collections import defaultdict, Counter
import json

from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from models import Person
from .transaction_models import DailyResult, SimulationConfig, Transaction, SocialInteraction
from .analyzer import CategoryNormalizer
from llm_api import call_openai


class BehavioralPatternAnalyzer:
    """Simplified behavioral pattern analyzer"""

    def analyze_lifestyle_patterns(self, results: List[DailyResult], person: Person) -> Dict[str, Any]:
        activity_hours = Counter()
        wake_times = []
        end_times = []
        for day in results:
            if day.transactions:
                wake_times.append(day.transactions[0].time)
                end_times.append(day.transactions[-1].time)
            for t in day.transactions:
                try:
                    hour = int(t.time.split(':')[0])
                    activity_hours[hour] += 1
                except Exception:
                    pass
        peak_hour = activity_hours.most_common(1)[0][0] if activity_hours else None
        life_rhythm = {
            'typical_wake_time': self._avg_time(wake_times),
            'typical_end_time': self._avg_time(end_times),
            'routine_stability': 0.0,
        }
        activity_timeline = {
            'peak_activity_time': peak_hour,
        }
        return {
            'activity_timeline': activity_timeline,
            'social_influence': {},
            'emotional_triggers': {},
            'brand_preferences': {},
            'life_rhythm': life_rhythm,
            'financial_behavior': {},
            'lifestyle_type': 'сбалансированный тип',
        }

    def _avg_time(self, times: List[str]) -> str:
        minutes = []
        for t in times:
            try:
                h, m = map(int, t.split(':'))
                minutes.append(h * 60 + m)
            except Exception:
                pass
        if not minutes:
            return 'не определено'
        avg = sum(minutes) / len(minutes)
        return f"{int(avg // 60):02d}:{int(avg % 60):02d}"


class TargetedAdvertisingRecommender:
    """Very simplified advertising recommender"""

    def generate_ad_recommendations(self, behavioral: Dict[str, Any], spending: Dict[str, Any], person: Person) -> Dict[str, Any]:
        """Call LLM to propose advertising ideas based on spending analysis."""

        default = {
            'immediate_opportunities': [],
            'product_recommendations': {},
            'optimal_ad_timing': {},
            'messaging_strategy': {},
            'channel_recommendations': [],
            'budget_recommendations': {},
            'competitor_opportunities': [],
        }

        categories = spending.get('category_deep_dive', {})
        top = sorted(categories.items(), key=lambda x: x[1].get('total', 0), reverse=True)[:3]
        cat_summary = "; ".join(f"{c}:{d.get('total',0):.0f}р" for c, d in top)

        prompt = (
            "Сформируй краткие рекомендации по таргетированной рекламе. "
            f"Профиль: {person.gender}, {person.age} лет, регион {person.region}. "
            f"Тип жизни: {behavioral.get('lifestyle_type','не указан')}. "
            f"Траты: {cat_summary}. "
            "Верни JSON c ключами: immediate_opportunities, product_recommendations, "
            "optimal_ad_timing, messaging_strategy, channel_recommendations, "
            "budget_recommendations, competitor_opportunities."
        )

        raw = call_openai([{"role": "user", "content": prompt}])
        try:
            data = json.loads(raw)
        except Exception:
            return default

        if isinstance(data, dict):
            default.update(data)
        return default


class AdvancedSimulationAnalyzer:
    """Produce comprehensive report with basic statistics"""

    def __init__(self):
        self.behavioral_analyzer = BehavioralPatternAnalyzer()
        self.ad_recommender = TargetedAdvertisingRecommender()
        self.category_normalizer = CategoryNormalizer()

    def generate_comprehensive_report(
        self,
        daily_results: List[DailyResult],
        person: Person,
        config: SimulationConfig | None = None,
    ) -> Dict[str, Any]:
        basic_stats = self._calculate_basic_statistics(daily_results)
        behavioral = self.behavioral_analyzer.analyze_lifestyle_patterns(daily_results, person)
        spending = self._analyze_spending_in_depth(daily_results)
        social = self._analyze_social_dynamics(daily_results)
        ads = self.ad_recommender.generate_ad_recommendations(behavioral, spending, person)
        predictions = self._generate_predictions(behavioral, spending, person)
        key_insights = self._extract_key_insights(behavioral, spending, social, person)
        return {
            'executive_summary': self._create_executive_summary(basic_stats, behavioral, ads),
            'basic_statistics': basic_stats,
            'behavioral_analysis': behavioral,
            'spending_deep_dive': spending,
            'social_dynamics': social,
            'advertising_opportunities': ads,
            'predictions': predictions,
            'key_insights': key_insights,
            'actionable_recommendations': self._create_actionable_recommendations(behavioral, ads),
        }

    def _calculate_basic_statistics(self, results: List[DailyResult]) -> Dict[str, Any]:
        total_spent = sum(sum(t.amount for t in d.transactions) for d in results)
        total_transactions = sum(len(d.transactions) for d in results)
        total_interactions = sum(len(d.social_interactions) for d in results)
        return {
            'period': f"{results[0].date} - {results[-1].date}" if results else 'нет данных',
            'days_analyzed': len(results),
            'total_spent': total_spent,
            'average_daily_spent': total_spent / len(results) if results else 0,
            'total_transactions': total_transactions,
            'total_social_interactions': total_interactions,
            'spending_range': {
                'min': min((sum(t.amount for t in d.transactions) for d in results), default=0),
                'max': max((sum(t.amount for t in d.transactions) for d in results), default=0),
            },
        }

    def _analyze_spending_in_depth(self, results: List[DailyResult]) -> Dict[str, Any]:
        categories = defaultdict(lambda: {'amounts': [], 'items': []})
        for day in results:
            for t in day.transactions:
                cat = self.category_normalizer.normalize_category(t.category)
                categories[cat]['amounts'].append(t.amount)
                categories[cat]['items'].extend(t.items)
        cat_info = {
            c: {
                'total': sum(v['amounts']),
                'average': sum(v['amounts']) / len(v['amounts']) if v['amounts'] else 0,
                'frequency': len(v['amounts']),
                'top_items': Counter(v['items']).most_common(3),
            }
            for c, v in categories.items()
        }
        return {
            'category_deep_dive': cat_info,
            'purchase_frequency': {},
            'place_intelligence': {},
            'basket_analysis': {},
            'price_sensitivity_index': 0,
            'spending_velocity': {},
        }

    def _analyze_social_dynamics(self, results: List[DailyResult]) -> Dict[str, Any]:
        interactions = defaultdict(int)
        for day in results:
            for si in day.social_interactions:
                interactions[si.with_person] += 1
        return {
            'social_network': {p: {'interactions': n} for p, n in interactions.items()},
            'relationship_classifications': {},
            'communication_patterns': {},
            'emotional_support_network': [],
            'influence_matrix': {},
        }

    def _generate_predictions(self, behavioral: Dict[str, Any], spending: Dict[str, Any], person: Person) -> Dict[str, Any]:
        """Use LLM to forecast future behaviour and spending."""

        default = {
            'next_month_spending': {},
            'likely_major_purchases': [],
            'churn_risk': {},
            'upsell_probability': {},
            'lifestyle_changes': [],
        }

        categories = spending.get('category_deep_dive', {})
        top = sorted(categories.items(), key=lambda x: x[1].get('total', 0), reverse=True)[:3]
        cat_summary = "; ".join(f"{c}:{d.get('total',0):.0f}р" for c, d in top)

        prompt = (
            "Сделай краткий прогноз финансового поведения на основе данных. "
            f"Возраст {person.age}, доход {person.income_level}. "
            f"Тип жизни {behavioral.get('lifestyle_type')}. "
            f"Основные траты: {cat_summary}. "
            "Верни JSON с ключами next_month_spending, likely_major_purchases, "
            "churn_risk, upsell_probability, lifestyle_changes."
        )

        raw = call_openai([{"role": "user", "content": prompt}])
        try:
            data = json.loads(raw)
        except Exception:
            return default

        if isinstance(data, dict):
            default.update(data)
        return default

    def _extract_key_insights(self, behavioral: Dict[str, Any], spending: Dict[str, Any], social: Dict[str, Any], person: Person) -> List[Dict[str, Any]]:
        """Ask LLM to highlight important observations."""

        categories = spending.get('category_deep_dive', {})
        top = sorted(categories.items(), key=lambda x: x[1].get('total', 0), reverse=True)[:3]
        cat_summary = "; ".join(f"{c}:{d.get('total',0):.0f}р" for c, d in top)

        prompt = (
            "Выведи 3-5 ключевых инсайтов из поведения и трат. "
            f"Тип жизни {behavioral.get('lifestyle_type')}. "
            f"Траты: {cat_summary}. "
            "Формат ответа: JSON список объектов с полями type, insight, details, recommendation."
        )

        raw = call_openai([{"role": "user", "content": prompt}])
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return data
        except Exception:
            pass

        fallback = []
        if behavioral.get('life_rhythm', {}).get('typical_wake_time') == 'не определено':
            fallback.append({'type': 'warning', 'insight': 'Мало данных о режиме дня', 'details': '', 'recommendation': ''})
        return fallback

    def _create_executive_summary(self, stats: Dict[str, Any], behavioral: Dict[str, Any], ads: Dict[str, Any]) -> str:
        return (
            f"ПРОФИЛЬ: {behavioral.get('lifestyle_type','N/A')}\n"
            f"Средние траты: {stats.get('average_daily_spent',0):.0f} руб/день"
        )

    def _create_actionable_recommendations(self, behavioral: Dict[str, Any], ads: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate short action plan for marketing team using LLM."""

        prompt = (
            "Составь список конкретных действий маркетологов для такого клиента. "
            f"Тип жизни: {behavioral.get('lifestyle_type')}. "
            "Ответь JSON списком объектов с полями action, priority, timeline, expected_roi."
        )

        raw = call_openai([{"role": "user", "content": prompt}])
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return data
        except Exception:
            pass
        return []
