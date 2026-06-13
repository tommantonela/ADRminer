"""Smoke tests for the adrchecker CLI.

Uses Typer's CliRunner with a mocked ADRChecker to test CLI behavior
without making actual LLM API calls.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from adrchecker.cli import app
from adrchecker.schemas import (
    ADRAlternative,
    ADRConsistencyResult,
    ADRConsistencySections,
    ADRTemplate,
)


runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_ADR_TEXT = """# Use PostgreSQL for Data Persistence

Date: 2024-01-15

## Status
Accepted

## Context
We need a reliable relational database.

## Decision
We will use PostgreSQL.
"""

SAMPLE_ADHERENCE = ADRTemplate(
    title="Use PostgreSQL for Data Persistence",
    status="Accepted",
    context="We need a reliable relational database.",
    decision_drivers="Consistency",
    decision="We will use PostgreSQL.",
    consequences="Operational overhead.",
    alternatives=[
        ADRAlternative(description="MongoDB", pros=["flexible"], cons=["no ACID"]),
    ],
    date="2024-01-15",
    adherence_score=0.90,
    assessment="Well-structured ADR.",
)

SAMPLE_SECTION = ADRConsistencyResult(
    section_name="Context",
    presence="Yes",
    content_quality="Yes",
    purpose_consistency="Yes",
    justification="Clear context.",
    alternate_title=[],
)

SAMPLE_SECTIONS_RESULT = ADRConsistencySections(section_assessments=[SAMPLE_SECTION])


@pytest.fixture
def mock_checker():
    """Create a mock ADRChecker instance."""
    checker = MagicMock()
    checker.check_madr_adherence_batch.return_value = [
        json.loads(SAMPLE_ADHERENCE.model_dump_json())
    ]
    checker.check_sections_batch.return_value = [
        json.loads(SAMPLE_SECTIONS_RESULT.model_dump_json())
    ]
    # For full check, combine both into ADRAssessmentReport format
    full_result = {
        "section_assessments": json.loads(SAMPLE_SECTIONS_RESULT.model_dump_json())[
            "section_assessments"
        ],
        "template_adherence": json.loads(SAMPLE_ADHERENCE.model_dump_json()),
    }
    checker.check_batch.return_value = [full_result]
    return checker


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCLI:
    """Tests for CLI commands."""

    def test_version(self):
        """Test the version command."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "adrchecker" in result.stdout

    def test_check_single_file(self, tmp_path, mock_checker):
        """Test checking a single ADR file."""
        adr_file = tmp_path / "adr-001.md"
        adr_file.write_text(SAMPLE_ADR_TEXT, encoding="utf-8")

        with patch("adrchecker.cli.ADRChecker", return_value=mock_checker):
            result = runner.invoke(app, ["check", str(adr_file)])

        assert result.exit_code == 0
        assert "Found 1 ADR file(s)" in result.stdout
        assert "Checking completed" in result.stdout

    def test_check_directory(self, tmp_path, mock_checker):
        """Test checking a directory of ADRs."""
        for i in range(3):
            (tmp_path / f"adr-{i:03d}.md").write_text(
                f"# ADR {i}\n\nSome content.", encoding="utf-8"
            )

        with patch("adrchecker.cli.ADRChecker", return_value=mock_checker):
            result = runner.invoke(app, ["check", str(tmp_path)])

        assert result.exit_code == 0
        assert "Found 3 ADR file(s)" in result.stdout

    def test_check_mode_adherence(self, tmp_path, mock_checker):
        """Test checking with adherence mode."""
        adr_file = tmp_path / "adr-001.md"
        adr_file.write_text(SAMPLE_ADR_TEXT, encoding="utf-8")

        with patch("adrchecker.cli.ADRChecker", return_value=mock_checker):
            result = runner.invoke(app, ["check", str(adr_file), "--mode", "adherence"])

        assert result.exit_code == 0
        assert "mode: adherence" in result.stdout
        mock_checker.check_madr_adherence_batch.assert_called_once()

    def test_check_mode_sections(self, tmp_path, mock_checker):
        """Test checking with sections mode."""
        adr_file = tmp_path / "adr-001.md"
        adr_file.write_text(SAMPLE_ADR_TEXT, encoding="utf-8")

        with patch("adrchecker.cli.ADRChecker", return_value=mock_checker):
            result = runner.invoke(app, ["check", str(adr_file), "--mode", "sections"])

        assert result.exit_code == 0
        mock_checker.check_sections_batch.assert_called_once()

    def test_check_json_output(self, tmp_path, mock_checker):
        """Test saving results to JSON."""
        adr_file = tmp_path / "adr-001.md"
        adr_file.write_text(SAMPLE_ADR_TEXT, encoding="utf-8")
        json_output = tmp_path / "results.json"

        with patch("adrchecker.cli.ADRChecker", return_value=mock_checker):
            result = runner.invoke(
                app, ["check", str(adr_file), "--json", str(json_output)]
            )

        assert result.exit_code == 0
        assert "Results saved" in result.stdout
        assert json_output.exists()

        with open(json_output, "r") as f:
            saved = json.load(f)
        assert len(saved) == 1

    def test_check_no_files_found(self, tmp_path, mock_checker):
        """Test that the CLI handles empty directories."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with patch("adrchecker.cli.ADRChecker", return_value=mock_checker):
            result = runner.invoke(app, ["check", str(empty_dir)])

        assert result.exit_code == 1
        assert "No ADR files found" in result.stdout