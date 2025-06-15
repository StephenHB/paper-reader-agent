from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from nltk.translate.bleu_score import sentence_bleu
import re
import time
import psutil
import json


class RetrievalMetrics:
    """Methods for evaluating retrieval performance"""

    @staticmethod
    def evaluate(actual_sources, expected_sources, actual_pages, expected_pages):
        """Evaluate retrieval performance metrics"""
        # Calculate recall
        recall = (
            len(set(actual_sources) & set(expected_sources)) / len(expected_sources)
            if expected_sources
            else 0
        )

        # Calculate precision
        precision = (
            len(set(actual_sources) & set(expected_sources)) / len(actual_sources)
            if actual_sources
            else 0
        )

        # Calculate F1 score
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        # Calculate page accuracy
        page_accuracy = (
            len(set(actual_pages) & set(expected_pages)) / len(expected_pages)
            if expected_pages
            else 0
        )

        return {
            "recall": recall,
            "precision": precision,
            "f1": f1,
            "page_accuracy": page_accuracy,
        }


class GenerationMetrics:
    """Methods for evaluating answer generation quality"""

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(model_name)

    def evaluate(self, actual_answer, expected_answer):
        """Evaluate generated answer quality"""
        # Embed answers
        actual_embed = self.embedding_model.encode([actual_answer])
        expected_embed = self.embedding_model.encode([expected_answer])

        # Calculate semantic similarity
        semantic_sim = cosine_similarity(actual_embed, expected_embed)[0][0]

        # Calculate BLEU score
        try:
            bleu = sentence_bleu(
                [expected_answer.split()], actual_answer.split(), weights=(0.5, 0.5)
            )
        except:
            bleu = 0.0  # Handle empty text cases

        # Calculate entity coverage
        expected_entities = self.extract_entities(expected_answer)
        actual_entities = self.extract_entities(actual_answer)
        entity_coverage = (
            len(set(actual_entities) & set(expected_entities)) / len(expected_entities)
            if expected_entities
            else 0
        )

        return {
            "semantic_similarity": semantic_sim,
            "bleu_score": bleu,
            "entity_coverage": entity_coverage,
        }

    @staticmethod
    def extract_entities(text):
        """Extract key entities (simplified version)"""
        return list(set(re.findall(r"\b[A-Z][a-z]+\b", text)))


class SystemPerformance:
    """Methods for evaluating system performance"""

    @staticmethod
    def evaluate_single_query(query_function, question):
        """Evaluate performance of a single query"""
        # Record resource usage before query
        process = psutil.Process()
        cpu_before = process.cpu_percent(interval=None)
        mem_before = process.memory_info().rss / (1024 * 1024)  # MB

        # Execute query and time it
        start_time = time.time()
        response = query_function(question)
        elapsed = time.time() - start_time

        # Record resource usage after query
        cpu_after = process.cpu_percent(interval=None)
        mem_after = process.memory_info().rss / (1024 * 1024)

        return {
            "response_time": elapsed,
            "cpu_usage": cpu_after - cpu_before,
            "memory_delta": mem_after - mem_before,
        }

    @staticmethod
    def evaluate(query_function, question, num_iterations=10):
        """Evaluate system performance over multiple iterations"""
        metrics = {"response_times": [], "cpu_usages": [], "memory_deltas": []}

        for _ in range(num_iterations):
            result = SystemPerformance.evaluate_single_query(query_function, question)
            metrics["response_times"].append(result["response_time"])
            metrics["cpu_usages"].append(result["cpu_usage"])
            metrics["memory_deltas"].append(result["memory_delta"])

        return {
            "avg_response_time": sum(metrics["response_times"]) / num_iterations,
            "max_response_time": max(metrics["response_times"]),
            "min_response_time": min(metrics["response_times"]),
            "avg_cpu_usage": sum(metrics["cpu_usages"]) / num_iterations,
            "avg_memory_delta": sum(metrics["memory_deltas"]) / num_iterations,
        }


class TestDataLoader:
    """Methods for loading test datasets"""

    @staticmethod
    def load_test_data(file_path="test_data.test_data.json"):
        """Load test dataset from JSON file"""
        try:
            with open(file_path, "r") as f:
                test_data = json.load(f)
            print(f"✅ Successfully loaded test dataset: {len(test_data)} test cases")
            return test_data
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
            return []
        except json.JSONDecodeError:
            print(f"❌ JSON decode error: {file_path}")
            return []
