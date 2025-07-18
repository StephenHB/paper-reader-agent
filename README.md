# Paper Reader Agent & Evaluation System

## Overview

This project provides a comprehensive system for processing academic PDFs into a queryable knowledge base with advanced reference management capabilities. The system consists of two main components:

1. **Paper Reader Agent**: Processes PDF documents into a vector database and provides an interface for querying the knowledge base
2. **Reference Management System**: Automatically extracts references from PDFs and downloads related papers from online sources

## Key Features

- **PDF Processing**: Efficient text extraction and chunking from PDFs
- **Vector Storage**: FAISS-based vector storage with metadata management
- **Natural Language Querying**: Question-answering interface powered by Ollama LLMs
- **Reference Extraction**: Automatic extraction of bibliographic references from PDFs
- **Reference Download**: Automated downloading of reference papers from arXiv, PubMed, and other sources
- **Customized Reference Download**: Manual entry and download of specific papers
- **Comprehensive Evaluation**: Metrics for retrieval, generation quality, and system performance
- **Modular Design**: Reusable components with clear interfaces
- **Streamlit Web Interface**: User-friendly web application for all operations

## Installation

### Prerequisites
- Python 3.9+
- Ollama server (running locally)

```bash
# Install Ollama (Linux/Mac)
curl -fsSL https://ollama.com/install.sh | sh

# Windows users: Download installer from https://ollama.com/download

# Install embedding model
ollama pull nomic-embed-text

# Install LLM model
ollama pull llama3.2:latest

# Clone repository
git clone https://github.com/StephenHB/paper-reader-agent.git
cd paper-reader-agent

# Create virtual environment
python -m venv paper-reader

# Activate environment
source paper-reader/bin/activate  # Linux/Mac
paper-reader\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Running the Application
After activating the virtual environment, you can run the Streamlit app:

```bash
# Navigate to the code directory
cd code

# Run Streamlit app
streamlit run streamlit_app.py

# The app will be available at:
# Local URL: http://localhost:8501
# Network URL: http://your-ip:8501
```

### Using the Application

1. **Upload PDFs**: Use the file uploader to add academic papers
2. **Build Knowledge Base**: The system automatically processes PDFs and creates a vector store
3. **Query Papers**: Ask questions about the uploaded papers using natural language
4. **Extract References**: Enable reference extraction to find papers cited in your documents
5. **Download References**: Select and download reference papers automatically
6. **Custom Downloads**: Use the customized reference download feature for specific papers

## System Architecture

```text
+----------------+       +----------------+       +----------------+
|  PDF Documents |       |  Paper Reader  |       |  Vector Store  |
|  (Input)       | ----> |  Agent         | ----> |  (FAISS Index) |
+----------------+       +----------------+       +----------------+
                          |           |
                          |           |    +----------------+
                          |           +--> |  Query Engine  |
                          |                +----------------+
                          |                        |
                          |                        v
                          |                +----------------+
                          +-------------> |  Reference      |
                                          |  Management     |
                                          +----------------+
                                                  |
                                                  v
                                          +----------------+
                                          |  Reference      |
                                          |  Downloader     |
                                          +----------------+
```

## System Components

### 1. Paper Reader Agent
The Paper Reader Agent processes PDF documents and creates a queryable knowledge base.

**File Structure:**
```text
agents/
├── paper_agent.py           # Main agent interface
├── process_pdf.py           # PDF text extraction and processing
├── vector_store.py          # Vector store management
├── reference_extractor.py   # Reference extraction from PDFs
├── reference_downloader.py  # Download reference papers
└── reference_manager.py     # Orchestrates reference operations
```

### 2. Reference Management System
The reference management system provides comprehensive reference handling:

- **Reference Extraction**: Automatically identifies and extracts bibliographic references from PDFs
- **Reference Download**: Downloads papers from multiple sources (arXiv, PubMed, etc.)
- **User Consent**: Implements proper consent logging for copyright compliance
- **Batch Processing**: Handles multiple references efficiently
- **Error Handling**: Graceful handling of download failures and unavailable papers

### 3. Streamlit Web Interface
The web interface provides a user-friendly way to interact with the system:

- **PDF Upload**: Drag-and-drop interface for uploading papers
- **Knowledge Base Building**: Automatic processing and vector store creation
- **Query Interface**: Natural language question-answering
- **Reference Management**: Visual interface for reference extraction and download
- **Download Progress**: Real-time feedback on download operations
- **Results Display**: Clear presentation of query results and download status

## Usage Examples

### Interactive Querying
```bash
# Sample session
👤 Your question: What is the energy distance?
🤖 Assistant (1.24s):
The energy distance is defined as the Euclidean distance between the empirical distributions of d-dimensional independent random variables X and Y.

📚 Sources:
1. Energy_statistics.pdf - Page 1251
```

### Reference Download
The system can automatically:
1. Extract references from uploaded PDFs
2. Search for papers online
3. Download available papers to a local directory
4. Provide detailed feedback on download success/failure

### Customized Reference Download
Users can manually enter reference details and download specific papers:
- Author names
- Paper titles
- Journal names
- Publication years

## Configuration

### Reference Download Settings
Configure reference download behavior in the Streamlit sidebar:
- **Download Path**: Specify where downloaded papers are saved
- **Max Concurrent Downloads**: Control parallel download operations
- **Retry Attempts**: Number of retry attempts for failed downloads
- **Timeout Settings**: Network timeout configuration

### Vector Store Configuration
- **Chunk Size**: Control text chunking for vector storage
- **Overlap**: Configure overlap between text chunks
- **Embedding Model**: Select embedding model for vector generation

## Evaluation System

The evaluation system provides comprehensive assessment of the Paper Reader Agent's performance:

**File Structure:**
```text
evaluation/
├── evaluation_metrics.py  # Core metric calculations
└── evaluator.py           # Evaluation orchestration
```

**Metrics:**
- **Retrieval Metrics**: Recall, Precision, F1 Score
- **Generation Metrics**: Semantic Similarity, BLEU Score, Entity Coverage
- **System Metrics**: Response Time, CPU/Memory Usage

Run evaluation:
```bash
python evaluate_model.py \
    --test_data evaluation/test_data.json \
    --index_name physics_papers \
    --vector_store_dir ./vector_stores
```

## Project Structure

```text
paper-reader-agent/
├── code/
│   ├── agents/                 # Core agent modules
│   ├── evaluation/             # Evaluation system
│   ├── notebooks/              # Jupyter notebooks
│   ├── uploaded_pdfs/          # User uploaded PDFs
│   ├── downloaded_references/  # Downloaded reference papers
│   ├── vector_stores/          # FAISS vector stores
│   ├── streamlit_app.py        # Main web application
│   ├── build_agent.py          # Knowledge base builder
│   └── evaluate_model.py       # Evaluation runner
├── docs/                       # Documentation
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Project configuration
├── README.md                  # This file
└── developer.md               # Developer documentation
```

## Performance Benchmarks

The system is optimized for:
- **Fast PDF Processing**: Efficient text extraction and chunking
- **Quick Query Response**: Optimized vector search and retrieval
- **Reliable Downloads**: Robust error handling and retry mechanisms
- **Scalable Storage**: Efficient FAISS indexing for large document collections

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the documentation in the `docs/` directory
2. Review the developer documentation in `developer.md`
3. Open an issue on GitHub
