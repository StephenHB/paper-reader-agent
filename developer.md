# Developer Guide - Paper Reader Agent

This file provides guidance to AI assistants such as Claude (claude.ai/code) when working with code in this repository.

## Overview

This is a Retrieval-Augmented Generation (RAG) system for processing academic PDFs into a queryable knowledge base. The system includes:
- PDF processing and vector storage
- Local LLM integration via Ollama
- Web interface using Streamlit
- Comprehensive evaluation framework
- Command-line tools for automation

## Development Environment

### macOS Setup
This project is optimized for macOS development. Ensure you have:

```bash
# Check macOS version
sw_vers

# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.9+ via Homebrew
brew install python@3.11

# Install Ollama
brew install ollama

# Install required models
ollama pull nomic-embed-text
ollama pull llama3.2:latest
```

### Virtual Environment Management
Always use the existing virtual environment:

```bash
# Activate the existing environment
source paper-reader/bin/activate

# Verify activation
which python  # Should show: /path/to/paper-reader/bin/python

# Install dependencies if needed
pip install -r requirements.txt
```

## Code Architecture Principles

### 1. Modular Design
**CRITICAL**: Maintain strict modularity. Each component should have a single responsibility:

```
code/
├── agents/                 # Core RAG components
│   ├── paper_agent.py     # Main orchestrator
│   ├── process_pdf.py     # PDF processing only
│   └── vector_store.py    # Vector storage only
├── evaluation/            # Evaluation framework
│   ├── evaluator.py       # Evaluation orchestration
│   └── evaluation_metrics.py  # Metrics calculation
├── test_data/            # Test datasets
└── streamlit_app.py      # Web interface
```

### 2. Interface Contracts
Each module must have clear interfaces:

```python
# Example: PDFProcessor interface
class PDFProcessor:
    def load_pdfs_from_directory(self, directory_path) -> Tuple[List[str], List[dict]]:
        """Load and process PDFs from directory.
        
        Returns:
            Tuple of (text_chunks, metadata_list)
        """
        pass
    
    def split_text(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        pass
```

### 3. Error Handling
Implement comprehensive error handling:

```python
# Example: Graceful error handling
try:
    response = ollama.embeddings(model=self.embedding_model, prompt=text_chunk)
    if "embedding" not in response:
        raise ValueError("Missing 'embedding' in response")
except Exception as e:
    logger.error(f"Embedding generation failed: {str(e)}")
    return None
```

## Enhancement Guidelines

### Rule 1: Avoid New Functions/Modules
**PRIORITY**: When enhancing existing code, modify existing functions rather than adding new ones.

```python
# ❌ DON'T: Add new function
def process_pdf_advanced(self, file_path):
    # New function
    pass

# ✅ DO: Enhance existing function
def load_pdfs_from_directory(self, directory_path, advanced_processing=False):
    # Enhanced existing function
    if advanced_processing:
        # New functionality
        pass
    # Existing functionality
```

### Rule 2: Successful Enhancement Cleanup
After successful enhancement, **ALWAYS** perform cleanup:

#### 3.1 Remove Unused Code
```bash
# Find unused imports
python -m flake8 --select=F401 code/

# Find unused functions
python -m vulture code/

# Remove dead code
git add -u
git commit -m "Remove unused code after enhancement"
```

#### 3.2 Update Documentation
```python
# Update docstrings
def enhanced_function(self, param1, param2, new_param=None):
    """Enhanced function with new capabilities.
    
    Args:
        param1: Original parameter
        param2: Original parameter  
        new_param: New parameter for enhanced functionality
        
    Returns:
        Enhanced result with additional features
    """
    pass

# Update README.md with new features
# Update PRD.md if requirements changed
# Update inline comments
```

### Rule 3: Backward Compatibility
Maintain backward compatibility when possible:

```python
# Use default parameters for new features
def query(self, question, k=5, include_metadata=True):
    # New parameter with default value
    pass
```

### Rule 4: PRD Updates for Completed Tasks
**MANDATORY**: After completing any task or enhancement, update the PRD with a summary of what was accomplished.

#### 4.1 Update PRD.md with Task Completion
```markdown
## Implementation Status

### Completed Features
- [x] **PDF Processing Engine** (Completed: 7/18/2025)
  - Text extraction from PDFs using PyMuPDF
  - Intelligent chunking with configurable size and overlap
  - Memory optimization with garbage collection
  - Comprehensive metadata tracking
  - Error handling for corrupted files

- [x] **Vector Storage System** (Completed: 7/18/2025)
  - FAISS-based vector storage with batch processing
  - Retry mechanisms for embedding generation
  - Error handling for failed embeddings
  - Persistent storage of indices and metadata

- [x] **Local LLM Integration** (Completed: 7/18/2025)
  - Ollama integration for embeddings and LLM
  - Complete offline operation
  - Context-aware responses with source attribution

- [x] **Web Interface** (Completed: 7/18/2025)
  - Streamlit-based application
  - PDF upload with drag-and-drop
  - Interactive querying interface
  - Source attribution display

- [x] **Evaluation Framework** (Completed: 7/18/2025)
  - Multi-dimensional performance assessment
  - Retrieval, generation, and system metrics
  - Detailed reporting and export capabilities

### Recent Enhancements
- [x] **Virtual Environment Setup** (7/18/2025)
  - Added comprehensive setup instructions for macOS
  - Documented existing `paper-reader` virtual environment usage
  - Added troubleshooting for environment issues

- [x] **Developer Documentation** (7/18/2025)
  - Created comprehensive developer guide
  - Added enhancement guidelines and cleanup procedures
  - Established testing requirements and CI/CD structure

### In Progress
- [ ] **Performance Optimization** (Planned)
  - Memory usage optimization for large document collections
  - Response time improvements for complex queries
  - Batch processing enhancements

### Planned Features
- [ ] **Multi-language Support**
- [ ] **Image and Table Extraction**
- [ ] **Collaborative Features**
- [ ] **Cloud Backup and Synchronization**
```

#### 4.2 Task Summary Template
For each completed task, add a summary section:

```markdown
## Task Completion Summary

### Task: [Task Name]
**Date Completed**: [YYYY-MM-DD]
**Developer**: [Name/AI Assistant]

#### What Was Accomplished
- [Specific feature/functionality implemented]
- [Technical details and implementation approach]
- [Key decisions made during development]

#### Files Modified
- `path/to/file1.py` - [Brief description of changes]
- `path/to/file2.py` - [Brief description of changes]
- `README.md` - [Documentation updates]

#### Testing Performed
- [Unit tests added/modified]
- [Integration tests performed]
- [Manual testing scenarios]

#### Performance Impact
- [Any performance improvements or considerations]
- [Memory usage changes]
- [Response time improvements]

#### Known Issues/Limitations
- [Any remaining issues or limitations]
- [Workarounds implemented]

#### Next Steps
- [What should be done next]
- [Related tasks or improvements]
```

#### 4.3 Update Process
```bash
# After completing a task:
# 1. Update PRD.md with completion status
# 2. Add task summary section
# 3. Update acceptance criteria if needed
# 4. Commit changes with descriptive message

git add PRD.md
git commit -m "Update PRD: Complete [Task Name] - [Brief description]"
```

#### 4.4 PRD Maintenance Checklist
- [ ] Update implementation status for completed features
- [ ] Add task completion summary with technical details
- [ ] Update acceptance criteria if requirements changed
- [ ] Review and update constraints/limitations
- [ ] Update timeline with actual completion dates
- [ ] Ensure all file modifications are documented
- [ ] Update success metrics if new benchmarks were achieved

## Testing Requirements

### 4. CI/CD Test Structure
**MANDATORY**: Add tests under `test/` folder for all new functionality:

```
test/
├── unit/                    # Unit tests
│   ├── test_pdf_processor.py
│   ├── test_vector_store.py
│   └── test_paper_agent.py
├── integration/             # Integration tests
│   ├── test_end_to_end.py
│   └── test_evaluation.py
├── fixtures/               # Test data
│   ├── sample_pdfs/
│   └── test_datasets/
└── conftest.py             # Pytest configuration
```

### Test Implementation Standards

#### Unit Tests
```python
# test/test_pdf_processor.py
import pytest
from agents.process_pdf import PDFProcessor

class TestPDFProcessor:
    def setup_method(self):
        self.processor = PDFProcessor()
    
    def test_split_text_basic(self):
        text = "This is a test document with multiple sentences."
        chunks = self.processor.split_text(text, chunk_size=10, overlap=2)
        assert len(chunks) > 0
        assert all(len(chunk) <= 10 for chunk in chunks)
    
    def test_split_text_empty(self):
        chunks = self.processor.split_text("")
        assert chunks == []
```

#### Integration Tests
```python
# test/test_end_to_end.py
import pytest
from agents.paper_agent import PaperAgent

class TestEndToEnd:
    def test_build_and_query_knowledge_base(self, tmp_path):
        # Test complete workflow
        agent = PaperAgent(vector_store_dir=str(tmp_path))
        
        # Build knowledge base
        success = agent.build_knowledge_base("./test/fixtures/sample_pdfs")
        assert success
        
        # Query knowledge base
        answer, sources = agent.query("What is the main topic?")
        assert answer is not None
        assert sources is not None
```

### Test Execution
```bash
# Run all tests
pytest test/

# Run specific test file
pytest test/unit/test_pdf_processor.py

# Run with coverage
pytest --cov=code test/

# Run integration tests only
pytest test/integration/
```

## Development Workflow

### 1. Environment Setup
```bash
# Always start with activated environment
source paper-reader/bin/activate
cd code
```

### 2. Code Enhancement Process
```bash
# 1. Identify existing function to enhance
# 2. Modify existing function (don't add new ones)
# 3. Test enhancement
python -c "from agents.paper_agent import PaperAgent; agent = PaperAgent(); print('Import successful')"

# 4. Run existing tests
pytest test/ -v

# 5. Add new tests if needed
# 6. Clean up unused code
python -m flake8 --select=F401 code/

# 7. Update documentation
# 8. Commit changes
git add -u
git commit -m "Enhance existing_function with new_feature"
```

### 3. Quality Assurance
```bash
# Lint code
python -m flake8 code/
python -m black code/
python -m isort code/

# Type checking (if using type hints)
python -m mypy code/

# Security check
python -m bandit code/
```

## Common Patterns

### Error Handling Pattern
```python
def robust_function(self, input_data):
    """Robust function with comprehensive error handling."""
    try:
        # Main logic
        result = self._process_data(input_data)
        return result
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return None
    except ConnectionError as e:
        logger.error(f"Connection failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

### Configuration Pattern
```python
class ConfigurableComponent:
    def __init__(self, config=None):
        self.config = config or self._default_config()
    
    def _default_config(self):
        return {
            'chunk_size': 2000,
            'overlap': 200,
            'batch_size': 50
        }
```

### Logging Pattern
```python
import logging

logger = logging.getLogger(__name__)

def function_with_logging(self, param):
    logger.info(f"Processing {param}")
    try:
        result = self._process(param)
        logger.info(f"Successfully processed {param}")
        return result
    except Exception as e:
        logger.error(f"Failed to process {param}: {e}")
        raise
```

## Performance Considerations

### Memory Management
```python
# Use generators for large datasets
def process_large_pdfs(self, pdf_files):
    for pdf_file in pdf_files:
        yield self._process_single_pdf(pdf_file)

# Clean up resources
import gc
gc.collect()
```

### Batch Processing
```python
# Process in batches to avoid memory issues
def batch_process(self, items, batch_size=50):
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        yield self._process_batch(batch)
```

## Troubleshooting

### Common Issues

#### Virtual Environment Issues
```bash
# If activation fails
rm -rf paper-reader
python -m venv paper-reader
source paper-reader/bin/activate
pip install -r requirements.txt
```

#### Ollama Connection Issues
```bash
# Check Ollama status
ollama list

# Restart Ollama
brew services restart ollama

# Test connection
python -c "import ollama; print(ollama.embeddings(model='nomic-embed-text', prompt='test'))"
```

#### Import Errors
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Verify virtual environment
which python
pip list | grep -E "(fitz|ollama|streamlit)"
```

## Best Practices Summary

1. **Always use existing virtual environment** (`paper-reader`)
2. **Modify existing functions** instead of adding new ones
3. **Clean up after successful enhancements** (remove unused code, update docs)
4. **Add tests for all new functionality** under `test/` folder
5. **Maintain backward compatibility** when possible
6. **Use comprehensive error handling** and logging
7. **Follow modular design principles** with clear interfaces
8. **Test thoroughly** before committing changes

---

*Last updated: 7/18/2025*
*Version: 1.0*
