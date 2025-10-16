"""AI subpackage for core.

Includes:
- summary: AI hero card content
- budget: AI budget target suggestions
"""

from . import summary  # re-export for convenience
from .budget import BudgetSuggestion, DEFAULT_MODEL as BUDGET_MODEL, generate_budget_suggestions

__all__ = [
	"summary",
	"BudgetSuggestion",
	"BUDGET_MODEL",
	"generate_budget_suggestions",
]
