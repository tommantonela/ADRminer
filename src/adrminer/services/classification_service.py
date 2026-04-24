"""Classification service using LLM models."""

import concurrent.futures
import json
from pathlib import Path
from typing import Dict, List, Optional, Literal

from langchain_core.prompts import ChatPromptTemplate

from adrminer.config import Settings
from adrminer.models import get_llm
from adrminer.models.classification_schemas import (
    ClassificationFramework,
    KruchtenClassificationResult,
    QualityAttributeClassificationResult,
    ZimmermannClassificationResult,
)
from adrminer.services.base import BaseService
from adrminer.services.adr_parser_service import ADRParserService


# Framework definitions
FRAMEWORKS = {
    "kruchten": {
        "name": "Kruchten",
        "categories": [
            "Existence (ontocrisis)",
            "Property (diacrisis)",
            "Executive (pericrisis)",
            "Ban (anticrisis)",
        ],
        "description": "Classifies ADRs by type of architectural decision based on crisis type",
        "category_descriptions": {
            "Existence (ontocrisis)": "Decisions that create or introduce new architectural elements, components, or systems. These are 'creation' decisions that establish what exists in the architecture.",
            "Property (diacrisis)": "Decisions that modify or change existing architectural elements, components, or properties. These are 'modification' decisions that alter how existing elements behave or are configured.",
            "Executive (pericrisis)": "Decisions related to organizational processes, governance, or management of architecture. These are 'management' decisions that how architecture is governed and executed.",
            "Ban (anticrisis)": "Decisions that explicitly prohibit or reject certain architectural choices, technologies, or approaches. These are 'negative' decisions that specify what should NOT be used.",
        },
    },
    "quality_attributes": {
        "name": "Quality Attributes",
        "categories": [
            "Performance",
            "Reliability",
            "Security",
            "Maintainability",
            "Scalability",
            "Usability",
            "Portability",
            "Compatibility",
            "Observability",
            "Testability",
            "Other/Only Functional Concern",
        ],
        "description": "Classifies ADRs by quality attribute (non-functional requirement) they address",
        "category_descriptions": {
            "Performance": "Decisions related to system speed, response time, throughput, latency, and overall performance characteristics.",
            "Reliability": "Decisions related to system stability, error handling, fault tolerance, and consistent behavior under load.",
            "Security": "Decisions related to authentication, authorization, encryption, data protection, vulnerability management, and security controls.",
            "Maintainability": "Decisions related to code quality, documentation, technical debt management, and ease of system maintenance.",
            "Scalability": "Decisions related to system's ability to handle growing loads, horizontal/vertical scaling, and resource management.",
            "Usability": "Decisions related to user experience, user interface design, accessibility, and ease of use.",
            "Portability": "Decisions related to system's ability to run on different platforms, environments, or with minimal adaptation.",
            "Compatibility": "Decisions related to ensuring system works with other systems, APIs, standards, or maintains backward compatibility.",
            "Observability": "Decisions related to monitoring, logging, tracing, metrics, and system visibility.",
            "Testability": "Decisions related to testing strategies, test automation, test coverage, and quality assurance practices.",
            "Other/Only Functional Concern": "Decisions that only address functional requirements without explicitly targeting any specific non-functional quality attribute.",
        },
    },
    "zimmermann": {
        "name": "Zimmermann",
        "categories": [
            "Design",
            "Technology",
            "Infrastructure",
            "Organizational/Process",
            "Constraint",
            "Quality Attribute",
            "Crosscutting Concerns",
            "Implementation",
            "Other",
        ],
        "description": "Classifies ADRs by architectural aspect",
        "category_descriptions": {
            "Design": "Decisions about system design, patterns, architectural principles, and structural organization.",
            "Technology": "Decisions about specific technologies, frameworks, languages, libraries, and technical stacks used in system.",
            "Infrastructure": "Decisions about infrastructure components, cloud providers, deployment environments, and infrastructure as code.",
            "Organizational/Process": "Decisions about team structure, organizational processes, governance, roles, responsibilities, and development methodologies.",
            "Constraint": "Decisions about constraints, limitations, or restrictions that impact architectural choices.",
            "Quality Attribute": "Decisions that address specific non-functional requirements or quality attributes (e.g., performance, security, scalability).",
            "Crosscutting Concerns": "Decisions about aspects that affect multiple parts of the system (e.g., logging, security, error handling).",
            "Implementation": "Decisions about implementation details, coding standards, libraries, and how architectural decisions are realized in code.",
            "Other": "Decisions that don't fit into other specific categories or address unique concerns.",
        },
    },
}


class ClassificationService(BaseService):
    """Service for classifying ADRs using LLM models."""
    
    def __init__(
        self,
        framework: Literal["kruchten", "quality_attributes", "zimmermann"] = "kruchten",
        examples_path: Optional[str] = None,
        use_examples: bool = True,
        use_parser: bool = False,
        parser_config: Optional[Dict] = None,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize classification service.
        
        Args:
            framework: Classification framework to use
            examples_path: Path to examples JSON file
            use_examples: Whether to use examples (few-shot)
            use_parser: Whether to use ADR parser for section extraction
            parser_config: Optional configuration for parser (strict, detect_language)
            settings: Settings instance
        """
        # Initialize base class
        super().__init__(settings)
        
        self._framework = framework or settings.classification.framework
        self.examples_path = Path(examples_path) if examples_path else Path(settings.classification.examples)
        self.use_examples = use_examples if use_examples is not None else settings.classification.use_examples
        self.use_parser = use_parser if use_parser is not None else settings.classification.use_parser
        
        # Initialize parser if enabled
        if self.use_parser:
            parser_config = parser_config or {}
            self.parser = ADRParserService(**parser_config)
        else:
            self.parser = None
        
        # Validate framework
        if self.framework not in FRAMEWORKS:
            raise ValueError(
                f"Invalid framework: {self.framework}. "
                f"Valid frameworks: {', '.join(FRAMEWORKS.keys())}"
            )
        
        # Load examples if requested
        self.examples = self._load_examples() if self.use_examples else None
        
        # Get LLM
        self.llm = get_llm(settings=settings)
        
        # Configure chain with structured output
        self.chain = None
        self._configure_chain()
    
    @property
    def framework(self) -> str:
        """Get current classification framework."""
        return self._framework
    
    @framework.setter
    def framework(self, value: str) -> None:
        """
        Set classification framework and reconfigure chain.
        
        Args:
            value: New framework name (kruchten, quality_attributes, zimmermann)
        """
        if value not in FRAMEWORKS:
            raise ValueError(
                f"Invalid framework: {value}. "
                f"Valid frameworks: {', '.join(FRAMEWORKS.keys())}"
            )
        
        self._framework = value
        self._configure_chain()  # Reconfigure with new framework
    
    def _load_examples(self) -> Optional[List[Dict]]:
        """Load classification examples from JSON file."""
        if not self.examples_path.exists():
            print(f"Warning: Examples file not found at {self.examples_path}. Using zero-shot.")
            return None
        
        try:
            with open(self.examples_path, "r") as f:
                data = json.load(f)
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "examples" in data:
                return data["examples"]
            else:
                print(f"Warning: Invalid examples format in {self.examples_path}")
                return None
        except Exception as e:
            print(f"Warning: Failed to load examples from {self.examples_path}: {e}")
            return None
    
    def _configure_chain(self):
        """Configure LangChain chain with structured output."""
        # Map framework to appropriate Pydantic model
        if self.framework == "kruchten":
            schema = KruchtenClassificationResult
        elif self.framework == "quality_attributes":
            schema = QualityAttributeClassificationResult
        elif self.framework == "zimmermann":
            schema = ZimmermannClassificationResult
        else:
            raise ValueError(f"Unsupported framework: {self.framework}")
        
        # Load base prompt
        prompt_str = self.load_prompt(self._get_prompt_name())
        
        # Create ChatPromptTemplate
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", prompt_str),
            ("human", "{adr}"),
        ])
        
        # Configure chain with structured output
        self.chain = prompt_template | self.llm.with_structured_output(schema)
    
    def _get_prompt_name(self) -> str:
        """Get prompt file name for current framework."""
        prompt_mapping = {
            "kruchten": "kruchten_classification_v2",
            "quality_attributes": "quality_attributes_classification_v2",
            "zimmermann": "zimmermann_classification_v2",
        }
        return prompt_mapping.get(self.framework)
    
    def classify(
        self,
        text: str,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Classify a single ADR with optional parser.
        
        Args:
            text: ADR text content
            metadata: Optional metadata about the ADR
        
        Returns:
            Dictionary with classification results
        """
        # Use parser if enabled
        if self.use_parser and self.parser:
            try:
                # Extract decision section only (more focused for classification)
                text = self.parser.get_decision_section(text)
                
                # Extract title and add to metadata
                title = self.parser.get_title(text)
                if metadata is None:
                    metadata = {}
                metadata["title"] = title
                
            except Exception as e:
                # Fallback to full text
                self.logger.warning(f"Parser failed for classification: {e}. Using full text.")
        
        # Use structured output chain
        try:
            result = self.chain.invoke({"adr": text})
        except Exception as e:
            raise RuntimeError(f"LLM classification failed: {e}")
        
        # Convert Pydantic model to dictionary
        result_dict = result.model_dump()
        
        # Add metadata
        if metadata:
            result_dict["metadata"] = metadata
        else:
            result_dict["metadata"] = {}
        
        # Normalize field names for backward compatibility
        return {
            "framework": self.framework,
            "primary_category": result_dict["primary_category"],
            "confidence": result_dict["primary_score"],
            "explanation": result_dict["explanation"],
            "alternatives": result_dict.get("alternative_categories", []),
            "metadata": result_dict.get("metadata", {}),
        }
    
    def classify_batch(
        self,
        texts: List[str],
        metadata_list: Optional[List[Dict]] = None,
        parallel: bool = True,
    ) -> List[Dict]:
        """
        Classify multiple ADRs with optional parallel processing.
        
        Args:
            texts: List of ADR text contents
            metadata_list: Optional list of metadata for each ADR
            parallel: Enable parallel processing
        
        Returns:
            List of classification results
        """
        results = []
        
        if parallel and len(texts) > 1:
            # Use ThreadPoolExecutor for parallel processing
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Store (index, future) pairs to maintain order
                futures = []
                for i, text in enumerate(texts):
                    metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
                    future = executor.submit(self.classify, text, metadata)
                    futures.append((i, future))
                
                # Wait for all futures to complete and collect in order
                results = [None] * len(texts)
                for i, future in futures:
                    try:
                        results[i] = future.result()
                    except Exception as e:
                        print(f"Warning: Failed to classify ADR at index {i}: {e}")
                        # Create error result with metadata
                        metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else {}
                        results[i] = {
                            "framework": self.framework,
                            "primary_category": FRAMEWORKS[self.framework]["categories"][0],
                            "confidence": 0.0,
                            "explanation": f"Classification failed: {e}",
                            "alternatives": [],
                            "metadata": metadata,
                            "error": str(e),
                        }
        else:
            # Sequential processing
            for i, text in enumerate(texts):
                metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
                result = self.classify(text, metadata)
                results.append(result)
        
        return results
    
    def get_category_distribution(self, results: List[Dict]) -> Dict:
        """
        Get distribution of categories across results.
        
        Args:
            results: List of classification results
        
        Returns:
            Dictionary with category distribution statistics
        """
        categories = FRAMEWORKS[self.framework]["categories"]
        
        # Count occurrences and sum confidence
        category_counts = {cat: {"count": 0, "total_confidence": 0.0} for cat in categories}
        
        for result in results:
            category = result["primary_category"]
            confidence = result["confidence"]
            
            if category in category_counts:
                category_counts[category]["count"] += 1
                category_counts[category]["total_confidence"] += confidence
        
        # Calculate statistics
        distribution = {}
        total = len(results)
        
        for category, data in category_counts.items():
            count = data["count"]
            distribution[category] = {
                "count": count,
                "percentage": count / total if total > 0 else 0.0,
                "avg_confidence": data["total_confidence"] / count if count > 0 else 0.0,
            }
        
        # Calculate overall statistics
        high_confidence = sum(1 for r in results if r["confidence"] > 0.8)
        avg_confidence = sum(r["confidence"] for r in results) / total if total > 0 else 0.0
        
        return {
            "framework": self.framework,
            "total_adrs": total,
            "avg_confidence": avg_confidence,
            "high_confidence_count": high_confidence,
            "high_confidence_percentage": high_confidence / total if total > 0 else 0.0,
            "distribution": distribution,
        }