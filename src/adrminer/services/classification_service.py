"""Classification service using LLM models."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Literal

from adrminer.config import Settings
from adrminer.models import get_llm


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
            "Security",
            "Availability",
            "Scalability",
            "Maintainability",
            "Usability",
            "Interoperability",
            "Modifiability",
            "Testability",
            "Reliability",
        ],
        "description": "Classifies ADRs by the quality attribute (non-functional requirement) they address",
        "category_descriptions": {
            "Performance": "Decisions related to system speed, response time, throughput, latency, and overall performance characteristics.",
            "Security": "Decisions related to authentication, authorization, encryption, data protection, vulnerability management, and security controls.",
            "Availability": "Decisions related to system uptime, fault tolerance, redundancy, disaster recovery, and high availability.",
            "Scalability": "Decisions related to the system's ability to handle growing loads, horizontal/vertical scaling, and resource management.",
            "Maintainability": "Decisions related to code quality, documentation, technical debt management, and ease of system maintenance.",
            "Usability": "Decisions related to user experience, user interface design, accessibility, and ease of use.",
            "Interoperability": "Decisions related to system integration, API design, data exchange, and compatibility with other systems.",
            "Modifiability": "Decisions related to the ease of making changes to the system, extensibility, and flexibility.",
            "Testability": "Decisions related to testing strategies, test automation, test coverage, and quality assurance practices.",
            "Reliability": "Decisions related to system stability, error handling, fault tolerance, and consistent behavior under load.",
        },
    },
    "zimmermann": {
        "name": "Zimmermann",
        "categories": [
            "Technology",
            "Organization",
            "Information",
            "Architecture",
            "Process",
            "Tools",
        ],
        "description": "Classifies ADRs by architectural aspect using the ATAM (Architecture Tradeoff Analysis Method) framework",
        "category_descriptions": {
            "Technology": "Decisions about specific technologies, frameworks, languages, libraries, and technical stacks used in the system.",
            "Organization": "Decisions about team structure, organizational processes, governance, roles, and responsibilities.",
            "Information": "Decisions about data models, information flow, data storage, data exchange formats, and information architecture.",
            "Architecture": "Decisions about system architecture, patterns, structural design, components, and architectural principles.",
            "Process": "Decisions about development processes, methodologies, workflows, deployment pipelines, and operational processes.",
            "Tools": "Decisions about development tools, build systems, CI/CD tools, monitoring, and infrastructure tooling.",
        },
    },
}


class ClassificationService:
    """Service for classifying ADRs using LLM models."""
    
    def __init__(
        self,
        framework: Literal["kruchten", "quality_attributes", "zimmermann"] = "kruchten",
        examples_path: Optional[str] = None,
        use_examples: bool = True,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize classification service.
        
        Args:
            framework: Classification framework to use
            examples_path: Path to examples JSON file
            use_examples: Whether to use examples (few-shot)
            settings: Settings instance
        """
        if settings is None:
            from adrminer.config import get_settings
            settings = get_settings()
        
        self.settings = settings
        self.framework = framework or settings.classification.framework
        self.examples_path = Path(examples_path) if examples_path else Path(settings.classification.examples)
        self.use_examples = use_examples if use_examples is not None else settings.classification.use_examples
        
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
    
    def _build_prompt(
        self,
        text: str,
        framework: str,
        examples: Optional[List[Dict]] = None,
    ) -> str:
        """
        Build classification prompt.
        
        Args:
            text: ADR text to classify
            framework: Classification framework
            examples: Optional few-shot examples
        
        Returns:
            Formatted prompt string
        """
        framework_info = FRAMEWORKS[framework]
        categories = framework_info["categories"]
        
        # Start with system instructions
        prompt = f"""You are an expert architectural decision analyst. Your task is to classify the given Architectural Decision Record (ADR) into one of the following categories for the {framework_info['name']} framework.

Categories:
"""
        
        # Add categories
        for i, category in enumerate(categories, 1):
            prompt += f"{i}. {category}\n"
        
        prompt += """
Instructions:
1. Read the ADR carefully
2. Identify the most appropriate category based on the decision's primary focus
3. Provide your classification in JSON format with the following structure:
   {
     "category": "<category name>",
     "confidence": <0.0 to 1.0>,
     "explanation": "<brief explanation of why this category was chosen>",
     "alternatives": ["<alternative category 1>", "<alternative category 2>"]
   }

"""
        
        # Add examples if provided (few-shot)
        if examples:
            prompt += "Here are some examples to guide your classification:\n\n"
            
            for i, example in enumerate(examples[:3], 1):  # Use up to 3 examples
                if "text" in example and "category" in example:
                    prompt += f"Example {i}:\n"
                    prompt += f"ADR: {example['text'][:500]}...\n"
                    prompt += f"Category: {example['category']}\n\n"
            
            prompt += "---\n\n"
        
        # Add the ADR to classify
        prompt += f"Now classify the following ADR:\n\n{text}\n\n"
        prompt += "Provide your classification in JSON format:"
        
        return prompt
    
    def classify(
        self,
        text: str,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Classify a single ADR.
        
        Args:
            text: ADR text content
            metadata: Optional metadata about the ADR
        
        Returns:
            Dictionary with classification results
        """
        # Build prompt
        prompt = self._build_prompt(text, self.framework, self.examples)
        
        # Get classification from LLM
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content
        except Exception as e:
            raise RuntimeError(f"LLM classification failed: {e}")
        
        # Parse response
        try:
            # Try to extract JSON from response
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            
            result = json.loads(json_str)
        except json.JSONDecodeError as e:
            # Fallback: try to extract category from text
            result = self._parse_fallback(response_text)
        
        # Validate and normalize result
        result = self._normalize_result(result)
        
        return {
            "framework": self.framework,
            "primary_category": result["category"],
            "confidence": result["confidence"],
            "explanation": result.get("explanation", ""),
            "alternatives": result.get("alternatives", []),
            "metadata": metadata or {},
        }
    
    def _parse_fallback(self, text: str) -> Dict:
        """
        Fallback parsing when JSON extraction fails.
        
        Args:
            text: LLM response text
        
        Returns:
            Parsed result dictionary
        """
        # Try to extract category from text
        categories = FRAMEWORKS[self.framework]["categories"]
        
        for category in categories:
            if category.lower() in text.lower():
                return {
                    "category": category,
                    "confidence": 0.5,  # Low confidence for fallback
                    "explanation": "Extracted from text (JSON parsing failed)",
                    "alternatives": [],
                }
        
        # Ultimate fallback
        return {
            "category": categories[0],
            "confidence": 0.3,
            "explanation": "Default category (parsing failed)",
            "alternatives": [],
        }
    
    def _normalize_result(self, result: Dict) -> Dict:
        """
        Normalize and validate classification result.
        
        Args:
            result: Raw result dictionary
        
        Returns:
            Normalized result
        """
        categories = FRAMEWORKS[self.framework]["categories"]
        
        # Validate category
        if "category" not in result or result["category"] not in categories:
            result["category"] = categories[0]
        
        # Validate confidence
        if "confidence" not in result or not isinstance(result["confidence"], (int, float)):
            result["confidence"] = 0.5
        result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))
        
        # Ensure fields exist
        result.setdefault("explanation", "")
        result.setdefault("alternatives", [])
        
        return result
    
    def classify_batch(
        self,
        texts: List[str],
        metadata_list: Optional[List[Dict]] = None,
        parallel: bool = True,
    ) -> List[Dict]:
        """
        Classify multiple ADRs.
        
        Args:
            texts: List of ADR text contents
            metadata_list: Optional list of metadata for each ADR
            parallel: Enable parallel processing (not yet implemented)
        
        Returns:
            List of classification results
        """
        # For now, process sequentially
        # TODO: Implement parallel processing with ThreadPoolExecutor or similar
        results = []
        
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