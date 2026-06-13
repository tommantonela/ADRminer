#!/usr/bin/env python
"""Example: Using adrchecker programmatically to assess ADR quality.

This script demonstrates how to use the `adrchecker` Python API to:
1. Check a single ADR's MADR template adherence.
2. Check section-wise consistency.
3. Perform a full assessment (both combined).
4. Batch-check multiple ADRs.

Prerequisites:
    - Set the OPENAI_API_KEY environment variable (or via .env file).
    - Install adrchecker: pip install -e . --config-settings pyproject.toml=pyproject.adrchecker.toml

Usage:
    python examples/check_example.py
"""

import json
import sys
from pathlib import Path

# Ensure src/ is on the path when running from the repository root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from adrchecker import ADRChecker  # noqa: E402


def main():
    # --- Initialize the checker ---
    # Configuration is loaded from environment variables / .env file.
    # You can also pass model_name, temperature, max_tokens explicitly.
    print("=" * 70)
    print("ADR Checker — Programmatic Usage Example")
    print("=" * 70)

    checker = ADRChecker()

    # --- Load a sample ADR ---
    sample_adr_path = Path(__file__).parent / "sample_adr.md"
    adr_text = sample_adr_path.read_text(encoding="utf-8")
    print(f"\n📋 Loaded ADR: {sample_adr_path.name}")

    # --- 1. MADR Template Adherence ---
    print("\n" + "─" * 70)
    print("1. MADR Template Adherence Check")
    print("─" * 70)

    adherence = checker.check_madr_adherence(adr_text)
    print(f"   Title:           {adherence['title']}")
    print(f"   Status:          {adherence['status']}")
    print(f"   Date:            {adherence['date']}")
    print(f"   Adherence score: {adherence['adherence_score']:.2f}")
    print(f"   Assessment:      {adherence['assessment'][:200]}...")

    # --- 2. Section-wise Consistency ---
    print("\n" + "─" * 70)
    print("2. Section-wise Consistency Check")
    print("─" * 70)

    sections = checker.check_sections(adr_text)
    for assessment in sections["section_assessments"]:
        presence_icon = "✅" if assessment["presence"] == "Yes" else "❌"
        quality_icon = "✅" if assessment["content_quality"] == "Yes" else "❌"
        print(
            f"   {presence_icon} {quality_icon}  "
            f"{assessment['section_name']:20s} "
            f"(purpose: {assessment['purpose_consistency']})"
        )

    # --- 3. Full Assessment ---
    print("\n" + "─" * 70)
    print("3. Full Assessment (Adherence + Sections)")
    print("─" * 70)

    full_result = checker.check(adr_text)
    score = full_result["template_adherence"]["adherence_score"]
    num_sections = len(full_result["section_assessments"])
    present_sections = sum(
        1 for s in full_result["section_assessments"] if s["presence"] == "Yes"
    )
    print(f"   Overall adherence score: {score:.2f}")
    print(f"   Sections present:        {present_sections}/{num_sections}")

    # Save full result to JSON
    output_path = Path(__file__).parent / "sample_adr_result.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(full_result, f, indent=4)
    print(f"\n   💾 Full result saved to: {output_path}")

    # --- 4. Batch Processing ---
    print("\n" + "─" * 70)
    print("4. Batch Processing Example")
    print("─" * 70)

    adr_texts = {
        "sample_adr.md": adr_text,
        "minimal_adr.md": (
            "# Use Redis for Caching\n\n## Decision\nWe will use Redis.\n"
        ),
    }

    results = checker.check_batch(adr_texts, parallel=False)
    for result, key in zip(results, adr_texts.keys()):
        score = result.get("template_adherence", {}).get("adherence_score", 0.0)
        print(f"   📄 {key}: adherence score = {score:.2f}")

    print("\n" + "=" * 70)
    print("✅ Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()