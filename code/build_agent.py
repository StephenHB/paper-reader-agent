from agents.paper_agent import PaperAgent
import argparse

def main():
    parser = argparse.ArgumentParser(description='Build and run a paper reader agent')
    parser.add_argument('--pdf_dir', type=str, required=True, help='Directory containing PDF files')
    parser.add_argument('--index_name', type=str, default="research_papers", help='Name for the vector store index')
    parser.add_argument('--interactive', action='store_true', help='Start interactive session after building')
    args = parser.parse_args()

    # Initialize agent
    agent = PaperAgent(
        embedding_model="nomic-embed-text",
        llm_model="llama3.2:latest",
        vector_store_dir="./vector_stores"
    )
    
    # Build knowledge base
    if agent.build_knowledge_base(args.pdf_dir, index_name=args.index_name):
        print("✅ Knowledge base built successfully!")
        
        # Start interactive session if requested
        if args.interactive:
            agent.interactive_query()
    else:
        print("❌ Failed to build knowledge base")

if __name__ == "__main__":
    main()