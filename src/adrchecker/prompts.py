"""Prompt templates for ADR quality checking.

These prompts are used to guide the LLM in assessing:
- Overall MADR template adherence of an ADR.
- Section-wise consistency (presence, quality, purpose) for each MADR section.
"""

from typing import Dict


# ----------------------------------------------------------------------------
# Full consistency / MADR template adherence prompt
# ----------------------------------------------------------------------------

FULL_CONSISTENCY_OVER_EXTRACTED_ADR = """
You are an expert software architect that knows about Architecture Decision Records (ADRs).
Your task is to check the ADR below and assess its adherence to the sections of the MADR template based on the following JSON format:

For each section, analyze:
- if the section is present in the ADR under the right title/subtitle, and
- if the section contents are present somewhere in the ADR text.

Note:
- A section can have its content present but lack a proper heading (e.g., 'Decision' content is present but not under a clear heading).
- If such misalignments exist (title vs. content location), describe them in your assessment.

Your adherence score, between 0.0 (lack of alignment) and 1.0 (almost perfect alignment), should be calculated based on the presence and degree of alignment of each section.
Please make your assessment of each section before giving the adherence score.

For the assessment, use a string list of bullets to enumerate your individual analysis of each template section.

ADR text: "{input_text}"
"""


# ----------------------------------------------------------------------------
# Section-wise consistency prompt
# ----------------------------------------------------------------------------

CONSISTENCY_PROMPT_BY_SECTION = """
Your purpose is to analyze the MADR section "{section_name}".
Assume the following expected purpose of the "{section_name}" section:
{section_purpose}

## Instructions
For the MADR section "{section_name}", return the following information:
* Presence: Only answer "Yes" if the ADR includes a heading that exactly matches the expected section title (e.g., "{section_name}"). Otherwise, answer "No".
* Alternate Title: If the content clearly fulfilling the intended purpose of this section appears under a different heading, return that heading or those headings exactly as written in the ADR, as a list.
    * If multiple headings serve this role, list them all.
    * If no such alternate heading exists, return an empty list.
    * Example: If {section_name} appears under "Context", return ["Context"].
    * Example: If the content of {section_name} is scattered across "Decision" and "Context", use: ["Decision", "Context"]

* Content Quality: If the section (or its alternate) is present, does it include meaningful, project-specific content?
    * Return "Yes" if it contains actual decisions or reasoning, not just placeholders or vague statements.
    * Return "No" if the content is generic, minimal, empty, or only an example.

* Purpose Consistency: Does the content fulfill only the intended purpose of this section, without overlapping with the roles of other sections?
    * "Yes": Clear, well-scoped content.
    * "Partial": Some overlap with another section.
    * "No": Content mostly belongs elsewhere or completely fails to fulfill its purpose.

* Justification: A brief but precise explanation of your assessment. Point out:
    * If the section is missing or mislabeled
    * If content is vague, off-topic, or misplaced
    * Why the content does or doesn't fulfill the section's intended role

## Chain-of-Thought Checklist (Follow these reasoning steps)
1. Is a section with the expected title present? (Set presence)
2. If not, is the content fulfilling this role found under another heading? (Set alternate_title)
3. Is the content substantial and project-specific? (Set content_quality)
4. Is the content dedicated to this purpose and not another? (Set purpose_consistency)
5. Explain briefly why your assessments above (1 to 4) in your justification.

## Important guidelines:
* Use all available information: Base your assessment on what's actually in the ADR.
* Assume minimal context: Do not infer intentions; rely only on text.
* Favor clarity over assumption: Label vague or misplaced sections accordingly.
* Be conservative in evaluation: If the section lacks substance or structure, mark it as "No" or "Partial".
* Consistency matters: Penalize sections that duplicate or overlap with others.
* Treat examples cautiously: Placeholder/sample content should be marked as misuse unless replaced with real content.
* Strict Scope Rule: Even if content is well-written, if it appears under the wrong heading (e.g., "Context" instead of "Considered Options" or "Context" instead of "Decision Drivers"), you must:
    * Set presence = "No"
    * Include the heading under alternate_title
    * Set purpose_consistency = "Partial" or "No"

## ADR Input
{adr_input}
"""


# ----------------------------------------------------------------------------
# Section metadata (expected purpose of each MADR section)
# ----------------------------------------------------------------------------

def get_adr_sections_metadata() -> Dict[str, str]:
    """Return the expected purpose for each MADR section.

    Returns:
        Dictionary mapping section names to their expected purpose descriptions.
    """
    sections: Dict[str, str] = {}
    sections["Context"] = (
        'Describes the background, system state, problem, or motivation. '
        'It must not include detailed comparisons between solutions, rationales, '
        'or final decisions—those belong in "Considered Options" or "Decision". '
        "If present, mark purpose_consistency = No. "
        "Includes: technical constraints, stakeholder needs, project circumstances, or related issues."
    )
    sections["Decision"] = (
        "Clearly and explicitly states the final choice that was made in response to the context. "
        "This is the core of the ADR and should be unambiguous. "
        "Includes: selected approach, accepted alternative, or implemented design."
    )
    sections["Consequences"] = (
        "Explains the results, implications, trade-offs, and expected impact of the decision"
        "—both positive and negative. Should address what follows from the decision in terms "
        "of system behavior, future maintenance, or risks. "
        "Includes: technical debt, performance effects, maintainability implications, limitations."
    )
    sections["Decision Drivers"] = (
        "Lists the main criteria, goals, or forces that shaped the decision-making process. "
        "Should clarify what mattered most when choosing between options. "
        "Includes: performance, cost, simplicity, compatibility, regulatory compliance."
    )
    sections["Considered Options"] = (
        "Enumerates alternative approaches or solutions that were evaluated and explains why "
        "they were not chosen. Should demonstrate that the decision was made after a comparison "
        "of viable options. "
        "Includes: at least two alternatives, with brief pros and cons or rejection justifications."
    )

    return sections