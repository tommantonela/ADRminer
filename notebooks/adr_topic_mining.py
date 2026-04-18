
import pandas as pd
import json
from tqdm import tqdm
import numpy as np
import os
import sys

import logging

from pythonjsonlogger.json import JsonFormatter

from wordcloud import WordCloud
import matplotlib.pyplot as plt
from itertools import combinations

from pydantic import BaseModel, Field

from typing import Dict, List

import utils

from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired
from sklearn.feature_extraction.text import CountVectorizer
from bertopic.backend._sentencetransformers import SentenceTransformerBackend
from sentence_transformers import SentenceTransformer
from umap import UMAP

from bertopic.representation import OpenAI
import openai
import tiktoken

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# formatter = JsonFormatter(fmt='%(asctime)s %(levelname)s %(name)s %(message)s')
# logHandler = logging.StreamHandler(sys.stdout)
# logHandler.setFormatter(formatter)
# logger.addHandler(logHandler)


class TopicResult(BaseModel):
    text: str = Field("Original (corpus) text for the ADR.")
    topics: List[int] = Field(..., description="A list of inferred topic ids for a text (ADR).")
    keywords: List[List[str]] = Field(..., description="A list of lists of keywords, each list characterizing the text and corresponding topic.")
    keybert_representation: List[str] = Field(..., description="A list of topic labels according to the KeyBERT representation of the text.")
    openai_representation: List[str] = Field(..., description="A list of topic labels according to the OpenAI representation of the text.")
    probabilities: List[float] = Field(..., description="A list of topic probabilities.")


class ADRTopicModel:

    DEFAULT_PROMPT = """"
    You are an assistant for a software developer that needs to analyze documents containing architectural design decisions.
    In this context, I have a software-related topic that affects the following documents:
    [DOCUMENTS]

    The topic is described by the following keywords: '[KEYWORDS]'.

    Based on the above information, can you assign a descriptive label of at most 7 words to the topic?
    Answer:
    """

    def __init__(self):
        self.dict_adrs = {}
        self.adr_texts = []
        self.corpus = None
        self.all_adr_keys = None
        self.topic_model = None
        self.embeddings = None
        self.topic_distribution = None
    

    def prepare_corpus(self, docs: dict=None):
        if docs is not None:
            self.dict_adrs = docs
        
        self.corpus, self.all_adr_keys = utils.prune_corpus(self.dict_adrs)
    
    def configure_representation(self, use_openai=False, prompt=None):

        representation_model1 = KeyBERTInspired()

        self.open_ai_representation = use_openai

        if use_openai:
            # Tokenizer
            tokenizer= tiktoken.get_encoding("o200k_base") 
            # tokenizer= tiktoken.encoding_for_model(os.environ["OPENAI_MODEL_NAME"])

            if prompt is None:
                prompt = ADRTopicModel.DEFAULT_PROMPT

            # Create your representation model
            self.client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            representation_model2 = OpenAI(
                self.client,
                model=os.environ["OPENAI_MODEL_NAME"], 
                delay_in_seconds=2, 
                chat=True,
                nr_docs=4,
                doc_length=100,
                tokenizer=tokenizer,
                prompt=prompt
            )
        
        if not use_openai:
            self.representation_model = {
                "Main": representation_model1, # KeyBERT
            }
        else:
            self.representation_model = {
                "Main": representation_model1, # KeyBERT
                "OpenAI": representation_model2 # OpenAI-based
            }

    def configure_embeddings(self, language='english', predefined_embedding_model='all-MiniLM-L6-v2', metric='cosine'):
        self.vectorizer_model = CountVectorizer(stop_words=language)

        # Pre-calculate embeddings
        self.embedding_model = SentenceTransformer(predefined_embedding_model)
        self.embeddings = None

        self.umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric=metric, random_state=42)

    def build(self, n_topics=None, use_openai=True, prompt=None) -> pd.DataFrame:

        logger.info("Creating new topic model...")
        self.configure_representation(use_openai=use_openai, prompt=prompt)
        self.configure_embeddings()
        
        self.topic_model = BERTopic(embedding_model=self.embedding_model, 
                        umap_model=self.umap_model,
                        representation_model=self.representation_model,
                        vectorizer_model=self.vectorizer_model,
                        nr_topics='auto', # It tries to find a reduced number of topics
                        verbose=True)
        
        logger.info("Fitting topic model to corpus...")
        self.topics = self.topic_model.fit_transform(self.corpus) # This takes around 5 minutes
        n = len(self.topic_model.get_topics())
        logger.info("Topics:", n)
        self.topic_distribution = None

        # Further reduce topics. Only if we want to give a specific number of topics
        if n_topics is not None:
            logger.info("Reducing topics to:", n_topics)
            self.topic_model.reduce_topics(self.corpus, nr_topics=n_topics)
            n = len(self.topic_model.get_topics())
            logger.info("Reduced topics:", n)
        
        self.topics_df = self.topic_model.get_topic_info()

        if use_openai:
            self.openai_topics = [x[0].strip('"') for x in self.topics_df['OpenAI'].tolist()]
            self.topic_model.set_topic_labels(topic_labels=self.openai_topics)

        return self.topics_df

    def load(self, folder: str, predefined_embedding_model='all-MiniLM-L6-v2', corpus_file: str='corpus.json') -> pd.DataFrame | None:
        if os.path.exists(folder):
            logger.info("Loading existing topic model...")
            self.topic_distribution = None
            self.configure_embeddings()
            
            # Retrieve corpus
            relative_path = os.path.join(folder, corpus_file)
            try:
                with open(relative_path, 'r') as f:
                    self.corpus = json.load(f)
                logger.info(f"Successfully loaded data from {relative_path}")
                # print(f"Loaded data: {loaded_data}")
            except FileNotFoundError:
                logger.error(f"{relative_path} not found.")
            except json.JSONDecodeError:
                logger.error(f"Could not decode JSON from {relative_path}.")

            embedding_model_st = SentenceTransformerBackend(predefined_embedding_model) 
            loaded_model = BERTopic.load(folder, embedding_model=embedding_model_st) #embedding_model_openai)
            self.topic_model = loaded_model
            n = len(self.topic_model.get_topics())
            logger.info("Topics:", n)
            self.topics_df = self.topic_model.get_topic_info()
            if 'OpenAI' in self.topics_df.columns:
                self.open_ai_representation = True
                self.openai_topics = [x[0].strip('"') for x in self.topics_df['OpenAI'].tolist()]
                self.topic_model.set_topic_labels(topic_labels=self.openai_topics)
            else:
                self.open_ai_representation = False

            return self.topics_df
        else:
            logger.error("Topic model folder does not exist (no topic model was created):", folder)
            return None


    def persist(self, folder: str, dataframe_file: str='topics_dataframe.csv', corpus_file: str='corpus.json'):
        if not os.path.exists(folder):
            os.makedirs(folder)

        logger.info(f"Saving newly-created topic model... {folder}")
        self.topic_model.save(folder, serialization="safetensors", save_ctfidf=True, save_embedding_model=self.embedding_model)
        
        relative_path = os.path.join(folder, dataframe_file)
        self.topics_df.to_pickle(relative_path.replace('.csv', '.pickle'))
        
        # Persist corpus as a JSON file
        relative_path = os.path.join(folder, corpus_file)
        try:
            with open(relative_path, 'w') as f:
                json.dump(self.corpus, f)
            logger.info(f"Successfully wrote corpus to {relative_path}")
        except IOError as e:
            logger.error(f"Error writing to file: {e}")
        
    
    def get_topk_topics(self, k: int=20) -> pd.DataFrame:
        top20_topics = self.topics_df.sort_values(by="Count", ascending=False).reset_index(drop=True).head(k) # Top 20 topics
        return top20_topics
    
    def get_topic_labels(self, representation='Main') -> list[str]:
        if representation == 'Main' or not self.open_ai_representation:
            return list(self.topic_model.topic_labels_.values())
        elif representation == 'OpenAI' and self.open_ai_representation:
            return self.openai_topics
        else:
            logger.warning("Unknown representation for topic labels:", representation)
            return []
    
    def show_topic_map(self, k: int=20, suppress_title=False, recompute_embeddings=False):
        if (self.embeddings is None) or recompute_embeddings:
            self.embeddings = self.embedding_model.encode(self.corpus, show_progress_bar=True)

        first_20_topics = list(range(-1,k))
        n_adrs = len(self.corpus)
        n_topics = len(self.topic_model.get_topics())
        title =  "Top-{} Topics in ADRs (ADRs: {} - Topics: {})".format(k, n_adrs, n_topics) if not suppress_title else None
        fig = self.topic_model.visualize_document_datamap(self.corpus, embeddings=self.embeddings, custom_labels=True, topic_prefix=True, topics=first_20_topics,
                                            title=title, #"Top-20 Topics in ADRs (ADRs: {} - Topics: {})".format(n_adrs, n_topics), 
                                            datamap_kwds={"label_over_points": True,  
                                                            #"label_font_size": 11,
                                                            "dynamic_label_size": True, "max_font_size": 18, "min_font_size": 9
                                                            })   

    def show_wordcloud(self, topic_id, max_words=1000):
        text = {word: value for word, value in self.topic_model.get_topic(topic_id)}
        wc = WordCloud(background_color="white", max_words=max_words)
        wc.generate_from_frequencies(text)
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        plt.show()    
    
    def get_relevant_documents_for_topic(topic_id, threshold=0.5, recompute_distribution=False):
        """
        Get the most relevant documents for a given topic.
        :param topic_model: BERTopic model
        :param corpus: list of documents
        :param topic_id: topic id
        :param n: number of documents to return
        :return: list of tuples (document, probability)
        """  
        if (self.topic_distribution is None) or recompute_distribution:
            self.topic_distribution, _ = self.topic_model.approximate_distribution(self.corpus)
        
        # Get the probabilities of the topic in each document
        topic_probabilities = self.topic_distribution[:, topic_id]

        # Identify documents where the topic has a significant probability (e.g., > 0.1)
        affected_documents = [(doc_idx, prob) for doc_idx, prob in enumerate(topic_probabilities) if prob > threshold]
        # Order by probability
        affected_documents = sorted(affected_documents, key=lambda x: x[1], reverse=True)

        return affected_documents
    
    def get_topic_words(self, topic_id, threshold=0.3) -> List[str]:
        list_keywords = self.topic_model.get_topic(topic_id) if topic_id != -1 else []
        # print("list_keywords:", list_keywords)
        return [x[0] for x in list_keywords if x[1] >= threshold]
    
    def get_topics_probabilities_per_document(self, doc: str, threshold=0.0):
        probabilities = self.topic_model.approximate_distribution([doc])
        document_probabilities = probabilities[0][0]

        topic_info_df = self.topic_model.get_topic_info()
        # Filter out the outlier topic (-1)
        valid_topics = topic_info_df[topic_info_df['Topic'] != -1]
        topic_ids = valid_topics['Topic'].tolist()
        
        new_topics = []
        new_probs = []
        for topic_id, prob in zip(topic_ids, document_probabilities):
            if prob > threshold:
                new_topics.append(topic_id)
                new_probs.append(prob)

        return new_topics, new_probs


    def predict(self, adr_text: str, as_dict=True, metadata=None, multiple_topics=False) -> Dict:

        if multiple_topics:
            new_topics, new_probs = self.get_topics_probabilities_per_document(adr_text)
        else:
            new_topics, new_probs = self.topic_model.transform(adr_text)
            if not isinstance(new_topics, list):
                new_topics = new_topics.tolist()
            if not isinstance(new_probs, list):
                new_probs = new_probs.tolist()
        
        all_keybert_labels = list(self.topic_model.topic_labels_.values())
        keybert_labels = [all_keybert_labels[t] for t in new_topics]
        keywords = [self.get_topic_words(t, threshold=0.0) for t in new_topics]
        
        openai_labels = []
        if self.open_ai_representation:
            openai_labels = [self.openai_topics[t] for t in new_topics]

        result = TopicResult(text=adr_text, topics=new_topics, keywords=keywords, keybert_representation=keybert_labels, openai_representation=openai_labels, probabilities=new_probs)    
        if as_dict:
            json_string = result.model_dump_json()
            result = json.loads(json_string)
            if metadata is not None:
                result['metadata'] = metadata
            return result
        else:
            return result
    
    def predict_batch(self, adr_texts: Dict[str,str], organization=None, project=None, as_dict=True, json_file=None, multiple_topics=False) -> List[Dict]:
        
        if multiple_topics:
            new_topics = []
            new_probs = []
            for adr in adr_texts.keys():
                nt, np = self.get_topics_probabilities_per_document(adr_texts[adr])
                new_topics.append(nt)
                new_probs.append(np)
        else:
            new_topics, new_probs = self.topic_model.transform(list(adr_texts.values()))
            if not isinstance(new_topics, list):
                new_topics = new_topics.tolist()
            if not isinstance(new_probs, list):
                new_probs = new_probs.tolist()

        results = []
        all_keybert_labels = list(self.topic_model.topic_labels_.values())
        for adr, topics, probs in tqdm(zip(adr_texts.keys(), new_topics, new_probs), desc="Inferring topics for ADRs"):
            if isinstance(topics, list):
                keybert_labels = [all_keybert_labels[t] for t in topics]
                keywords = [self.get_topic_words(t, threshold=0.0) for t in topics]
                if self.open_ai_representation:
                    openai_labels = [self.openai_topics[t] for t in topics]
                topics_ = topics
                probs_ = probs
            else:
                keybert_labels = [all_keybert_labels[topics]]
                # print("keybert_labels", topics)
                keywords = [self.get_topic_words(topics, threshold=0.0)]
                openai_labels = []
                if self.open_ai_representation:
                    openai_labels = [self.openai_topics[topics]]  
                topics_ = [topics]   
                probs_ = [probs]
            
            result = TopicResult(text=adr_texts[adr], topics=topics_, keywords=keywords, keybert_representation=keybert_labels, openai_representation=openai_labels, probabilities=probs_)    
            if as_dict:
                json_string = result.model_dump_json()
                result = json.loads(json_string)
            results.append(result)
        
        # Add metadata of the ADR (name, project, organization), if provided
        if as_dict: 
            if organization is not None and project is not None:
                results = [{**res, 'metadata': {'organization': organization, 'project': project, 'adr_key': adr_key}} for res, adr_key in zip(results, adr_texts.keys())]
            else:
                results = [{**res, 'metadata': {'adr_key': adr_key}} for res, adr_key in zip(results, adr_texts.keys())]

        if (json_file is not None) and as_dict and (len(results) > 0):
            ADRTopicModel.save_results(results, json_file)
        
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
    
    def compute_topic_coherence(self, top_n=20) -> float:
        topics = self.topic_model.get_topics()
        if -1 in topics:
            del topics[-1]
        
        coherence_scores = []
        for topic_id in topics:
            words = [word for word, _ in topics[topic_id][:top_n]]
            embeddings = self.embedding_model.encode(words)
            
            # Compute pairwise cosine similarities
            sim_matrix = np.zeros((len(words), len(words)))
            for i in range(len(words)):
                for j in range(i+1, len(words)):
                    sim = np.dot(embeddings[i], embeddings[j]) / (
                        np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                    )
                    sim_matrix[i][j] = sim
            avg_sim = np.mean(sim_matrix[np.triu_indices(len(words), k=1)])
            coherence_scores.append(avg_sim) # Mean similarity for the topic
        
        return np.mean(coherence_scores) # Mean similarity for all topics

    def compute_topic_diversity(self, top_n=20) -> float:
        # Exclude outlier topic (-1) if present
        topics = self.topic_model.get_topics()
        if -1 in topics:
            del topics[-1]
        
        # Extract top words for each topic
        topic_words = [set([word for word, _ in topics[topic][:top_n]]) for topic in topics]
        
        # Compute pairwise Jaccard similarities
        jaccard_sims = []
        for t1, t2 in combinations(topic_words, 2):
            intersection = len(t1 & t2)
            union = len(t1 | t2)
            jaccard_sim = intersection / union if union != 0 else 0
            jaccard_sims.append(jaccard_sim)
        
        # Average similarity and compute diversity
        avg_sim = sum(jaccard_sims) / len(jaccard_sims)
        diversity = 1 - avg_sim
        return diversity