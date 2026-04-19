Section-wise MADR Consistency Check

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