import os
import time
import numpy as np
import faiss
from tqdm import tqdm
import ollama
import pickle

class VectorStoreBuilder:
    def __init__(self, embedding_model="nomic-embed-text", vector_store_dir="./vector_stores"):
        """
        Initialize vector store builder
        :param embedding_model: Ollama embedding model name
        :param vector_store_dir: Directory to store vector indexes
        """
        self.embedding_model = embedding_model
        self.vector_store_dir = vector_store_dir
        os.makedirs(vector_store_dir, exist_ok=True)

    def build_pdf_vector_store(self, all_chunks, metadata, index_name="default_index", batch_size=50):
        """Build and save vector store from text chunks"""
        if not all_chunks:
            print("⚠️ No text chunks available for vector store")
            return None, None, None
        
        # Create vector store
        index, valid_chunks, valid_metadata = self.create_vector_store(
            all_chunks, metadata, batch_size
        )
        
        if index is None:
            return None, None, None
        
        # Save vector store
        index_path = os.path.join(self.vector_store_dir, f"{index_name}.faiss")
        faiss.write_index(index, index_path)
        
        # Save metadata
        metadata_path = os.path.join(self.vector_store_dir, f"{index_name}_metadata.pkl")
        with open(metadata_path, "wb") as f:
            pickle.dump({"chunks": valid_chunks, "metadata": valid_metadata}, f)
        
        print(f"✅ Vector store built! Index size: {index.ntotal} vectors")
        return index, valid_chunks, valid_metadata

    def create_vector_store(self, all_chunks, metadata, batch_size=50):
        """Create FAISS index from text chunks"""
        if not all_chunks:
            print("⚠️ No text chunks available for vector store")
            return None, [], []
        
        embeddings = []
        failed_indices = []
        print(f"Generating embeddings ({len(all_chunks)} chunks)...")
        
        # Process in batches
        for i in tqdm(range(0, len(all_chunks), batch_size), desc="Generating embeddings"):
            batch = all_chunks[i:i+batch_size]
            batch_embeddings = []
            
            try:
                for j, text_chunk in enumerate(batch):
                    chunk_index = i + j
                    
                    for attempt in range(3):  # Retry mechanism
                        try:
                            response = ollama.embeddings(
                                model=self.embedding_model,
                                prompt=text_chunk
                            )
                            
                            if 'embedding' in response:
                                batch_embeddings.append(response['embedding'])
                                break
                            else:
                                raise ValueError("Missing 'embedding' in response")
                                
                        except Exception as e:
                            if attempt < 2:
                                print(f"🔄 Retry {attempt+1}/3: Chunk {chunk_index} failed ({str(e)[:100]})")
                                time.sleep(2 ** attempt)
                            else:
                                print(f"❌ Chunk {chunk_index} failed: {str(e)[:200]}")
                                failed_indices.append(chunk_index)
                                batch_embeddings.append(None)
                                break
                
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                print(f"❌ Batch processing error: {str(e)[:200]}")
                failed_indices.extend(range(i, min(i+batch_size, len(all_chunks))))
                embeddings.extend([None] * len(batch))
        
        # Remove failed embeddings
        if failed_indices:
            print(f"⚠️ Removed {len(failed_indices)} failed embeddings")
            for idx in sorted(failed_indices, reverse=True):
                if idx < len(all_chunks):
                    del all_chunks[idx]
                if idx < len(metadata):
                    del metadata[idx]
                if idx < len(embeddings):
                    del embeddings[idx]
        
        # Filter valid embeddings
        valid_embeddings = [e for e in embeddings if e is not None]
        if not valid_embeddings:
            print("❌ No valid embeddings for index creation")
            return None, [], []
        
        # Verify dimension consistency
        dimension = len(valid_embeddings[0])
        consistent_embeddings = [e for e in valid_embeddings if len(e) == dimension]
        
        if len(consistent_embeddings) != len(valid_embeddings):
            print(f"⚠️ Removed {len(valid_embeddings)-len(consistent_embeddings)} inconsistent embeddings")
        
        # Create FAISS index
        try:
            index = faiss.IndexFlatL2(dimension)
            index.add(np.array(consistent_embeddings, dtype=np.float32))
            print(f"Index created! Dimension: {dimension} | Vectors: {index.ntotal}")
            
            # Get valid chunks and metadata
            valid_indices = [i for i, emb in enumerate(embeddings) 
                             if emb is not None and emb in consistent_embeddings]
            valid_chunks = [all_chunks[i] for i in valid_indices]
            valid_metadata = [metadata[i] for i in valid_indices]
            
            return index, valid_chunks, valid_metadata
            
        except Exception as e:
            print(f"❌ FAISS index creation failed: {str(e)[:200]}")
            return None, [], []
    
    def load_vector_store(self, index_name="default_index"):
        """Load existing vector store"""
        index_path = os.path.join(self.vector_store_dir, f"{index_name}.faiss")
        metadata_path = os.path.join(self.vector_store_dir, f"{index_name}_metadata.pkl")
        
        try:
            index = faiss.read_index(index_path)
            with open(metadata_path, "rb") as f:
                data = pickle.load(f)
                chunks = data['chunks']
                metadata = data['metadata']
            print(f"✅ Loaded vector store | Size: {index.ntotal}")
            return index, chunks, metadata
        except Exception as e:
            print(f"❌ Loading failed: {str(e)}")
            return None, None, None