from typing import List, Dict, Any
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from models import Person
from .transaction_models import DailyResult
from .advanced_analyzer import AdvancedSimulationAnalyzer


class EnhancedReportGenerator:
    """Generate human friendly reports using advanced analytics."""

    def __init__(self, person: Person):
        self.person = person
        self.analyzer = AdvancedSimulationAnalyzer()

    def generate_detailed_report(self, daily_results: List[DailyResult]) -> str:
        analysis = self.analyzer.generate_comprehensive_report(daily_results, self.person, None)
        stats = analysis.get('basic_statistics', {})
        lines = [
            f"Отчет по {self.person.name}",
            f"Период: {stats.get('period','')}",
            f"Дней: {stats.get('days_analyzed',0)}",
            f"Всего потрачено: {stats.get('total_spent',0):.0f} RUB",
            f"Средние траты: {stats.get('average_daily_spent',0):.0f} RUB/день",
            '',
            analysis.get('executive_summary','')
        ]
        return "\n".join(lines)

    def generate_executive_summary(self, daily_results: List[DailyResult]) -> str:
        analysis = self.analyzer.generate_comprehensive_report(daily_results, self.person, None)
        return analysis.get('executive_summary', '')
