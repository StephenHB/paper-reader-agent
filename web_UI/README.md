# Paper Reader Agent - FastAPI Backend

## Overview

This is the FastAPI backend for the Paper Reader Agent web application. It provides RESTful APIs and WebSocket support for the modern web interface, while reusing all existing agent functionality.

## Features

- **RESTful APIs**: PDF upload, querying, reference management
- **WebSocket Support**: Real-time progress tracking
- **CORS Enabled**: Cross-origin requests for frontend integration
- **Existing Agent Integration**: Reuses all existing PaperAgent and ReferenceManager functionality
- **Error Handling**: Comprehensive error handling and logging

## Setup

### Prerequisites

1. Ensure you have the existing `paper-reader` virtual environment activated
2. Install FastAPI dependencies:

```bash
# Activate existing environment
source ../paper-reader/bin/activate

# Install FastAPI dependencies
pip install -r requirements.txt
```

### Running the Backend

```bash
# Development mode
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Core Endpoints
- `GET /` - API information
- `GET /health` - Health check

### PDF Management
- `POST /api/upload` - Upload PDF files
- `POST /api/build-kb` - Build knowledge base

### Query Interface
- `POST /api/query` - Query the knowledge base

### Reference Management
- `POST /api/references/extract` - Extract references from PDFs
- `POST /api/references/download` - Download selected references
- `GET /api/references/list` - List available references

### WebSocket
- `WS /ws` - Real-time progress updates

## Project Structure

```
web_UI/
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
├── api/                 # API route handlers
├── websockets/          # WebSocket handlers
├── services/            # Business logic services
├── models/              # Data models and schemas
└── static/              # Static file serving
```

## Integration with Existing Code

This backend reuses all existing agent classes from the `code/agents/` directory:

- **PaperAgent**: For PDF processing and querying
- **ReferenceManager**: For reference extraction and download
- **PDFProcessor**: For PDF text extraction
- **VectorStoreBuilder**: For vector store management

No modifications to existing code are required - the backend acts as a wrapper around existing functionality.

## Development

### Adding New Endpoints

1. Create new route files in the `api/` directory
2. Import and include them in `main.py`
3. Follow existing patterns for error handling and response formatting

### WebSocket Integration

WebSocket handlers are in the `websockets/` directory and provide real-time progress updates for:
- PDF processing
- Reference downloads
- Knowledge base building

## Configuration

The backend uses the same configuration as the existing system:
- Vector store directory: `./vector_stores`
- Downloaded references: `./downloaded_references`
- Uploaded PDFs: `./uploaded_pdfs`

## Error Handling

All endpoints include comprehensive error handling:
- Input validation using Pydantic models
- Graceful handling of agent errors
- Proper HTTP status codes
- Detailed error messages for debugging 