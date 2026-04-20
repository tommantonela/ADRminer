"""Pydantic models for structured insight output."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ContentSummary(BaseModel):
    """Structured output for ADR content summary."""
    summary: str = Field(
        ...,
        description="A 1-2 paragraph summary of the ADR content. Focus on: what decision was made, why it was made (key drivers), and main consequences or trade-offs."
    )


class ClassificationAlignment(BaseModel):
    """Analysis of classification alignment across frameworks."""
    alignment_level: str = Field(
        ...,
        description="One of: 'High', 'Medium', or 'Low' - indicating how well the three frameworks agree"
    )
    analysis: str = Field(
        ...,
        description="Detailed analysis of whether Kruchten, Zimmermann, and Quality Attributes classifications agree, and what this indicates about the decision"
    )
    is_consistent: bool = Field(
        ...,
        description="True if classifications are logically consistent with each other"
    )


class QualityAssessment(BaseModel):
    """Assessment of ADR quality based on metadata."""
    overall_quality: str = Field(
        ...,
        description="One of: 'Excellent', 'Good', 'Fair', or 'Poor' - based on adherence score and completeness"
    )
    interpretation: str = Field(
        ...,
        description="Interpretation of the adherence score and missing sections"
    )
    missing_sections: List[str] = Field(
        default_factory=list,
        description="List of sections that are missing or incomplete"
    )
    improvement_suggestions: List[str] = Field(
        ...,
        description="Specific recommendations for improving the ADR's quality and completeness"
    )


class ConfidenceAssessment(BaseModel):
    """Assessment of classification confidence."""
    overall_confidence: str = Field(
        ...,
        description="One of: 'High', 'Medium', or 'Low' - based on average confidence scores"
    )
    interpretation: str = Field(
        ...,
        description="What the confidence scores indicate about the clarity and structure of the ADR"
    )
    areas_of_uncertainty: List[str] = Field(
        default_factory=list,
        description="Any specific aspects where the LLM was uncertain (if applicable)"
    )


class TopicContentMatch(BaseModel):
    """Analysis of topic alignment with classifications and content."""
    alignment_level: str = Field(
        ...,
        description="One of: 'Strong', 'Moderate', or 'Weak' - how well the topic aligns with classifications"
    )
    analysis: str = Field(
        ...,
        description="Analysis of whether the topic label aligns with classifications and decision content"
    )
    is_consistent: bool = Field(
        ...,
        description="True if topic is consistent with the ADR's content and classifications"
    )


class ActionableRecommendation(BaseModel):
    """A specific, actionable recommendation for improving the ADR."""
    priority: str = Field(
        ...,
        description="One of: 'High', 'Medium', or 'Low' - priority of the recommendation"
    )
    category: str = Field(
        ...,
        description="Category of recommendation, e.g., 'Documentation', 'Structure', 'Content', 'Clarity'"
    )
    recommendation: str = Field(
        ...,
        description="Specific, actionable recommendation for improving this ADR"
    )


class ADRInsights(BaseModel):
    """Complete insights analysis for a single ADR."""
    classification_alignment: ClassificationAlignment = Field(
        ...,
        description="Analysis of classification alignment across frameworks"
    )
    quality_assessment: QualityAssessment = Field(
        ...,
        description="Assessment of ADR quality based on metadata"
    )
    confidence_assessment: ConfidenceAssessment = Field(
        ...,
        description="Assessment of classification confidence"
    )
    topic_content_match: TopicContentMatch = Field(
        ...,
        description="Analysis of topic alignment with classifications and content"
    )
    recommendations: List[ActionableRecommendation] = Field(
        ...,
        description="3-5 specific, actionable recommendations for improving this ADR"
    )
    overall_summary: str = Field(
        ...,
        description="A brief 2-3 sentence overall summary of the ADR's strengths and areas for improvement"
    )


class ClassificationPattern(BaseModel):
    """Pattern identified in classifications."""
    category: str = Field(
        ...,
        description="The category name"
    )
    framework: str = Field(
        ...,
        description="The framework name (Kruchten, Zimmermann, or Quality Attributes)"
    )
    count: int = Field(
        ...,
        description="Number of ADRs with this classification"
    )
    percentage: float = Field(
        ...,
        description="Percentage of ADRs with this classification"
    )
    adr_references: List[str] = Field(
        default_factory=list,
        description="List of ADR titles or filenames that have this classification (top 5 most relevant)"
    )


class QualityTrend(BaseModel):
    """Quality trend analysis."""
    average_adherence_score: float = Field(
        ...,
        description="Average quality adherence score across all ADRs"
    )
    quality_distribution: str = Field(
        ...,
        description="Description of quality distribution, e.g., 'Most ADRs are high quality'"
    )
    common_missing_sections: List[str] = Field(
        ...,
        description="Most commonly missing sections across all ADRs, ordered by frequency"
    )


class ArchitecturalTheme(BaseModel):
    """An architectural theme identified from topics."""
    theme: str = Field(
        ...,
        description="The architectural theme name"
    )
    adr_count: int = Field(
        ...,
        description="Number of ADRs related to this theme"
    )
    description: str = Field(
        ...,
        description="Brief description of what this theme represents"
    )


class RiskAssessment(BaseModel):
    """Risk assessment for ADRs."""
    high_risk_adrs: List[str] = Field(
        default_factory=list,
        description="List of ADRs with low confidence (< 0.7) or poor quality (adherence < 0.6)"
    )
    medium_risk_adrs: List[str] = Field(
        default_factory=list,
        description="List of ADRs with medium confidence (0.7-0.8) or medium quality (adherence 0.6-0.8)"
    )
    risk_summary: str = Field(
        ...,
        description="Summary of overall project risk level and key concerns"
    )


class ConsistencyAnalysis(BaseModel):
    """Analysis of classification consistency across the project."""
    overall_consistency: str = Field(
        ...,
        description="One of: 'High', 'Medium', or 'Low' - how consistent classifications are across the project"
    )
    inconsistencies: List[str] = Field(
        default_factory=list,
        description="Any notable inconsistencies or outliers in classifications"
    )
    analysis: str = Field(
        ...,
        description="Detailed analysis of classification patterns and consistency"
    )


class ProjectRecommendation(BaseModel):
    """A project-level recommendation."""
    priority: str = Field(
        ...,
        description="One of: 'High', 'Medium', or 'Low' - priority of the recommendation"
    )
    area: str = Field(
        ...,
        description="Area of recommendation, e.g., 'Documentation Standards', 'Quality Assurance', 'Classification Consistency'"
    )
    recommendation: str = Field(
        ...,
        description="Specific, actionable recommendation for improving the project's ADRs"
    )


class ProjectInsights(BaseModel):
    """Complete project-wide insights analysis."""
    total_adrs: int = Field(
        ...,
        description="Total number of ADRs analyzed"
    )
    classification_patterns: List[ClassificationPattern] = Field(
        ...,
        description="Patterns in classifications across frameworks"
    )
    quality_trends: QualityTrend = Field(
        ...,
        description="Quality trends and common issues"
    )
    architectural_themes: List[ArchitecturalTheme] = Field(
        ...,
        description="Main architectural themes identified from topics"
    )
    risk_assessment: RiskAssessment = Field(
        ...,
        description="Risk assessment for ADRs with low confidence or poor quality"
    )
    consistency_analysis: ConsistencyAnalysis = Field(
        ...,
        description="Analysis of classification consistency across the project"
    )
    recommendations: List[ProjectRecommendation] = Field(
        ...,
        description="3-5 project-level recommendations for improving ADR quality and consistency"
    )
    overall_summary: str = Field(
        ...,
        description="A brief 2-3 sentence summary of the project's ADR health and key focus areas"
    )