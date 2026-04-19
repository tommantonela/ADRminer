"""Topic mining service using BERTopic."""

import contextlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import hdbscan
import numpy as np
import pandas as pd
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired, OpenAI
from rich.console import Console
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP

from adrminer.config import Settings
from adrminer.models import get_llm
from adrminer.services.base import BaseService
from adrminer.services.adr_parser_service import ADRParserService

console = Console()


class TopicService(BaseService):
    """Service for topic mining using BERTopic."""
    
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        use_parser: bool = True,
        parser_config: Optional[Dict] = None,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize topic service.
        
        Args:
            model_path: Path to saved BERTopic model
            use_parser: Whether to use ADR parser for language detection (enabled by default)
            parser_config: Optional configuration for parser (strict, detect_language)
            settings: Settings instance
        """
        # Initialize base class
        super().__init__(settings)
        
        self.model_path = Path(model_path) if model_path else Path(self.settings.topic_model.path)
        self.model: Optional[BERTopic] = None
        self.use_llm_representation = self.settings.topic_model.use_llm_representation
        self._load_model()
        
        # Initialize parser if enabled (default for language detection)
        if use_parser:
            parser_config = parser_config or {"detect_language": True}
            self.parser = ADRParserService(**parser_config)
        else:
            self.parser = None
        
        # Initialize LLM if needed for topic naming
        if self.use_llm_representation:
            self.llm = get_llm(settings=settings)
        else:
            self.llm = None
    
    @staticmethod
    def _suppress_output():
        """Context manager to suppress stdout and stderr."""
        import sys
        
        class NullIO:
            """A file-like object that discards all writes."""
            def write(self, txt):
                pass
            def flush(self):
                pass
        
        null_io = NullIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        @contextlib.contextmanager
        def suppress():
            try:
                sys.stdout = null_io
                sys.stderr = null_io
                yield
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
        
        return suppress()
    
    def _load_model(self):
        """Load BERTopic model from disk."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Topic model not found at {self.model_path}. "
                "Please train a model first using 'adrminer train topics'."
            )
        
        try:
            # Use SentenceTransformerBackend from BERTopic (matching notebook approach)
            from bertopic.backend._sentencetransformers import SentenceTransformerBackend
            embedding_model_name = self.settings.topic_model.embedding_model
            embedding_model = SentenceTransformerBackend(embedding_model_name)
            
            self.model = BERTopic.load(self.model_path, embedding_model=embedding_model)
            
            # Verify model was loaded correctly
            if self.model is None:
                raise RuntimeError("Model loaded but is None")
                
        except Exception as e:
            # Fallback: try loading without embedding model
            self.logger.warning(f"Failed to load with embedding model: {e}. Trying without...")
            try:
                self.model = BERTopic.load(self.model_path)
                
                # Verify model was loaded correctly
                if self.model is None:
                    raise RuntimeError("Model loaded but is None")
                    
            except Exception as e2:
                raise RuntimeError(
                    f"Failed to load topic model from {self.model_path}. "
                    f"Original error: {e}. Fallback error: {e2}"
                )
        
        self.logger.info(f"Successfully loaded topic model from {self.model_path}")
    
    def predict(
        self,
        text: str,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Predict topics for a single ADR with language detection and warning.
        
        Args:
            text: ADR text content
            metadata: Optional metadata about the ADR
        
        Returns:
            Dictionary with topic prediction results
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        # Use parser for language detection if enabled
        if self.parser:
            try:
                parsed = self.parser.parse_adr(text)
                
                # Extract title and add to metadata
                if metadata is None:
                    metadata = {}
                metadata["title"] = parsed.title
                
                # Add language detection to metadata
                if parsed.language:
                    metadata["language"] = parsed.language
                    
                    # Warn if non-English (but don't skip)
                    if parsed.language != 'en':
                        self.logger.warning(
                            f"Non-English ADR detected (language='{parsed.language}'). "
                            f"Topic modeling may be less accurate. "
                            f"Consider training a topic model on ADRs in this language."
                        )
                
            except Exception as e:
                # Parser failed, but still process ADR
                if metadata is None:
                    metadata = {}
                self.logger.warning(f"Parser failed for language detection: {e}. Proceeding with topic modeling.")
        
        # Predict topic (suppress progress bar)
        with self._suppress_output():
            topics, probs = self.model.transform([text])
        topic_id = topics[0]
        probability = probs[0] if len(probs) > 0 else 0.0
        
        # Get topic info
        topic_info = self.model.get_topic_info(topic_id)
        topic_label = topic_info["Name"].iloc[0] if not topic_info.empty else f"Topic {topic_id}"
        
        # Get topic keywords
        if topic_id != -1:  # -1 is outlier topic
            words = self.model.get_topic(topic_id)
            keywords = [word for word, _ in words[:10]] if words else []
        else:
            keywords = []
        
        return {
            "topic_id": int(topic_id),
            "topic_label": topic_label,
            "probability": float(probability),
            "keywords": keywords,
            "metadata": metadata or {},
        }
    
    def predict_batch(
        self,
        texts: List[str],
        metadata_list: Optional[List[Dict]] = None,
        parallel: bool = True,
    ) -> List[Dict]:
        """
        Predict topics for multiple ADRs with language detection and warning.
        
        Args:
            texts: List of ADR text contents
            metadata_list: Optional list of metadata for each ADR
            parallel: Enable parallel processing
        
        Returns:
            List of topic prediction results
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        # Use parser for language detection if enabled
        if self.parser:
            non_english_count = 0
            for i, text in enumerate(texts):
                try:
                    parsed = self.parser.parse_adr(text)
                    
                    # Update metadata
                    if metadata_list is None or i >= len(metadata_list):
                        metadata_list = [{}] * len(texts)
                    
                    # Extract title
                    metadata_list[i]["title"] = parsed.title
                    
                    # Add language detection
                    if parsed.language:
                        metadata_list[i]["language"] = parsed.language
                        
                        # Count non-English ADRs
                        if parsed.language != 'en':
                            non_english_count += 1
                
                except Exception as e:
                    # Parser failed for this ADR, but still process it
                    if metadata_list is None or i >= len(metadata_list):
                        metadata_list = [{}] * len(texts)
                    self.logger.warning(f"Parser failed for ADR {i} language detection: {e}")
            
            # Warn if any non-English ADRs detected
            if non_english_count > 0:
                self.logger.warning(
                    f"Detected {non_english_count} non-English ADR(s) in batch. "
                    f"Topic modeling may be less accurate for these ADRs. "
                    f"Consider training a topic model on ADRs in these languages."
                )
        
        # Predict topics for all texts (suppress progress bar)
        with self._suppress_output():
            topics, probs = self.model.transform(texts)
        
        # Build results
        results = []
        for i, (topic_id, prob) in enumerate(zip(topics, probs)):
            topic_info = self.model.get_topic_info(topic_id)
            topic_label = topic_info["Name"].iloc[0] if not topic_info.empty else f"Topic {topic_id}"
            
            if topic_id != -1:
                words = self.model.get_topic(topic_id)
                keywords = [word for word, _ in words[:10]] if words else []
            else:
                keywords = []
            
            results.append({
                "topic_id": int(topic_id),
                "topic_label": topic_label,
                "probability": float(prob),
                "keywords": keywords,
                "metadata": metadata_list[i] if metadata_list and i < len(metadata_list) else {},
            })
        
        return results
    
    def get_topic_distribution(self, results: List[Dict]) -> Dict:
        """
        Get distribution of topics across results.
        
        Args:
            results: List of topic prediction results
        
        Returns:
            Dictionary with topic distribution statistics
        """
        # Count occurrences of each topic
        topic_counts = {}
        for result in results:
            topic_id = result["topic_id"]
            topic_label = result["topic_label"]
            
            if topic_label not in topic_counts:
                topic_counts[topic_label] = {
                    "count": 0,
                    "topic_id": topic_id,
                    "total_probability": 0.0,
                }
            
            topic_counts[topic_label]["count"] += 1
            topic_counts[topic_label]["total_probability"] += result["probability"]
        
        # Calculate statistics
        distribution = {}
        total = len(results)
        
        for topic_label, data in topic_counts.items():
            distribution[topic_label] = {
                "count": data["count"],
                "percentage": data["count"] / total if total > 0 else 0.0,
                "avg_probability": data["total_probability"] / data["count"],
            }
        
        return {
            "total_adrs": total,
            "unique_topics": len(distribution),
            "distribution": distribution,
        }
    
    def get_topic_info(self, topic_id: int) -> Dict:
        """
        Get detailed information about a topic.
        
        Args:
            topic_id: Topic ID
        
        Returns:
            Dictionary with topic information
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        topic_df = self.model.get_topic_info()
        topic_row = topic_df[topic_df["Topic"] == topic_id]
        
        if topic_row.empty:
            return {}
        
        # Get topic words
        if topic_id != -1:
            words = self.model.get_topic(topic_id)
            word_list = [(word, float(prob)) for word, prob in words]
        else:
            word_list = []
        
        # Get topic name
        keybert_name = str(topic_row["Name"].iloc[0])
        
        # Use LLM to generate human-readable name if enabled
        if self.use_llm_representation and self.llm is not None and topic_id != -1:
            llm_name = self._generate_llm_topic_name(topic_id, words[:10])
            display_name = llm_name if llm_name else keybert_name
        else:
            display_name = keybert_name
        
        return {
            "topic_id": int(topic_id),
            "name": display_name,
            "keybert_name": keybert_name,
            "count": int(topic_row["Count"].iloc[0]),
            "representation": word_list,
        }
    
    def _generate_llm_topic_name(self, topic_id: int, words: List) -> Optional[str]:
        """
        Generate a human-readable topic name using LLM.
        
        Args:
            topic_id: Topic ID
            words: List of (word, probability) tuples
        
        Returns:
            Generated topic name or None if generation fails
        
        Raises:
            FileNotFoundError: If prompt file doesn't exist and LLM naming is enabled
        """
        if not words:
            return None
        
        # Load prompt from external file
        topic_naming_prompt = self.load_prompt("topic_naming")
        
        # Handle case where prompt file wasn't found
        if topic_naming_prompt is None:
            raise FileNotFoundError(
                f"Prompt file not found: topic_naming.md in {self.prompts_dir}"
            )
        
        # Create prompt for topic naming
        keywords = ", ".join([word for word, _ in words])
        prompt = topic_naming_prompt.format(keywords=keywords)
        
        try:
            response = self.llm.invoke(prompt)
            llm_name = response.content.strip()
            
            # Clean up response
            if llm_name and len(llm_name) < 100:  # Sanity check
                return llm_name
        except Exception as e:
            print(f"Warning: Failed to generate LLM topic name for topic {topic_id}: {e}")
        
        return None
    
    @staticmethod
    def train(
        docs: List[str],
        output_path: Path,
        use_llm: bool = False,
        reduce_topics: bool = False,
        n_topics: Optional[int] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
        language: str = "english",
        umap_n_neighbors: int = 15,
        umap_n_components: int = 5,
        umap_min_dist: float = 0.0,
        umap_metric: str = "cosine",
    ) -> Dict:
        """
        Train a new BERTopic model on ADR documents.
        
        Args:
            docs: List of ADR document texts
            output_path: Path to save the trained model
            use_llm: Whether to use LLM for topic naming
            reduce_topics: Whether to reduce topics after training
            n_topics: Number of topics (None for auto)
            embedding_model: Name of embedding model
            language: Language for stop words
            umap_n_neighbors: UMAP n_neighbors parameter
            umap_n_components: UMAP n_components parameter
            umap_min_dist: UMAP min_dist parameter
            umap_metric: UMAP metric parameter
        
        Returns:
            Dictionary with training metrics
        """
        import tiktoken
        import openai
        
        # Set environment variable to avoid tokenizer warnings
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        
        console.print(f"[blue]Training topic model...[/blue]")
        console.print(f"[cyan]Documents: {len(docs)}[/cyan]")
        console.print(f"[cyan]Embedding model: {embedding_model}[/cyan]")
        console.print(f"[cyan]LLM representation: {use_llm}[/cyan]")
        
        # Configure vectorizer
        vectorizer_model = CountVectorizer(stop_words=language)
        
        # Configure embedding model
        embedding_model_obj = SentenceTransformer(embedding_model)
        
        # Configure UMAP (adjust parameters for small datasets)
        n_docs = len(docs)
        
        # For very small datasets, use more aggressive parameter reduction
        if n_docs < 10:
            adjusted_n_neighbors = min(3, n_docs - 1)
            adjusted_n_components = min(2, n_docs - 1)
        else:
            adjusted_n_neighbors = min(umap_n_neighbors, n_docs - 1)
            adjusted_n_components = min(umap_n_components, n_docs - 1)
        
        # Ensure minimum values
        adjusted_n_neighbors = max(adjusted_n_neighbors, 2)
        adjusted_n_components = max(adjusted_n_components, 2)
        
        umap_model = UMAP(
            n_neighbors=adjusted_n_neighbors,
            n_components=adjusted_n_components,
            min_dist=umap_min_dist,
            metric=umap_metric,
            random_state=42
        )
        
        console.print(f"[cyan]UMAP n_neighbors: {umap_model.n_neighbors}[/cyan]")
        console.print(f"[cyan]UMAP n_components: {umap_model.n_components}[/cyan]")
        
        # Configure HDBSCAN for small datasets
        if n_docs < 10:
            hdbscan_model = hdbscan.HDBSCAN(
                min_cluster_size=2,  # Smaller clusters for small datasets
                min_samples=1,
                metric='euclidean',
                cluster_selection_method='eom',
                prediction_data=True
            )
            console.print(f"[cyan]HDBSCAN min_cluster_size: 2 (small dataset)[/cyan]")
        else:
            hdbscan_model = None  # Use BERTopic default
        
        # Configure representation model
        representation_model1 = KeyBERTInspired()
        
        if use_llm:
            console.print("[blue]Configuring LLM representation...[/blue]")
            # Tokenizer
            tokenizer = tiktoken.get_encoding("cl100k_base")
            
            # Get LLM
            from adrminer.config import get_settings
            settings = get_settings()
            llm = get_llm(settings=settings)
            
            # Create OpenAI representation model
            from openai import OpenAI
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            representation_model2 = OpenAI(
                client,
                delay_in_seconds=2,
                chat=True,
                nr_docs=4,
                doc_length=100,
                tokenizer=tokenizer
            )
            
            representation_model = {
                "Main": representation_model1,  # KeyBERT
                "LLM": representation_model2  # LLM
            }
        else:
            representation_model = representation_model1  # Only KeyBERT
        
        # Create BERTopic model
        console.print("[blue]Creating BERTopic model...[/blue]")
        
        if hdbscan_model:
            topic_model = BERTopic(
                embedding_model=embedding_model_obj,
                umap_model=umap_model,
                hdbscan_model=hdbscan_model,
                representation_model=representation_model,
                vectorizer_model=vectorizer_model,
                nr_topics="auto",  # Let BERTopic determine optimal number
                verbose=True
            )
        else:
            topic_model = BERTopic(
                embedding_model=embedding_model_obj,
                umap_model=umap_model,
                representation_model=representation_model,
                vectorizer_model=vectorizer_model,
                nr_topics="auto",  # Let BERTopic determine optimal number
                verbose=True
            )
        
        # Fit model to documents
        console.print("[blue]Fitting model to corpus...[/blue]")
        topics, probs = topic_model.fit_transform(docs)
        initial_n_topics = len(topic_model.get_topics())
        console.print(f"[green]✓ Initial topics: {initial_n_topics}[/green]")
        
        # Reduce topics if requested
        if reduce_topics and n_topics is not None and n_topics < initial_n_topics:
            console.print(f"[blue]Reducing topics to: {n_topics}[/blue]")
            topic_model.reduce_topics(docs, nr_topics=n_topics)
            final_n_topics = len(topic_model.get_topics())
            console.print(f"[green]✓ Reduced topics: {final_n_topics}[/green]")
        else:
            final_n_topics = initial_n_topics
        
        # Calculate metrics
        console.print("[blue]Calculating metrics...[/blue]")
        coherence = TopicService._compute_topic_coherence(topic_model, embedding_model_obj)
        diversity = TopicService._compute_topic_diversity(topic_model)
        
        console.print(f"[cyan]Coherence: {coherence:.3f}[/cyan]")
        console.print(f"[cyan]Diversity: {diversity:.3f}[/cyan]")
        
        # Save model
        console.print(f"[blue]Saving model to: {output_path}[/blue]")
        output_path.mkdir(parents=True, exist_ok=True)
        topic_model.save(
            str(output_path),
            serialization="safetensors",
            save_ctfidf=True,
            save_embedding_model=embedding_model_obj
        )
        
        # Save corpus for future reference
        corpus_path = output_path / "corpus.json"
        with open(corpus_path, "w") as f:
            json.dump(docs, f)
        
        console.print(f"[green]✓ Model saved successfully[/green]")
        
        return {
            "n_topics": final_n_topics,
            "coherence": coherence,
            "diversity": diversity,
            "output_path": str(output_path),
        }
    
    @staticmethod
    def _compute_topic_coherence(topic_model: BERTopic, embedding_model: SentenceTransformer, top_n: int = 20) -> float:
        """Compute topic coherence score."""
        topics = topic_model.get_topics()
        if -1 in topics:
            del topics[-1]
        
        coherence_scores = []
        for topic_id in topics:
            words = [word for word, _ in topics[topic_id][:top_n]]
            embeddings = embedding_model.encode(words)
            
            # Compute pairwise cosine similarities
            sim_matrix = np.zeros((len(words), len(words)))
            for i in range(len(words)):
                for j in range(i+1, len(words)):
                    sim = np.dot(embeddings[i], embeddings[j]) / (
                        np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                    )
                    sim_matrix[i][j] = sim
            avg_sim = np.mean(sim_matrix[np.triu_indices(len(words), k=1)])
            coherence_scores.append(avg_sim)  # Mean similarity for topic
        
        return np.mean(coherence_scores)  # Mean similarity for all topics
    
    @staticmethod
    def _compute_topic_diversity(topic_model: BERTopic, top_n: int = 20) -> float:
        """Compute topic diversity score."""
        from itertools import combinations
        
        # Exclude outlier topic (-1) if present
        topics = topic_model.get_topics()
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
