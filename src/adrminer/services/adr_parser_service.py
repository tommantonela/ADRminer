"""ADR parsing service with error handling, fallback, and language detection."""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# Pydantic models for parsed ADR
class ParsedADR:
    """Structured representation of a parsed ADR."""
    
    def __init__(
        self,
        title: str,
        hierarchy: Dict[str, List[str]],
        sections: Dict[str, str],
        code_blocks: Dict[str, List[str]],
        properties: Dict[str, str],
        decision_content: Optional[str],
        full_text: str,
        language: Optional[str] = None,
        parsing_failed: bool = False,
        parsing_error: Optional[str] = None,
    ):
        self.title = title
        self.hierarchy = hierarchy
        self.sections = sections
        self.code_blocks = code_blocks
        self.properties = properties
        self.decision_content = decision_content
        self.full_text = full_text
        self.language = language
        self.parsing_failed = parsing_failed
        self.parsing_error = parsing_error
    
    def model_dump(self) -> Dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "hierarchy": self.hierarchy,
            "sections": self.sections,
            "code_blocks": self.code_blocks,
            "properties": self.properties,
            "decision_content": self.decision_content,
            "full_text": self.full_text,
            "language": self.language,
            "parsing_failed": self.parsing_failed,
            "parsing_error": self.parsing_error,
        }


class ADRParserService:
    """Service for parsing ADRs with graceful error handling and fallback."""
    
    def __init__(
        self,
        strict: bool = False,
        detect_language: bool = True,
        use_langdetect: bool = True,
        fallback_on_error: bool = True,
    ):
        """
        Initialize ADR parser service.
        
        Args:
            strict: If True, raise errors; if False, fallback to basic parsing
            detect_language: Whether to detect ADR language
            use_langdetect: Whether to use langdetect library (if available)
            fallback_on_error: Whether to fall back to basic parsing on error
        """
        self.strict = strict
        self.detect_language = detect_language
        self.use_langdetect = use_langdetect
        self.fallback_on_error = fallback_on_error
    
    def parse_adr(
        self,
        text: str,
        source: Optional[str] = None,
    ) -> ParsedADR:
        """
        Parse ADR with error handling and fallback.
        
        Args:
            text: ADR text content
            source: Optional source identifier (e.g., filename)
        
        Returns:
            ParsedADR object (may be partial if parsing failed)
        """
        source_info = f" ({source})" if source else ""
        
        try:
            # Attempt full parsing
            parsed = self._parse_full(text)
            
            # Validate in strict mode
            if self.strict:
                self._validate_parsed_adr(parsed, text)
            
            # Detect language if enabled
            if self.detect_language and not parsed.language:
                parsed.language = self._detect_language(text)
                # Warn if non-English
                if parsed.language and parsed.language != 'en':
                    logger.warning(
                        f"Non-English ADR detected{source_info}: "
                        f"language='{parsed.language}'. "
                        f"Topic modeling and classification may be less accurate."
                    )
            
            return parsed
            
        except Exception as e:
            error_msg = f"ADR parsing failed{source_info}: {e}"
            
            if self.strict:
                raise ValueError(error_msg)
            
            # Log warning and fall back to basic parsing
            logger.warning(f"{error_msg}. Falling back to basic parsing.")
            
            # Fallback: Return basic structure
            return self._create_fallback_parsed_adr(text, str(e))
    
    def _validate_parsed_adr(self, parsed: ParsedADR, text: str) -> None:
        """
        Validate parsed ADR in strict mode.
        
        Args:
            parsed: ParsedADR object
            text: Original text for reference
        
        Raises:
            ValueError: If validation fails
        """
        # Check if we have any sections at all
        if not parsed.sections:
            raise ValueError("No sections found in ADR")
        
        # In strict mode, require Decision section as it's the core of an ADR
        if "Decision" not in parsed.sections:
            raise ValueError("Failed to parse ADR")
    
    def _parse_full(self, text: str) -> ParsedADR:
        """
        Simplified parsing logic that extracts MADR sections.
        
        Args:
            text: ADR text content
        
        Returns:
            ParsedADR with section structure
        """
        # Extract title (first line, typically ADR title)
        # Look for # heading format
        lines = text.strip().split('\n')
        title = ""
        
        # Standard section headers for various templates (MADR, Zimmermann, Nygard)
        standard_sections = [
            "Status", "Context", "Decision", "Consequences", "Decision Drivers", 
            "Considered Options", "Problem", "Rationale", "Proposed Solution", 
            "Alternative", "Pros and Cons", "Argument", "Scope", "Constraints"
        ]

        # First, try to find a # heading at the start (but skip section headers)
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            line_stripped = line.strip()
            if line_stripped.startswith('#'):
                # Skip if it's a known section header
                if not any(section in line_stripped for section in standard_sections):
                    title = line_stripped.lstrip('#').strip()
                    break
        
        # If no # heading found, use first non-empty line (but skip section headers and section content)
        if not title:
            prev_was_section_header = False
            for line in lines:
                line_stripped = line.strip()
                if line_stripped:
                    # Remove ## prefix for comparison
                    line_without_hash = line_stripped.replace('#', '').strip()
                    # Check if this is a section header
                    if line_without_hash in standard_sections:
                        prev_was_section_header = True
                        continue
                    # Skip content immediately following a section header (likely not a title)
                    if prev_was_section_header:
                        prev_was_section_header = False
                        continue
                    # Skip very short lines (likely section content, not a title)
                    if len(line_stripped.split()) < 3:  # Less than 3 words
                        continue
                    title = line_stripped
                    break
        
        # Extract sections using regex (support both ## and underlined styles)
        sections = {}
        hierarchy = {}
        
        # Find all sections (both hash and underlined styles)
        # Hash pattern: ## Section Name
        section_pattern = re.compile(r'^##\s+([^\n]+)', re.MULTILINE)
        # Underlined pattern: Section Name\n-------
        underlined_pattern = re.compile(r'^([A-Za-z][^\n]*)\n[-=]{3,}$', re.MULTILINE)
        
        matches = []
        
        # Find ## sections
        for match in section_pattern.finditer(text):
            matches.append({
                'type': 'hash',
                'name': match.group(1).strip(),
                'pos': match.start(),
                'end': match.end(),
            })
        
        # Find underlined sections
        for match in underlined_pattern.finditer(text):
            matches.append({
                'type': 'underlined',
                'name': match.group(1).strip(),
                'pos': match.start(),
                'end': match.end(),
            })
        
        # Sort by position
        matches.sort(key=lambda x: x['pos'])
        
        for i, match in enumerate(matches):
            section_name = match['name']
            start = match['end']
            
            # Find end of section (next header or end of text)
            if i + 1 < len(matches):
                end = matches[i + 1]['pos']
            else:
                end = len(text)
            
            # Extract content
            content = text[start:end].strip()
            sections[section_name] = content
            hierarchy[section_name] = []
        
        # Extract decision content if Decision section exists
        decision_content = None
        if "Decision" in sections:
            decision_content = sections["Decision"]
        
        return ParsedADR(
            title=title,
            hierarchy=hierarchy,
            sections=sections,
            code_blocks={},
            properties={},
            decision_content=decision_content,
            full_text=text,
            language=None,  # Will be set by parse_adr if enabled
            parsing_failed=False,
            parsing_error=None,
        )
    
    def _create_fallback_parsed_adr(
        self,
        text: str,
        error: str,
    ) -> ParsedADR:
        """Create basic ParsedADR when full parsing fails."""
        title = text.split('\n')[0][:100] if text else "Untitled"
        
        return ParsedADR(
            title=title,
            hierarchy={},
            sections={'full': text},
            code_blocks={},
            properties={},
            decision_content=None,
            full_text=text,
            language=None,
            parsing_failed=True,
            parsing_error=error,
        )
    
    def remove_code_blocks(self, text: str) -> str:
        """
        Remove code blocks from ADR text with fallback.
        
        Args:
            text: ADR text content
        
        Returns:
            Text with code blocks removed
        """
        try:
            # Simple regex removal
            text = re.sub(r'```[^\n]*\n.*?```', '', text, flags=re.DOTALL)
            text = re.sub(r'`[^`]+`', '', text)
            return text
        except Exception as e:
            logger.warning(f"Code removal failed: {e}. Returning original text.")
            return text
    
    def get_section_content(
        self,
        text: str,
        section_name: str,
        include_code: bool = False,
    ) -> str:
        """
        Get content for a specific section with fallback.
        
        Args:
            text: ADR text content
            section_name: Name of section to extract (case-insensitive)
            include_code: Whether to include code blocks
        
        Returns:
            Section content as string
        """
        try:
            parsed = self.parse_adr(text)
            
            if parsed.parsing_failed:
                # Fallback: simple text search
                return self._extract_section_regex(text, section_name)
            
            # Use section structure (sections are strings now)
            for key, content in parsed.sections.items():
                if section_name.lower() in key.lower():
                    return content
            
            return ""
        except Exception as e:
            logger.warning(f"Section extraction failed: {e}. Using regex fallback.")
            return self._extract_section_regex(text, section_name)
    
    def _extract_section_regex(self, text: str, section_name: str) -> str:
        """Simple regex-based section extraction (fallback)."""
        # Look for section header (case-insensitive)
        pattern = re.compile(
            rf'^##\s+{re.escape(section_name)}.*$',
            re.IGNORECASE | re.MULTILINE
        )
        
        match = pattern.search(text)
        if not match:
            return ""
        
        # Extract content until next header
        start = match.end()
        next_header = re.search(r'^##\s+', text[start:], re.MULTILINE)
        end = next_header.start() if next_header else len(text)
        
        return text[start:start + end].strip()
    
    def get_decision_section(self, text: str) -> str:
        """Extract decision section content."""
        try:
            parsed = self.parse_adr(text)
            
            if parsed.decision_content:
                return parsed.decision_content
            
            # Fallback: simple extraction
            return self._extract_section_regex(text, "Decision")
        except Exception as e:
            logger.warning(f"Decision section extraction failed: {e}")
            return self._extract_section_regex(text, "Decision")
    
    def get_title(self, text: str) -> str:
        """Extract main title of ADR."""
        try:
            parsed = self.parse_adr(text)
            return parsed.title
        except Exception as e:
            logger.warning(f"Title extraction failed: {e}")
            return text.split('\n')[0][:100]
    
    def _detect_language(self, text: str) -> str:
        """
        Detect language of ADR with multiple fallback strategies.
        
        Args:
            text: ADR text content
        
        Returns:
            ISO 639-1 language code (e.g., 'en', 'es', 'de')
        """
        # Strategy 1: Try langdetect library (if enabled)
        if self.use_langdetect:
            try:
                from langdetect import detect
                return detect(text)
            except ImportError:
                logger.debug("langdetect not available, using basic detection")
            except Exception as e:
                logger.debug(f"langdetect failed: {e}. Using basic detection")
        
        # Strategy 2: Basic detection using common words
        return self._detect_language_basic(text)
    
    def _detect_language_basic(self, text: str) -> str:
        """
        Basic language detection using common words.
        
        Args:
            text: ADR text content
        
        Returns:
            ISO 639-1 language code
        """
        # Common words for different languages - using distinctive words with word boundaries
        # Split text into words to avoid substring matches
        text_lower = text.lower()
        words = text_lower.split()
        
        language_keywords = {
            'en': ['the', 'and', 'that', 'this', 'with', 'from', 'they', 'will', 'been', 'would', 'have', 'not'],
            'es': ['el', 'que', 'como', 'pero', 'donde', 'cuando', 'solo', 'muy', 'hacer', 'puede', 'es', 'un', 'una', 'los', 'las', 'por', 'para', 'todo', 'todo'],
            'de': ['der', 'die', 'das', 'ein', 'eine', 'einer', 'eines', 'für', 'von', 'aus', 'ist', 'nicht'],
            'fr': ['le', 'la', 'les', 'un', 'une', 'des', 'qui', 'dans', 'avec', 'pour', 'mais', 'est', 'et', 'dans', 'par'],
            'pt': ['os', 'ser', 'estar', 'fazer', 'ter', 'para', 'como', 'mas', 'seu', 'sua', 'de', 'a', 'o', 'em'],
            'it': ['il', 'lo', 'una', 'che', 'per', 'con', 'come', 'essere', 'fare', 'avere', 'di', 'la', 'il'],
        }
        
        scores = {}
        
        for lang, keywords in language_keywords.items():
            score = sum(words.count(word) for word in keywords)
            scores[lang] = score
        
        # Return language with highest score, default to 'en'
        # Only return a non-English language if it has significantly higher score
        detected_lang = max(scores, key=scores.get) if scores else 'en'
        
        # Check if detected language has meaningful advantage over English
        if detected_lang != 'en' and scores[detected_lang] > scores.get('en', 0) * 1.5:
            return detected_lang
        
        return 'en'
