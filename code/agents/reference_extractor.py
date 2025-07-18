import re
import fitz
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Reference:
    """Structured reference data"""
    authors: str
    title: str
    journal: str
    year: str
    doi: Optional[str] = None
    url: Optional[str] = None
    raw_text: str = ""
    confidence: float = 0.0


class ReferenceExtractor:
    """Extract reference citations from PDF documents"""
    
    def __init__(self):
        # Common reference section headers
        self.reference_headers = [
            r'references?',
            r'bibliography',
            r'literature\s+cited',
            r'works\s+cited',
            r'sources',
            r'citations?'
        ]
        
        # Citation patterns for different formats
        self.citation_patterns = {
            'apa': [
                # APA format: Author, A. A., Author, B. B., & Author, C. C. (Year). Title. Journal, Volume(Issue), Pages.
                r'([A-Z][a-z]+,\s*[A-Z]\.\s*(?:[A-Z]\.\s*)*)(?:[A-Z][a-z]+,\s*[A-Z]\.\s*(?:[A-Z]\.\s*)*)*\s*\((\d{4})\)\.\s*([^\.]+)\.\s*([^,]+),\s*(\d+)(?:\((\d+)\))?,\s*([^\.]+)\.',
                # APA with DOI
                r'([A-Z][a-z]+,\s*[A-Z]\.\s*(?:[A-Z]\.\s*)*)(?:[A-Z][a-z]+,\s*[A-Z]\.\s*(?:[A-Z]\.\s*)*)*\s*\((\d{4})\)\.\s*([^\.]+)\.\s*([^,]+),\s*(\d+)(?:\((\d+)\))?,\s*([^\.]+)\.\s*https?://doi\.org/([^\s]+)'
            ],
            'mla': [
                # MLA format: Author, A. "Title." Journal, vol. Volume, no. Issue, Year, pp. Pages.
                r'([A-Z][a-z]+,\s*[A-Z][a-z]+)\.\s*"([^"]+)"\.\s*([^,]+),\s*vol\.\s*(\d+)(?:,\s*no\.\s*(\d+))?,\s*(\d{4}),\s*pp\.\s*([^\.]+)\.'
            ],
            'chicago': [
                # Chicago format: Author, A. "Title." Journal Volume, no. Issue (Year): Pages.
                r'([A-Z][a-z]+,\s*[A-Z][a-z]+)\.\s*"([^"]+)"\.\s*([^,]+)\s*(\d+),\s*no\.\s*(\d+)\s*\((\d{4})\):\s*([^\.]+)\.'
            ],
            'ieee': [
                # IEEE format: A. Author, B. Author, and C. Author, "Title," Journal, vol. Volume, no. Issue, pp. Pages, Month Year.
                r'([A-Z]\.\s*[A-Z][a-z]+(?:\s*,\s*[A-Z]\.\s*[A-Z][a-z]+)*)\s*"([^"]+)"\s*([^,]+),\s*vol\.\s*(\d+)(?:,\s*no\.\s*(\d+))?,\s*pp\.\s*([^,]+),\s*([A-Za-z]+)\s*(\d{4})\.'
            ],
            'generic': [
                # Generic pattern for various formats
                r'([A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+)*)\s*\((\d{4})\)\.\s*([^\.]+)\.\s*([^,]+),\s*(\d+)(?:\((\d+)\))?,\s*([^\.]+)\.',
                # Pattern with DOI
                r'([A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+)*)\s*\((\d{4})\)\.\s*([^\.]+)\.\s*([^,]+),\s*(\d+)(?:\((\d+)\))?,\s*([^\.]+)\.\s*https?://doi\.org/([^\s]+)'
            ]
        }
        
        # DOI pattern
        self.doi_pattern = r'https?://doi\.org/([^\s]+)'
        
    def extract_references_from_pdf(self, pdf_path: str) -> List[Reference]:
        """
        Extract references from a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of Reference objects
        """
        try:
            with fitz.open(pdf_path) as doc:
                # Find reference section
                reference_section = self._find_reference_section(doc)
                if not reference_section:
                    logger.warning(f"No reference section found in {pdf_path}")
                    return []
                
                # Extract references from the section
                references = self._extract_references_from_text(reference_section)
                logger.info(f"Extracted {len(references)} references from {pdf_path}")
                return references
                
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            return []
    
    def _find_reference_section(self, doc) -> str:
        """
        Find the reference section in the PDF
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            Text content of the reference section
        """
        reference_text = ""
        in_reference_section = False
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text("text")
            
            # Check if this page contains reference section headers
            page_lower = page_text.lower()
            
            # Check if we're entering a reference section
            if not in_reference_section:
                for header_pattern in self.reference_headers:
                    if re.search(header_pattern, page_lower):
                        in_reference_section = True
                        logger.info(f"Found reference section starting at page {page_num + 1}")
                        break
            
            # If we're in reference section, collect text
            if in_reference_section:
                reference_text += page_text + "\n"
                
                # Check if we've reached the end (next major section)
                # This is a simple heuristic - could be improved
                if re.search(r'\n\s*\d+\.\s*[A-Z]', page_text):
                    # Might be the start of a new numbered section
                    break
        
        return reference_text
    
    def _extract_references_from_text(self, text: str) -> List[Reference]:
        """
        Extract references from text using regex patterns
        
        Args:
            text: Text containing references
            
        Returns:
            List of Reference objects
        """
        references = []
        
        # Split the text into lines and process them
        lines = text.split('\n')
        current_entry = ""
        reference_entries = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip header lines
            if line.upper() in ['REFERENCES', 'BIBLIOGRAPHY', 'LITERATURE CITED']:
                continue
            
            # Check if this line looks like the start of a new reference
            # Pattern: starts with capitalized name (author)
            if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*,', line):
                # Save previous entry if it exists
                if current_entry.strip():
                    reference_entries.append(current_entry.strip())
                current_entry = line
            elif re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+and\s+[A-Z][a-z]+', line):
                # Pattern: starts with "Author1, Author2, and Author3"
                if current_entry.strip():
                    reference_entries.append(current_entry.strip())
                current_entry = line
            elif re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+et al\.', line):
                # Pattern: starts with "Author1, Author2, et al."
                if current_entry.strip():
                    reference_entries.append(current_entry.strip())
                current_entry = line
            elif re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*,', line):
                # Pattern: starts with "FirstName LastName, FirstName LastName,"
                if current_entry.strip():
                    reference_entries.append(current_entry.strip())
                current_entry = line
            elif re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*\.', line):
                # Pattern: starts with "FirstName LastName, FirstName LastName."
                if current_entry.strip():
                    reference_entries.append(current_entry.strip())
                current_entry = line
            elif re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*,', line):
                # Pattern: starts with "FirstName LastName, FirstName LastName, FirstName LastName,"
                if current_entry.strip():
                    reference_entries.append(current_entry.strip())
                current_entry = line
            else:
                # Continue building current entry
                if current_entry:
                    current_entry += " " + line
                else:
                    # If no current entry, this might be a standalone reference
                    current_entry = line
        
        # Add the last entry
        if current_entry.strip():
            reference_entries.append(current_entry.strip())
        
        # Process each reference entry
        for entry in reference_entries:
            entry = entry.strip()
            if not entry or len(entry) < 20:  # Skip very short entries
                continue
                
            # Try to match with different citation patterns
            reference = self._parse_reference_entry(entry)
            if reference:
                references.append(reference)
        
        return references
    
    def _parse_reference_entry(self, entry: str) -> Optional[Reference]:
        """
        Parse a single reference entry
        
        Args:
            entry: Single reference entry text
            
        Returns:
            Reference object if successfully parsed, None otherwise
        """
        # Try each citation format
        for format_name, patterns in self.citation_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, entry, re.IGNORECASE)
                if match:
                    try:
                        reference = self._create_reference_from_match(match, format_name, entry)
                        if reference:
                            return reference
                    except Exception as e:
                        logger.debug(f"Error parsing reference with {format_name} pattern: {str(e)}")
                        continue
        
        # If no pattern matches, try to extract basic information
        return self._extract_basic_reference_info(entry)
    
    def _create_reference_from_match(self, match, format_name: str, raw_text: str) -> Optional[Reference]:
        """
        Create a Reference object from regex match
        
        Args:
            match: Regex match object
            format_name: Name of the citation format
            raw_text: Original reference text
            
        Returns:
            Reference object
        """
        groups = match.groups()
        
        try:
            if format_name == 'apa':
                if len(groups) >= 7:
                    authors = groups[0].strip()
                    year = groups[1]
                    title = groups[2].strip()
                    journal = groups[3].strip()
                    volume = groups[4]
                    issue = groups[5] if len(groups) > 5 and groups[5] else ""
                    pages = groups[6] if len(groups) > 6 else ""
                    doi = groups[7] if len(groups) > 7 else None
                    
                    return Reference(
                        authors=authors,
                        title=title,
                        journal=journal,
                        year=year,
                        doi=doi,
                        raw_text=raw_text,
                        confidence=0.9
                    )
            
            elif format_name == 'mla':
                if len(groups) >= 6:
                    authors = groups[0].strip()
                    title = groups[1].strip()
                    journal = groups[2].strip()
                    volume = groups[3]
                    issue = groups[4] if len(groups) > 4 and groups[4] else ""
                    year = groups[5]
                    pages = groups[6] if len(groups) > 6 else ""
                    
                    return Reference(
                        authors=authors,
                        title=title,
                        journal=journal,
                        year=year,
                        raw_text=raw_text,
                        confidence=0.85
                    )
            
            elif format_name == 'chicago':
                if len(groups) >= 7:
                    authors = groups[0].strip()
                    title = groups[1].strip()
                    journal = groups[2].strip()
                    volume = groups[3]
                    issue = groups[4]
                    year = groups[5]
                    pages = groups[6]
                    
                    return Reference(
                        authors=authors,
                        title=title,
                        journal=journal,
                        year=year,
                        raw_text=raw_text,
                        confidence=0.85
                    )
            
            elif format_name == 'ieee':
                if len(groups) >= 8:
                    authors = groups[0].strip()
                    title = groups[1].strip()
                    journal = groups[2].strip()
                    volume = groups[3]
                    issue = groups[4] if len(groups) > 4 and groups[4] else ""
                    pages = groups[5]
                    month = groups[6]
                    year = groups[7]
                    
                    return Reference(
                        authors=authors,
                        title=title,
                        journal=journal,
                        year=year,
                        raw_text=raw_text,
                        confidence=0.8
                    )
            
            elif format_name == 'generic':
                if len(groups) >= 7:
                    authors = groups[0].strip()
                    year = groups[1]
                    title = groups[2].strip()
                    journal = groups[3].strip()
                    volume = groups[4]
                    issue = groups[5] if len(groups) > 5 and groups[5] else ""
                    pages = groups[6]
                    doi = groups[7] if len(groups) > 7 else None
                    
                    return Reference(
                        authors=authors,
                        title=title,
                        journal=journal,
                        year=year,
                        doi=doi,
                        raw_text=raw_text,
                        confidence=0.7
                    )
        
        except Exception as e:
            logger.debug(f"Error creating reference from {format_name} match: {str(e)}")
        
        return None
    
    def _extract_basic_reference_info(self, entry: str) -> Optional[Reference]:
        """
        Extract basic reference information when no pattern matches
        
        Args:
            entry: Reference entry text
            
        Returns:
            Reference object with basic information
        """
        # Try to extract year (look for 4-digit years, but be more careful)
        year_match = re.search(r'\b(19|20)\d{2}\b', entry)
        year = year_match.group(0) if year_match else ""
        
        # Try to extract DOI
        doi_match = re.search(self.doi_pattern, entry)
        doi = doi_match.group(1) if doi_match else None
        
        # Try to extract arXiv ID
        arxiv_match = re.search(r'arXiv:(\d+\.\d+)', entry)
        arxiv_id = arxiv_match.group(1) if arxiv_match else None
        
        # Try to extract authors - look for the pattern: "Author1, Author2, and Author3."
        # This is more specific to the format we're seeing
        author_pattern = r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*\s+(?:and\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\.'
        author_match = re.match(author_pattern, entry)
        
        if author_match:
            authors = author_match.group(1).strip()
            # Remove the authors and the period from the beginning
            remaining_text = entry[len(authors) + 1:].strip()
        else:
            # Fallback: try to find authors at the beginning
            # Look for text that ends with a period and contains capitalized names
            simple_author_pattern = r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*\s+(?:and\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\.'
            simple_match = re.match(simple_author_pattern, entry)
            if simple_match:
                authors = simple_match.group(1).strip()
                remaining_text = entry[len(authors) + 1:].strip()
            else:
                authors = ""
                remaining_text = entry
        
        # Try to extract title from the remaining text
        title = ""
        if remaining_text:
            # Look for title in quotes first
            title_match = re.search(r'"([^"]+)"', remaining_text)
            if title_match:
                title = title_match.group(1)
            else:
                # Take the first sentence as title, but be more careful
                # Look for the first sentence that doesn't start with common journal words
                sentences = re.split(r'[.!?]', remaining_text)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence and len(sentence) > 10:
                        # Skip sentences that start with common journal/publication words
                        if not re.match(r'^(In\s+)?(Proceedings|Conference|Journal|arXiv|preprint|Published)', sentence, re.IGNORECASE):
                            title = sentence
                            break
                
                # If still no title, take the first substantial sentence
                if not title and sentences:
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if sentence and len(sentence) > 10:
                            title = sentence
                            break
        
        # Try to extract journal information
        journal = ""
        if remaining_text:
            # Look for journal patterns
            journal_patterns = [
                r'(?:In\s+)?(?:Proceedings\s+of\s+)?([A-Z][A-Za-z\s]+(?:Conference|Journal|Transactions|Letters))',
                r'(arXiv\s+preprint\s+arXiv:\d+\.\d+)',
                r'(Published\s+as\s+a\s+[^,]+)',
                r'([A-Z][A-Za-z\s]+(?:Conference|Journal|Transactions|Letters))'
            ]
            
            for pattern in journal_patterns:
                journal_match = re.search(pattern, remaining_text, re.IGNORECASE)
                if journal_match:
                    journal = journal_match.group(1).strip()
                    break
        
        # If we have reasonable data, create the reference
        if authors and title and year:
            return Reference(
                authors=authors,
                title=title,
                journal=journal,
                year=year,
                doi=doi,
                raw_text=entry,
                confidence=0.6
            )
        elif authors and title:  # Even without year, it might be useful
            return Reference(
                authors=authors,
                title=title,
                journal=journal,
                year=year,
                doi=doi,
                raw_text=entry,
                confidence=0.4
            )
        
        return None
    
    def get_extraction_stats(self, references: List[Reference]) -> Dict:
        """
        Get statistics about extracted references
        
        Args:
            references: List of extracted references
            
        Returns:
            Dictionary with extraction statistics
        """
        if not references:
            return {
                'total_references': 0,
                'high_confidence': 0,
                'medium_confidence': 0,
                'low_confidence': 0,
                'with_doi': 0,
                'with_year': 0
            }
        
        high_conf = sum(1 for r in references if r.confidence >= 0.8)
        medium_conf = sum(1 for r in references if 0.5 <= r.confidence < 0.8)
        low_conf = sum(1 for r in references if r.confidence < 0.5)
        with_doi = sum(1 for r in references if r.doi)
        with_year = sum(1 for r in references if r.year)
        
        return {
            'total_references': len(references),
            'high_confidence': high_conf,
            'medium_confidence': medium_conf,
            'low_confidence': low_conf,
            'with_doi': with_doi,
            'with_year': with_year,
            'avg_confidence': sum(r.confidence for r in references) / len(references)
        } 