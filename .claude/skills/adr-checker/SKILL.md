---
name: adr-checker
description: |
  Check the quality of Architectural Decision Records (ADRs) against the MADR template
  using the adrchecker CLI. Use this skill whenever the user asks to check, validate,
  review, assess, or improve ADRs, decision records, or architectural decisions — even
  if they don't explicitly mention "MADR" or "adrchecker." Also trigger when the user
  wants to evaluate ADR structure, completeness, or template adherence, or when they
  ask "is this a good ADR?" or "what's wrong with my decision record?" or "help me fix
  this ADR."
---

# ADR Checker Skill

## What This Skill Does

This skill evaluates the quality of Architectural Decision Records (ADRs) using the
`adrchecker` CLI, which performs LLM-powered analysis against the MADR (Markdown Any
Decision Record) template. It produces:

- **Template adherence score** (0.0–1.0): how closely the ADR follows the expected structure.
- **Section-wise assessment**: for each of five key MADR sections, whether it is present,
  well-written, and serving its intended purpose.

## Prerequisites

### Checking Installation

Verify the tool is available:

```bash
python -m adrchecker version
```

If not installed, install from the project root:

```bash
pip install -e . --config-settings pyproject.toml=pyproject.adrchecker.toml
```

### API Key

The checker uses OpenAI GPT models. It will automatically look for the API key in
this order:

1. `ADRCHECKER_OPENAI_API_KEY` environment variable
2. `OPENAI_API_KEY` environment variable
3. Any of the above in a `.env` file (loaded via `python-dotenv`)

If no key is found, the checker will fail with an OpenAI authentication error.
Inform the user they need to set one of these variables.

Other settings (all prefixed with `ADRCHECKER_`):
- `ADRCHECKER_MODEL` (default: `gpt-4o-mini`)
- `ADRCHECKER_TEMPERATURE` (default: `0.0`)
- `ADRCHECKER_MAX_TOKENS` (default: `4096`)

## How to Check ADRs

Always use `--json` to capture detailed results — the terminal table is a summary,
but the JSON contains per-section justifications needed for actionable feedback.

### Commands

```bash
# Single file — full check with JSON output
python -m adrchecker check path/to/adr.md --json /tmp/adr-results.json

# Directory of ADRs — full check, parallel, with JSON
python -m adrchecker check path/to/adrs/ --parallel --json /tmp/adr-results.json

# Quick adherence-only check (faster, no section detail)
python -m adrchecker check path/to/adr.md --mode adherence --json /tmp/adr-results.json
```

### Modes

| Mode | Flag | When to use |
|------|------|-------------|
| `full` (default) | `--mode full` | Complete assessment — adherence + section detail |
| `adherence` | `--mode adherence` | Quick structural score only |
| `sections` | `--mode sections` | Detailed section-by-section feedback without overall score |

## Reading JSON Results

After running the checker with `--json`, read the output file. The structure is:

### Full mode (default)

Each entry in the JSON array has:

```json
{
  "section_assessments": [
    {
      "section_name": "Context",
      "presence": "Yes",
      "content_quality": "Yes",
      "purpose_consistency": "Yes",
      "justification": "Detailed explanation of issues...",
      "alternate_title": []
    }
    // ...one entry per section: Context, Decision, Consequences, Decision Drivers, Considered Options
  ],
  "template_adherence": {
    "title": "Extracted title",
    "status": "Accepted",
    "context": "Extracted context text",
    "decision": "Extracted decision text",
    "consequences": "Extracted consequences text",
    "decision_drivers": "Extracted drivers or empty",
    "alternatives": [],
    "date": "2024-01-15",
    "adherence_score": 0.85,
    "assessment": "Bullet-by-bullet analysis of each section..."
  },
  "metadata": { "file": "path/to/adr.md", "name": "adr.md" }
}
```

The fields that matter most for advising the user:

- `template_adherence.adherence_score` — the overall quality score (0.0–1.0)
- `template_adherence.assessment` — bullet-point analysis of what's present/missing
- `section_assessments[].justification` — specific reasoning for each section's evaluation
- `section_assessments[].presence` — "Yes" or "No" for each of the 5 sections

## The Five MADR Sections

For detailed guidance on each section (what good and bad content looks like),
read `references/madr-template-guide.md`.

| Section | Purpose | Common issues |
|---------|---------|---------------|
| **Context** | Background, problem, motivation | Contains decision rationale instead of background |
| **Decision** | The final choice, clearly stated | Vague, or buried without a clear heading |
| **Consequences** | Positive and negative impacts | Only lists positives, or is empty |
| **Decision Drivers** | Criteria that shaped the choice | Often entirely missing |
| **Considered Options** | Alternatives with pros/cons | Often entirely missing, or lists no pros/cons |

## Advising the User

After reading the JSON results, present findings in this structure:

### 1. Overall Summary

State the adherence score and a one-line assessment:
- **0.8–1.0**: Well-structured. Minor tweaks at most.
- **0.6–0.8**: Decent but has gaps. Specific sections need work.
- **0.4–0.6**: Significant issues. Multiple sections missing or weak.
- **Below 0.4**: Needs substantial revision to meet MADR standards.

### 2. Section-by-Section Issues

For each section that failed (presence=No, content_quality=No, or purpose_consistency=No/Partial),
explain the problem using the `justification` field and suggest a fix:

- "Decision Drivers is missing entirely — add a bulleted list of criteria that influenced
  the choice (e.g., performance, cost, team familiarity)."
- "Consequences only lists positives — add negative impacts like operational overhead
  or technical debt."
- "Context contains solution comparisons — move those to Considered Options."

### 3. Offer to Help

If sections need rewriting, offer to draft improved content following the MADR template.
Use the extracted text in `template_adherence` (context, decision, etc.) as a starting point.

### Batch Results

When checking multiple ADRs, identify patterns across the set:
- Which sections are most commonly missing across all ADRs?
- Are there any ADRs that score notably lower?
- Summarize as a quick table: filename, score, top issue.

## Workflow

1. Confirm `python -m adrchecker version` works and API key is set.
2. Run the checker with `--json` on the user's ADR file(s).
3. Read the JSON results file.
4. Summarize the adherence score and section results for the user.
5. For each failing section, cite the justification and suggest a concrete fix.
6. If asked, help rewrite weak sections using the MADR structure.