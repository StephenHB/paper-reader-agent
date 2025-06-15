from tqdm import tqdm
from evaluation_metrics import RetrievalMetrics, GenerationMetrics, SystemPerformance
import time
import json

class ModelEvaluator:
    """End-to-end model evaluation"""
    
    def __init__(self, query_function, test_dataset, embedding_model="all-MiniLM-L6-v2"):
        """
        Initialize evaluator
        :param query_function: Function that takes a question and returns (answer, sources)
        :param test_dataset: Test dataset
        :param embedding_model: Embedding model for generation evaluation
        """
        self.query = query_function
        self.test_data = test_dataset
        self.results = []
        self.generation_metrics = GenerationMetrics(embedding_model)
    
    def run_evaluation(self, progress_bar=True):
        """Run full evaluation"""
        iterable = self.test_data
        if progress_bar:
            iterable = tqdm(self.test_data, desc="Evaluation Progress")
            
        for test_case in iterable:
            try:
                result = self._evaluate_single_case(test_case)
                self.results.append(result)
            except Exception as e:
                print(f"❌ Evaluation failed for {test_case.get('id', 'unknown')}: {str(e)}")
                self.results.append({
                    "id": test_case.get("id", "error"),
                    "question": test_case.get("question", ""),
                    "error": str(e)
                })
        return self.results
    
    def _evaluate_single_case(self, test_case):
        """Evaluate a single test case"""
        # Execute query
        start_time = time.time()
        answer, sources = self.query(test_case["question"])
        response_time = time.time() - start_time
        
        # Extract actual sources and pages
        actual_sources = [s["filename"] for s in sources] if sources else []
        actual_pages = [s["page"] for s in sources] if sources else []
        
        # Evaluate retrieval performance
        retrieval_metrics = RetrievalMetrics.evaluate(
            actual_sources,
            test_case.get("expected_sources", []),
            actual_pages,
            test_case.get("expected_pages", []),
        )
        
        # Evaluate generation quality
        generation_metrics = self.generation_metrics.evaluate(
            answer, test_case.get("expected_answer", "")
        )
        
        # Return results
        return {
            "id": test_case["id"],
            "question": test_case["question"],
            "answer": answer,
            "expected_answer": test_case["expected_answer"],
            "response_time": response_time,
            **retrieval_metrics,
            **generation_metrics,
            "difficulty": test_case.get("difficulty", "unknown"),
            "category": test_case.get("category", "unknown"),
        }
    
    def generate_report(self):
        """Generate evaluation report"""
        if not self.results:
            return "No evaluation results available"
        
        # Calculate overall metrics
        avg_recall = self._calculate_average("recall")
        avg_precision = self._calculate_average("precision")
        avg_f1 = self._calculate_average("f1")
        avg_semantic_sim = self._calculate_average("semantic_similarity")
        avg_response_time = self._calculate_average("response_time")
        avg_bleu = self._calculate_average("bleu_score")
        avg_entity_cov = self._calculate_average("entity_coverage")
        
        # Analyze by difficulty
        difficulties = self._analyze_by_difficulty()
        
        # Generate report
        report = f"""
        ================= Model Evaluation Report =================
        Overall Metrics:
        - Average Recall: {avg_recall:.2%}
        - Average Precision: {avg_precision:.2%}
        - Average F1 Score: {avg_f1:.2%}
        - Average Semantic Similarity: {avg_semantic_sim:.2%}
        - Average BLEU Score: {avg_bleu:.4f}
        - Average Entity Coverage: {avg_entity_cov:.2%}
        - Average Response Time: {avg_response_time:.2f} seconds
        
        Analysis by Difficulty:
        """
        for diff, metrics in difficulties.items():
            report += f"""
        {diff} Questions:
          - Count: {metrics['count']}
          - Avg F1: {metrics['avg_f1']:.2%}
          - Avg Semantic Similarity: {metrics['avg_semantic_sim']:.2%}
          - Avg BLEU: {metrics['avg_bleu']:.4f}
            """
        return report
    
    def export_results(self, file_path="evaluation_results.json"):
        """Export evaluation results to JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"✅ Evaluation results exported to: {file_path}")
            return True
        except Exception as e:
            print(f"❌ Export failed: {str(e)}")
            return False
    
    def _calculate_average(self, metric_key):
        """Calculate average of a specific metric"""
        valid_results = [r for r in self.results if metric_key in r]
        if not valid_results:
            return 0
        return sum(r[metric_key] for r in valid_results) / len(valid_results)
    
    def _analyze_by_difficulty(self):
        """Analyze results by difficulty level"""
        difficulties = {}
        # Automatically detect all existing difficulty levels
        all_difficulties = set(r.get("difficulty", "unknown") for r in self.results)
        
        for diff in all_difficulties:
            diff_results = [r for r in self.results if r.get("difficulty") == diff]
            if diff_results:
                difficulties[diff] = {
                    "count": len(diff_results),
                    "avg_f1": sum(r["f1"] for r in diff_results) / len(diff_results),
                    "avg_semantic_sim": sum(
                        r["semantic_similarity"] for r in diff_results
                    ) / len(diff_results),
                    "avg_bleu": sum(r["bleu_score"] for r in diff_results) / len(diff_results),
                }
        return difficulties


class SystemBenchmark:
    """System performance benchmarking tools"""
    
    @staticmethod
    def run(query_function, test_questions, num_iterations=10):
        """Run system performance benchmark"""
        performance_results = []
        
        for question in test_questions:
            perf = SystemPerformance.evaluate(
                query_function, question, num_iterations
            )
            performance_results.append({"question": question, **perf})
        
        # Generate performance report
        return SystemBenchmark._generate_report(performance_results)
    
    @staticmethod
    def _generate_report(performance_results):
        """Generate performance report"""
        if not performance_results:
            return {
                "report": "No performance data available",
                "metrics": {}
            }
            
        avg_response = sum(p["avg_response_time"] for p in performance_results) / len(
            performance_results
        )
        max_response = max(p["max_response_time"] for p in performance_results)
        min_response = min(p["min_response_time"] for p in performance_results)
        avg_cpu = sum(p["avg_cpu_usage"] for p in performance_results) / len(
            performance_results
        )
        avg_mem = sum(p["avg_memory_delta"] for p in performance_results) / len(
            performance_results
        )
        
        report = f"""
        ============== System Performance Benchmark Report ==============
        Average Response Time: {avg_response:.4f} seconds
        Minimum Response Time: {min_response:.4f} seconds
        Maximum Response Time: {max_response:.4f} seconds
        Average CPU Usage: {avg_cpu:.2f}%
        Average Memory Delta: {avg_mem:.4f} MB
        """
        
        return {
            "report": report,
            "metrics": {
                "avg_response_time": avg_response,
                "min_response_time": min_response,
                "max_response_time": max_response,
                "avg_cpu_usage": avg_cpu,
                "avg_memory_delta": avg_mem
            }
        }