"""Unit tests for the ADRChecker class.

These tests use a mock LLM to avoid making actual API calls.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from adrchecker.schemas import (
    ADRAssessmentReport,
    ADRConsistencyResult,
    ADRConsistencySections,
    ADRTemplate,
    ADRAlternative,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_ADR = """# Use PostgreSQL for Data Persistence

Date: 2024-01-15

## Status
Accepted

## Context
We need a reliable relational database to store user data, orders, and
inventory for our e-commerce platform. The system must handle concurrent
transactions and provide ACID guarantees.

## Decision Drivers
- Data consistency and integrity
- Mature ecosystem and tooling
- Team familiarity with SQL

## Considered Options
1. PostgreSQL
2. MongoDB
3. SQLite

## Decision
We will use PostgreSQL as our primary data store.

## Consequences
PostgreSQL requires operational overhead for backups and replication,
but provides robust data integrity and excellent performance for our use case.
"""

SAMPLE_ADHERENCE_RESULT = ADRTemplate(
    title="Use PostgreSQL for Data Persistence",
    status="Accepted",
    context="We need a reliable relational database...",
    decision_drivers="Data consistency, ecosystem, team familiarity",
    decision="We will use PostgreSQL as our primary data store.",
    consequences="Requires operational overhead but provides robust data integrity.",
    alternatives=[
        ADRAlternative(description="MongoDB", pros=["Flexible schema"], cons=["No ACID"]),
    ],
    date="2024-01-15",
    adherence_score=0.85,
    assessment="The ADR follows the MADR template closely.",
)

SAMPLE_SECTION_RESULT = ADRConsistencyResult(
    section_name="Context",
    presence="Yes",
    content_quality="Yes",
    purpose_consistency="Yes",
    justification="The context section clearly describes the problem.",
    alternate_title=[],
)


@pytest.fixture
def checker():
    """Create an ADRChecker with mocked chains (no real LLM calls)."""
    from adrchecker.checker import ADRChecker

    mock_llm = MagicMock()
    mock_llm.max_tokens = None
    chk = ADRChecker(llm=mock_llm)

    # Replace the real chains with mocks that return predictable results
    chk.global_consistency_chain = MagicMock()
    chk.global_consistency_chain.invoke.return_value = SAMPLE_ADHERENCE_RESULT

    chk.section_wise_consistency_chain = MagicMock()
    chk.section_wise_consistency_chain.invoke.return_value = SAMPLE_SECTION_RESULT

    return chk


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestSchemas:
    """Tests for Pydantic schema models."""

    def test_adr_alternative_creation(self):
        alt = ADRAlternative(
            description="MongoDB",
            pros=["Flexible schema"],
            cons=["No ACID guarantees"],
        )
        assert alt.description == "MongoDB"
        assert len(alt.pros) == 1
        assert len(alt.cons) == 1

    def test_adr_template_creation(self):
        template = SAMPLE_ADHERENCE_RESULT
        assert template.title == "Use PostgreSQL for Data Persistence"
        assert template.adherence_score == 0.85
        assert len(template.alternatives) == 1

    def test_adr_template_serialization(self):
        json_str = SAMPLE_ADHERENCE_RESULT.model_dump_json()
        data = json.loads(json_str)
        assert "title" in data
        assert "adherence_score" in data
        assert "alternatives" in data

    def test_adr_consistency_result_creation(self):
        result = SAMPLE_SECTION_RESULT
        assert result.section_name == "Context"
        assert result.presence == "Yes"
        assert result.content_quality == "Yes"
        assert result.purpose_consistency == "Yes"

    def test_adr_assessment_report_creation(self):
        report = ADRAssessmentReport(
            section_assessments=[SAMPLE_SECTION_RESULT],
            template_adherence=SAMPLE_ADHERENCE_RESULT,
        )
        assert len(report.section_assessments) == 1
        assert report.template_adherence.adherence_score == 0.85


# ---------------------------------------------------------------------------
# Checker tests
# ---------------------------------------------------------------------------

class TestADRChecker:
    """Tests for the ADRChecker class."""

    def test_checker_initialization(self, checker):
        """Test that the checker initializes correctly."""
        assert checker.llm is not None
        assert checker.global_consistency_chain is not None
        assert checker.section_wise_consistency_chain is not None

    def test_num_tokens(self):
        """Test token counting."""
        from adrchecker.checker import ADRChecker

        tokens = ADRChecker._num_tokens_from_adr("Hello world")
        assert tokens > 0

    def test_check_madr_adherence(self, checker):
        """Test MADR adherence check."""
        result = checker.check_madr_adherence(SAMPLE_ADR)

        assert result is not None
        assert isinstance(result, dict)
        assert "adherence_score" in result
        assert result["adherence_score"] == 0.85

    def test_check_madr_adherence_with_metadata(self, checker):
        """Test that metadata is included when provided."""
        metadata = {"project": "test-project"}
        result = checker.check_madr_adherence(SAMPLE_ADR, metadata=metadata)

        assert result is not None
        assert result["metadata"] == metadata

    def test_check_madr_adherence_pydantic(self, checker):
        """Test that Pydantic model is returned when as_dict=False."""
        result = checker.check_madr_adherence(SAMPLE_ADR, as_dict=False)

        assert result is not None
        assert isinstance(result, ADRTemplate)

    def test_check_sections(self, checker):
        """Test section-wise consistency check."""
        result = checker.check_sections(SAMPLE_ADR)

        assert result is not None
        assert isinstance(result, dict)
        assert "section_assessments" in result
        assert len(result["section_assessments"]) > 0

    def test_check_sections_pydantic(self, checker):
        """Test that Pydantic model is returned when as_dict=False."""
        result = checker.check_sections(SAMPLE_ADR, as_dict=False)

        assert result is not None
        assert isinstance(result, ADRConsistencySections)

    def test_check_full(self, checker):
        """Test full check (adherence + sections)."""
        result = checker.check(SAMPLE_ADR)

        assert result is not None
        assert isinstance(result, dict)
        assert "section_assessments" in result
        assert "template_adherence" in result
        assert result["template_adherence"]["adherence_score"] == 0.85

    def test_check_full_pydantic(self, checker):
        """Test that Pydantic model is returned for full check when as_dict=False."""
        result = checker.check(SAMPLE_ADR, as_dict=False)

        assert result is not None
        assert isinstance(result, ADRAssessmentReport)

    def test_check_batch(self, checker):
        """Test batch checking."""
        adr_texts = {
            "adr-001.md": SAMPLE_ADR,
            "adr-002.md": "# Another ADR\n\nSome content.",
        }

        results = checker.check_batch(adr_texts)

        assert len(results) == 2
        for result in results:
            assert "section_assessments" in result
            assert "template_adherence" in result

    def test_check_batch_with_metadata(self, checker):
        """Test batch checking with organization/project metadata."""
        adr_texts = {"adr-001.md": SAMPLE_ADR}

        results = checker.check_batch(
            adr_texts,
            organization="my-org",
            project="my-project",
        )

        assert len(results) == 1
        assert results[0]["metadata"]["organization"] == "my-org"
        assert results[0]["metadata"]["project"] == "my-project"
        assert results[0]["metadata"]["adr_key"] == "adr-001.md"

    def test_save_results(self, tmp_path):
        """Test saving results to JSON."""
        from adrchecker.checker import ADRChecker

        results = [{"test": "data"}]
        json_file = str(tmp_path / "results.json")

        ADRChecker.save_results(results, json_file)

        with open(json_file, "r") as f:
            saved = json.load(f)
        assert saved == results

    def test_check_batch_parallel(self, checker):
        """Test parallel batch processing."""
        adr_texts = {
            "adr-001.md": SAMPLE_ADR,
            "adr-002.md": "# Another ADR\n\nSome content.",
        }

        results = checker.check_batch(adr_texts, parallel=True)
        assert len(results) == 2