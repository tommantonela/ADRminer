"""ADR quality checking service using LLM models."""

import concurrent.futures
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional

from adrminer.config import Settings
from adrminer.models import get_llm

from pydantic import BaseModel, Field


# Pydantic models for checking results
class ADRAlternative(BaseModel):
    """Represents an alternative option considered in an ADR."""
    
    description: str = Field(description="Description of the alternative")
    pros: List[str] = Field(default_factory=list, description="Pros of this alternative")
    cons: List[str] = Field(default_factory=list, description="Cons of this alternative")


class ADRTemplate(BaseModel):
    """
    ADR template assessment (MADR, Zimmermann, etc.)
    """
    
    title: str = Field(default="", description="Extracted title of the ADR")
    status: str = Field(default="", description="Extracted status of the ADR")
    context: str = Field(default="", description="Extracted context section")
    decision_drivers: str = Field(default="", description="Extracted decision drivers section")
    decision: str = Field(default="", description="Extracted decision section")
    consequences: str = Field(default="", description="Extracted consequences section")
    alternatives: List[ADRAlternative] = Field(
        default_factory=list,
        description="List of alternative options considered"
    )
    date: str = Field(default="", description="Extracted date of the ADR")
    adherence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Adherence score between 0.0 and 1.0"
    )
    assessment: str = Field(
        default="",
        description="Detailed assessment as a list of bullets"
    )


class ADRConsistencyResult(BaseModel):
    """Result of consistency check for a single section."""
    
    section_name: str = Field(description="Name of the MADR section being checked")
    presence: Literal["Yes", "No"] = Field(
        description="Whether the section is present with exact heading"
    )
    content_quality: Literal["Yes", "No"] = Field(
        description="Whether the section has meaningful, project-specific content"
    )
    purpose_consistency: Literal["Yes", "Partial", "No"] = Field(
        description="Whether content fulfills the intended purpose without overlap"
    )
    justification: str = Field(
        description="Brief explanation of the assessment"
    )
    alternate_title: List[str] = Field(
        default_factory=list,
        description="Alternate headings where this content appears"
    )


class ADRConsistencySections:
    """Collection of section consistency results."""
    
    def __init__(self, section_assessments: List[ADRConsistencyResult]):
        self.section_assessments = section_assessments
    
    def model_dump(self) -> Dict:
        """Convert to dictionary."""
        return {
            "section_assessments": [
                section.model_dump() for section in self.section_assessments
            ]
        }


class ADRAssessmentReport:
    """Full assessment report combining template adherence and section consistency."""
    
    def __init__(
        self,
        section_assessments: List[ADRConsistencyResult],
        template_adherence: ADRTemplate,
    ):
        self.section_assessments = section_assessments
        self.template_adherence = template_adherence
    
    def model_dump(self) -> Dict:
        """Convert to dictionary."""
        return {
            "section_assessments": [
                section.model_dump() for section in self.section_assessments
            ],
            "template_adherence": self.template_adherence.model_dump(),
        }


# Prompts for checking
FULL_CONSISTENCY_PROMPT = """
You are an expert software architect who knows about Architecture Decision Records (ADRs).
Your task is to check the ADR below and assess its adherence to the sections of the MADR template.

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

SECTION_CONSISTENCY_PROMPT = """
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


# MADR section definitions
MADR_SECTIONS = {
    'Context': 'Describes the background, system state, problem, or motivation. It must not include detailed comparisons between solutions, rationales, or final decisions—those belong in "Considered Options" or "Decision". Includes: technical constraints, stakeholder needs, project circumstances, or related issues.',
    'Decision': 'Clearly and explicitly states the final choice that was made in response to the context. This is the core of the ADR and should be unambiguous. Includes: selected approach, accepted alternative, or implemented design.',
    'Consequences': 'Explains the results, implications, trade-offs, and expected impact of the decision—both positive and negative. Should address what follows from the decision in terms of system behavior, future maintenance, or risks. Includes: technical debt, performance effects, maintainability implications, limitations.',
    'Decision Drivers': 'Lists the main criteria, goals, or forces that shaped the decision-making process. Should clarify what mattered most when choosing between options. Includes: performance, cost, simplicity, compatibility, regulatory compliance.',
    'Considered Options': 'Enumerates alternative approaches or solutions that were evaluated and explains why they were not chosen. Should demonstrate that the decision was made after a comparison of viable options. Includes: at least two alternatives, with brief pros and cons or rejection justifications.',
}


class CheckingService:
    """Service for checking ADR quality using LLM models."""
    
    def __init__(
        self,
        mode: Literal["adherence", "sections", "full"] = "full",
        settings: Optional[Settings] = None,
    ):
        """
        Initialize checking service.
        
        Args:
            mode: Checking mode (adherence|sections|full)
            settings: Settings instance
        """
        if settings is None:
            from adrminer.config import get_settings
            settings = get_settings()
        
        self.settings = settings
        self.mode = mode or "full"
        
        # Get LLM (shared with other services)
        self.llm = get_llm(settings=settings)
        
        # Configure prompts for adherence check
        self._configure_adherence_chain()
        
        # Configure prompts for section check
        self._configure_section_chain()
    
    def _configure_adherence_chain(self):
        """Configure chain for MADR template adherence check using structured output."""
        from langchain_core.prompts import PromptTemplate
        
        self.adherence_prompt = PromptTemplate(
            template=FULL_CONSISTENCY_PROMPT,
            input_variables=["input_text"],
        )
        
        # Create structured output chain
        self.adherence_chain = self.adherence_prompt | self.llm.with_structured_output(ADRTemplate)
    
    def _configure_section_chain(self):
        """Configure chain for section-wise consistency check using structured output."""
        from langchain_core.prompts import PromptTemplate
        
        self.section_prompt = PromptTemplate(
            template=SECTION_CONSISTENCY_PROMPT,
            input_variables=["adr_input", "section_name", "section_purpose"],
        )
        
        # Create structured output chain
        self.section_chain = self.section_prompt | self.llm.with_structured_output(ADRConsistencyResult)
    
    @staticmethod
    def _num_tokens_from_adr(string: str, encoding_name: str = "cl100k_base") -> int:
        """Returns the number of tokens in a text string."""
        import tiktoken
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    
    def _parse_adherence_response(self, response_text: str) -> ADRTemplate:
        """
        Parse LLM response for adherence check.
        
        Args:
            response_text: LLM response text
        
        Returns:
            ADRTemplate object
        """
        try:
            # Clean response text
            response_text = response_text.strip()
            
            # Extract JSON if present
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text
            
            # Try to find JSON-like structure
            if not json_str.startswith('{'):
                # Look for first { and last }
                start = json_str.find('{')
                end = json_str.rfind('}')
                if start >= 0 and end > start:
                    json_str = json_str[start:end+1]
            
            json_str = json_str.strip()
            
            # Skip if empty
            if not json_str:
                raise ValueError("Empty JSON string")
            
            data = json.loads(json_str)
            
            # Parse alternatives
            alternatives = []
            if "alternatives" in data:
                for alt_data in data["alternatives"]:
                    alternatives.append(ADRAlternative(
                        description=alt_data.get("description", ""),
                        pros=alt_data.get("pros", []),
                        cons=alt_data.get("cons", []),
                    ))
            
            return ADRTemplate(
                title=data.get("title", ""),
                status=data.get("status", ""),
                context=data.get("context", ""),
                decision_drivers=data.get("decision_drivers", ""),
                decision=data.get("decision", ""),
                consequences=data.get("consequences", ""),
                alternatives=alternatives,
                date=data.get("date", ""),
                adherence_score=data.get("adherence_score", 0.0),
                assessment=data.get("assessment", ""),
            )
        except Exception as e:
            # Fallback: create minimal template
            return ADRTemplate(
                title="",
                status="",
                context="",
                decision_drivers="",
                decision="",
                consequences="",
                alternatives=[],
                date="",
                adherence_score=0.0,
                assessment=f"Failed to parse response: {e}",
            )
    
    def _parse_section_response(self, response_text: str) -> ADRConsistencyResult:
        """
        Parse LLM response for section consistency check.
        
        Args:
            response_text: LLM response text
        
        Returns:
            ADRConsistencyResult object
        """
        try:
            # Extract JSON if present
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            
            data = json.loads(json_str)
            
            return ADRConsistencyResult(
                section_name=data.get("section_name", ""),
                presence=data.get("presence", "No"),
                content_quality=data.get("content_quality", "No"),
                purpose_consistency=data.get("purpose_consistency", "No"),
                justification=data.get("justification", ""),
                alternate_title=data.get("alternate_title", []),
            )
        except Exception as e:
            # Fallback: create minimal result
            return ADRConsistencyResult(
                section_name="",
                presence="No",
                content_quality="No",
                purpose_consistency="No",
                justification=f"Failed to parse response: {e}",
                alternate_title=[],
            )
    
    def check_adherence(self, text: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Check MADR template adherence for a single ADR using structured output.
        
        Args:
            text: ADR text content
            metadata: Optional metadata about the ADR
        
        Returns:
            Dictionary with adherence check results
        """
        # Count tokens
        count_tokens = self._num_tokens_from_adr(text)
        
        # Use structured output chain
        try:
            result = self.adherence_chain.invoke({"input_text": text})
        except Exception as e:
            raise RuntimeError(f"LLM adherence check failed: {e}")
        
        return {
            "mode": "adherence",
            "tokens": count_tokens,
            "template_adherence": result.model_dump(),
            "metadata": metadata or {},
        }
    
    def check_sections(self, text: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Check section-wise consistency for a single ADR using structured output.
        
        Args:
            text: ADR text content
            metadata: Optional metadata about the ADR
        
        Returns:
            Dictionary with section check results
        """
        # Count tokens
        count_tokens = self._num_tokens_from_adr(text)
        
        # Check each section
        all_section_results = []
        for section_name, section_purpose in MADR_SECTIONS.items():
            # Use structured output chain
            try:
                section_result = self.section_chain.invoke({
                    "adr_input": text,
                    "section_name": section_name,
                    "section_purpose": section_purpose,
                })
                all_section_results.append(section_result)
            except Exception as e:
                # Create fallback result
                section_result = ADRConsistencyResult(
                    section_name=section_name,
                    presence="No",
                    content_quality="No",
                    purpose_consistency="No",
                    justification=f"LLM check failed: {e}",
                    alternate_title=[],
                )
                all_section_results.append(section_result)
        
        result = ADRConsistencySections(section_assessments=all_section_results)
        
        return {
            "mode": "sections",
            "tokens": count_tokens,
            "section_assessments": result.model_dump()["section_assessments"],
            "metadata": metadata or {},
        }
    
    def check(self, text: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Perform full assessment (adherence + sections) for a single ADR.
        
        Args:
            text: ADR text content
            metadata: Optional metadata about the ADR
        
        Returns:
            Dictionary with full assessment results
        """
        # Run both checks
        adherence_result = self.check_adherence(text, metadata)
        sections_result = self.check_sections(text, metadata)
        
        return {
            "mode": "full",
            "tokens": max(adherence_result["tokens"], sections_result["tokens"]),
            "section_assessments": sections_result["section_assessments"],
            "template_adherence": adherence_result["template_adherence"],
            "metadata": metadata or {},
        }
    
    def check_adherence_batch(
        self,
        texts: List[str],
        metadata_list: Optional[List[Dict]] = None,
        parallel: bool = True,
    ) -> List[Dict]:
        """
        Check MADR template adherence for multiple ADRs.
        
        Args:
            texts: List of ADR text contents
            metadata_list: Optional list of metadata for each ADR
            parallel: Enable parallel processing
        
        Returns:
            List of adherence check results
        """
        results = []
        
        if parallel and len(texts) > 1:
            # Use ThreadPoolExecutor for parallel processing
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Store (index, future) pairs to maintain order
                futures = []
                for i, text in enumerate(texts):
                    metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
                    future = executor.submit(self.check_adherence, text, metadata)
                    futures.append((i, future))
                
                # Wait for all futures to complete
                results = [None] * len(texts)
                for i, future in futures:
                    try:
                        results[i] = future.result()
                    except Exception as e:
                        print(f"Warning: Failed to check ADR: {e}")
                        results[i] = {"error": str(e)}
        else:
            # Sequential processing
            for i, text in enumerate(texts):
                metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
                result = self.check_adherence(text, metadata)
                results.append(result)
        
        return results
    
    def check_sections_batch(
        self,
        texts: List[str],
        metadata_list: Optional[List[Dict]] = None,
        parallel: bool = True,
    ) -> List[Dict]:
        """
        Check section-wise consistency for multiple ADRs.
        
        Args:
            texts: List of ADR text contents
            metadata_list: Optional list of metadata for each ADR
            parallel: Enable parallel processing
        
        Returns:
            List of section check results
        """
        results = []
        
        if parallel and len(texts) > 1:
            # Use ThreadPoolExecutor for parallel processing
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Store (index, future) pairs to maintain order
                futures = []
                for i, text in enumerate(texts):
                    metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
                    future = executor.submit(self.check_sections, text, metadata)
                    futures.append((i, future))
                
                # Wait for all futures to complete
                results = [None] * len(texts)
                for i, future in futures:
                    try:
                        results[i] = future.result()
                    except Exception as e:
                        print(f"Warning: Failed to check ADR: {e}")
                        results[i] = {"error": str(e)}
        else:
            # Sequential processing
            for i, text in enumerate(texts):
                metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
                result = self.check_sections(text, metadata)
                results.append(result)
        
        return results
    
    def check_batch(
        self,
        texts: List[str],
        metadata_list: Optional[List[Dict]] = None,
        parallel: bool = True,
    ) -> List[Dict]:
        """
        Perform full assessment for multiple ADRs.
        
        Args:
            texts: List of ADR text contents
            metadata_list: Optional list of metadata for each ADR
            parallel: Enable parallel processing
        
        Returns:
            List of full assessment results
        """
        results = []
        
        if parallel and len(texts) > 1:
            # Use ThreadPoolExecutor for parallel processing
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Store (index, future) pairs to maintain order
                futures = []
                for i, text in enumerate(texts):
                    metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
                    future = executor.submit(self.check, text, metadata)
                    futures.append((i, future))
                
                # Wait for all futures to complete
                results = [None] * len(texts)
                for i, future in futures:
                    try:
                        results[i] = future.result()
                    except Exception as e:
                        print(f"Warning: Failed to check ADR: {e}")
                        results[i] = {"error": str(e)}
        else:
            # Sequential processing
            for i, text in enumerate(texts):
                metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
                result = self.check(text, metadata)
                results.append(result)
        
        return results
