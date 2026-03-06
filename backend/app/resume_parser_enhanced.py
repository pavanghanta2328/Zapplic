import os
import re
from typing import Dict, Optional, List
import pytesseract
from pdf2image import convert_from_path
import spacy
from tika import parser
import ssl
import threading
import re
import geonamescache
import unicodedata

# --- NEW ENGINES --
# # from docling.document_converter import DocumentConverter
# # import spacy
# from markitdown import MarkItDown
# import textract


# Fix for SSL certificate errors
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

import logging

# 1. SHUT UP THE LOGS (Put this at the very top of your file)
# logging.getLogger("docling").setLevel(logging.ERROR)
logging.getLogger("tika").setLevel(logging.INFO)
# logging.getLogger("pdfminer").setLevel(logging.ERROR)
# logging.getLogger("markitdown").setLevel(logging.ERROR)



# # Execute during module import
# initialize_resources()

# # GLOBAL INITIALIZATION (Do this outside the class to prevent reloading)
# print("Initializing Docling and Spire Engines (this may take a moment)...")
# doc_converter = DocumentConverter()
# markitdown = MarkItDown()
# nlp = spacy.load("en_core_web_md")

# Global lock for thread-unsafe engines
engine_lock = threading.Lock()


# 1. GLOBAL INITIALIZATION (Outside the class)
# These are "Heavy" objects. We load them once and reuse them.
print("Loading AI Models into memory. This may take a few seconds...")
# Global initialization for performance
gc = geonamescache.GeonamesCache()
# Get all cities and states once
CITIES = {city['name'].lower() for city in gc.get_cities().values()}
STATES = {s['name'].lower() for s in gc.get_us_states().values()} # geonamescache also has global states

# Constants for Filtering Noise
NAME_BLACKLIST = {
    'manager', 'director', 'assistant', 'senior', 'lead', 'consultant', 'specialist', 
    'analyst', 'developer', 'engineer', 'representative', 'coordinator', 'intern',
    'results', 'passionate', 'dynamic', 'proactive', 'experienced', 'innovative', 
    'strategic', 'executive', 'dedicated', 'resume', 'cv', 'candidate', 'objective', 'yrs'
}

LOCATION_BLACKLIST = {
    'remote', 'virtual', 'on-site', 'domestic', 'international', 'location', 'address',
    'inc', 'ltd', 'llc', 'corp', 'corporation', 'group', 'gmbh', 'private', 'limited',
    'university', 'institute', 'college', 'campus', 'department', 'faculty', 'school'
}


try:
    # nlp = spacy.load("en_core_web_sm")
    nlp = spacy.load("en_core_web_md")
except OSError:
    import spacy.cli
    spacy.cli.download("en_core_web_md")
    # nlp = spacy.load("en_core_web_sm")
    nlp = spacy.load("en_core_web_md")

# Centralized section landmarks to prevent "bleeding" between columns
SECTION_CONCEPTS = {
    "experience": ["experience", "work history", "employment", "professional background", "projects"],
    "education": ["education", "academic", "qualification", "university", "schooling", "certifications"],
    "skills": ["skills", "technical expertise", "technologies", "tools", "competencies"],
    "summary": ["summary", "objective", "profile", "about me"]
}

class ResumeParser:
    """
    Enhanced resume parser with significantly improved extraction accuracy.
    
    Key Improvements:
    - Better name extraction (multiple strategies)
    - Improved skills detection
    - Enhanced experience parsing
    - Better quality assessment
    - More robust text cleaning
    """
    
    # Comprehensive blacklist of terms that should NOT be considered as names
    # NAME_BLACKLIST = [
    #     # Common section headers
    #     'professional summary', 'professional summery', 'professional overview',
    #     'career summary', 'career objective', 'executive summary',
    #     'summary of qualifications', 'profile summary', 'professional profile',
        
    #     # Experience-related headers
    #     'key engagements', 'experience summary', 'professional experience',
    #     'work experience', 'employment history', 'work history',
    #     'professional and business experience', 'business experience',
        
    #     # Document types
    #     'resume', 'cv', 'curriculum vitae', 'curriculum', 'vitae',
        
    #     # Other common headers
    #     'education', 'skills', 'technical skills', 'core competencies',
    #     'contact information', 'personal details', 'personal information',
    #     'professional objective', 'career goal', 'objective',
        
    #     # Misc phrases that appear in resumes
    #     'please click here', 'click here for', 'please click here for',
    #     'professional', 'summary', 'overview', 'objective',
    #     'governance and compliance', 'areas of expertise', 'key skills',
    #     'technical proficiency', 'academic profile', '.net core', 'sql server',
    #     'java developer', 'software engineer', 'curriculum vitae'
    # ]

    # def __init__(self, file_path: str, use_ocr_fallback: bool = True):
    #     self.file_path = file_path
    #     self.file_extension = os.path.splitext(file_path)[1].lower()
    #     self.text = ""
    #     self.lines = []
    #     self.use_ocr_fallback = use_ocr_fallback
    #     self.extraction_method = "unknown"
    
    def __init__(self, file_path: str, use_ocr_fallback: bool = True):
        self.file_path = file_path
        self.text = ""
        self.metadata = {}
        self.extraction_method = "Tika"
        self.lines = []
        
    
    # ============================================================
    # TEXT EXTRACTION
    # ============================================================
    
    def _extract_text(self) -> str:
        """
        Pure Tika extraction for .doc, .docx, and .pdf.
        Ensures no content is missed by capturing full Tika output.
        """
        try:
            self.extraction_method = "Tika"
            parsed = parser.from_file(self.file_path)
            
            # Extracting exactly as requested
            self.text = parsed.get('content', '')
            self.metadata = parsed.get('metadata', {})
            
            if self.text:
                # Standardize whitespace to ensure regex and NER work reliably
                self.text = re.sub(r'\n{3,}', '\n\n', self.text).strip()
                
            return self.text
        except Exception as e:
            logging.error(f"Tika failed to extract {self.file_path}: {e}")
            return ""

    def _clean_markdown_artifacts(self, text: str) -> str:
        """Removes symbols like ## or ** that can confuse NER engines."""
        if not text: return ""
        # Remove hashes, asterisks, and excess symbols
        clean = re.sub(r'[#\*•●○\t]', ' ', text)
        return " ".join(clean.split()).strip()
    
    
    def _extract_pdf_with_ocr(self):
        """Handles scanned documents using Tesseract."""
        self.extraction_method = "ocr_tesseract"
        try:
            images = convert_from_path(self.file_path)
            full_text = []
            for img in images:
                img = self._preprocess_image_for_ocr(img)
                full_text.append(pytesseract.image_to_string(img))
            self.text = self._clean_ocr_text("\n".join(full_text))
        except Exception as e:
            print(f"OCR Error: {e}")
    def _preprocess_image_for_ocr(self, img):
        return img.convert('L') # Grayscale
    

    
    def _clean_ocr_text(self, text: str) -> str:
        text = re.sub(r'[|\\_~«»]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _assess_text_quality(self, parsed_data: Dict) -> str:
        """
        Precise quality logic using comparison between search_text and full content.
        Uses ratios to determine if the extraction missed significant portions.
        """
        if not self.text or len(self.text) < 150:
            return "poor"

        # 1. Coverage Analysis: How much of the resume was actually 'parsed'?
        search_text = " ".join(str(v) for v in parsed_data.values() if v)
        coverage_ratio = len(search_text) / len(self.text) if self.text else 0
        
        # 2. Character Noise Analysis
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s]', self.text)) / len(self.text)
        
        # 3. Field Completeness
        required_fields = ["name", "email"]
        filled_count = sum(1 for f in required_fields if parsed_data.get(f))
        
        has_skills = parsed_data.get("skills") and len(str(parsed_data.get("skills"))) > 20
        has_experience = parsed_data.get("experience") and len(str(parsed_data.get("experience"))) > 50

        # Dynamic Threshold Logic
        if special_char_ratio > 0.35:
            return "poor" # Text is likely garbage/binary noise
            
        if filled_count == 2 and has_skills and has_experience:
            # If we have core info AND a high coverage ratio, it's good
            return "good" if coverage_ratio > 0.20 else "partial"
            
        if filled_count >= 1 and (has_skills or has_experience):
            return "partial"
            
        return "poor"
    
    # ============================================================
    # MAIN PARSING
    # ============================================================
    
    def parse(self) -> Dict:
        """Main parsing strategy with multi-stage validation fallbacks."""
        if not self.text:
            self.text = self._extract_text()
        
        # Clean lines for section logic
        self.lines = [
            self._clean_markdown_artifacts(line) 
            for line in self.text.split('\n') 
            if line.strip()
        ]

        # --- ENHANCED NAME LOGIC ---
        # Try text-based extraction first
        name = self._extract_name()
        
        # Fallback to filename if text extraction returned noise or unknown
        if not name or name.lower() == "unknown":
            fn_name = self._extract_name_from_filename()
            if fn_name:
                name = fn_name
        
        # --- ENHANCED LOCATION LOGIC ---
        location = self._extract_location()
        
        # --- EXTRACT URLS ---
        urls = self._extract_urls()
        personal_info = self._extract_personal_details()

        return {
            "name": name or "unknown",
            "email": self._extract_email(),
            "mobile_number": self._extract_phone(),
            "skills": self._extract_skills(),
            "experience": self._extract_experience(),
            "education": self._extract_education(),
            "location": location,
            "linkedin_url": urls.get("linkedin"),
            "github_url": urls.get("github"),
            "personal_details":personal_info
        }

    def parse_full(self) -> Dict:
        """
        Ensures search_text contains the ENTIRE document content
        while providing structured, validated fields.
        """
        if not self.text:
            self.text = self._extract_text()
        
        parsed = self.parse()
        
        # CLEAN FULL TEXT: Crucial for your search engine (Elastic/Solr/SQL)
        # This keeps technical terms searchable even if not in 'skills'
        full_searchable_content = " ".join(self.text.split())

        quality = self._assess_text_quality(parsed)

        return {
            "basic_fields": {
                "id": getattr(self, 'id', None),
                "original_filename": os.path.basename(self.file_path),
                "name": parsed.get("name"),
                "email": parsed.get("email"),
                "mobile_number": parsed.get("mobile_number"),
                "location": parsed.get("location"),
                "skills":parsed.get("skills"),
                "experience":parsed.get("experience"),
                "education":parsed.get("education"),
                "linkedin_url": parsed.get("linkedin_url"),
                "github_url": parsed.get("github_url"),
                "personal_details": parsed.get("personal_details", {}),
            },
            "parsed_data": parsed,
            "search_text": full_searchable_content, 
            "parsing_quality": quality,
            "raw_text_length": len(self.text),
            "extraction_method": self.extraction_method,
        }

    
    # ============================================================
    # ENHANCED NAME EXTRACTION
    # ============================================================
    
    # def _extract_name(self) -> Optional[str]:
    #     """
    #     Ultra-robust name extraction with 8 strategies and validation.
    #     Significantly improved from original version.
    #     """
        
    #     # Prepare clean lines - IMPORTANT: Clean artifacts before NLP processing
    #     clean_lines = []
    #     for line in self.lines[:30]:
    #         line = self._clean_markdown_artifacts(line.strip()) 
    #         if line and len(line) > 2:
    #             clean_lines.append(line)
        
    #     if not clean_lines: return None
        
    #     # Strategy 1: "Name:" Labels
    #     for line in clean_lines[:15]:
    #         match = re.search(r'(?:^|\s)name\s*[:|-]\s*(.+?)(?:\||$)', line, re.IGNORECASE)
    #         if match:
    #             potential = re.sub(r'[^\w\s\.]', '', match.group(1)).strip()
    #             if self._validate_name(potential):
    #                 return potential.title()
        
    #     # Strategy 2: ALL CAPS names in first 5 lines
    #     for line in clean_lines[:5]:
    #         if any(x in line for x in ['@', 'http', '+', '.com']): continue
    #         if line.isupper() and 5 < len(line) < 60:
    #             if self._validate_name(line):
    #                 return line.title()
        
    #     # Strategy 3: Find email, search nearby lines
    #     email_idx = -1
    #     for i, line in enumerate(clean_lines[:25]):
    #         if '@' in line:
    #             email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', line)
    #             if email_match:
    #                 email_idx = i
    #                 break
        
    #     if email_idx >= 0:
    #         # Search before email (more common)
    #         search_range = range(max(0, email_idx - 4), min(len(clean_lines), email_idx + 2))
            
    #         for i in search_range:
    #             if i == email_idx:
    #                 continue
                
    #             line = clean_lines[i]
                
    #             # Skip contact info
    #             if any(x in line for x in ['@', 'http', '+', '📞', '✉️', 'www', '|']):
    #                 continue
                
    #             # Skip numeric-heavy lines
    #             if sum(c.isdigit() for c in line) > len(line) / 2:
    #                 continue
                
    #             words = line.split()
                
    #             # Check for valid names (1-5 words)
    #             if 1 <= len(words) <= 5:
    #                 # All words mostly alphabetic
    #                 if all(w.replace('.', '').replace(',', '').isalpha() for w in words if w):
    #                     if 3 < len(line) < 60:
    #                         name = ' '.join(words).title()
    #                         if self._validate_name(name):
    #                             return name
        
    #     # Strategy 4: Find phone, search nearby
    #     phone_idx = -1
    #     phone_patterns = [
    #         r'\+\d{1,3}[-.\s]?\d{10}',
    #         r'\d{10}',
    #         r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
    #     ]
        
    #     for i, line in enumerate(clean_lines[:25]):
    #         for pattern in phone_patterns:
    #             if re.search(pattern, line):
    #                 phone_idx = i
    #                 break
    #         if phone_idx >= 0:
    #             break
        
    #     if phone_idx >= 0:
    #         # Search before and after phone
    #         search_range = range(max(0, phone_idx - 3), min(len(clean_lines), phone_idx + 3))
            
    #         for i in search_range:
    #             if i == phone_idx:
    #                 continue
                
    #             line = clean_lines[i]
                
    #             # Skip contact info
    #             if any(x in line for x in ['@', 'http', '+', '📞', '✉️', '|']):
    #                 continue
                
    #             words = line.split()
                
    #             if 1 <= len(words) <= 5:
    #                 if all(w.replace('.', '').isalpha() for w in words if w):
    #                     if 3 < len(line) < 60:
    #                         name = ' '.join(words).title()
    #                         if self._validate_name(name):
    #                             return name
        
    #     # Strategy 5: Extract from filename (MOVED UP FOR PRIORITY)
    #     # This is now tried before title-case and other fallbacks
    #     # Highly reliable when document has no clear name
    #     name_from_file = self._extract_name_from_filename()
    #     if name_from_file and self._validate_name(name_from_file):
    #         return name_from_file
        
    #     # Strategy 6: Title Case names (proper capitalization)
    #     for line in clean_lines[:20]:
    #         if any(x in line for x in ['@', 'http', '+', '|']): continue
    #         words = line.split()
    #         if 2 <= len(words) <= 5:
    #             # Check if every word starts with a Capital Letter
    #             if all(w[0].isupper() for w in words if w.isalpha()):
    #                 if self._validate_name(line):
    #                     return line.title()
        
    #     # Strategy 7: Combine consecutive single-word lines
    #     potential_parts = []
    #     for i in range(min(12, len(clean_lines))):
    #         line = clean_lines[i]
            
    #         # Skip contact info
    #         if any(x in line for x in ['@', 'http', '+', '📞', '✉️', '.com']):
    #             potential_parts = []  # Reset
    #             continue
            
    #         words = line.split()
    #         if len(words) == 1:
    #             word = words[0]
    #             if word.replace('.', '').isalpha() and 2 < len(word) < 20:
    #                 if word.upper() not in ['RESUME', 'CV', 'PROFILE', 'SUMMARY', 'ABOUT', 'CONTACT']:
    #                     potential_parts.append(word)
                        
    #                     if len(potential_parts) >= 2:
    #                         combined = ' '.join(potential_parts[:3])
    #                         if self._validate_name(combined): 
    #                             return combined.title()
    #         else:
    #             # Multi-word line - check if it's a name
    #             if len(words) <= 4:
    #                 if all(w.replace('.', '').isalpha() for w in words):
    #                     # --- REPLACE YOUR OLD RETURN WITH THIS ---
    #                     if self._validate_name(line):
    #                         return line.title()
    #         potential_parts = []
        
    #     # Strategy 8: Look for first non-contact line that looks like a name
    #     for i, line in enumerate(clean_lines[:10]):
    #         # Skip obvious non-name lines
    #         skip_patterns = ['@', 'http', 'www', '+', '📞', '✉️', '📍', '.com', 'years', 'experience']
    #         if any(pattern in line.lower() for pattern in skip_patterns):
    #             continue
            
    #         # Skip very long lines (likely descriptions)
    #         if len(line) > 60:
    #             continue
            
    #         words = line.split()
            
    #         # 1-4 words, mostly alphabetic
    #         if 1 <= len(words) <= 4:
    #             alpha_words = [w for w in words if w.replace('.', '').replace(',', '').isalpha()]
    #             if len(alpha_words) == len(words) and len(alpha_words) >= 1:
    #                 name_candidate = ' '.join(alpha_words).title()
    #                 # Final validation
    #                 if 3 < len(name_candidate) < 50:
    #                     if self._validate_name(name_candidate):
    #                         return name_candidate
        
    #     return None
    
    
    # def _validate_name(self, name: str) -> bool:
    #     """
    #     Validate extracted name against blacklist and basic rules.
    #     Returns True if name is valid, False otherwise.
    #     """
    #     if not name or len(name) < 3:
    #         return False
        
    #     name_lower = name.lower().strip()
        
    #     # Check against blacklist
    #     for blacklisted in self.NAME_BLACKLIST:
    #         if blacklisted in name_lower or name_lower in blacklisted:
    #             return False
        
    #     # Must be mostly alphabetic (at least 70%)
    #     alpha_chars = sum(c.isalpha() for c in name)
    #     total_chars = len(name.replace(' ', ''))
    #     if total_chars > 0 and alpha_chars < total_chars * 0.7:
    #         return False
        
    #     # Should not be all numbers
    #     if name.replace(' ', '').replace('.', '').isdigit():
    #         return False
        
    #     # Check if it looks like a section header (ends with colon)
    #     if name.strip().endswith(':'):
    #         return False
        
    #     # Reject common company/organization keywords
    #     company_keywords = [
    #         'economy', 'solutions', 'pvt', 'ltd', 'inc', 'corp', 'llc',
    #         'technologies', 'systems', 'services', 'consulting', 'group',
    #         'data economy', 'data product', 'data solutions',
    #         'professional and business', 'banking', 'insurance'
    #     ]
        
    #     for keyword in company_keywords:
    #         if keyword in name_lower:
    #             return False
        
    #     return True
    


    # def _validate_name(self, name_candidate: str) -> bool:
    #     """
    #     Dynamic validation using NLP to distinguish between 
    #     human names and technical/section headers.
    #     """
    #     if not name_candidate or len(name_candidate) < 3:
    #         return False

    #     # 1. Process with NLP
    #     doc = nlp(name_candidate)
        
    #     # 2. Check Entity Type
    #     # We look if Spacy identifies this specific string as a PERSON
    #     is_person_ent = any(ent.label_ == "PERSON" for ent in doc.ents)
        
    #     # 3. Part-of-Speech Validation
    #     # Real names usually consist of Proper Nouns (PROPN)
    #     pos_tags = [token.pos_ for token in doc]
    #     is_mainly_proper_nouns = pos_tags.count("PROPN") >= 1
        
    #     # 4. Negative Context Check (The "Lokesh/And Css" Fix)
    #     # If the candidate contains common technical verbs or conjunctions
    #     # identified by the NLP as non-nouns, reject it.
    #     for token in doc:
    #         # Reject if it contains common coding symbols or lowercase verbs
    #         if token.pos_ == "VERB" and token.is_lower:
    #             return False
    #         # Reject if it's a known technical dependency (like 'and' in 'Java and CSS')
    #         if token.dep_ == "cc" and token.text.lower() == "and":
    #             return False

    #     # 5. Case Sensitivity Check
    #     # Most headers like "GOVERNANCE AND COMPLIANCE" are all caps or 
    #     # contain words that aren't typically names.
    #     if name_candidate.isupper() and len(name_candidate.split()) > 3:
    #         # Large all-cap strings are usually headers, not names
    #         return False

    #     # Combine: It should be a PERSON entity OR a sequence of Proper Nouns 
    #     # that doesn't trigger the technical filters.
    #     return is_person_ent or is_mainly_proper_nouns
    
    # def _is_valid_name(self, text: str) -> bool:
    #     """Enhanced validation: Vetoes cities and technical noise."""
    #     if not text or len(text.split()) < 2 or len(text.split()) > 4:
    #         return False
        
    #     text_lower = text.lower()
        
    #     # 1. SUBSTRING BLACKLIST: Rejects 'Professional Summary', 'Objective', etc.
    #     if any(blacklisted in text_lower for blacklisted in NAME_BLACKLIST):
    #         return False

    #     # 2. CROSS-COLUMN VETO: Reject if the 'name' is actually a known city
    #     # We load geonames cache locally within the function for strict gating
    #     gc = geonamescache.GeonamesCache()
    #     cities = gc.get_cities()
    #     if any(text_lower == city['name'].lower() for city in cities.values()):
    #         return False # It's a location, not a name

    #     # 3. Metadata/Artifact Patterns
    #     skip_patterns = ['@', 'http', 'www', '+', '📞', '✉️', '📍', '.com', 'years', 'experience']
    #     if any(p in text_lower for p in skip_patterns):
    #         return False

    #     # 4. POS-TAG VETO: Reject if it contains Verbs or Adjectives (Technical noise)
    #     doc = nlp(text)
    #     invalid_tags = {"VERB", "ADJ", "ADP", "ADV"}
    #     if any(token.pos_ in invalid_tags for token in doc):
    #         return False
                
    #     return True
    
    def _is_valid_name(self, text: str) -> bool:
        """Hard-gate validation for names."""
        if not text or len(text.split()) < 2 or len(text.split()) > 4:
            return False
        
        text_lower = text.lower()
        
        # 1. Reject if any part is in the Title/Business Blacklist
        if any(blacklisted in text_lower for blacklisted in NAME_BLACKLIST):
            return False

        # 2. CROSS-COLUMN VETO: Reject if the name is actually a City
        gc = geonamescache.GeonamesCache()
        cities = gc.get_cities()
        if any(text_lower == city['name'].lower() for city in cities.values()):
            return False 

        # 3. POS Veto: Must be Proper Nouns ONLY
        doc = nlp(text)
        if any(token.pos_ not in ["PROPN", "PUNCT", "SPACE"] for token in doc):
            return False
                
        return True
    
    def _extract_urls(self) -> Dict[str, Optional[str]]:
        """Extracts LinkedIn and GitHub URLs using regex."""
        # The (?:https?://)? makes the http/https completely optional
        # We also added periods and hyphens to the allowed profile characters
        linkedin_regex = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_.-]+/?'
        github_regex = r'(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_.-]+/?'
        
        linkedin = re.search(linkedin_regex, self.text, re.IGNORECASE)
        github = re.search(github_regex, self.text, re.IGNORECASE)
        
        # Clean them up so they always save as valid clickable links in the DB
        linkedin_url = linkedin.group(0) if linkedin else None
        if linkedin_url and not linkedin_url.startswith('http'):
            linkedin_url = f"https://{linkedin_url}"
            
        github_url = github.group(0) if github else None
        if github_url and not github_url.startswith('http'):
            github_url = f"https://{github_url}"
        
        return {
            "linkedin": linkedin_url,
            "github": github_url
        }
    def _extract_personal_details(self) -> dict:
        """Extracts common personal details into a JSON-friendly dictionary."""
        details = {}
        
        # 1. Date of Birth (DOB)
        # Catches formats like: "DOB: 15/08/1995", "Date of Birth - 15-Aug-1995"
        dob_match = re.search(r'(?i)(?:dob|date of birth)\s*[:\-]?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})', self.text)
        if dob_match:
            details['dob'] = dob_match.group(1).strip()

        # 2. Gender
        gender_match = re.search(r'(?i)\b(?:gender|sex)\s*[:\-]?\s*(male|female|other)\b', self.text)
        if gender_match:
            details['gender'] = gender_match.group(1).strip().capitalize()

        # 3. Marital Status
        marital_match = re.search(r'(?i)marital status\s*[:\-]?\s*(single|married|unmarried|divorced)\b', self.text)
        if marital_match:
            details['marital_status'] = marital_match.group(1).strip().capitalize()

        # 4. Nationality
        nationality_match = re.search(r'(?i)nationality\s*[:\-]?\s*([a-zA-Z]+)', self.text)
        # Avoid catching generic words if the formatting is weird
        if nationality_match and len(nationality_match.group(1)) > 3:
            details['nationality'] = nationality_match.group(1).strip().capitalize()

        return details
 
    def _normalize_text(self, text: any) -> str:
        """Fix: Ensure the input is a string before normalizing."""
        if not isinstance(text, str):
            # If text is a list, join it; if it's None, return empty string
            if isinstance(text, list):
                text = " ".join(text)
            else:
                return ""
            
                
        return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')

    # def _extract_name(self) -> Optional[str]:
    #     # 1. Search for "Name:" labels anywhere (Personal Details Fix)
    #     for line in self.lines:
    #         clean_line = self._normalize_text(line).strip()
    #         if re.search(r'^(name|candidate|person)\s*[:|-]\s*', clean_line, re.I):
    #             name_candidate = re.sub(r'^(name|candidate|person)\s*[:|-]\s*', '', clean_line, flags=re.I).strip()
    #             if self._is_valid_name(name_candidate):
    #                 return name_candidate.title()

    #     # 2. Fallback to top of document
    #     for line in self.lines[:10]:
    #         clean_line = self._normalize_text(line).strip()
    #         if self._is_valid_name(clean_line):
    #             return clean_line.title()
                
    #     return "unknown"
    
    def _extract_name(self) -> Optional[str]:
        """
        Extracts candidate name using text analysis with strict filtering 
        against common resume headers and keywords.
        """
        raw_name = None
        
        # 1. Grab the first few non-empty lines as the most likely name candidates
        # (This avoids grabbing data deep in the resume)
        if hasattr(self, 'lines') and self.lines:
            for line in self.lines[:7]:
                clean_line = line.strip()
                # Skip lines with numbers, @ symbols, or URLs (emails, phones, links)
                if not re.search(r'\d|@|http|www', clean_line) and 0 < len(clean_line.split()) < 5:
                    raw_name = clean_line
                    break

        if not raw_name:
            return None

        # 2. Clean the string (remove trailing punctuation, tabs)
        clean_name = re.sub(r'[^\w\s\.\-]', '', raw_name).strip()

        # 3. The Strict Blacklist: Reject if it contains common resume headers
        blacklist = [
            "professional", "experience", "summary", "module", "pool", 
            "curriculum", "vitae", "resume", "objective", "profile", 
            "mobile", "email", "address", "contact", "details", "personal",
            "skills", "education", "work", "history", "project", "technologies"
        ]
        
        name_lower = clean_name.lower()
        if any(bad_word in name_lower for bad_word in blacklist):
            return None # FORCE FALLBACK TO FILENAME!

        # 4. Final sanity check: A real name is usually 1 to 4 words
        word_count = len(clean_name.split())
        if word_count < 1 or word_count > 4:
            return None

        return clean_name.title()
    
    
    def _extract_location(self) -> str:
        """
        Extracts location and strictly filters out phone labels, email labels, 
        and trailing countries (like "India.").
        """
        raw_location = None
        
        # 1. Search the top portion of the resume (first 1000 chars) for location markers
        search_area = self.text[:1000] if self.text else ""
        
        # Look for explicit "Location: Hyderabad" patterns
        explicit_loc = re.search(r'(?i)(?:location|address|city)\s*[:\-]?\s*([a-zA-Z\s,]+)', search_area)
        if explicit_loc:
            raw_location = explicit_loc.group(1)
            
        # 2. If no explicit label, look for common Indian cities as a fallback
        if not raw_location:
            common_cities = r'(?i)\b(Hyderabad|Pune|Mumbai|Navi Mumbai|Bengaluru|Bangalore|Chennai|Delhi|Noida|Gurgaon|Kolkata|Amalner|Balasore|Lucknow)\b'
            city_match = re.search(common_cities, search_area)
            if city_match:
                raw_location = city_match.group(1)

        if not raw_location:
            return "unknown"

        # 3. Clean the string
        clean_loc = raw_location.strip()
        
        # 4. The Location Blacklist: Words that are definitely not cities
        blacklist = [
            "mobile", "phone", "cell", "email", "tel", "ph", "dob", 
            "date", "name", "linkedin", "github", "unknown", "india"
        ]
        
        if clean_loc.lower() in blacklist:
            return "unknown"
            
        # 5. Formatting Cleanup: 
        # If it says "Hyderabad, India" or "Pune, MH", just grab the city part
        if "," in clean_loc:
            clean_loc = clean_loc.split(",")[0].strip()
            
        # Remove trailing periods and non-alphabetic chars
        clean_loc = re.sub(r'[^a-zA-Z\s]', '', clean_loc).strip()

        # Final sanity check on length
        if len(clean_loc) < 3 or len(clean_loc) > 20:
            return "unknown"

        return clean_loc.title()
    
    # def _extract_location(self) -> str:
    #     """Strictly verified location extraction."""
    #     gc = geonamescache.GeonamesCache()
    #     cities = gc.get_cities()
    #     states = gc.get_us_states()
        
    #     # 1. Look for explicit Location Labels (Address/Place)
    #     for line in self.lines:
    #         clean_line = self._normalize_text(line).strip()
    #         if re.search(r'^(place|location|address|residing)\s*[:|-]\s*', clean_line, re.I):
    #             loc_candidate = re.sub(r'^(place|location|address|residing)\s*[:|-]\s*', '', clean_line, flags=re.I).strip()
    #             # Verify if this labeled value is a real city
    #             if any(loc_candidate.title() == c['name'] for c in cities.values()):
    #                 return loc_candidate.title()

    #     # 2. NLP Header/Footer Scan with Hard Gate
    #     context_text = "\n".join(self.lines[:15] + self.lines[-10:])
    #     doc = nlp(self._normalize_text(context_text))
        
    #     valid_candidates = []
    #     for ent in doc.ents:
    #         if ent.label_ == "GPE":
    #             text = ent.text.strip()
    #             # HARD GATE: Reject common noise
    #             if len(text) < 3 or any(term in text.lower() for term in LOCATION_BLACKLIST):
    #                 continue
                
    #             # GEONAMES VERIFICATION
    #             is_real = any(text.title() == c['name'] for c in cities.values()) or text.upper() in states
    #             if is_real:
    #                 valid_candidates.append(text.title())

    #     return valid_candidates[0] if valid_candidates else "unknown"
    
    

    # def _extract_location(self) -> str:
    #     if not self.text: return "unknown"
        
    #     # 1. Get contact info for proximity check
    #     email = self._extract_email()
    #     phone = self._extract_phone()
        
    #     # 2. Process text with NLP
    #     doc = nlp(self.text)
    #     gpe_candidates = [ent for ent in doc.ents if ent.label_ == "GPE"]
        
    #     # 3. Proximity Check (Near Email/Phone)
    #     for ent in gpe_candidates:
    #         start = max(0, ent.start - 10)
    #         end = min(len(doc), ent.end + 10)
    #         context_window = doc[start:end].text
            
    #         if (email and email in context_window) or (phone and phone in context_window):
    #             # Validation A: Ensure it's a Proper Noun location
    #             if all(token.pos_ in ["PROPN", "PUNCT", "SPACE"] for token in ent):
    #                 # Validation B: Ensure it's not part of an 'Experience' or 'Education' sentence
    #                 if not any(word in ent.sent.text.lower() for word in ['university', 'college', 'limited', 'inc']):
    #                     return ent.text.strip()

    #     # 4. Fallback: Specific Header/Footer lines only
    #     candidate_lines = self.lines[:10] + self.lines[-5:]
    #     candidate_area = "\n".join(candidate_lines)
    #     temp_doc = nlp(candidate_area)
        
    #     for ent in temp_doc.ents:
    #         if ent.label_ == "GPE":
    #             if all(token.pos_ in ["PROPN", "PUNCT", "SPACE"] for token in ent):
    #                 if not any(word in ent.sent.text.lower() for word in ['university', 'college', 'limited', 'inc']):
    #                     if ent.text.strip().lower() not in ['india', 'usa', 'state', 'location']:
    #                         return ent.text.strip()

    #     return "unknown"
    
    def _extract_name_from_filename(self) -> Optional[str]:
        """Uses a boundary-detection strategy to isolate names from complex filenames."""
        filename = os.path.basename(self.file_path)
        # Remove extension
        name_part = re.sub(r'\.[^.]+$', '', filename)
        
        # 1. Broad Noise Cluster (Tech stacks, Locations, Titles)
        # Added 'azure', 'cloud', 'html', 'sdet', 'qa' to your list
        noise_pattern = r'(_|-|\s)?(\d+\+?\s*yrs?|java|python|sap|senior|junior|sr|jr|architect|developer|lead|hyd|blr|pune|noida|resume|cv|azure|cloud|html|sdet|qa|testing)\b.*'
        
        # Split the filename at the first sign of professional noise
        clean_name = re.split(noise_pattern, name_part, flags=re.IGNORECASE)[0]
        
        # 2. Cleanup symbols and digits
        clean_name = re.sub(r'[_|-]', ' ', clean_name)
        clean_name = re.sub(r'\d+', '', clean_name).strip()
        
        # 3. VERIFICATION: Use your new geonamescache & Noise check
        # This prevents filenames like 'Hyderabad_Resume.pdf' from returning 'Hyderabad'
        if not self._is_valid_name(clean_name):
            return None
        
        words = clean_name.split()
        if 1 <= len(words) <= 4:
            if all(w.replace('.', '').isalpha() for w in words):
                return " ".join(words).title()
                
        return None
    
    
    # ============================================================
    # EMAIL & PHONE EXTRACTION
    # ============================================================
    
    def _extract_email(self) -> Optional[str]:
        """Primary email extraction with validation against system noise."""
        # Regex that ensures the email is not part of a larger garbled string
        pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]{2,}'
        emails = re.findall(pattern, self.text)
        
        # Logic: Prioritize emails that don't contain 'placeholder' keywords
        for email in emails:
            if not any(x in email.lower() for x in ['example', 'domain', 'test', 'email.com']):
                return email.lower()
        return emails[0] if emails else None

    def _extract_phone(self) -> Optional[str]:
        """Uses localized patterns to extract valid phone numbers."""
        # Remove common OCR noise/formatting but keep '+'
        clean_text = re.sub(r'[()|\t]', ' ', self.text)
        
        # Focus on Indian and International formats found in your files
        patterns = [
            r'(?:\+91|91|0)?[-\s]?[6-9]\d{9}', # Indian Mobile
            r'\b\d{10}\b',                       # Standard 10-digit
            r'\b\d{3}[-\s]\d{3}[-\s]\d{4}\b'     # US/Formatted
        ]
        
        for p in patterns:
            match = re.search(p, clean_text)
            if match:
                # Final validation: check digit density
                num_only = re.sub(r'\D', '', match.group())
                if 10 <= len(num_only) <= 12:
                    return match.group().strip()
        return None
    
    

    # def _extract_location(self) -> str:
    #     """Verified Regex + Geonamescache strategy."""
    #     if not self.text: return "unknown"
    #     header = self.text
        
    #     # Look for 'City, State' or 'Location: City'
    #     patterns = [
    #         r"(?:Location|Address|Place|Work Location)\s*[:|-]\s*([A-Z][a-z]+)",
    #         r"([A-Z][a-z]+)\s*,\s*([A-Z][a-z]+)"
    #     ]
        
    #     for pattern in patterns:
    #         for match in re.finditer(pattern, header):
    #             city_candidate = match.group(1).strip()
    #             # Double check with Geonamescache
    #             if city_candidate.lower() in CITIES:
    #                 # If city is verified, return the formatted match
    #                 if "," in match.group(0):
    #                     return f"{city_candidate}, {match.group(2).strip()}"
    #                 return city_candidate
                    
    #     return "unknown"  
    

    def _extract_address(self) -> Optional[str]:
        """Extracts address by finding the Address label and capturing until a line break or next label."""
        pattern = r'(?:Address|Residence|Location)\s*[:|-]\s*(.*)'
        match = re.search(pattern, self.text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    

    
    # ============================================================
    # SKILLS EXTRACTION
    # ============================================================
    
    def _extract_skills(self) -> str:
        # Get the raw section text first
        raw_text = self._find_section_dynamically("skills")
        if not raw_text: return ""
        
        # NLP Filter: Reject any 'skill' that contains a Verb (Action word)
        # This prevents job duties from showing up in the Skills column
        doc = nlp(raw_text)
        skills = []
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.strip()
            # Check if the chunk is short (1-3 words) and lacks verbs
            if 1 <= len(chunk_text.split()) <= 3:
                if not any(token.pos_ == "VERB" for token in nlp(chunk_text)):
                    skills.append(chunk_text)
        
        return ", ".join(list(set(skills)))
    
    # ============================================================
    # EXPERIENCE & EDUCATION EXTRACTION
    # ============================================================
    # def _find_section(self, keywords: List[str], stop_keywords: List[str]) -> Optional[str]:
    #     """Smart section crawler that stops at the next logical header."""
    #     lines = self.lines
    #     section_content = []
    #     is_capturing = False
        
    #     # Headers are usually: Short (1-4 words), Uppercase, or end with ':'
    #     def is_header(text, kw_list):
    #         t = text.lower().strip()
    #         is_match = any(k in t for k in kw_list)
    #         is_styled = text.isupper() or text.endswith(':') or len(text.split()) <= 4
    #         return is_match and is_styled

    #     for line in lines:
    #         if not is_capturing:
    #             if is_header(line, keywords):
    #                 is_capturing = True
    #                 continue
    #         else:
    #             # Check if we hit a stop keyword or a NEW generic header
    #             if is_header(line, stop_keywords) or (line.isupper() and len(line) > 3):
    #                 break
    #             section_content.append(line)
                
    #     return "\n".join(section_content).strip() if section_content else None
    
    # def _find_section(self, target_concept_str: str) -> str:
    #     """
    #     Einstein-Level Discovery:
    #     Finds a section by its 'Semantic Flavor'. No stop-words required.
    #     """
    #     # Initialize flag to prevent UnboundLocalError
    #     found_target = False
    #     content = []
        
    #     # Use the medium model 'md' for actual vector reasoning
    #     goal_vec = nlp(target_concept_str)
    #     lines = self.text.split('\n')
        
    #     for line in lines:
    #         clean = line.strip()
    #         if not clean: continue
            
    #         # Identify Headers: Short lines that look like structural landmarks
    #         is_header = len(clean) < 50 and (clean.isupper() or clean.endswith(':'))
            
    #         if is_header:
    #             header_vec = nlp(clean.lower())
                
    #             # Semantic Similarity Check
    #             # Note: Similarity works best with en_core_web_md or lg
    #             similarity = header_vec.similarity(goal_vec)
                
    #             if similarity > 0.6: # Found the section
    #                 found_target = True
    #                 continue
    #             elif found_target: # Hit a NEW header, stop collecting
    #                 break
            
    #         if found_target:
    #             content.append(clean)
                
    #     return "\n".join(content).strip()
    
    # At the top of your class or module
    

    def _find_section_dynamically(self, target_key: str) -> str:
        """
        Finds section text and stops immediately if a DIFFERENT section starts.
        """
        target_keywords = SECTION_CONCEPTS.get(target_key, [])
        lines = self.text.split('\n')
        
        content = []
        found_target = False
        
        for line in lines:
            clean = line.strip()
            if not clean: continue
            
            # 1. Detect if this line looks like a header (short and bold/caps)
            is_header = len(clean) < 50 and (clean.isupper() or clean.endswith(':'))
            
            if is_header:
                # 2. Check if this header matches the section we want
                if any(kw in clean.lower() for kw in target_keywords):
                    found_target = True
                    continue
                
                # 3. CRITICAL FIX: If we are already collecting text, check if this 
                # new header belongs to ANY OTHER category. If so, STOP.
                if found_target:
                    is_other_section = any(
                        any(kw in clean.lower() for kw in keywords)
                        for key, keywords in SECTION_CONCEPTS.items() if key != target_key
                    )
                    if is_other_section:
                        break
            
            if found_target:
                content.append(clean)
                
        return "\n".join(content).strip()
        
    def _extract_experience(self) -> str:
        # Just get the section; experience is usually raw text
        return self._find_section_dynamically("experience")

    def _extract_education(self) -> str:
        # Uses the same dynamic engine but stops if 'Experience' or 'Skills' follow
        return self._find_section_dynamically("education")
    
    
    # UPDATE THIS IN YOUR CODE:
    def _is_reversed_text(self, input_text: Optional[str] = None) -> bool:
        """
        Checks if text is reversed using character entropy.
        If input_text is provided, checks that; otherwise checks self.text.
        """
        target_text = input_text if input_text is not None else self.text
        if not target_text:
            return False
            
        sample = re.sub(r'[^a-z]', '', target_text[:500].lower())
        if len(sample) < 20: 
            return False
        
        english_bigrams = {'th', 'he', 'in', 'er', 'an', 're', 'on', 'at', 'st', 'ed'}
        
        def calculate_score(text):
            return sum(1 for i in range(len(text)-1) if text[i:i+2] in english_bigrams)

        normal_score = calculate_score(sample)
        reversed_score = calculate_score(sample[::-1])
        
        return reversed_score > (normal_score * 1.5)
        
    # ============================================================
    # JOB DESCRIPTION DETECTION
    # ============================================================
    def is_job_description(self) -> bool:
        """Uses keyword density to distinguish a JD from a Resume."""
        if not self.text: return False
        
        # JDs contain 'Company' info and 'Requirements', Resumes contain 'Personal' info
        jd_weights = {
            "responsibilities": 1, "requirements": 1, "qualifications": 1,
            "we are looking for": 2, "job description": 3, "benefits": 1,
            "competitive salary": 1, "reporting to": 1
        }
        
        text_lower = self.text.lower()
        score = sum(weight for kw, weight in jd_weights.items() if kw in text_lower)
        
        # If the text has high JD indicators but lacks a Name/Email combo, it's a JD
        return score >= 4
    
    
    # def _extract_experience(self) -> Optional[str]:
    #     keywords = ['experience', 'employment', 'history', 'work', 'background']
    #     stops = ['education', 'skills', 'projects', 'certification', 'personal']
    #     return self._find_section(keywords, stops)
    
   
    
    # def _extract_education(self) -> Optional[str]:
    #     """Enhanced education extraction"""
    #     edu_keywords = [
    #         'education', 'academic', 'qualification', 'educational background', 
    #         'academics', 'academic background', 'educational qualifications'
    #     ]
        
    #     stop_keywords = [
    #         'experience', 'skills', 'projects', 'certification', 
    #         'achievements', 'languages', 'references', 'hobbies', 
    #         'contact', 'interests'
    #     ]
        
    #     edu_text = self._find_section(edu_keywords, stop_keywords)
        
    #     if edu_text:
    #         edu_text = re.sub(r'\n+', '\n', edu_text)
    #         lines = edu_text.split('\n')
    #         cleaned_lines = [line for line in lines if not self._is_reversed_text(line)]
    #         edu_text = '\n'.join(cleaned_lines)
    #         return edu_text if cleaned_lines else None
        
    #     return None
    
    # def _find_section(self, keywords: List[str], stop_keywords: List[str] = None) -> Optional[str]:
    #     """Generic section finder"""
    #     if stop_keywords is None:
    #         stop_keywords = []
        
    #     section_lines = []
    #     capture = False
        
    #     for i, line in enumerate(self.lines):
    #         line_lower = line.lower().strip()
            
    #         if not capture:
    #             for keyword in keywords:
    #                 if keyword in line_lower:
    #                     if (line.isupper() or 
    #                         line.endswith(':') or 
    #                         len(line.split()) <= 4 or
    #                         line_lower == keyword):
    #                         capture = True
    #                         break
    #             continue
            
    #         if capture:
    #             for stop_keyword in stop_keywords:
    #                 if (stop_keyword in line_lower and 
    #                     (line.isupper() or line.endswith(':') or len(line.split()) <= 4)):
    #                     return '\n'.join(section_lines).strip() if section_lines else None
                
    #             if line.isupper() and len(line) > 5:
    #                 reversed_check = line[::-1].lower()
    #                 common_sections = ['experience', 'education', 'skills', 'projects', 'contact']
    #                 if any(section in reversed_check for section in common_sections):
    #                     return '\n'.join(section_lines).strip() if section_lines else None
                
    #             section_lines.append(line)
                
    #             if len(section_lines) > 50:
    #                 break
        
    #     return '\n'.join(section_lines).strip() if section_lines else None
    

    
    
    # def is_job_description(self) -> bool:
    #     """Detect if document is a Job Description"""
    #     if not self.text:
    #         return False

    #     jd_keywords = [
    #         "job description",
    #         "role summary",
    #         "key responsibilities",
    #         "required qualifications",
    #         "we are seeking",
    #         "responsibilities",
    #         "competencies",
    #         "nice-to-have",
    #         "job requirements",
    #         "position summary",
    #         "required skills",
    #         "preferred qualifications"
    #     ]

    #     text_lower = self.text.lower()
    #     score = sum(keyword in text_lower for keyword in jd_keywords)

    #     return score >= 3  # More strict threshold


# Test function
if __name__ == "__main__":
    parser = ResumeParser("path/to/resume.pdf", use_ocr_fallback=True)
    result = parser.parse_full()
    print(result)