"""Simple textual report generator for transaction simulation."""

from typing import List
from datetime import datetime

from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from models import Person
from .transaction_models import DailyResult, SimulationConfig
from .analyzer import ImprovedSimulationAnalyzer
from .enhanced_report_generator import EnhancedReportGenerator as AdvancedReportGen


class ReportGenerator:
    """Generates a human readable report from simulation results."""

    def __init__(self, person: Person):
        self.person = person
        self.analyzer = ImprovedSimulationAnalyzer()
        self.advanced_generator = AdvancedReportGen(person)

    def generate_detailed_report(self, daily_results: List[DailyResult]) -> str:
        return self.advanced_generator.generate_detailed_report(daily_results)

    def generate_brief_summary(self, daily_results: List[DailyResult]) -> str:
        summary = self.analyzer.generate_summary(daily_results)
        lines = [
            f"📊 КРАТКАЯ СВОДКА",
            f"{'='*40}",
            f"Период: {summary['total_days']} дней",
            f"Потрачено: {summary['total_spent']:.0f} RUB (в среднем {summary['daily_average']:.0f} RUB/день)",
            f"Транзакций: {summary['total_transactions']}",
            f"Социальных взаимодействий: {summary['total_interactions']} с {summary['unique_contacts']} людьми",
            f"Настроение: {summary['overall_mood']}",
        ]
        top_category = summary.get('top_spending_category')
        if top_category:
            lines.append(f"Основная категория трат: {top_category['category']} ({top_category['amount']:.0f} RUB)")
        if summary.get('key_insights'):
            lines.append("\n💡 Ключевые выводы:")
            for ins in summary['key_insights'][:3]:
                lines.append(f"  • {ins}")
        return "\n".join(lines)


# Экспортируем улучшенный генератор для прямого использования
EnhancedReportGenerator = AdvancedReportGen
