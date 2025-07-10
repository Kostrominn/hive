"""Simple textual report generator for transaction simulation."""

from typing import List

from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from models import Person
from .transaction_models import DailyResult
from .analyzer import ImprovedSimulationAnalyzer


class ReportGenerator:
    """Generates a human readable report from simulation results."""

    def __init__(self, person: Person):
        self.person = person
        self.analyzer = ImprovedSimulationAnalyzer()

    def generate_detailed_report(self, daily_results: List[DailyResult]) -> str:
        summary = self.analyzer.generate_summary(daily_results)
        lines = [
            f"Отчёт по симуляции для {self.person.name}",
            f"Период: {summary['total_days']} дней",
            f"Всего потрачено: {summary['total_spent']:.0f} RUB (средне {summary['daily_average']:.0f} RUB/день)",
            f"Транзакций: {summary['total_transactions']}",
            f"Социальных взаимодействий: {summary['total_interactions']} ({summary['unique_contacts']} контактов)",
            f"Настроение: {summary['overall_mood']}",
        ]
        top_category = summary.get("top_spending_category")
        if top_category:
            lines.append(
                f"Основная категория трат: {top_category['category']} ({top_category['amount']:.0f} RUB)"
            )
        if summary.get("key_insights"):
            lines.append("\nКлючевые инсайты:")
            for ins in summary["key_insights"]:
                lines.append(f"- {ins}")
        return "\n".join(lines)
