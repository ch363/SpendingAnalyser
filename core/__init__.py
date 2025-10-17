"""Core business logic package for the spending analyser app.

Expose stable submodules for external imports and tooling.
"""

# Explicitly import submodules so that names in __all__ are real attributes
# This avoids linter warnings and makes from core import <module> work reliably.
from . import data_loader as data_loader  # noqa: F401
from . import models as models  # noqa: F401
from . import summary_service as summary_service  # noqa: F401
from . import monthly_service as monthly_service  # noqa: F401
from . import ai as ai  # noqa: F401

__all__ = [
	"data_loader",
	"models",
	"summary_service",
	"monthly_service",
	"ai",
]
