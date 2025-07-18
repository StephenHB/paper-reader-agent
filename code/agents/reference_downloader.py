import requests
import time
import os
import re
import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReferenceDownloader:
    """Download reference papers from academic databases"""
    
    def __init__(self, download_dir: str = "./downloaded_references"):
        """
        Initialize the reference downloader
        
        Args:
            download_dir: Directory to store downloaded papers
        """
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        
        # API endpoints and configurations
        self.arxiv_api_url = "http://export.arxiv.org/api/query"
        self.pubmed_api_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        
        # Rate limiting settings
        self.arxiv_delay = 3  # seconds between arXiv requests
        self.pubmed_delay = 1  # seconds between PubMed requests
        self.last_arxiv_request = 0
        self.last_pubmed_request = 0
        
        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_and_download_references(self, references: List, progress_callback=None) -> Dict:
        """
        Search and download multiple references
        
        Args:
            references: List of Reference objects
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with download results
        """
        results = {
            'total_references': len(references),
            'successful_downloads': 0,
            'failed_downloads': 0,
            'skipped_downloads': 0,
            'download_details': []
        }
        
        for i, reference in enumerate(references):
            if progress_callback:
                progress_callback(i, len(references), f"Processing {reference.title[:50]}...")
            
            try:
                download_result = self.download_single_reference(reference)
                results['download_details'].append(download_result)
                
                if download_result['status'] == 'success':
                    results['successful_downloads'] += 1
                elif download_result['status'] == 'skipped':
                    results['skipped_downloads'] += 1
                else:
                    results['failed_downloads'] += 1
                    
            except Exception as e:
                logger.error(f"Error downloading reference {reference.title}: {str(e)}")
                results['failed_downloads'] += 1
                results['download_details'].append({
                    'reference': reference,
                    'status': 'error',
                    'error': str(e),
                    'file_path': None
                })
        
        return results
    
    def download_single_reference(self, reference) -> Dict:
        """
        Download a single reference paper
        
        Args:
            reference: Reference object
            
        Returns:
            Dictionary with download result
        """
        # Check if already downloaded
        existing_file = self._check_existing_download(reference)
        if existing_file:
            return {
                'reference': reference,
                'status': 'skipped',
                'message': 'Already downloaded',
                'file_path': existing_file
            }
        
        # Try different search methods in order of preference
        search_methods = [
            self._search_arxiv,
            self._search_pubmed,
            self._search_google_scholar
        ]
        
        for method in search_methods:
            try:
                download_url = method(reference)
                if download_url:
                    file_path = self._download_pdf(download_url, reference)
                    if file_path:
                        return {
                            'reference': reference,
                            'status': 'success',
                            'message': f'Downloaded via {method.__name__}',
                            'file_path': file_path,
                            'source': method.__name__
                        }
            except Exception as e:
                logger.debug(f"Method {method.__name__} failed: {str(e)}")
                continue
        
        return {
            'reference': reference,
            'status': 'failed',
            'message': 'No download source found',
            'file_path': None
        }
    
    def _search_arxiv(self, reference) -> Optional[str]:
        """
        Search arXiv for the reference
        
        Args:
            reference: Reference object
            
        Returns:
            Download URL if found, None otherwise
        """
        # Rate limiting
        self._rate_limit_arxiv()
        
        # Build search query
        query_parts = []
        if reference.title:
            query_parts.append(f'ti:"{reference.title}"')
        if reference.authors:
            # Extract first author's last name
            first_author = reference.authors.split(',')[0].strip()
            if ' ' in first_author:
                last_name = first_author.split()[-1]
                query_parts.append(f'au:"{last_name}"')
        
        if not query_parts:
            return None
        
        query = ' AND '.join(query_parts)
        
        try:
            params = {
                'search_query': query,
                'start': 0,
                'max_results': 5,
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }
            
            response = self.session.get(self.arxiv_api_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse XML response
            soup = BeautifulSoup(response.content, 'xml')
            entries = soup.find_all('entry')
            
            for entry in entries:
                title = entry.find('title').text.strip() if entry.find('title') else ""
                authors = [author.find('name').text.strip() for author in entry.find_all('author')]
                
                # Check if this matches our reference
                if self._is_similar_paper(reference, title, authors):
                    # Get PDF download link
                    pdf_link = entry.find('link', title='pdf')
                    if pdf_link and pdf_link.get('href'):
                        return pdf_link['href']
            
            return None
            
        except Exception as e:
            logger.error(f"arXiv search failed: {str(e)}")
            return None
    
    def _search_pubmed(self, reference) -> Optional[str]:
        """
        Search PubMed for the reference
        
        Args:
            reference: Reference object
            
        Returns:
            Download URL if found, None otherwise
        """
        # Rate limiting
        self._rate_limit_pubmed()
        
        # Build search query
        query_parts = []
        if reference.title:
            query_parts.append(f'"{reference.title}"[Title]')
        if reference.authors:
            first_author = reference.authors.split(',')[0].strip()
            if ' ' in first_author:
                last_name = first_author.split()[-1]
                query_parts.append(f'"{last_name}"[Author]')
        
        if not query_parts:
            return None
        
        query = ' AND '.join(query_parts)
        
        try:
            # Search for papers
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmode': 'json',
                'retmax': 5
            }
            
            search_url = f"{self.pubmed_api_url}/esearch.fcgi"
            response = self.session.get(search_url, params=search_params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'esearchresult' not in data or 'idlist' not in data['esearchresult']:
                return None
            
            paper_ids = data['esearchresult']['idlist']
            
            # Get paper details
            for paper_id in paper_ids[:3]:  # Limit to first 3 results
                fetch_params = {
                    'db': 'pubmed',
                    'id': paper_id,
                    'retmode': 'xml'
                }
                
                fetch_url = f"{self.pubmed_api_url}/efetch.fcgi"
                response = self.session.get(fetch_url, params=fetch_params, timeout=30)
                response.raise_for_status()
                
                # Parse XML response
                soup = BeautifulSoup(response.content, 'xml')
                article = soup.find('PubmedArticle')
                
                if article:
                    title = article.find('ArticleTitle')
                    title_text = title.text.strip() if title and hasattr(title, 'text') else ""
                    
                    authors = []
                    author_list = article.find('AuthorList')
                    if author_list and hasattr(author_list, 'find_all'):
                        for author in author_list.find_all('Author'):
                            last_name = author.find('LastName')
                            first_name = author.find('ForeName')
                            if last_name and first_name and hasattr(last_name, 'text') and hasattr(first_name, 'text'):
                                authors.append(f"{last_name.text} {first_name.text}")
                    
                    # Check if this matches our reference
                    if self._is_similar_paper(reference, title_text, authors):
                        # Try to find PDF link (PubMed Central)
                        pmc_link = self._find_pmc_pdf(paper_id)
                        if pmc_link:
                            return pmc_link
            
            return None
            
        except Exception as e:
            logger.error(f"PubMed search failed: {str(e)}")
            return None
    
    def _search_google_scholar(self, reference) -> Optional[str]:
        """
        Search Google Scholar for the reference (fallback method)
        
        Args:
            reference: Reference object
            
        Returns:
            Download URL if found, None otherwise
        """
        # Note: Google Scholar doesn't have a public API, so this is a basic implementation
        # In a real implementation, you might use a service like SerpAPI or similar
        
        try:
            # Build search query
            query_parts = []
            if reference.title:
                query_parts.append(f'"{reference.title}"')
            if reference.authors:
                first_author = reference.authors.split(',')[0].strip()
                query_parts.append(first_author)
            
            if not query_parts:
                return None
            
            query = ' '.join(query_parts)
            
            # This is a placeholder - in practice, you'd need to use a service
            # that can scrape Google Scholar or use an API service
            logger.info(f"Google Scholar search would be performed for: {query}")
            
            # For now, return None to indicate no direct download available
            return None
            
        except Exception as e:
            logger.error(f"Google Scholar search failed: {str(e)}")
            return None
    
    def _find_pmc_pdf(self, pubmed_id: str) -> Optional[str]:
        """
        Find PDF link in PubMed Central
        
        Args:
            pubmed_id: PubMed ID
            
        Returns:
            PDF URL if found, None otherwise
        """
        try:
            # Check if paper is in PubMed Central
            pmc_params = {
                'db': 'pmc',
                'term': f'{pubmed_id}[pmid]',
                'retmode': 'json'
            }
            
            pmc_url = f"{self.pubmed_api_url}/esearch.fcgi"
            response = self.session.get(pmc_url, params=pmc_params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'esearchresult' in data and 'idlist' in data['esearchresult']:
                pmc_ids = data['esearchresult']['idlist']
                if pmc_ids:
                    # Return PMC PDF URL
                    return f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_ids[0]}/pdf/"
            
            return None
            
        except Exception as e:
            logger.error(f"PMC PDF search failed: {str(e)}")
            return None
    
    def _download_pdf(self, url: str, reference) -> Optional[str]:
        """
        Download PDF from URL
        
        Args:
            url: PDF download URL
            reference: Reference object for filename
            
        Returns:
            File path if successful, None otherwise
        """
        try:
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Check if response is actually a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and not url.endswith('.pdf'):
                logger.warning(f"URL does not appear to be a PDF: {content_type}")
                return None
            
            # Generate filename
            filename = self._generate_filename(reference)
            file_path = os.path.join(self.download_dir, filename)
            
            # Download file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded: {filename}")
            return file_path
            
        except Exception as e:
            logger.error(f"PDF download failed: {str(e)}")
            return None
    
    def _generate_filename(self, reference) -> str:
        """
        Generate filename for downloaded paper
        
        Args:
            reference: Reference object
            
        Returns:
            Generated filename
        """
        # Clean title for filename
        title = re.sub(r'[^\w\s-]', '', reference.title)
        title = re.sub(r'[-\s]+', '_', title)
        title = title[:50]  # Limit length
        
        # Add year if available
        year = reference.year if reference.year else "unknown"
        
        return f"{title}_{year}.pdf"
    
    def _check_existing_download(self, reference) -> Optional[str]:
        """
        Check if reference is already downloaded
        
        Args:
            reference: Reference object
            
        Returns:
            File path if exists, None otherwise
        """
        filename = self._generate_filename(reference)
        file_path = os.path.join(self.download_dir, filename)
        
        if os.path.exists(file_path):
            return file_path
        
        return None
    
    def _is_similar_paper(self, reference, title: str, authors: List[str]) -> bool:
        """
        Check if a paper matches our reference
        
        Args:
            reference: Reference object
            title: Paper title
            authors: List of author names
            
        Returns:
            True if similar, False otherwise
        """
        # Simple similarity check - could be improved with more sophisticated matching
        if not title or not reference.title:
            return False
        
        # Check title similarity
        ref_title_lower = reference.title.lower()
        title_lower = title.lower()
        
        # Simple word overlap check
        ref_words = set(ref_title_lower.split())
        title_words = set(title_lower.split())
        
        if len(ref_words) > 0:
            overlap = len(ref_words.intersection(title_words)) / len(ref_words)
            if overlap < 0.3:  # At least 30% word overlap
                return False
        
        # Check year if available
        if reference.year and reference.year in title:
            return True
        
        # Check authors if available
        if authors and reference.authors:
            ref_authors = [name.strip().lower() for name in reference.authors.split(',')]
            for author in authors:
                author_lower = author.lower()
                for ref_author in ref_authors:
                    if ref_author in author_lower or author_lower in ref_author:
                        return True
        
        return True  # Default to True if basic checks pass
    
    def _rate_limit_arxiv(self):
        """Rate limiting for arXiv API"""
        current_time = time.time()
        time_since_last = current_time - self.last_arxiv_request
        if time_since_last < self.arxiv_delay:
            sleep_time = self.arxiv_delay - time_since_last
            time.sleep(sleep_time)
        self.last_arxiv_request = time.time()
    
    def _rate_limit_pubmed(self):
        """Rate limiting for PubMed API"""
        current_time = time.time()
        time_since_last = current_time - self.last_pubmed_request
        if time_since_last < self.pubmed_delay:
            sleep_time = self.pubmed_delay - time_since_last
            time.sleep(sleep_time)
        self.last_pubmed_request = time.time()
    
    def get_download_stats(self, results: Dict) -> Dict:
        """
        Get statistics about download results
        
        Args:
            results: Download results dictionary
            
        Returns:
            Statistics dictionary
        """
        total = results['total_references']
        successful = results['successful_downloads']
        failed = results['failed_downloads']
        skipped = results['skipped_downloads']
        
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            'total_references': total,
            'successful_downloads': successful,
            'failed_downloads': failed,
            'skipped_downloads': skipped,
            'success_rate': success_rate,
            'download_dir': self.download_dir
        } 