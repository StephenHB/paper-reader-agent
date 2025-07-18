import os
import json
import time
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from .reference_extractor import ReferenceExtractor, Reference
from .reference_downloader import ReferenceDownloader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConsentRecord:
    """Record of user consent for reference downloading"""
    timestamp: str
    user_id: str
    pdf_filename: str
    total_references: int
    selected_references: int
    download_path: str
    consent_given: bool
    session_id: str


@dataclass
class DownloadConfig:
    """Configuration for reference downloading"""
    download_path: str
    max_concurrent_downloads: int = 3
    retry_attempts: int = 3
    timeout_seconds: int = 60
    enable_arxiv: bool = True
    enable_pubmed: bool = True
    enable_google_scholar: bool = False
    rate_limit_delay: float = 1.0


class ReferenceManager:
    """Manage reference extraction, user consent, and downloading"""
    
    def __init__(self, config: Optional[DownloadConfig] = None):
        """
        Initialize the reference manager
        
        Args:
            config: Download configuration
        """
        self.config = config if config is not None else DownloadConfig(download_path="./downloaded_references")
        self.extractor = ReferenceExtractor()
        self.downloader = ReferenceDownloader(self.config.download_path)
        
        # Create necessary directories
        os.makedirs(self.config.download_path, exist_ok=True)
        os.makedirs("./logs", exist_ok=True)
        
        # Initialize consent log file
        self.consent_log_path = "./logs/consent_log.jsonl"
        self._init_consent_log()
    
    def _init_consent_log(self):
        """Initialize consent log file if it doesn't exist"""
        if not os.path.exists(self.consent_log_path):
            with open(self.consent_log_path, 'w') as f:
                pass  # Create empty file
    
    def extract_references_from_pdf(self, pdf_path: str) -> List[Reference]:
        """
        Extract references from a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of extracted references
        """
        try:
            references = self.extractor.extract_references_from_pdf(pdf_path)
            logger.info(f"Extracted {len(references)} references from {pdf_path}")
            return references
        except Exception as e:
            logger.error(f"Error extracting references from {pdf_path}: {str(e)}")
            return []
    
    def get_reference_summary(self, references: List[Reference]) -> Dict:
        """
        Get a summary of extracted references for user display
        
        Args:
            references: List of references
            
        Returns:
            Summary dictionary
        """
        if not references:
            return {
                'total_references': 0,
                'high_confidence': 0,
                'medium_confidence': 0,
                'low_confidence': 0,
                'with_doi': 0,
                'with_year': 0,
                'sample_references': []
            }
        
        # Get statistics
        stats = self.extractor.get_extraction_stats(references)
        
        # Get sample references for display
        sample_references = []
        for ref in references[:5]:  # Show first 5
            sample_references.append({
                'authors': ref.authors,
                'title': ref.title,
                'journal': ref.journal,
                'year': ref.year,
                'doi': ref.doi,
                'confidence': ref.confidence
            })
        
        return {
            **stats,
            'sample_references': sample_references
        }
    
    def log_consent(self, consent_record: ConsentRecord):
        """
        Log user consent decision
        
        Args:
            consent_record: Consent record to log
        """
        try:
            with open(self.consent_log_path, 'a') as f:
                f.write(json.dumps(asdict(consent_record)) + '\n')
            logger.info(f"Consent logged for {consent_record.pdf_filename}")
        except Exception as e:
            logger.error(f"Error logging consent: {str(e)}")
    
    def get_consent_history(self, user_id: Optional[str] = None, limit: int = 100) -> List[ConsentRecord]:
        """
        Get consent history for audit purposes
        
        Args:
            user_id: Optional user ID to filter by
            limit: Maximum number of records to return
            
        Returns:
            List of consent records
        """
        records = []
        try:
            with open(self.consent_log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        record = ConsentRecord(**data)
                        if user_id is None or record.user_id == user_id:
                            records.append(record)
                            if len(records) >= limit:
                                break
        except Exception as e:
            logger.error(f"Error reading consent history: {str(e)}")
        
        return records
    
    def download_selected_references(self, 
                                   references: List[Reference], 
                                   selected_indices: List[int],
                                   progress_callback=None) -> Dict:
        """
        Download selected references
        
        Args:
            references: List of all references
            selected_indices: Indices of references to download
            progress_callback: Optional progress callback function
            
        Returns:
            Download results dictionary
        """
        if not selected_indices:
            return {
                'total_references': 0,
                'successful_downloads': 0,
                'failed_downloads': 0,
                'skipped_downloads': 0,
                'download_details': []
            }
        
        # Get selected references
        selected_references = [references[i] for i in selected_indices if i < len(references)]
        
        # Download references
        results = self.downloader.search_and_download_references(
            selected_references, 
            progress_callback
        )
        
        # Get statistics
        stats = self.downloader.get_download_stats(results)
        logger.info(f"Download completed: {stats['successful_downloads']}/{stats['total_references']} successful")
        
        return results
    
    def process_pdf_with_consent(self, 
                               pdf_path: str, 
                               user_id: str,
                               session_id: str,
                               consent_given: bool,
                               selected_reference_indices: Optional[List[int]] = None,
                               custom_download_path: Optional[str] = None) -> Dict:
        """
        Process a PDF with user consent for reference downloading
        
        Args:
            pdf_path: Path to the PDF file
            user_id: User identifier
            session_id: Session identifier
            consent_given: Whether user gave consent
            selected_reference_indices: Indices of references to download (if consent given)
            custom_download_path: Custom download path (optional)
            
        Returns:
            Processing results dictionary
        """
        results = {
            'pdf_filename': os.path.basename(pdf_path),
            'references_extracted': 0,
            'consent_given': consent_given,
            'download_results': None,
            'error': None
        }
        
        try:
            # Extract references
            references = self.extract_references_from_pdf(pdf_path)
            results['references_extracted'] = len(references)
            
            # Update download path if custom path provided
            if custom_download_path:
                self.config.download_path = custom_download_path
                self.downloader.download_dir = custom_download_path
                os.makedirs(custom_download_path, exist_ok=True)
            
            # Log consent
            consent_record = ConsentRecord(
                timestamp=datetime.now().isoformat(),
                user_id=user_id,
                pdf_filename=os.path.basename(pdf_path),
                total_references=len(references),
                selected_references=len(selected_reference_indices) if selected_reference_indices else 0,
                download_path=self.config.download_path,
                consent_given=consent_given,
                session_id=session_id
            )
            self.log_consent(consent_record)
            
            # Download references if consent given
            if consent_given and selected_reference_indices and references:
                download_results = self.download_selected_references(
                    references, 
                    selected_reference_indices
                )
                results['download_results'] = download_results
            
            logger.info(f"PDF processing completed: {pdf_path}")
            
        except Exception as e:
            error_msg = f"Error processing PDF {pdf_path}: {str(e)}"
            logger.error(error_msg)
            results['error'] = error_msg
        
        return results
    
    def batch_process_pdfs(self, 
                          pdf_paths: List[str], 
                          user_id: str,
                          session_id: str,
                          consent_given: bool,
                          selected_references_map: Optional[Dict[str, List[int]]] = None,
                          custom_download_path: Optional[str] = None,
                          progress_callback=None) -> Dict:
        """
        Process multiple PDFs with batch consent
        
        Args:
            pdf_paths: List of PDF file paths
            user_id: User identifier
            session_id: Session identifier
            consent_given: Whether user gave consent for all PDFs
            selected_references_map: Map of PDF path to selected reference indices
            custom_download_path: Custom download path (optional)
            progress_callback: Optional progress callback function
            
        Returns:
            Batch processing results
        """
        batch_results = {
            'total_pdfs': len(pdf_paths),
            'processed_pdfs': 0,
            'successful_pdfs': 0,
            'failed_pdfs': 0,
            'total_references_extracted': 0,
            'total_references_downloaded': 0,
            'pdf_results': []
        }
        
        for i, pdf_path in enumerate(pdf_paths):
            if progress_callback:
                progress_callback(i, len(pdf_paths), f"Processing {os.path.basename(pdf_path)}...")
            
            try:
                # Get selected references for this PDF
                selected_indices = selected_references_map.get(pdf_path, []) if selected_references_map else None
                
                # Process PDF
                result = self.process_pdf_with_consent(
                    pdf_path=pdf_path,
                    user_id=user_id,
                    session_id=session_id,
                    consent_given=consent_given,
                    selected_reference_indices=selected_indices,
                    custom_download_path=custom_download_path
                )
                
                batch_results['pdf_results'].append(result)
                batch_results['processed_pdfs'] += 1
                
                if result['error'] is None:
                    batch_results['successful_pdfs'] += 1
                    batch_results['total_references_extracted'] += result['references_extracted']
                    
                    if result['download_results'] and isinstance(result['download_results'], dict):
                        batch_results['total_references_downloaded'] += result['download_results'].get('successful_downloads', 0)
                else:
                    batch_results['failed_pdfs'] += 1
                    
            except Exception as e:
                logger.error(f"Error in batch processing {pdf_path}: {str(e)}")
                batch_results['failed_pdfs'] += 1
                batch_results['pdf_results'].append({
                    'pdf_filename': os.path.basename(pdf_path),
                    'error': str(e)
                })
        
        logger.info(f"Batch processing completed: {batch_results['successful_pdfs']}/{batch_results['total_pdfs']} successful")
        return batch_results
    
    def get_download_path_info(self) -> Dict:
        """
        Get information about the download path
        
        Returns:
            Dictionary with download path information
        """
        try:
            path = Path(self.config.download_path)
            if path.exists():
                files = list(path.glob("*.pdf"))
                total_size = sum(f.stat().st_size for f in files)
                
                return {
                    'path': str(path.absolute()),
                    'exists': True,
                    'file_count': len(files),
                    'total_size_mb': round(total_size / (1024 * 1024), 2),
                    'writable': os.access(path, os.W_OK)
                }
            else:
                return {
                    'path': str(path.absolute()),
                    'exists': False,
                    'file_count': 0,
                    'total_size_mb': 0,
                    'writable': False
                }
        except Exception as e:
            logger.error(f"Error getting download path info: {str(e)}")
            return {
                'path': self.config.download_path,
                'exists': False,
                'file_count': 0,
                'total_size_mb': 0,
                'writable': False,
                'error': str(e)
            }
    
    def cleanup_downloads(self, older_than_days: int = 30) -> Dict:
        """
        Clean up old downloaded files
        
        Args:
            older_than_days: Remove files older than this many days
            
        Returns:
            Cleanup results
        """
        results = {
            'files_removed': 0,
            'space_freed_mb': 0,
            'errors': []
        }
        
        try:
            path = Path(self.config.download_path)
            if not path.exists():
                return results
            
            cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
            
            for file_path in path.glob("*.pdf"):
                try:
                    if file_path.stat().st_mtime < cutoff_time:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        results['files_removed'] += 1
                        results['space_freed_mb'] += file_size / (1024 * 1024)
                except Exception as e:
                    results['errors'].append(f"Error removing {file_path}: {str(e)}")
            
            results['space_freed_mb'] = round(results['space_freed_mb'], 2)
            logger.info(f"Cleanup completed: {results['files_removed']} files removed, {results['space_freed_mb']} MB freed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            results['errors'].append(str(e))
        
        return results
    
    def validate_config(self) -> Dict:
        """
        Validate the current configuration
        
        Returns:
            Validation results
        """
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check download path
        try:
            path = Path(self.config.download_path)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                validation_results['warnings'].append(f"Created download directory: {path}")
            
            if not os.access(path, os.W_OK):
                validation_results['valid'] = False
                validation_results['errors'].append(f"Download path not writable: {path}")
        except Exception as e:
            validation_results['valid'] = False
            validation_results['errors'].append(f"Invalid download path: {str(e)}")
        
        # Check configuration values
        if self.config.max_concurrent_downloads < 1:
            validation_results['warnings'].append("max_concurrent_downloads should be at least 1")
        
        if self.config.retry_attempts < 0:
            validation_results['warnings'].append("retry_attempts should be non-negative")
        
        if self.config.timeout_seconds < 10:
            validation_results['warnings'].append("timeout_seconds should be at least 10 seconds")
        
        return validation_results 