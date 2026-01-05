import pandas as pd
import tiktoken

from tqdm.notebook import tqdm

from pydantic import BaseModel, Field
import json

from enum import Enum

from pythonjsonlogger.json import JsonFormatter

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from typing import Literal, Dict, List, Tuple, Any
import logging
import sys
import numpy as np

import concurrent.futures

from collections import Counter

from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import cohen_kappa_score
from sklearn.metrics import matthews_corrcoef

import numpy as np
from sklearn.preprocessing import LabelBinarizer

import seaborn as sns # Optional: for a visual heatmap
import matplotlib.pyplot as plt # Optional: for plotting

# from adr import adr
from prompts import get_classification_prompts
import utils

from custom_selector import CustomExampleSelector, get_base_selector


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = JsonFormatter(fmt='%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler = logging.StreamHandler(sys.stdout)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)


class ClassificationFramework(str, Enum):
    KRUCHTEN = "kruchten"
    QUALITY_ATTRIBUTES = "quality_attributes"
    ZIMMERMANN = "zimmermann"

class KruchtenEnum(str, Enum):
    EXISTENCE = "Existence (ontocrisis)"
    BAN = "Ban/Non-Existence (anticrisis)"
    PROPERTY = "Property (diacrisis)"
    EXECUTIVE = "Executive (pericrisis)"

class KruchtenClassificationResult(BaseModel):
    framework: Literal[ClassificationFramework.KRUCHTEN] = Field(ClassificationFramework.KRUCHTEN, description="The classification framework used.")
    primary_category: KruchtenEnum = Field(..., description="The closest or more appropriate category for the ADR.")
    explanation: str = Field(..., description="A brief rationale for choosing the primary category.")
    primary_score: float = Field(..., description="Confidence score for the primary category (value between 0.0 and 1.0).")
    alternative_categories: List[KruchtenEnum] = Field(..., description="A list of alternative categories considered suitable for the ADR, in addition to the category chosen as primary. Do not include the primary category here.")
    alternative_confidence_scores: List[float] = Field(..., description="A list of confidence scores for each alternative category (values between 0.0 and 1.0). Sum of all scores (primary + alternatives) should equal 1.0. Length of list of scores must be equal to length of list of alternative categories.")

class QualityAttributesEnum(str, Enum):
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
    framework: Literal[ClassificationFramework.QUALITY_ATTRIBUTES] = Field(ClassificationFramework.QUALITY_ATTRIBUTES, description="The classification framework used.")
    primary_category: QualityAttributesEnum = Field(..., description="The closest or more appropriate category for the ADR.")
    explanation: str = Field(..., description="A brief rationale for choosing the primary category.")
    primary_score: float = Field(..., description="Confidence score for the primary category (value between 0.0 and 1.0).")
    alternative_categories: List[QualityAttributesEnum] = Field(..., description="A list of alternative categories considered suitable for the ADR, in addition to the category chosen as primary. Do not include the primary category here.")
    alternative_confidence_scores: List[float] = Field(..., description="A list of confidence scores for each alternative category (values between 0.0 and 1.0). Sum of all scores (primary + alternatives) should equal 1.0. Length of list of scores must be equal to length of list of alternative categories.")

class ZimmermannEnum(str, Enum):
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
    framework: Literal[ClassificationFramework.ZIMMERMANN] = Field(ClassificationFramework.ZIMMERMANN, description="The classification framework used.")
    primary_category: ZimmermannEnum = Field(..., description="The closest or more appropriate category for the ADR.")
    explanation: str = Field(..., description="A brief rationale for choosing the primary category.")
    primary_score: float = Field(..., description="Confidence score for the primary category (value between 0.0 and 1.0).")
    alternative_categories: List[ZimmermannEnum] = Field(..., description="A list of alternative categories considered suitable for the ADR, in addition to the category chosen as primary. Do not include the primary category here.")
    alternative_confidence_scores: List[float] = Field(..., description="A list of confidence scores for each alternative category (values between 0.0 and 1.0). Sum of all scores (primary + alternatives) should equal 1.0. Length of list of scores must be equal to length of list of alternative categories.")


class ADRClassifier:

    SYSTEM_TEMPLATE = "You are a software architecture expert that has to analyze Architectural Decision Records (ADRs) and classify them based on a specific framework or ontology for decision types."

    def __init__(self, llm: ChatOpenAI, model_name: str = "gpt-4o-mini", temperature: float = 0.0, max_tokens: int = None):
        self.llm = llm or ChatOpenAI(model_name=model_name, temperature=temperature, max_tokens=max_tokens)
        self.classification_prompt = None
        self.qa_chain = None
        self.prompt_template = None
        # Note: this is a workaround for now
        self.backup_classification_prompt = None
        self.backup_chain = None
    
    @staticmethod
    def _num_tokens_from_adr(string: str, encoding_name: str ="cl100k_base") -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    @staticmethod
    def _configure_chain(framework: ClassificationFramework, classification_prompt: ChatPromptTemplate, llm: ChatOpenAI):
        if framework == ClassificationFramework.KRUCHTEN:
            return classification_prompt | llm.with_structured_output(KruchtenClassificationResult)
        elif framework == ClassificationFramework.QUALITY_ATTRIBUTES:
            return classification_prompt | llm.with_structured_output(QualityAttributeClassificationResult)
        elif framework == ClassificationFramework.ZIMMERMANN:
            return classification_prompt | llm.with_structured_output(ZimmermannClassificationResult)

        return None
    
    def set_framework(self, framework: ClassificationFramework, include_examples: bool = True, examples: List[Any] = None, k: int = 7):
        
        # TODO: If examples is not None/empty, consider using dyanmic few-shots (from sample of ground truth)
        # and also configure an appropriate chain

        self.prompt_template = None
        dynamic_few_shots = False
        self.backup_classification_prompt = None
        self.backup_chain = None
        if not include_examples: # Zero-shot
            self.prompt_template = get_classification_prompts(False).get(framework.value, None)
        if include_examples and examples is None: # Static few-shots
            self.prompt_template = get_classification_prompts(True).get(framework.value, None)
        if include_examples and (examples is not None) and len(examples) > 0: # Dynamic few-shots
            self.prompt_template = get_classification_prompts(False).get(framework.value, None)
            dynamic_few_shots = True

        # print(prompt_template)
        logger.info(f"Using classification framework: {framework.value}, include_examples={include_examples}")
        if self.prompt_template is None:
            logger.warning(f"Unsupported classification framework: {framework}")
            return
        
        # Create the classification prompt
        prompt_str = self.prompt_template # ADRClassifier.SYSTEM_TEMPLATE+"\n\n"+self.prompt_template
        if not dynamic_few_shots:
            self.classification_prompt = ChatPromptTemplate.from_messages(
                    [
                        ("system", prompt_str),
                        # ("human", self.prompt_template),
                        ("human", "{adr}"),
                    ]
            )
        else: # Dynamic few-shots with a custom selector
            base_selector = get_base_selector(examples, base='max-marginal-relevance', k=15*k) #base='max-marginal-relevance') base='semantic-similarity'
            example_selector = CustomExampleSelector.from_selector(k=k, selector=base_selector) #, class_variety=True)
            self.classification_prompt = example_selector.make_prompt_template(prompt_str, template_format='jinja2')
            self.backup_classification_prompt = example_selector.make_prompt_template(prompt_str, template_format='f-string')
        
        # Use always the same chain
        self.qa_chain = ADRClassifier._configure_chain(framework, self.classification_prompt, self.llm)
        if self.backup_classification_prompt is not None:
            self.backup_chain = ADRClassifier._configure_chain(framework, self.backup_classification_prompt, self.llm)
        if self.qa_chain is None:
            logger.error(f"Failed to configure chain for framework: {framework}")
        
    def classify(self, adr_text: str, as_dict=True, metadata=None) -> Dict:
        if self.qa_chain is None:
            logger.error("Classification chain is not configured. Please set the framework first.")
            return None
        
        count_tokens = ADRClassifier._num_tokens_from_adr(adr_text)
        logger.info(f"Classifying ADR with {count_tokens} tokens.")
        if (self.llm.max_tokens is not None) and (count_tokens > self.llm.max_tokens):
            logger.warning("The ADR text exceeds the token limit for the model and may be truncated.")
        
        if self.backup_chain is not None: # It's dynamic few-shots
            adr_text = adr_text.replace('.', '\\.')
        # result = self.qa_chain.invoke(input=adr_text)
        result = None
        error = False
        msg = metadata if metadata is not None else adr_text
        try:
            result = self.qa_chain.invoke({'adr': adr_text})
        except Exception as ex: # (jinja2.exceptions.TemplateSyntaxError, KeyError) as ex: # jinja2.exceptions.TemplateSyntaxError
            # print(ex)
            logging.warning(f"A parsing error occurred (using f-string formatting instead): {msg}") #, exc_info=True)
            try:
                result = self.backup_chain.invoke({'adr': adr_text})
            except Exception as ex:
                logging.error(f"Another parsing error occurred with fallback, skipping ADR: {msg}") #, exc_info=True)
                error = True
        
        if error:
            return None

        if as_dict:
            json_string = result.model_dump_json()
            result = json.loads(json_string)
            if metadata is not None:
                result['metadata'] = metadata
            return result
        else:
            return result

    def classify_batch(self, adr_texts: Dict[str,str], organization=None, project=None, as_dict=True, parallel=False, json_file=None) -> List[Dict]:
        # Note that it runs in parallel using ThreadPoolExecutor
        results = []
        keys_removed = []
        skipped = 0
        if parallel:
            # logging.disable()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results1 = executor.map(lambda adr_key, adr_text: self.classify(adr_text, as_dict=as_dict, metadata={'adr': adr_key}), adr_texts.keys(), adr_texts.values())
            for adr_key, r in zip(adr_texts.keys(), results1): # The results1 generator is emptied, once traversed
                if r is not None:
                    results.append(r)
                else:
                    keys_removed.append(adr_key)
                    skipped += 1
        else:
            # Use tqdm
            for adr_key, adr_text in tqdm(adr_texts.items(), desc="Classifying ADRs"):
                r = self.classify(adr_text, as_dict=as_dict, metadata={'adr': adr_key})
                if r is not None:
                    results.append(r)
                else:
                    keys_removed.append(adr_key)
                    skipped += 1
        if skipped > 0:
            logger.warning(f"{skipped} ADRs were skipped due to parsing problems. {keys_removed}")

        # Add metadata of the ADR (name, project, organization), if provided
        if as_dict and organization is not None and project is not None:
            adr_keys = [item for item in adr_texts.keys() if item not in keys_removed]
            results = [{**res, 'metadata': {'organization': organization, 'project': project, 'adr_key': adr_key}} for res, adr_key in zip(results, adr_keys)]
   
        if (json_file is not None) and as_dict and (len(results) > 0):
            ADRClassifier.save_results(results, json_file)
        return results
    
    def evaluate_on_ground_truth(self, ground_truth: pd.DataFrame, llm_results: List, max_labels=None,
                adr_key_column: str = 'ADR', adr_text_column: str = 'raw_text', true_label_column: str = 'human') -> Dict:
        # ground_truth is a DataFrame with columns: 
        # 'text': adr_text
        # 'ADR': adr_key
        # 'Organization-Project': 'org-project' tuple
        # 'human': true label
        
        gt_df = ground_truth.dropna(subset=[adr_text_column, true_label_column, adr_key_column])
        if gt_df.shape[0] < ground_truth.shape[0]:
            logger.warning(f"Dropping {ground_truth.shape[0] - gt_df.shape[0]} rows with missing text or human label.")
        
        n_rows = gt_df.shape[0]
        adr_keys = gt_df[adr_key_column].tolist()
        llm_keys = [item['metadata'][adr_key_column.lower()] for item in llm_results if ('metadata' in item) and (adr_key_column.lower() in item['metadata'])]
        rows_to_remove = [key for key in adr_keys if key not in llm_keys]
        gt_df = gt_df[~gt_df[adr_key_column].isin(rows_to_remove)]
        if gt_df.shape[0] < n_rows:
            logger.warning(f"Dropping {n_rows - gt_df.shape[0]} as they are not part of the LLM results. {rows_to_remove}")

        y_true = gt_df[true_label_column].tolist()
        n_labels = len(set(y_true)) 
        if (max_labels is not None) and (n_labels > max_labels):
            logger.warning(f"Number of unique labels in ground truth ({n_labels}) exceeds max_labels ({max_labels}).")
        
        y_pred = [res['primary_category'] for res in llm_results]
        adr_pred = [res['metadata']['adr'] if 'metadata' in res else None for res in llm_results]
        for y in y_pred:
            if y not in y_true:
                logger.warning(f"Predicted label '{y}' not in ground truth labels.")
        
        labels = list(set(y_true).union(set(y_pred)))
        le = LabelEncoder()
        encoding = le.fit_transform(labels)
        y_pred1 = le.transform(y_pred)
        y_true1 = le.transform(y_true)

        report = classification_report(y_true1, y_pred1, labels=encoding, target_names=le.classes_, output_dict=True)
        cm = confusion_matrix(y_true1, y_pred1) #, labels=encoding)
        cm_df = pd.DataFrame(cm, index=le.classes_, columns=le.classes_) #, index=labels, columns=labels)

        kappa = cohen_kappa_score(y_true1, y_pred1)
        kappa_scores_per_class = ADRClassifier.compute_kappa_per_class(y_true1, y_pred1)
        kappa_scores_per_class = {le.inverse_transform([int(idx)])[0]:k for idx,k in kappa_scores_per_class.items()}
        similarities = ADRClassifier.count_similarities(y_true1, y_pred1)
        differences = ADRClassifier.find_differences(y_true, y_pred, adr_pred)
        mcoeff = matthews_corrcoef(y_true1, y_pred1)

        return {
            "report": report,
            "confusion_matrix": cm_df,
            "matthews": mcoeff,
            "kappa": kappa,
            "kappa_scores": kappa_scores_per_class,
            "similarities": similarities,
            "differences": differences, 
            "labels": labels
        }

    def predict_and_evaluate_on_ground_truth(self, ground_truth: pd.DataFrame, parallel: bool = True, max_labels=None,
                adr_key_column: str = 'ADR', adr_text_column: str = 'raw_text', true_label_column: str = 'human') -> Dict:
        # ground_truth is a DataFrame with columns: 
        # 'text': adr_text
        # 'ADR': adr_key
        # 'Organization-Project': 'org-project' tuple
        # 'human': true label

        gt_df = ground_truth.dropna(subset=[adr_text_column, true_label_column, adr_key_column])
        if len(gt_df) < len(ground_truth):
            logger.warning(f"Dropping {len(ground_truth) - len(gt_df)} rows with missing text or human label.")

        # Call LLM classifier
        adr_texts = {row[adr_key_column]: row[adr_text_column] for _, row in gt_df.iterrows()}
        logger.info(f"Evaluating on ground truth with {len(adr_texts)} ADRs.")
        results = self.classify_batch(adr_texts, as_dict=True, parallel=parallel)

        output_dict = self.evaluate_on_ground_truth(ground_truth=gt_df, llm_results=results, max_labels=max_labels,
                adr_key_column=adr_key_column, adr_text_column=adr_text_column, true_label_column=true_label_column)

        output_dict['llm_results'] = results
        return output_dict

    
    @staticmethod
    def save_results(classifications: List[Dict], json_file: str):
        # Open the file and write the data
        try:
            with open(json_file, 'w') as json_file:
                json.dump(classifications, json_file, indent=4) # The indent=4 makes the file easy to read
        except IOError as e:
            print(f"Error saving file: {e}")
        logger.info(f"Classifications saved to {json_file}")

    @staticmethod
    def count_similarities(y_true, y_pred) -> float: # This doesn't account for random chance (as Kappa does)
        count_matches = 0
        for i in range(len(y_true)):
            if (i < len(y_pred)) and (y_true[i] == y_pred[i]):
                count_matches += 1
        return count_matches * 100.0 / len(y_pred)

    @staticmethod
    def find_differences(y_true, y_pred, adr_pred) -> list[tuple[int, str]]: # 
        differences = []
        for i in range(len(y_true)):
            if (i < len(y_pred)):
                if y_true[i] != y_pred[i]: # This is a difference
                    differences.append((i, y_true[i], y_pred[i], adr_pred[i]))

        return differences
    
    @staticmethod
    def rank_differences(differences: list[tuple], n_categories: int):
        all_pairs = []
        for _, y_true, y_pred, _ in differences:
            all_pairs.append((y_true, y_pred))
        counts = Counter(all_pairs)
        most_common_differences = counts.most_common(n_categories)
        return most_common_differences

    @staticmethod
    def compute_kappa_per_class(y_true, y_pred, labels=None) -> dict[str, float]:
        """
        Calculates the Cohen's kappa score for each class individually.

        Args:
            y_true (array-like): True labels.
            y_pred (array-like): Predicted labels.
            labels (list, optional): List of labels to index the matrix. 
                                    If None, all labels in y_true or y_pred are used.

        Returns:
            dict: A dictionary with class labels as keys and their 
                corresponding kappa scores as values.
        """

        if labels is None:
            # Get all unique labels present in both true and predicted values
            all_labels = sorted(list(set(y_true) | set(y_pred)))
        else:
            all_labels = labels
        
        kappa_scores = {}
        
        # Use LabelBinarizer to convert multi-class labels to binary (one-vs-rest)
        lb = LabelBinarizer()
        lb.fit(np.array(all_labels)) # Fit on all labels to ensure consistency

        y_true_bin = lb.transform(y_true)
        y_pred_bin = lb.transform(y_pred)
        
        # Adjust for single-class cases if necessary (LabelBinarizer output shape)
        if len(all_labels) == 1:
            y_true_bin = y_true_bin.flatten()
            y_pred_bin = y_pred_bin.flatten()

        for i, label in enumerate(all_labels):
            # Extract binary true and predicted values for the current class
            if len(all_labels) > 1:
                y_true_class = y_true_bin[:, i]
                y_pred_class = y_pred_bin[:, i]
            else:
                y_true_class = y_true_bin
                y_pred_class = y_pred_bin
                
            # Calculate kappa for the binary case (current class vs rest)
            # Handle potential edge cases (e.g., if a class is completely absent in true labels, kappa is undefined)
            try:
                kappa = cohen_kappa_score(y_true_class, y_pred_class)
                kappa_scores[label] = kappa
            except ValueError:
                kappa_scores[label] = np.nan # or some indicator that it couldn't be calculated

        return kappa_scores


# Filter specific cases of differences with GT
# true_categories = ['Other/Only Functional Concern', 'Maintainability']
# pred_categories = ['Other/Only Functional Concern', 'Maintainability']

# print(10*'--')
# for idx, cat_true, cat_pred, adr in output_dict['differences']:
#     if cat_true in true_categories and cat_pred in pred_categories:
#         print(cat_true, "vs.", cat_pred, "->", idx, adr)
#         print(10*'--')


