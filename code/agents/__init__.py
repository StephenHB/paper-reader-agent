from .paper_agent import PaperAgent
from .process_pdf import PDFProcessor
from .vector_store import VectorStoreBuilder
from .reference_extractor import ReferenceExtractor, Reference, ExtractionConfig
from .mcp_fetch_client import MCPFetchClient, MCPFetchConfig, MCPFetchResult
from .reference_downloader import ReferenceDownloader
from .reference_manager import ReferenceManager, DownloadConfig, ConsentRecord

__all__ = [
    'PaperAgent',
    'PDFProcessor', 
    'VectorStoreBuilder',
    'ReferenceExtractor',
    'Reference',
    'ExtractionConfig',
    'MCPFetchClient',
    'MCPFetchConfig',
    'MCPFetchResult',
    'ReferenceDownloader',
    'ReferenceManager',
    'DownloadConfig',
    'ConsentRecord'
]
