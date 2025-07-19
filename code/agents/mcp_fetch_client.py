"""
MCP Fetch Client for enhanced online resource downloading
"""

import json
import logging
import time
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
import requests

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MCPFetchConfig:
    """Configuration for MCP fetch operations"""
    enabled: bool = True
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_delay: float = 0.5
    user_agent: str = "PaperReaderAgent/2.0.0"


@dataclass
class MCPFetchResult:
    """Result of MCP fetch operation"""
    success: bool
    url: str
    content: Optional[bytes] = None
    content_type: Optional[str] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None


class MCPFetchClient:
    """Enhanced fetch client with MCP-like capabilities for academic resource downloading"""
    
    def __init__(self, config: Optional[MCPFetchConfig] = None):
        """
        Initialize MCP fetch client
        
        Args:
            config: Configuration for fetch operations
        """
        self.config = config if config is not None else MCPFetchConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Academic database endpoints
        self.academic_sources = {
            'arxiv': {
                'base_url': 'https://arxiv.org',
                'api_url': 'http://export.arxiv.org/api/query',
                'pdf_pattern': r'https://arxiv\.org/pdf/([^/]+)',
                'search_pattern': r'https://arxiv\.org/abs/([^/]+)'
            },
            'pubmed': {
                'base_url': 'https://pubmed.ncbi.nlm.nih.gov',
                'api_url': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils',
                'pdf_pattern': r'https://www\.ncbi\.nlm\.nih\.gov/pmc/articles/PMC\d+/pdf/',
                'search_pattern': r'https://pubmed\.ncbi\.nlm\.nih\.gov/(\d+)'
            },
            'biorxiv': {
                'base_url': 'https://www.biorxiv.org',
                'pdf_pattern': r'https://www\.biorxiv\.org/content/.*?\.full\.pdf',
                'search_pattern': r'https://www\.biorxiv\.org/content/([^/]+)'
            },
            'medrxiv': {
                'base_url': 'https://www.medrxiv.org',
                'pdf_pattern': r'https://www\.medrxiv\.org/content/.*?\.full\.pdf',
                'search_pattern': r'https://www\.medrxiv\.org/content/([^/]+)'
            },
            'research_square': {
                'base_url': 'https://www.researchsquare.com',
                'pdf_pattern': r'https://www\.researchsquare\.com/article/.*?\.pdf',
                'search_pattern': r'https://www\.researchsquare\.com/article/([^/]+)'
            }
        }
        
        # Rate limiting
        self.last_request_time = 0
    
    def fetch_with_metadata(self, url: str, method: str = 'GET', 
                           headers: Optional[Dict] = None, 
                           data: Optional[Dict] = None) -> MCPFetchResult:
        """
        Enhanced fetch with metadata extraction
        
        Args:
            url: URL to fetch
            method: HTTP method
            headers: Additional headers
            data: Request data
            
        Returns:
            MCPFetchResult with content and metadata
        """
        if not self.config.enabled:
            return MCPFetchResult(
                success=False,
                url=url,
                error="MCP fetch is disabled"
            )
        
        # Rate limiting
        self._rate_limit()
        
        # Prepare request
        request_headers = dict(self.session.headers)
        if headers:
            request_headers.update(headers)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=request_headers,
                data=data,
                timeout=self.config.timeout,
                allow_redirects=True
            )
            
            # Extract metadata
            metadata = self._extract_metadata(response, url)
            
            return MCPFetchResult(
                success=response.status_code == 200,
                url=url,
                content=response.content,
                content_type=response.headers.get('content-type'),
                status_code=response.status_code,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"MCP fetch failed for {url}: {str(e)}")
            return MCPFetchResult(
                success=False,
                url=url,
                error=str(e)
            )
    
    def search_academic_papers(self, query: str, source: str = 'arxiv', 
                             max_results: int = 5) -> List[Dict]:
        """
        Search academic papers using MCP-enhanced methods
        
        Args:
            query: Search query
            source: Academic source ('arxiv', 'pubmed', etc.)
            max_results: Maximum number of results
            
        Returns:
            List of paper metadata
        """
        if source not in self.academic_sources:
            logger.error(f"Unsupported academic source: {source}")
            return []
        
        source_config = self.academic_sources[source]
        
        try:
            if source == 'arxiv':
                return self._search_arxiv_api(query, max_results)
            elif source == 'pubmed':
                return self._search_pubmed_api(query, max_results)
            else:
                return self._search_generic(query, source_config, max_results)
                
        except Exception as e:
            logger.error(f"Academic search failed for {source}: {str(e)}")
            return []
    
    def download_paper_pdf(self, paper_info: Dict, download_dir: str) -> Optional[str]:
        """
        Download paper PDF using MCP-enhanced methods
        
        Args:
            paper_info: Paper information dictionary
            download_dir: Directory to save PDF
            
        Returns:
            Path to downloaded PDF file, or None if failed
        """
        try:
            # Try multiple download strategies
            download_urls = self._get_download_urls(paper_info)
            
            for url in download_urls:
                result = self.fetch_with_metadata(url)
                if result.success and result.content:
                    # Check if content is PDF
                    if self._is_pdf_content(result.content, result.content_type):
                        file_path = self._save_pdf(result.content, paper_info, download_dir)
                        if file_path:
                            return file_path
            
            return None
            
        except Exception as e:
            logger.error(f"PDF download failed: {str(e)}")
            return None
    
    def _extract_metadata(self, response, url: str) -> Dict:
        """Extract metadata from response"""
        metadata = {
            'url': url,
            'status_code': response.status_code,
            'content_type': response.headers.get('content-type'),
            'content_length': len(response.content),
            'headers': dict(response.headers)
        }
        
        # Try to extract academic metadata
        if 'application/pdf' in response.headers.get('content-type', ''):
            metadata['type'] = 'pdf'
        elif 'text/html' in response.headers.get('content-type', ''):
            metadata['type'] = 'html'
            # Could add HTML parsing for academic metadata here
        
        return metadata
    
    def _search_arxiv_api(self, query: str, max_results: int) -> List[Dict]:
        """Search arXiv using API"""
        params = {
            'search_query': query,
            'start': 0,
            'max_results': max_results,
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }
        
        result = self.fetch_with_metadata(
            self.academic_sources['arxiv']['api_url'],
            method='GET',
            headers={'Accept': 'application/xml'}
        )
        
        if result.success and result.content:
            return self._parse_arxiv_response(result.content)
        
        return []
    
    def _search_pubmed_api(self, query: str, max_results: int) -> List[Dict]:
        """Search PubMed using API"""
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'json',
            'tool': 'PaperReaderAgent',
            'email': 'agent@paperreader.com'
        }
        
        result = self.fetch_with_metadata(
            f"{self.academic_sources['pubmed']['api_url']}/esearch.fcgi",
            method='GET',
            data=params
        )
        
        if result.success and result.content:
            return self._parse_pubmed_response(result.content)
        
        return []
    
    def _search_generic(self, query: str, source_config: Dict, max_results: int) -> List[Dict]:
        """Generic search for other academic sources"""
        # This would implement web scraping for sources without APIs
        # For now, return empty list
        return []
    
    def _get_download_urls(self, paper_info: Dict) -> List[str]:
        """Get potential download URLs for a paper"""
        urls = []
        
        # Direct PDF links
        if 'pdf_url' in paper_info:
            urls.append(paper_info['pdf_url'])
        
        # Construct URLs based on paper ID
        if 'arxiv_id' in paper_info:
            urls.append(f"https://arxiv.org/pdf/{paper_info['arxiv_id']}")
        
        if 'pubmed_id' in paper_info:
            urls.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{paper_info['pubmed_id']}/pdf/")
        
        # DOI-based URLs
        if 'doi' in paper_info:
            urls.extend([
                f"https://doi.org/{paper_info['doi']}",
                f"https://sci-hub.se/{paper_info['doi']}"
            ])
        
        return urls
    
    def _is_pdf_content(self, content: bytes, content_type: Optional[str]) -> bool:
        """Check if content is PDF"""
        if content_type and 'application/pdf' in content_type:
            return True
        
        # Check PDF magic number
        return content.startswith(b'%PDF')
    
    def _save_pdf(self, content: bytes, paper_info: Dict, download_dir: str) -> Optional[str]:
        """Save PDF content to file"""
        try:
            import os
            from pathlib import Path
            
            # Generate filename
            title = paper_info.get('title', 'unknown')
            authors = paper_info.get('authors', ['unknown'])
            year = paper_info.get('year', 'unknown')
            
            # Clean filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title[:50]  # Limit length
            
            filename = f"{authors[0]}_{safe_title}_{year}.pdf"
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
            
            file_path = Path(download_dir) / filename
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save PDF: {str(e)}")
            return None
    
    def _parse_arxiv_response(self, content: bytes) -> List[Dict]:
        """Parse arXiv API response"""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(content, 'xml')
            entries = soup.find_all('entry')
            
            papers = []
            for entry in entries:
                paper = {
                    'title': entry.find('title').text.strip() if entry.find('title') else "",
                    'authors': [author.find('name').text.strip() for author in entry.find_all('author')],
                    'summary': entry.find('summary').text.strip() if entry.find('summary') else "",
                    'arxiv_id': entry.find('id').text.split('/')[-1] if entry.find('id') else "",
                    'pdf_url': None
                }
                
                # Get PDF link
                pdf_link = entry.find('link', title='pdf')
                if pdf_link and pdf_link.get('href'):
                    paper['pdf_url'] = pdf_link['href']
                
                papers.append(paper)
            
            return papers
            
        except Exception as e:
            logger.error(f"Failed to parse arXiv response: {str(e)}")
            return []
    
    def _parse_pubmed_response(self, content: bytes) -> List[Dict]:
        """Parse PubMed API response"""
        try:
            data = json.loads(content)
            papers = []
            
            if 'esearchresult' in data and 'idlist' in data['esearchresult']:
                for pubmed_id in data['esearchresult']['idlist']:
                    papers.append({
                        'pubmed_id': pubmed_id,
                        'title': '',  # Would need additional API call
                        'authors': [],  # Would need additional API call
                        'pdf_url': f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pubmed_id}/pdf/"
                    })
            
            return papers
            
        except Exception as e:
            logger.error(f"Failed to parse PubMed response: {str(e)}")
            return []
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.config.rate_limit_delay:
            sleep_time = self.config.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time() 