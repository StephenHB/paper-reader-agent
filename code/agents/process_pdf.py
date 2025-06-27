import os
import re
import gc
import time
import fitz
from tqdm import tqdm


class PDFProcessor:
    def __init__(self, max_chars_per_page=50000):
        self.max_chars_per_page = max_chars_per_page

    def load_pdfs_from_directory(self, directory_path):
        """Streaming PDF text extraction with optimized memory management"""
        all_chunks = []
        metadata = []

        if not os.path.exists(directory_path):
            print(f"❌ Directory not found: {directory_path}")
            return [], []

        pdf_files = [
            f for f in os.listdir(directory_path) if f.lower().endswith(".pdf")
        ]

        if not pdf_files:
            print(f"ℹ️ No PDFs found in: {directory_path}")
            return [], []

        print(f"Found {len(pdf_files)} PDFs, processing...")

        for filename in tqdm(pdf_files, desc="📄 Processing PDFs"):
            filepath = os.path.join(directory_path, filename)
            try:
                with fitz.open(filepath) as doc:
                    total_chunks = 0

                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        page_text = page.get_text("text")

                        # Clean and truncate text
                        clean_text = re.sub(r"\s+", " ", page_text).strip()
                        if len(clean_text) > self.max_chars_per_page:
                            clean_text = clean_text[: self.max_chars_per_page]
                            print(
                                f"⚠️ Truncated large page: {filename} page {page_num+1}"
                            )

                        # Split into chunks
                        page_chunks = self.split_text(clean_text)
                        total_chunks += len(page_chunks)

                        # Collect data
                        for i, chunk in enumerate(page_chunks):
                            all_chunks.append(chunk)
                            metadata.append(
                                {
                                    "filename": filename,
                                    "filepath": filepath,
                                    "page": page_num + 1,
                                    "chunk_index": i,
                                    "total_chunks": len(page_chunks),
                                    "timestamp": time.time(),
                                }
                            )

                        # Memory management
                        del page, page_text, clean_text
                        if page_num % 5 == 0:
                            gc.collect()

                    print(
                        f"✅ Loaded: {filename} | Pages: {len(doc)} | Chunks: {total_chunks}"
                    )

            except Exception as e:
                print(f"❌ Failed {filename}: {str(e)[:200]}")
                gc.collect()

        return all_chunks, metadata

    @staticmethod
    def split_text(text, chunk_size=2000, overlap=200):
        """Split text into overlapping chunks"""
        if not text.strip():
            return []

        chunks = []
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end == len(text):
                break

            start = end - overlap
            if start < 0:
                start = 0

        return chunks
