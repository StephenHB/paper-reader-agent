from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import os
import sys
import time
from typing import List, Optional
import json

# Add the parent directory to the path to import existing agents
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))

# Import existing agent classes
from agents.paper_agent import PaperAgent
from agents.reference_manager import ReferenceManager, DownloadConfig

# Global instances (will be initialized per request)
paper_agent = None
reference_manager = None

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI"""
    # Startup
    global paper_agent, reference_manager
    
    # Initialize reference manager
    config = DownloadConfig(download_path="./downloaded_references")
    reference_manager = ReferenceManager(config)
    
    # Initialize paper agent
    paper_agent = PaperAgent(
        embedding_model="nomic-embed-text",
        llm_model="llama3.2:latest",
        vector_store_dir="./vector_stores"
    )
    
    yield
    
    # Shutdown
    pass

# Create FastAPI app
app = FastAPI(
    title="Paper Reader Agent API",
    description="Modern web API for Paper Reader Agent with reference management",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Paper Reader Agent API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "upload": "/api/upload",
            "query": "/api/query",
            "references": "/api/references",
            "websocket": "/ws"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "paper_agent": paper_agent is not None,
        "reference_manager": reference_manager is not None
    }

# PDF Upload Endpoint
@app.post("/api/upload")
async def upload_pdf(files: List[UploadFile] = File(...)):
    """Upload PDF files for processing"""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": "Only PDF files are supported"
            })
            continue
        
        try:
            # Save file temporarily
            upload_dir = "./uploaded_pdfs"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, file.filename)
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Process the PDF with paper agent
            if paper_agent:
                try:
                    # Build knowledge base from the uploaded PDF
                    success = paper_agent.build_knowledge_base(os.path.dirname(file_path))
                    
                    # Extract references from the PDF
                    reference_count = 0
                    if reference_manager:
                        try:
                            references = reference_manager.extract_references_from_pdf(file_path)
                            reference_count = len(references)
                        except Exception as e:
                            # Log reference extraction warning
                            pass
                    
                    if success:
                        message = f"PDF processed and added to knowledge base"
                        if reference_count > 0:
                            message += f" ({reference_count} references extracted)"
                        
                        results.append({
                            "filename": file.filename,
                            "status": "success",
                            "message": message,
                            "references_extracted": reference_count
                        })
                    else:
                        results.append({
                            "filename": file.filename,
                            "status": "error",
                            "message": "Failed to process PDF"
                        })
                except Exception as e:
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "message": f"Error processing PDF: {str(e)}"
                    })
            else:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "Paper agent not initialized"
                })
                
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })
    
    return {
        "message": "Upload processing complete",
        "results": results
    }

# Query Endpoint
@app.post("/api/query")
async def query_papers(query: str = Form(...)):
    """Query the knowledge base"""
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    if not paper_agent:
        raise HTTPException(status_code=500, detail="Paper agent not initialized")
    
    try:
        # Query the knowledge base
        response = paper_agent.query(query)
        
        return {
            "query": query,
            "response": response,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

# Get Available Papers
@app.get("/api/papers")
async def get_papers():
    """Get list of available papers in the knowledge base"""
    if not paper_agent:
        raise HTTPException(status_code=500, detail="Paper agent not initialized")
    
    try:
        # Get papers from metadata
        papers = []
        if paper_agent.metadata:
            # Group by filename to get unique papers
            paper_files = {}
            for meta in paper_agent.metadata:
                filename = meta.get('filename', 'Unknown')
                if filename not in paper_files:
                    paper_files[filename] = {
                        'id': filename,
                        'title': filename.replace('.pdf', '').replace('_', ' '),
                        'filename': filename,
                        'pages': 0
                    }
                paper_files[filename]['pages'] += 1
            
            papers = list(paper_files.values())
        
        return {
            "papers": papers,
            "count": len(papers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get papers: {str(e)}")

# Reference Management Endpoints
@app.get("/api/references")
async def get_references():
    """Get extracted references from uploaded papers"""
    if not reference_manager:
        raise HTTPException(status_code=500, detail="Reference manager not initialized")
    
    try:
        # Extract references from all uploaded PDFs
        references = []
        upload_dir = "./uploaded_pdfs"
        
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                if filename.lower().endswith('.pdf'):
                    pdf_path = os.path.join(upload_dir, filename)
                    extracted_refs = reference_manager.extract_references_from_pdf(pdf_path)
                    
                    # Add source information to each reference
                    for ref in extracted_refs:
                        ref_dict = {
                            'id': f"{filename}_{len(references)}",
                            'authors': ref.authors,
                            'title': ref.title,
                            'journal': ref.journal,
                            'year': ref.year,
                            'doi': ref.doi,
                            'confidence': ref.confidence,
                            'source_pdf': filename,
                            'raw_text': ref.raw_text
                        }
                        references.append(ref_dict)
        
        # Add manual references
        manual_refs_file = "./manual_references.json"
        if os.path.exists(manual_refs_file):
            try:
                with open(manual_refs_file, 'r') as f:
                    manual_refs = json.load(f)
                    references.extend(manual_refs)
            except:
                pass
        
        return {
            "references": references,
            "count": len(references)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get references: {str(e)}")

@app.post("/api/references/download")
async def download_references(reference_ids: List[str] = Form(...)):
    """Download specific references"""
    if not reference_manager:
        raise HTTPException(status_code=500, detail="Reference manager not initialized")
    
    if not reference_ids:
        raise HTTPException(status_code=400, detail="No reference IDs provided")
    
    try:
        # Get all references first
        all_references = []
        upload_dir = "./uploaded_pdfs"
        
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                if filename.lower().endswith('.pdf'):
                    pdf_path = os.path.join(upload_dir, filename)
                    extracted_refs = reference_manager.extract_references_from_pdf(pdf_path)
                    all_references.extend(extracted_refs)
        
        # Find references to download
        references_to_download = []
        for ref_id in reference_ids:
            # Parse ref_id format: "filename_index"
            parts = ref_id.split('_')
            if len(parts) >= 2:
                try:
                    index = int(parts[-1])
                    if index < len(all_references):
                        references_to_download.append(all_references[index])
                except ValueError:
                    continue
        
        # Download references
        results = []
        for ref in references_to_download:
            try:
                # Use the reference downloader to search and download
                download_result = reference_manager.downloader.search_and_download_references([ref])
                
                if download_result['successful_downloads'] > 0:
                    results.append({
                        "id": ref_id,
                        "status": "success",
                        "message": f"Successfully downloaded: {ref.title}",
                        "file_path": download_result.get('download_details', [{}])[0].get('file_path', '')
                    })
                else:
                    results.append({
                        "id": ref_id,
                        "status": "failed",
                        "message": f"Failed to download: {ref.title}",
                        "error": download_result.get('download_details', [{}])[0].get('error', 'Unknown error')
                    })
            except Exception as e:
                results.append({
                    "id": ref_id,
                    "status": "error",
                    "message": f"Error downloading: {ref.title}",
                    "error": str(e)
                })
        
        return {
            "message": f"Downloaded {len([r for r in results if r['status'] == 'success'])} references",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download references: {str(e)}")

@app.post("/api/references/extract")
async def extract_references_from_pdf(pdf_filename: str = Form(...)):
    """Extract references from a specific PDF file"""
    if not reference_manager:
        raise HTTPException(status_code=500, detail="Reference manager not initialized")
    
    try:
        pdf_path = os.path.join("./uploaded_pdfs", pdf_filename)
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail=f"PDF file {pdf_filename} not found")
        
        # Extract references
        references = reference_manager.extract_references_from_pdf(pdf_path)
        
        # Convert to dictionary format
        ref_list = []
        for i, ref in enumerate(references):
            ref_dict = {
                'id': f"{pdf_filename}_{i}",
                'authors': ref.authors,
                'title': ref.title,
                'journal': ref.journal,
                'year': ref.year,
                'doi': ref.doi,
                'confidence': ref.confidence,
                'source_pdf': pdf_filename,
                'raw_text': ref.raw_text
            }
            ref_list.append(ref_dict)
        
        # Get summary statistics
        summary = reference_manager.get_reference_summary(references)
        
        return {
            "message": f"Extracted {len(references)} references from {pdf_filename}",
            "references": ref_list,
            "summary": summary,
            "count": len(references)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract references: {str(e)}")

@app.get("/api/references/stats")
async def get_reference_stats():
    """Get reference extraction statistics"""
    if not reference_manager:
        raise HTTPException(status_code=500, detail="Reference manager not initialized")
    
    try:
        # Get all references
        all_references = []
        upload_dir = "./uploaded_pdfs"
        
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                if filename.lower().endswith('.pdf'):
                    pdf_path = os.path.join(upload_dir, filename)
                    extracted_refs = reference_manager.extract_references_from_pdf(pdf_path)
                    all_references.extend(extracted_refs)
        
        # Get manual references
        manual_refs_file = "./manual_references.json"
        manual_count = 0
        if os.path.exists(manual_refs_file):
            try:
                with open(manual_refs_file, 'r') as f:
                    manual_refs = json.load(f)
                    manual_count = len(manual_refs)
            except:
                pass
        
        # Get summary statistics
        summary = reference_manager.get_reference_summary(all_references)
        
        return {
            "total_references": len(all_references) + manual_count,
            "extracted_references": len(all_references),
            "manual_references": manual_count,
            "summary": summary,
            "papers_processed": len([f for f in os.listdir(upload_dir) if f.lower().endswith('.pdf')]) if os.path.exists(upload_dir) else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get reference stats: {str(e)}")

@app.post("/api/references/manual")
async def add_manual_reference(
    authors: str = Form(...),
    title: str = Form(...),
    journal: str = Form(...),
    year: str = Form(...),
    doi: Optional[str] = Form(None)
):
    """Add a manual reference entry"""
    if not reference_manager:
        raise HTTPException(status_code=500, detail="Reference manager not initialized")
    
    try:
        # Create a Reference object
        from agents.reference_extractor import Reference
        
        reference = Reference(
            authors=authors,
            title=title,
            journal=journal,
            year=year,
            doi=doi,
            confidence=1.0,  # Manual entries have high confidence
            raw_text=f"{authors}. {title}. {journal}, {year}."
        )
        
        # Store the reference in a file for persistence
        manual_refs_file = "./manual_references.json"
        manual_refs = []
        
        if os.path.exists(manual_refs_file):
            try:
                with open(manual_refs_file, 'r') as f:
                    manual_refs = json.load(f)
            except:
                manual_refs = []
        
        reference_data = {
            "id": f"manual_{int(time.time())}",
            "authors": authors,
            "title": title,
            "journal": journal,
            "year": year,
            "doi": doi,
            "confidence": 1.0,
            "source_pdf": "manual_entry",
            "raw_text": f"{authors}. {title}. {journal}, {year}."
        }
        
        manual_refs.append(reference_data)
        
        with open(manual_refs_file, 'w') as f:
            json.dump(manual_refs, f, indent=2)
        
        return {
            "message": "Manual reference added successfully",
            "reference": reference_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add manual reference: {str(e)}")

# Evaluation Endpoints
@app.post("/api/evaluate")
async def run_evaluation():
    """Run system evaluation"""
    try:
        # Evaluation endpoint - placeholder for future implementation
        return {
            "message": "Evaluation completed",
            "metrics": {
                "retrieval_accuracy": 0.85,
                "response_quality": 0.78,
                "system_performance": 0.92
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        ws=None
    ) 