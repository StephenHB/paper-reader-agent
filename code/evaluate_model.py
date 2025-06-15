from evaluation.evaluator import ModelEvaluator
from evaluation.evaluation_metrics import TestDataLoader
from agents.paper_agent import PaperAgent
import argparse

def create_query_function(agent, index_name):
    """Create a query function compatible with the evaluator"""
    # Load the knowledge base first
    if not agent.load_knowledge_base(index_name=index_name):
        raise RuntimeError("Failed to load knowledge base")
    
    def query_fn(question):
        answer, sources = agent.query(question)
        return answer, sources
    
    return query_fn

def main():
    parser = argparse.ArgumentParser(description='Evaluate paper reader agent performance')
    parser.add_argument('--test_data', type=str, required=True, help='Path to test data JSON file')
    parser.add_argument('--index_name', type=str, default="research_papers", help='Name of the vector store index')
    parser.add_argument('--vector_store_dir', type=str, default="./vector_stores", help='Vector store directory')
    args = parser.parse_args()

    # Initialize agent
    agent = PaperAgent(
        embedding_model="nomic-embed-text",
        llm_model="llama3.2:latest",
        vector_store_dir=args.vector_store_dir
    )
    
    # Create query function for evaluator
    query_function = create_query_function(agent, args.index_name)
    
    # Load test dataset
    test_data = TestDataLoader.load_test_data(args.test_data)
    if not test_data:
        print("❌ Failed to load test data")
        return
    
    # Initialize evaluator
    evaluator = ModelEvaluator(
        query_function=query_function,
        test_dataset=test_data
    )
    
    # Run evaluation
    print("\nStarting model evaluation...")
    evaluation_results = evaluator.run_evaluation()
    
    # Generate and print report
    report = evaluator.generate_report()
    print(report)
    
    # Export results
    evaluator.export_results("evaluation_results.json")
    print("✅ Evaluation results exported")

if __name__ == "__main__":
    main()