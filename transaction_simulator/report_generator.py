"""Simple textual report generator for transaction simulation."""

from typing import List
from datetime import datetime

from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from models import Person
from .transaction_models import DailyResult, SimulationConfig
from .analyzer import ImprovedSimulationAnalyzer


class ReportGenerator:
    """Generates a human readable report from simulation results."""

    def __init__(self, person: Person):
        self.person = person
        self.analyzer = ImprovedSimulationAnalyzer()

    def generate_detailed_report(self, daily_results: List[DailyResult]) -> str:
        summary = self.analyzer.generate_summary(daily_results)
        analysis = self.analyzer.analyze_simulation(
            daily_results,
            self.person,
            SimulationConfig(
                target_person_id=self.person.id,
                start_date=datetime.now(),
                days=len(daily_results),
            ),
        )
        spending = analysis.get("spending_analysis", {})
        insights = analysis.get("insights", [])

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
        if spending.get("by_category"):
            lines.append("\nТоп категории трат:")
            for category, amount in list(spending["by_category"].items())[:5]:
                percent = spending.get("category_distribution", {}).get(category, 0)
                lines.append(f"- {category}: {amount:.0f} RUB ({percent:.1f}%)")

        if insights:
            lines.append("\nИнсайты и рекомендации:")
            for ins in insights:
                lines.append(f"- {ins}")

        if summary.get("key_insights"):
            lines.append("\nКлючевые инсайты:")
            for ins in summary["key_insights"]:
                lines.append(f"- {ins}")
        return "\n".join(lines)
