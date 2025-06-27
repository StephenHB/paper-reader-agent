from process_pdf import PDFProcessor
from vector_store import VectorStoreBuilder
import ollama
import numpy as np
import time


class PaperAgent:
    def __init__(
        self,
        embedding_model="nomic-embed-text",
        llm_model="llama3.2:latest",
        vector_store_dir="./vector_stores",
    ):
        """
        Initialize paper reading agent
        :param embedding_model: Embedding model name
        :param llm_model: LLM model name for queries
        :param vector_store_dir: Directory for vector stores
        """
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.vector_store_dir = vector_store_dir
        self.pdf_processor = PDFProcessor()
        self.vector_builder = VectorStoreBuilder(
            embedding_model=embedding_model, vector_store_dir=vector_store_dir
        )
        self.index = None
        self.chunks = []
        self.metadata = []

    def build_knowledge_base(self, pdf_directory, index_name="default_index"):
        """Build knowledge base from PDF directory"""
        print(f"📂 Processing directory: {pdf_directory}")
        all_chunks, metadata = self.pdf_processor.load_pdfs_from_directory(
            pdf_directory
        )

        if not all_chunks:
            print("⚠️ No valid PDFs processed")
            return False

        print(f"\n🛠️ Creating vector store ({len(all_chunks)} chunks)")
        self.index, self.chunks, self.metadata = (
            self.vector_builder.build_pdf_vector_store(
                all_chunks, metadata, index_name=index_name
            )
        )

        return self.index is not None

    def load_knowledge_base(self, index_name="default_index"):
        """Load existing knowledge base"""
        self.index, self.chunks, self.metadata = self.vector_builder.load_vector_store(
            index_name
        )
        return self.index is not None

    def query(self, question, k=5):
        """Query the knowledge base"""
        if not self.index:
            print(" Knowledge base not loaded")
            return "Knowledge base not available", []

        # Get question embedding
        response = ollama.embeddings(model=self.embedding_model, prompt=question)
        query_embedding = np.array([response["embedding"]], dtype=np.float32)

        # Search similar content
        distances, indices = self.index.search(query_embedding, k)

        # Retrieve context
        context_chunks = [self.chunks[i] for i in indices[0] if i < len(self.chunks)]
        context_metadata = [
            self.metadata[i] for i in indices[0] if i < len(self.metadata)
        ]

        # Build context
        context = "\n\n".join(
            [
                f"Source: {meta['filename']} Page {meta['page']}\nContent: {chunk}"
                for chunk, meta in zip(context_chunks, context_metadata)
            ]
        )

        # Generate response
        prompt = f"""
        You are a professional document assistant. Answer the question based on the context.
        If the information is not in the context, say you don't know.
        
        Context:
        {context}
        
        Question: {question}
        Answer:
        """

        response = ollama.chat(
            model=self.llm_model, messages=[{"role": "user", "content": prompt}]
        )

        return response["message"]["content"], context_metadata

    def interactive_query(self):
        """Start interactive query session"""
        if not self.index:
            print(" Knowledge base not loaded")
            return

        print("🚀 Document assistant ready! Type 'exit' to quit")

        while True:
            try:
                question = input("\n👤 Your question: ")
                if question.lower() in ["exit", "quit"]:
                    break

                if not question.strip():
                    continue

                start_time = time.time()
                answer, sources = self.query(question)
                elapsed = time.time() - start_time

                print(f"\n🤖 Assistant ({elapsed:.2f}s):")
                print(answer)

                if sources:
                    print("\n📚 Sources:")
                    for i, source in enumerate(sources):
                        print(f"{i+1}. {source['filename']} - Page {source['page']}")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
