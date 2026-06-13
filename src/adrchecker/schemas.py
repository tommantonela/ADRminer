"""Pydantic schemas for ADR quality checking results.

These models define the structured output returned by the LLM when assessing
ADR adherence to the MADR template and section-wise consistency.
"""

from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class ADRAlternative(BaseModel):
    """Represents an alternative option considered in an ADR."""

    description: str = Field(
        ..., description="Description of the alternative option considered."
    )
    pros: List[str] = Field(
        ...,
        description="List of pros of the alternative. It should be a list of strings.",
    )
    cons: List[str] = Field(
        ...,
        description="List of cons of the alternative. It should be a list of strings.",
    )


class ADRTemplate(BaseModel):
    """ADR template assessment (MADR template).

    Represents the LLM's extraction and adherence evaluation of an ADR
    against the expected MADR template structure.
    """

    title: str = Field(
        ...,
        description=(
            "Actual title of the ADR. It should convey the essence of the "
            "problem solved and the solution chosen."
        ),
    )
    status: str = Field(
        ...,
        description=(
            "Status of the ADR. Options include: proposed, accepted, "
            "rejected, deprecated, superseded."
        ),
    )
    context: str = Field(
        ...,
        description=(
            "Context of the ADR. Describes the context and problem statement "
            "in a few sentences. It articulates the problem being addressed."
        ),
    )
    decision_drivers: str = Field(
        ...,
        description=(
            "Drivers of the ADR. It describes the forces that influence the "
            "decision, including desired qualities and concerns identified."
        ),
    )
    decision: str = Field(
        ...,
        description=(
            "Decision of the ADR. It is the chosen option (among the "
            "alternatives) and the rationale for the decision."
        ),
    )
    consequences: str = Field(
        ...,
        description=(
            "Consequences of the ADR. It describes the impact of the decision, "
            "including the positive and negative effects of making the decision."
        ),
    )
    alternatives: List[ADRAlternative] = Field(
        ...,
        description=(
            "Alternatives of the ADR. It should mention a list of alternatives "
            "investigated and their pros and cons."
        ),
    )
    date: str = Field(
        ...,
        description="Date in which the ADR was updated.",
    )
    adherence_score: float = Field(
        ...,
        description=(
            "Degree of adherence of the ADR to the MADR template. "
            "It should be 1.0 if the sections and their contents closely match "
            "the template, and 0.0 if most sections and contents are not followed."
        ),
    )
    assessment: str = Field(
        ...,
        description=(
            "Justification of the adherence score regarding the template. "
            "It should explain why the ADR is or is not following certain template "
            "sections, expliciting listing any omitted sections or contents."
        ),
    )


class ADRConsistencyResult(BaseModel):
    """Result of consistency check for a single ADR section."""

    section_name: str = Field(
        ..., description="Name of the ADR section being evaluated."
    )
    presence: Literal["Yes", "No"] = Field(
        ...,
        description="Indicates whether the section is present in the ADR.",
    )
    content_quality: Literal["Yes", "No"] = Field(
        ...,
        description=(
            "Indicates whether the content of the section is of good quality "
            "(clear, complete, relevant)."
        ),
    )
    purpose_consistency: Literal["Yes", "Partial", "No"] = Field(
        ...,
        description=(
            "Indicates whether the purpose of the section is consistent with the template."
        ),
    )
    justification: str = Field(
        ...,
        description="Explanation and rationale for the above evaluation of the section.",
    )
    alternate_title: List[str] = Field(
        default_factory=list,
        description=(
            "List of other section titles (from the ADR) that could better "
            "reflect the content of the section."
        ),
    )


class ADRConsistencySections(BaseModel):
    """Collection of section consistency results for a single ADR."""

    section_assessments: List[ADRConsistencyResult] = Field(
        ...,
        description="List of assessments for each section of the ADR.",
    )


class ADRAssessmentReport(BaseModel):
    """Full assessment report combining template adherence and section consistency."""

    section_assessments: List[ADRConsistencyResult] = Field(
        ...,
        description="List of assessments for each section of the ADR.",
    )
    template_adherence: ADRTemplate = Field(
        ...,
        description="Assessment of the adherence of the ADR to the MADR template.",
    )


# Type aliases for convenience
CheckResult = Dict
CheckBatchResult = List[Dict]