"""Insight service for generating ADR content summaries and metadata insights."""

import json
from pathlib import Path
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel

from adrminer.config import get_settings
from adrminer.models.llm_factory import create_llm
from adrminer.models.insight_schemas import (
    ContentSummary,
    ADRInsights,
    ProjectInsights,
)


class InsightService:
    """Service for generating insights from ADR content and metadata."""
    
    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        prompts_dir: Optional[Path] = None,
    ):
        """
        Initialize the InsightService.
        
        Args:
            llm: LLM instance (creates default if not provided)
            prompts_dir: Directory containing prompt templates
        """
        if llm is None:
            settings = get_settings()
            llm = create_llm(settings=settings)
        
        self.llm = llm
        
        if prompts_dir is None:
            # Default to prompts directory
            prompts_dir = Path(__file__).parent.parent / "prompts"
        
        self.prompts_dir = Path(prompts_dir)
        
        # Load prompts
        self._content_summary_prompt = self._load_prompt("content_summary.md")
        self._adr_insights_prompt = self._load_prompt("adr_insights.md")
        self._project_insights_prompt = self._load_prompt("project_insights.md")
        
        # Create LangChain prompt templates
        self.content_summary_template = ChatPromptTemplate.from_template(
            self._content_summary_prompt
        )
        self.adr_insights_template = ChatPromptTemplate.from_template(
            self._adr_insights_prompt
        )
        self.project_insights_template = ChatPromptTemplate.from_template(
            self._project_insights_prompt
        )
        
        # Create structured output chains
        self._content_summary_chain = (
            self.content_summary_template
            | self.llm.with_structured_output(ContentSummary)
        )
        self._adr_insights_chain = (
            self.adr_insights_template
            | self.llm.with_structured_output(ADRInsights)
        )
        self._project_insights_chain = (
            self.project_insights_template
            | self.llm.with_structured_output(ProjectInsights)
        )
    
    def _load_prompt(self, filename: str) -> str:
        """
        Load a prompt template from file.
        
        Args:
            filename: Name of the prompt file
            
        Returns:
            Prompt template string
        """
        prompt_path = self.prompts_dir / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def generate_content_summary(
        self,
        adr_content: str,
    ) -> ContentSummary:
        """
        Generate a summary of ADR content.
        
        Args:
            adr_content: Full ADR markdown content
            
        Returns:
            ContentSummary object with summary text
        """
        result = self._content_summary_chain.invoke({"content": adr_content})
        return result
    
    def generate_adr_insights(
        self,
        adr_metadata: dict,
    ) -> ADRInsights:
        """
        Generate insights for a single ADR from its metadata.
        
        Args:
            adr_metadata: ADR metadata dictionary (from sidecar file)
            
        Returns:
            ADRInsights object with comprehensive analysis
        """
        # Convert metadata to JSON string for the prompt
        metadata_json = json.dumps(adr_metadata, indent=2, ensure_ascii=False)
        
        result = self._adr_insights_chain.invoke({"metadata": metadata_json})
        return result
    
    def generate_project_insights(
        self,
        all_metadata: list[dict],
    ) -> ProjectInsights:
        """
        Generate project-wide insights from all ADRs' metadata.
        
        Args:
            all_metadata: List of ADR metadata dictionaries
            
        Returns:
            ProjectInsights object with comprehensive project analysis
        """
        # Convert all metadata to JSON string for the prompt
        metadata_json = json.dumps(all_metadata, indent=2, ensure_ascii=False)
        
        result = self._project_insights_chain.invoke({"all_metadata": metadata_json})
        return result
    
    @property
    def model_name(self) -> str:
        """Get the name of the LLM model being used."""
        # Try to get model name from the LLM instance
        if hasattr(self.llm, "model_name"):
            return self.llm.model_name
        elif hasattr(self.llm, "model"):
            return str(self.llm.model)
        else:
            return "unknown"