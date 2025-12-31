import tiktoken

from tqdm.notebook import tqdm

from pydantic import BaseModel, Field
import json

from pythonjsonlogger.json import JsonFormatter

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

import prompts
from prompts import get_adr_sections_metadata

from typing import Literal, Dict, List, Tuple
import logging
import sys
import numpy as np

import concurrent.futures


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = JsonFormatter(fmt='%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler = logging.StreamHandler(sys.stdout)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)


class ADRAlternative(BaseModel):
    description: str
    pros: List[str] = Field(..., description="List of pros of the alternative. It should be a list of strings.")
    cons: List[str] = Field(..., description="List of cons of the alternative. It should be a list of strings.")

class ADRTemplate(BaseModel):
    """
    ADR template (MADR, Zimmermann)
    """
    title: str = Field(..., description="Actual title of the ADR. It should convey the essence of the problem solved and the solution chosen.")
    status: str = Field(..., description="Status of the ADR. Options include: proposed, accepted, rejected, deprecated, superseded.")
    context: str = Field(..., description="Context of the ADR. Describes the context and problem statement in a few sentences. It articulates the problem being addressed.")
    decision_drivers: str = Field(..., description="Drivers of the ADR. It describes the forces that influence the decision, including desired qualities and concerns identified.")
    decision: str = Field(..., description="Decision of the ADR. It is the chosen option (among the alternatives) and the rationale for the decision.")
    consequences: str = Field(..., description="Consequences of the ADR. It describes the impact of the decision, including the positive and negative effects of making the decision.")
#     alternatives: str = Field(..., description="Alternatives of the ADR. It should mention a list of alternatives investigated and their pros and cons.")
    alternatives: List[ADRAlternative] = Field(..., description="Alternatives of the ADR. It should mention a list of alternatives investigated and their pros and cons.")
    date: str = Field(..., description="Date in which the ADR was updated.")
    adherence_score: float = Field(..., description="Degree of adherence of the ADR to the MADR template. It should be 1.0 if the sections and their contents closely match the template, and 0.0 if most sections and contents are not followed.")
    assessment: str = Field(..., description="Justification of the adherence score regarding the template. It should explain why the ADR is or is not following certain template sections, expliciting listing any omitted sections or contents.")

class ADRConsistencyResult(BaseModel):
    section_name: str = Field(..., description="Name of the ADR section being evaluated.")
    presence: Literal["Yes", "No"] = Field(..., description="Indicates whether the section is present in the ADR.")
    content_quality: Literal["Yes", "No"] = Field(..., description="Indicates whether the content of the section is of good quality (clear, complete, relevant).")
    purpose_consistency: Literal["Yes", "Partial", "No"] = Field(..., description="Indicates whether the purpose of the section is consistent with the template.")
    justification: str = Field(..., description="Explanation and rationale for the above evaluation of the section.")
    alternate_title: List[str] = Field(default_factory=list, description="List of other section titles (from the ADR) that could better reflect the content of the section.")

class ADRConsistecySections(BaseModel):
    section_assessments: List[ADRConsistencyResult] = Field(..., description="List of assessments for each section of the ADR.")

class ADRAssessmentReport(BaseModel):
    section_assessments: List[ADRConsistencyResult] = Field(..., description="List of assessments for each section of the ADR.")
    template_adherence: ADRTemplate = Field(..., description="Assessment of the adherence of the ADR to the MADR template.")


class ADRChecker:

    def __init__(self, llm: ChatOpenAI, model_name: str = "gpt-4o-mini", temperature: float = 0.0, max_tokens: int = None):
        self.llm = llm or ChatOpenAI(model_name=model_name, temperature=temperature, max_tokens=max_tokens)
        self.configure_chains()

    def configure_chains(self):
        
        # Adherence to MADR template (global analysis)
        structured_llm = self.llm.with_structured_output(ADRTemplate)
        prompt = PromptTemplate(
            template=prompts.FULL_CONSISTENCY_OVER_EXTRACTED_ADR,
            input_variables=["input_text"],
            #partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        self.global_consistency_chain = prompt | structured_llm

        # Section-wise consistency analysis
        # structured_llm = self.llm.with_structured_output(ADRAssessmentReport)
        # prompt = PromptTemplate(
        #     template=prompts.CONSISTENCY_PROMPT_ALL_SECTIONS,
        #     input_variables=["input_text"],
        #     #partial_variables={"format_instructions": parser.get_format_instructions()},
        # )
        structured_llm = self.llm.with_structured_output(ADRConsistencyResult)
        prompt = PromptTemplate(
            template=prompts.CONSISTENCY_PROMPT_BY_SECTION,
            input_variables=["adr_input", "section_name", "section_purpose"],
            #partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        self.section_wise_consistency_chain = prompt | structured_llm

    
    @staticmethod
    def _num_tokens_from_adr(string: str, encoding_name: str ="cl100k_base") -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
        
    def check_madr_adherence(self, adr_text: str, as_dict=True, metadata=None) -> Dict:
        if self.global_consistency_chain is None:
            logger.error("Global consistency chain is not configured. Please set it first.")
            return None

        count_tokens = ADRChecker._num_tokens_from_adr(adr_text)
        logger.info(f"Classifying ADR with {count_tokens} tokens.")
        if (self.llm.max_tokens is not None) and (count_tokens > self.llm.max_tokens):
            logger.warning("The ADR text exceeds the token limit for the model and may be truncated.")
        
        result = self.global_consistency_chain.invoke(input=adr_text)
        if as_dict:
            json_string = result.model_dump_json()
            result = json.loads(json_string)
            if metadata is not None:
                result['metadata'] = metadata
            return result
        else:
            return result

    def check_madr_adherence_batch(self, adr_texts: Dict[str,str], organization=None, project=None, as_dict=True, parallel=False, json_file=None) -> List[Dict]:
        # Note that it runs in parallel using ThreadPoolExecutor
        results = []
        if parallel:
            # logging.disable()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = executor.map(lambda adr: self.check_madr_adherence(adr, as_dict=as_dict), adr_texts.values())
            results = list(results)
        else:
            # Use tqdm
            for adr in tqdm(adr_texts, desc="Classifying ADRs"):
                results.append(self.check_madr_adherence(adr, as_dict=as_dict))
        
        # Add metadata of the ADR (name, project, organization), if provided
        if as_dict and organization is not None and project is not None:
                results = [{**res, 'metadata': {'organization': organization, 'project': project, 'adr_key': adr_key}} for res, adr_key in zip(results, adr_texts.keys())]
   
        if (json_file is not None) and as_dict and (len(results) > 0):
            ADRChecker.save_results(results, json_file)
        return results
    
    # def check_sections(self, adr_text: str, as_dict=True, metadata=None) -> Dict:
    #     if self.section_wise_consistency_chain is None:
    #         logger.error("Section-wise consistency chain is not configured. Please set it first.")
    #         return None

    #     count_tokens = ADRChecker._num_tokens_from_adr(adr_text)
    #     logger.info(f"Classifying ADR with {count_tokens} tokens.")
    #     if (self.llm.max_tokens is not None) and (count_tokens > self.llm.max_tokens):
    #         logger.warning("The ADR text exceeds the token limit for the model and may be truncated.")
        
    #     result = self.section_wise_consistency_chain.invoke(input=adr_text)
    #     if as_dict:
    #         json_string = result.model_dump_json()
    #         result = json.loads(json_string)
    #         if metadata is not None:
    #             result['metadata'] = metadata
    #         return result
    #     else:
    #         return result

    def check_sections(self, adr_text: str, as_dict=True, metadata=None) -> Dict:
        if self.section_wise_consistency_chain is None:
            logger.error("Section-wise consistency chain is not configured. Please set it first.")
            return None

        count_tokens = ADRChecker._num_tokens_from_adr(adr_text)
        logger.info(f"Classifying ADR with {count_tokens} tokens.")
        if (self.llm.max_tokens is not None) and (count_tokens > self.llm.max_tokens):
            logger.warning("The ADR text exceeds the token limit for the model and may be truncated.")
        
        sections = get_adr_sections_metadata()
        all_section_results = []
        for s, description in sections.items(): # Invoke the chain for each section
            section_result = self.section_wise_consistency_chain.invoke(
                {'adr_input': adr_text, 'section_name': s, 'section_purpose': description})
            all_section_results.append(section_result)

        result = ADRConsistecySections(section_assessments=all_section_results)    
        if as_dict:
            json_string = result.model_dump_json()
            result = json.loads(json_string)
            if metadata is not None:
                result['metadata'] = metadata
            return result
        else:
            return result

    def check_sections_batch(self, adr_texts: Dict[str,str], organization=None, project=None, as_dict=True, parallel=False, json_file=None) -> List[Dict]:
        # Note that it runs in parallel using ThreadPoolExecutor
        results = []
        if parallel:
            # logging.disable()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = executor.map(lambda adr: self.check_sections(adr, as_dict=as_dict), adr_texts.values())
            results = list(results)
        else:
            # Use tqdm
            for adr in tqdm(adr_texts, desc="Classifying ADRs"):
                results.append(self.check_sections(adr, as_dict=as_dict))
        
        # Add metadata of the ADR (name, project, organization), if provided
        if as_dict and organization is not None and project is not None:
                results = [{**res, 'metadata': {'organization': organization, 'project': project, 'adr_key': adr_key}} for res, adr_key in zip(results, adr_texts.keys())]
   
        if (json_file is not None) and as_dict and (len(results) > 0):
            ADRChecker.save_results(results, json_file)
        return results
    
    def check(self, adr_text: str, as_dict=True, metadata=None) -> Dict:
        sections_result = self.check_sections(adr_text, as_dict=False)    
        adherence_result = self.check_madr_adherence(adr_text, as_dict=False)  

        result = ADRAssessmentReport(section_assessments=sections_result.section_assessments, template_adherence=adherence_result)    
        if as_dict:
            json_string = result.model_dump_json()
            result = json.loads(json_string)
            if metadata is not None:
                result['metadata'] = metadata
            return result
        else:
            return result
    
    def check_batch(self, adr_texts: Dict[str,str], organization=None, project=None, as_dict=True, parallel=False, json_file=None) -> List[Dict]:
        # Note that it runs in parallel using ThreadPoolExecutor
        results = []
        if parallel:
            # logging.disable()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = executor.map(lambda adr: self.check(adr, as_dict=as_dict), adr_texts.values())
            results = list(results)
        else:
            # Use tqdm
            for adr in tqdm(adr_texts, desc="Classifying ADRs"):
                results.append(self.check(adr, as_dict=as_dict))
        
        # Add metadata of the ADR (name, project, organization), if provided
        if as_dict and organization is not None and project is not None:
                results = [{**res, 'metadata': {'organization': organization, 'project': project, 'adr_key': adr_key}} for res, adr_key in zip(results, adr_texts.keys())]
   
        if (json_file is not None) and as_dict and (len(results) > 0):
            ADRChecker.save_results(results, json_file)
        return results
        

    @staticmethod
    def save_results(classifications: List[Dict], json_file: str):
        # Open the file and write the data
        try:
            with open(json_file, 'w') as json_file:
                json.dump(classifications, json_file, indent=4) # The indent=4 makes the file easy to read
        except IOError as e:
            print(f"Error saving file: {e}")
        logger.info(f"Classifications saved to {json_file}")