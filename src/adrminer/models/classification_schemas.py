"""Pydantic models for structured classification output."""

from enum import Enum
from typing import List, Literal
from pydantic import BaseModel, Field


class ClassificationFramework(str, Enum):
    """Classification framework types."""
    KRUCHTEN = "kruchten"
    QUALITY_ATTRIBUTES = "quality_attributes"
    ZIMMERMANN = "zimmermann"


# Kruchten framework enums and models
class KruchtenEnum(str, Enum):
    """Kruchten classification categories."""
    EXISTENCE = "Existence (ontocrisis)"
    BAN = "Ban/Non-Existence (anticrisis)"
    PROPERTY = "Property (diacrisis)"
    EXECUTIVE = "Executive (pericrisis)"


class KruchtenClassificationResult(BaseModel):
    """Structured output for Kruchten classification."""
    framework: Literal[ClassificationFramework.KRUCHTEN] = Field(
        ClassificationFramework.KRUCHTEN,
        description="The classification framework used."
    )
    primary_category: KruchtenEnum = Field(
        ...,
        description="The closest or more appropriate category for ADR."
    )
    explanation: str = Field(
        ...,
        description="A brief rationale for choosing primary category."
    )
    primary_score: float = Field(
        ...,
        description="Confidence score for primary category (value between 0.0 and 1.0)."
    )
    alternative_categories: List[KruchtenEnum] = Field(
        ...,
        description="A list of alternative categories considered suitable for ADR, in addition to category chosen as primary. Do not include primary category here."
    )
    alternative_confidence_scores: List[float] = Field(
        ...,
        description="A list of confidence scores for each alternative category (values between 0.0 and 1.0). Sum of all scores (primary + alternatives) should equal 1.0. Length of list of scores must be equal to length of list of alternative categories."
    )


# Quality Attributes framework enums and models
class QualityAttributesEnum(str, Enum):
    """Quality Attributes classification categories."""
    PERFORMANCE = "Performance"
    RELIABILITY = "Reliability"
    SECURITY = "Security"
    MAINTAINABILITY = "Maintainability"
    SCALABILITY = "Scalability"
    USABILITY = "Usability"
    PORTABILITY = "Portability"
    COMPATIBILITY = "Compatibility"
    OBSERVABILITY = "Observability"
    TESTABILITY = "Testability"
    ONLY_FUNCTIONAL_CONCERN = "Other/Only Functional Concern"


class QualityAttributeClassificationResult(BaseModel):
    """Structured output for Quality Attributes classification."""
    framework: Literal[ClassificationFramework.QUALITY_ATTRIBUTES] = Field(
        ClassificationFramework.QUALITY_ATTRIBUTES,
        description="The classification framework used."
    )
    primary_category: QualityAttributesEnum = Field(
        ...,
        description="The closest or more appropriate category for ADR."
    )
    explanation: str = Field(
        ...,
        description="A brief rationale for choosing primary category."
    )
    primary_score: float = Field(
        ...,
        description="Confidence score for primary category (value between 0.0 and 1.0)."
    )
    alternative_categories: List[QualityAttributesEnum] = Field(
        ...,
        description="A list of alternative categories considered suitable for ADR, in addition to category chosen as primary. Do not include primary category here."
    )
    alternative_confidence_scores: List[float] = Field(
        ...,
        description="A list of confidence scores for each alternative category (values between 0.0 and 1.0). Sum of all scores (primary + alternatives) should equal 1.0. Length of list of scores must be equal to length of list of alternative categories."
    )


# Zimmermann framework enums and models
class ZimmermannEnum(str, Enum):
    """Zimmermann classification categories."""
    DESIGN_DECISION = "Design"
    TECHNOLOGY_DECISION = "Technology"
    INFRASTRUCTURE_DECISION = "Infrastructure"
    ORGANIZATIONAL_PROCESS_DECISION = "Organizational/Process"
    CONSTRAINT = "Constraint"
    QUALITY_ATTRIBUTE_DECISION = "Quality Attribute"
    CROSSCUTTING_CONCERNS_DECISION = "Crosscutting Concerns"
    IMPLEMENTATION = "Implementation"
    OTHER = "Other"


class ZimmermannClassificationResult(BaseModel):
    """Structured output for Zimmermann classification."""
    framework: Literal[ClassificationFramework.ZIMMERMANN] = Field(
        ClassificationFramework.ZIMMERMANN,
        description="The classification framework used."
    )
    primary_category: ZimmermannEnum = Field(
        ...,
        description="The closest or more appropriate category for ADR."
    )
    explanation: str = Field(
        ...,
        description="A brief rationale for choosing primary category."
    )
    primary_score: float = Field(
        ...,
        description="Confidence score for primary category (value between 0.0 and 1.0)."
    )
    alternative_categories: List[ZimmermannEnum] = Field(
        ...,
        description="A list of alternative categories considered suitable for ADR, in addition to category chosen as primary. Do not include primary category here."
    )
    alternative_confidence_scores: List[float] = Field(
        ...,
        description="A list of confidence scores for each alternative category (values between 0.0 and 1.0). Sum of all scores (primary + alternatives) should equal 1.0. Length of list of scores must be equal to length of list of alternative categories."
    )