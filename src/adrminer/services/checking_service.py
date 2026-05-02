"""ADR quality checking service using LLM models."""

import concurrent.futures
import json
from pathlib import Path
from typing import Dict, List, Literal, Optional

from adrminer.config import Settings
from adrminer.models import get_llm
from adrminer.services.base import BaseService
from adrminer.services.adr_parser_service import ADRParserService

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


# MADR section definitions
MADR_SECTIONS = {
    'Context': 'Describes the background, system state, problem, or motivation. It must not include detailed comparisons between solutions, rationales, or final decisions—those belong in "Considered Options" or "Decision". Includes: technical constraints, stakeholder needs, project circumstances, or related issues.',
    'Decision': 'Clearly and explicitly states the final choice that was made in response to the context. This is the core of the ADR and should be unambiguous. Includes: selected approach, accepted alternative, or implemented design.',
    'Consequences': 'Explains the results, implications, trade-offs, and expected impact of the decision—both positive and negative. Should address what follows from the decision in terms of system behavior, future maintenance, or risks. Includes: technical debt, performance effects, maintainability implications, limitations.',
    'Decision Drivers': 'Lists the main criteria, goals, or forces that shaped the decision-making process. Should clarify what mattered most when choosing between options. Includes: performance, cost, simplicity, compatibility, regulatory compliance.',
    'Considered Options': 'Enumerates alternative approaches or solutions that were evaluated and explains why they were not chosen. Should demonstrate that the decision was made after a comparison of viable options. Includes: at least two alternatives, with brief pros and cons or rejection justifications.',
}


class CheckingService(BaseService):
    """Service for checking ADR quality using LLM models."""
    
    def __init__(
        self,
        mode: Literal["adherence", "sections", "full"] = "full",
        use_parser: bool = False,
        parser_config: Optional[Dict] = None,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize checking service.
        
        Args:
            mode: Checking mode (adherence|sections|full)
            use_parser: Whether to use ADR parser for section extraction
            parser_config: Optional configuration for parser (strict, detect_language)
            settings: Settings instance
        """
        # Initialize base class
        super().__init__(settings)
        
        self.mode = mode or "full"
        self.use_parser = use_parser if use_parser is not None else settings.checking.use_parser if hasattr(settings, 'checking') else False
        
        # Initialize parser if enabled
        if self.use_parser:
            parser_config = parser_config or {}
            self.parser = ADRParserService(**parser_config)
        else:
            self.parser = None
        
        # Get LLM (shared with other services)
        self.llm = get_llm(settings=settings)
        
        # Configure prompts for adherence check
        self._configure_adherence_chain()
        
        # Configure prompts for section check
        self._configure_section_chain()
    
    def _configure_adherence_chain(self):
        """Configure chain for MADR template adherence check using structured output.
        
        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        from langchain_core.prompts import PromptTemplate
        
        # Load prompt from external file
        full_consistency_prompt = self.load_prompt("full_consistency_check")
        
        # Handle case where prompt file wasn't found
        if full_consistency_prompt is None:
            raise FileNotFoundError(
                f"Prompt file not found: full_consistency_check.md in {self.prompts_dir}"
            )
        
        self.adherence_prompt = PromptTemplate(
            template=full_consistency_prompt,
            input_variables=["input_text"],
        )
        
        # Create structured output chain
        self.adherence_chain = self.adherence_prompt | self.llm.with_structured_output(ADRTemplate)
    
    def _configure_section_chain(self):
        """Configure chain for section-wise consistency check using structured output.
        
        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        from langchain_core.prompts import PromptTemplate
        
        # Load prompt from external file
        section_consistency_prompt = self.load_prompt("section_consistency_check")
        
        # Handle case where prompt file wasn't found
        if section_consistency_prompt is None:
            raise FileNotFoundError(
                f"Prompt file not found: section_consistency_check.md in {self.prompts_dir}"
            )
        
        self.section_prompt = PromptTemplate(
            template=section_consistency_prompt,
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
    
    def check_adherence(self, text: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Check MADR template adherence for a single ADR using structured output.
        
        Args:
            text: ADR text content
            metadata: Optional metadata about the ADR
        
        Returns:
            Dictionary with adherence check results
        """
        # Use parser if enabled (can extract sections better)
        if self.use_parser and self.parser:
            try:
                # Parse ADR to get better structure
                parsed = self.parser.parse_adr(text)
                
                # Extract title and add to metadata
                if metadata is None:
                    metadata = {}
                metadata["title"] = parsed.title
                
                # Use full text from parsed ADR (normalized)
                text = parsed.full_text
                
                # Add parsing info to metadata
                metadata["parsed"] = not parsed.parsing_failed
                if parsed.parsing_failed:
                    metadata["parsing_error"] = parsed.parsing_error
                
            except Exception as e:
                # Fallback to original text
                if metadata is None:
                    metadata = {}
                metadata["parser_error"] = str(e)
        
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
        # Use parser if enabled (can provide better section extraction)
        if self.use_parser and self.parser:
            try:
                # Parse ADR to get better structure
                parsed = self.parser.parse_adr(text)
                
                # Extract title and add to metadata
                if metadata is None:
                    metadata = {}
                metadata["title"] = parsed.title
                
                # Use full text from parsed ADR (normalized)
                text = parsed.full_text
                
                # Add parsing info to metadata
                metadata["parsed"] = not parsed.parsing_failed
                if parsed.parsing_failed:
                    metadata["parsing_error"] = parsed.parsing_error
                
            except Exception as e:
                # Fallback to original text
                if metadata is None:
                    metadata = {}
                metadata["parser_error"] = str(e)
        
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
