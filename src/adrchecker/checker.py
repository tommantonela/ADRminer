"""Core ADR quality checking logic.

This module provides the `ADRChecker` class, which uses LLM-based chains
to assess ADR adherence to the MADR template and evaluate section-wise
consistency.
"""

import concurrent.futures
import json
import logging
from typing import Dict, List, Optional

import tiktoken
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from adrchecker.config import get_settings
from adrchecker.prompts import (
    CONSISTENCY_PROMPT_BY_SECTION,
    FULL_CONSISTENCY_OVER_EXTRACTED_ADR,
    get_adr_sections_metadata,
)
from adrchecker.schemas import (
    ADRAssessmentReport,
    ADRConsistencyResult,
    ADRConsistencySections,
    ADRTemplate,
)

logger = logging.getLogger(__name__)


class ADRChecker:
    """Check ADR quality against the MADR template using LLM models.

    Provides three modes of assessment:
        - `check_madr_adherence`: Overall MADR template adherence (score + extraction).
        - `check_sections`: Section-wise consistency (presence, quality, purpose).
        - `check`: Full assessment combining both above.

    Args:
        llm: An optional pre-configured LangChain chat model. If not provided,
            one is created from the checker's settings.
        model_name: Model name (e.g., "gpt-4o-mini"). Used only if `llm` is None.
        temperature: Generation temperature. Used only if `llm` is None.
        max_tokens: Maximum tokens to generate. Used only if `llm` is None.
    """

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        if llm is not None:
            self.llm = llm
        else:
            settings = get_settings()
            kwargs = dict(
                model=model_name or settings.model,
                temperature=temperature if temperature is not None else settings.temperature,
                max_tokens=max_tokens or settings.max_tokens,
            )
            api_key = settings.resolved_api_key()
            if api_key:
                kwargs["api_key"] = api_key
            if settings.openai_base_url:
                kwargs["base_url"] = settings.openai_base_url
            self.llm = ChatOpenAI(**kwargs)

        self.configure_chains()

    # ------------------------------------------------------------------
    # Chain configuration
    # ------------------------------------------------------------------

    def configure_chains(self) -> None:
        """Configure the LangChain chains for adherence and section checks."""
        # Adherence to MADR template (global analysis)
        structured_llm_adherence = self.llm.with_structured_output(ADRTemplate)
        prompt_adherence = PromptTemplate(
            template=FULL_CONSISTENCY_OVER_EXTRACTED_ADR,
            input_variables=["input_text"],
        )
        self.global_consistency_chain = prompt_adherence | structured_llm_adherence

        # Section-wise consistency analysis
        structured_llm_section = self.llm.with_structured_output(ADRConsistencyResult)
        prompt_section = PromptTemplate(
            template=CONSISTENCY_PROMPT_BY_SECTION,
            input_variables=["adr_input", "section_name", "section_purpose"],
        )
        self.section_wise_consistency_chain = prompt_section | structured_llm_section

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _num_tokens_from_adr(string: str, encoding_name: str = "cl100k_base") -> int:
        """Return the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(string))

    def _check_token_limit(self, adr_text: str) -> int:
        """Count tokens and warn if the text exceeds the model's token limit.

        Returns:
            The token count.
        """
        count_tokens = self._num_tokens_from_adr(adr_text)
        logger.info("Classifying ADR with %s tokens.", count_tokens)

        max_tokens = getattr(self.llm, "max_tokens", None)
        if max_tokens is not None and count_tokens > max_tokens:
            logger.warning(
                "The ADR text exceeds the token limit (%s) for the model and may be truncated.",
                max_tokens,
            )
        return count_tokens

    # ------------------------------------------------------------------
    # MADR template adherence
    # ------------------------------------------------------------------

    def check_madr_adherence(
        self,
        adr_text: str,
        as_dict: bool = True,
        metadata: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """Check MADR template adherence for a single ADR.

        Args:
            adr_text: The full text content of the ADR.
            as_dict: If True, return a dictionary; otherwise return the Pydantic model.
            metadata: Optional metadata dict to include in the result.

        Returns:
            Assessment result as a dict (or Pydantic model), or None on failure.
        """
        if self.global_consistency_chain is None:
            logger.error("Global consistency chain is not configured. Please set it first.")
            return None

        self._check_token_limit(adr_text)

        result = self.global_consistency_chain.invoke(input=adr_text)

        if as_dict:
            result = json.loads(result.model_dump_json())
            if metadata is not None:
                result["metadata"] = metadata

        return result

    def check_madr_adherence_batch(
        self,
        adr_texts: Dict[str, str],
        organization: Optional[str] = None,
        project: Optional[str] = None,
        as_dict: bool = True,
        parallel: bool = False,
        json_file: Optional[str] = None,
    ) -> List[Dict]:
        """Check MADR template adherence for multiple ADRs.

        Args:
            adr_texts: Dictionary mapping ADR keys to their text content.
            organization: Optional organization name for metadata.
            project: Optional project name for metadata.
            as_dict: If True, return dictionaries.
            parallel: If True, use ThreadPoolExecutor for parallel processing.
            json_file: Optional path to save results as JSON.

        Returns:
            List of assessment results.
        """
        results = self._run_batch(
            self.check_madr_adherence,
            adr_texts,
            organization=organization,
            project=project,
            as_dict=as_dict,
            parallel=parallel,
        )

        if json_file is not None and as_dict and len(results) > 0:
            ADRChecker.save_results(results, json_file)

        return results

    # ------------------------------------------------------------------
    # Section-wise consistency
    # ------------------------------------------------------------------

    def check_sections(
        self,
        adr_text: str,
        as_dict: bool = True,
        metadata: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """Check section-wise consistency for a single ADR.

        Evaluates each MADR section for presence, content quality, and
        purpose consistency.

        Args:
            adr_text: The full text content of the ADR.
            as_dict: If True, return a dictionary; otherwise return the Pydantic model.
            metadata: Optional metadata dict to include in the result.

        Returns:
            Assessment result as a dict (or Pydantic model), or None on failure.
        """
        if self.section_wise_consistency_chain is None:
            logger.error("Section-wise consistency chain is not configured. Please set it first.")
            return None

        self._check_token_limit(adr_text)

        sections = get_adr_sections_metadata()
        all_section_results: List[ADRConsistencyResult] = []

        for section_name, section_purpose in sections.items():
            section_result = self.section_wise_consistency_chain.invoke(
                {
                    "adr_input": adr_text,
                    "section_name": section_name,
                    "section_purpose": section_purpose,
                }
            )
            all_section_results.append(section_result)

        result = ADRConsistencySections(section_assessments=all_section_results)

        if as_dict:
            result = json.loads(result.model_dump_json())
            if metadata is not None:
                result["metadata"] = metadata

        return result

    def check_sections_batch(
        self,
        adr_texts: Dict[str, str],
        organization: Optional[str] = None,
        project: Optional[str] = None,
        as_dict: bool = True,
        parallel: bool = False,
        json_file: Optional[str] = None,
    ) -> List[Dict]:
        """Check section-wise consistency for multiple ADRs.

        Args:
            adr_texts: Dictionary mapping ADR keys to their text content.
            organization: Optional organization name for metadata.
            project: Optional project name for metadata.
            as_dict: If True, return dictionaries.
            parallel: If True, use ThreadPoolExecutor for parallel processing.
            json_file: Optional path to save results as JSON.

        Returns:
            List of assessment results.
        """
        results = self._run_batch(
            self.check_sections,
            adr_texts,
            organization=organization,
            project=project,
            as_dict=as_dict,
            parallel=parallel,
        )

        if json_file is not None and as_dict and len(results) > 0:
            ADRChecker.save_results(results, json_file)

        return results

    # ------------------------------------------------------------------
    # Full check (adherence + sections)
    # ------------------------------------------------------------------

    def check(
        self,
        adr_text: str,
        as_dict: bool = True,
        metadata: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """Perform a full assessment (adherence + sections) for a single ADR.

        Args:
            adr_text: The full text content of the ADR.
            as_dict: If True, return a dictionary; otherwise return the Pydantic model.
            metadata: Optional metadata dict to include in the result.

        Returns:
            Full assessment result as a dict (or Pydantic model), or None on failure.
        """
        sections_result = self.check_sections(adr_text, as_dict=False)
        adherence_result = self.check_madr_adherence(adr_text, as_dict=False)

        if sections_result is None or adherence_result is None:
            logger.error("Full check failed: one or more sub-checks returned None.")
            return None

        result = ADRAssessmentReport(
            section_assessments=sections_result.section_assessments,
            template_adherence=adherence_result,
        )

        if as_dict:
            result = json.loads(result.model_dump_json())
            if metadata is not None:
                result["metadata"] = metadata

        return result

    def check_batch(
        self,
        adr_texts: Dict[str, str],
        organization: Optional[str] = None,
        project: Optional[str] = None,
        as_dict: bool = True,
        parallel: bool = False,
        json_file: Optional[str] = None,
    ) -> List[Dict]:
        """Perform a full assessment for multiple ADRs.

        Args:
            adr_texts: Dictionary mapping ADR keys to their text content.
            organization: Optional organization name for metadata.
            project: Optional project name for metadata.
            as_dict: If True, return dictionaries.
            parallel: If True, use ThreadPoolExecutor for parallel processing.
            json_file: Optional path to save results as JSON.

        Returns:
            List of full assessment results.
        """
        results = self._run_batch(
            self.check,
            adr_texts,
            organization=organization,
            project=project,
            as_dict=as_dict,
            parallel=parallel,
        )

        if json_file is not None and as_dict and len(results) > 0:
            ADRChecker.save_results(results, json_file)

        return results

    # ------------------------------------------------------------------
    # Batch helper
    # ------------------------------------------------------------------

    def _run_batch(
        self,
        check_fn,
        adr_texts: Dict[str, str],
        organization: Optional[str] = None,
        project: Optional[str] = None,
        as_dict: bool = True,
        parallel: bool = False,
    ) -> List[Dict]:
        """Run a check function over a batch of ADR texts.

        Args:
            check_fn: The check method to call (`check_madr_adherence`, `check_sections`, or `check`).
            adr_texts: Dictionary mapping ADR keys to their text content.
            organization: Optional organization name for metadata.
            project: Optional project name for metadata.
            as_dict: If True, return dictionaries.
            parallel: If True, use ThreadPoolExecutor for parallel processing.

        Returns:
            List of results, with metadata added if organization/project are provided.
        """
        results: List[Dict] = []

        if parallel:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = list(
                    executor.map(
                        lambda adr: check_fn(adr, as_dict=as_dict),
                        adr_texts.values(),
                    )
                )
        else:
            for adr_key in adr_texts:
                results.append(check_fn(adr_texts[adr_key], as_dict=as_dict))

        # Add metadata (organization, project, adr_key) if provided
        if as_dict and organization is not None and project is not None:
            results = [
                {
                    **res,
                    "metadata": {
                        "organization": organization,
                        "project": project,
                        "adr_key": adr_key,
                    },
                }
                for res, adr_key in zip(results, adr_texts.keys())
            ]

        return results

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @staticmethod
    def save_results(classifications: List[Dict], json_file: str) -> None:
        """Save classification results to a JSON file.

        Args:
            classifications: List of result dictionaries.
            json_file: Path to the output JSON file.
        """
        try:
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(classifications, f, indent=4)
            logger.info("Results saved to %s", json_file)
        except IOError as e:
            logger.error("Error saving file %s: %s", json_file, e)