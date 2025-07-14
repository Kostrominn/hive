"""
Transaction Simulator - симулятор повседневных трат с учетом социального контекста
"""

from .transaction_models import Transaction, DailyResult, SocialInteraction
from .life_simulator import LifeTransactionSimulator
from .report_generator import ReportGenerator, EnhancedReportGenerator

__version__ = "0.1.0"
__all__ = [
    "Transaction",
    "DailyResult", 
    "SocialInteraction",
    "LifeTransactionSimulator",
    "ReportGenerator",
    "EnhancedReportGenerator",
]
