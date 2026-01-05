from typing import Any, List, Dict
from abc import ABC
from pydantic import BaseModel, ConfigDict
from langchain_core.documents import Document

from langchain_core.example_selectors import SemanticSimilarityExampleSelector, MaxMarginalRelevanceExampleSelector
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate
from langchain_core.example_selectors import BaseExampleSelector
# from langchain_core.example_selectors import _VectorStoreExampleSelector
from langchain_core.vectorstores import VectorStore
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.example_selectors import SemanticSimilarityExampleSelector, MaxMarginalRelevanceExampleSelector
from langchain_core.vectorstores import InMemoryVectorStore

import numpy as np

def sorted_values(values: dict[str, str]) -> list[Any]:
    """Return a list of values in dict sorted by key.

    Args:
        values: A dictionary with keys as input variables
            and values as their values.

    Returns:
        A list of values in dict sorted by key.
    """
    return [values[val] for val in sorted(values)]


class _VectorStoreExampleSelector(BaseExampleSelector, BaseModel, ABC):
    """Example selector that selects examples based on SemanticSimilarity."""

    vectorstore: VectorStore
    """VectorStore that contains information about examples."""
    k: int = 4
    """Number of examples to select."""
    example_keys: list[str] | None = None
    """Optional keys to filter examples to."""
    input_keys: list[str] | None = None
    """Optional keys to filter input to. If provided, the search is based on
    the input variables instead of all variables."""
    vectorstore_kwargs: dict[str, Any] | None = None
    """Extra arguments passed to similarity_search function of the `VectorStore`."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
    )

    @staticmethod
    def _example_to_text(example: dict[str, str], input_keys: list[str] | None) -> str:
        if input_keys:
            return " ".join(sorted_values({key: example[key] for key in input_keys}))
        return " ".join(sorted_values(example))

    def _documents_to_examples(self, documents: list[Document]) -> list[dict]:
        # Get the examples from the metadata.
        # This assumes that examples are stored in metadata.
        examples = [dict(e.metadata) for e in documents]
        # If example keys are provided, filter examples to those keys.
        if self.example_keys:
            examples = [{k: eg[k] for k in self.example_keys} for eg in examples]
        return examples

    def add_example(self, example: dict[str, str]) -> str:
        """Add a new example to vectorstore.

        Args:
            example: A dictionary with keys as input variables
                and values as their values.

        Returns:
            The ID of the added example.
        """
        ids = self.vectorstore.add_texts(
            [self._example_to_text(example, self.input_keys)], metadatas=[example]
        )
        return ids[0]

    async def aadd_example(self, example: dict[str, str]) -> str:
        """Async add new example to vectorstore.

        Args:
            example: A dictionary with keys as input variables
                and values as their values.

        Returns:
            The ID of the added example.
        """
        ids = await self.vectorstore.aadd_texts(
            [self._example_to_text(example, self.input_keys)], metadatas=[example]
        )
        return ids[0]
    
class CustomExampleSelector(_VectorStoreExampleSelector):
    
    selector: BaseExampleSelector | None = None
    embeddings_model: str = "all-MiniLM-L6-v2"
    embeddings: Embeddings = None
    k: int = 4
    class_variety: bool = False
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.embeddings = HuggingFaceEmbeddings(model_name=self.embeddings_model)
        # print("Initializing")
    
    def set_wrapper(self, selector: BaseExampleSelector):
        self.selector = selector
    
    @staticmethod
    def cosine_similarity(vec1, vec2) -> float:
        dot = np.dot(vec1, vec2)
        return dot / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def compute_similarity(self, s1: str, s2: str) -> float:
        emb1 = self.embeddings.embed_query(s1)
        emb2 = self.embeddings.embed_query(s2)
        similarity = CustomExampleSelector.cosine_similarity(emb1, emb2)
        return similarity
    
    def select_examples(self, input_variables: dict[str, str]) -> list[dict]:
        
        main_key = list(input_variables.keys())[0] # TODO: This only work for 1 single key!
        main_question = input_variables.get(main_key, None)
        examples = self.selector.select_examples(input_variables)
        
        # print("Wrapper!", main_key)
        # print("-"*10)
        # for e in examples:
        #     print(e)
        #     print(self.compute_similarity(main_question, e.get(main_key,"" )))
        #     print("-"*10)
        # Remove instances that are exactly the same as the posed question
        # filtered_examples = [e for e in examples if (main_question != e.get(main_key,None))]
        
        # TODO: This part is kind of hard-coded (key, threshold)
        filtered_examples = [e for e in examples if self.compute_similarity(main_question, e.get("adr","")) < 0.95]
        # print("First round of examples retrieved:", len(filtered_examples))
        
        # TODO: I need to select without repeated categories
        if self.class_variety:
            final_examples = []
            considered_classes = []
            for e in filtered_examples:
                cat = e.get("category", None)
                adr = e.get("adr", None)
                if (cat is not None) and not (cat in considered_classes):
                    considered_classes.append(cat)
                    if adr is not None:
                        final_examples.append(e)
            # print("Second round of examples:", len(final_examples), considered_classes)
        else:
            final_examples = filtered_examples
            
        if len(final_examples) > self.k:
            final_examples = final_examples[:self.k]
        
        return final_examples # Return top-k elements
    
    @staticmethod
    def _example_to_text(example: dict[str, str], input_keys: list[str] | None) -> str:
        if input_keys:
            return " ".join(sorted_values({key: example[key] for key in input_keys}))
        return " ".join(sorted_values(example))
    
    @classmethod
    def from_selector(
        cls,
        # examples: list[dict],
        # embeddings: Embeddings,
        # vectorstore_cls: type[VectorStore],
        k: int = 4,
        selector: BaseExampleSelector | None = None,
        class_variety: bool = False,
        # input_keys: list[str] | None = None,
        # *,
        # example_keys: list[str] | None = None,
        # vectorstore_kwargs: dict | None = None,
        # **vectorstore_cls_kwargs: Any,
    ) -> BaseExampleSelector:
        """Create k-shot example selector using example list and embeddings.

        Reshuffles examples dynamically based on query similarity.

        Args:
            examples: List of examples to use in the prompt.
            embeddings: An initialized embedding API interface, e.g. OpenAIEmbeddings().
            vectorstore_cls: A vector store DB interface class, e.g. FAISS.
            k: Number of examples to select.
            input_keys: If provided, the search is based on the input variables
                instead of all variables.
            example_keys: If provided, keys to filter examples to.
            vectorstore_kwargs: Extra arguments passed to similarity_search function
                of the `VectorStore`.
            vectorstore_cls_kwargs: optional kwargs containing url for vector store

        Returns:
            The ExampleSelector instantiated, backed by a vector store.
        """

        # string_examples = [cls._example_to_text(eg, input_keys) for eg in examples]
        # vectorstore = vectorstore_cls.from_texts(
        #     string_examples, embeddings, metadatas=examples, **vectorstore_cls_kwargs
        # )
        return cls(
            vectorstore=selector.vectorstore,
            k=k, # selector.k
            selector=selector,
            input_keys=selector.input_keys,
            example_keys=selector.example_keys,
            vectorstore_kwargs=selector.vectorstore_kwargs,
        )
    
    def make_prompt_template(self, prompt: str, template_format="jinja2") -> FewShotPromptTemplate:

        suffix = None
        if template_format == 'jinja2':
            suffix = "ADR to classify: {{adr}}"
        if template_format == 'f-string':
            suffix = "ADR to classify: {adr}"
    
        # Formatting of the examples
        example_prompt = PromptTemplate(
            input_variables=["adr", "category"],
            template="-----------------------------------------------\n* ADR: {adr}\n\n=> CATEGORY: {category}",
        )

        few_shot_prompt = FewShotPromptTemplate(
            example_selector=self,
            example_prompt=example_prompt,
            prefix= prompt + "\n\n## Examples:",
            suffix=suffix,
            input_variables=["adr"],
            template_format=template_format
        )

        return few_shot_prompt


def get_base_selector(examples: List[Dict], k=4, embeddings_model="all-MiniLM-L6-v2", base='max-marginal-relevance') -> MaxMarginalRelevanceExampleSelector:
    
    to_vectorize = [" ".join(example.values()) for example in examples]
    embeddings = HuggingFaceEmbeddings(model_name=embeddings_model)
    adrs_vectorstore = InMemoryVectorStore(embedding=embeddings).from_texts(
        to_vectorize, 
        embeddings, 
        metadatas=examples    
    )

    if base == 'max-marginal-relevance':
        example_selector = MaxMarginalRelevanceExampleSelector.from_examples(
            examples,
            embeddings,
            adrs_vectorstore,
            k=k,
        )
    elif base == 'semantic-similarity':
        example_selector = SemanticSimilarityExampleSelector.from_examples(
            examples,
            embeddings,
            adrs_vectorstore,
            k=k,
        )
    else:
        example_selector = None

    return example_selector