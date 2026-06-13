"""ADR Checker - Standalone service for checking Architectural Decision Record (ADR) quality.

This package provides tools to assess ADR adherence to the MADR template and
evaluate section-wise consistency using LLM-based analysis.

Usage (programmatic):
    from adrchecker import ADRChecker
    checker = ADRChecker()
    result = checker.check(adr_text)

Usage (CLI):
    adrchecker check path/to/adrs/
"""

from adrchecker.checker import ADRChecker
from adrchecker.schemas import (
    ADRAlternative,
    ADRTemplate,
    ADRConsistencyResult,
    ADRConsistencySections,
    ADRAssessmentReport,
)

__version__ = "0.1.0"

__all__ = [
    "ADRChecker",
    "ADRAlternative",
    "ADRTemplate",
    "ADRConsistencyResult",
    "ADRConsistencySections",
    "ADRAssessmentReport",
    "__version__",
]