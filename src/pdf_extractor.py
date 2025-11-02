import fitz
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """Represents a text block with position information"""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page: int


class PDFExtractor:
    """Extracts text and structure from charter party PDFs"""
    
    def __init__(self, enable_ocr: bool = False):
        self.enable_ocr = enable_ocr
        
    def extract_template(self, pdf_path: str) -> Dict:
        """Extract structure from template PDF"""
        try:
            doc = fitz.open(pdf_path)
            result = {
                "part_i": self._extract_part_i_template(doc),
                "part_ii": self._extract_part_ii_template(doc),
                "pages": doc.page_count,
                "metadata": doc.metadata
            }
            doc.close()
            return result
        except Exception as e:
            logger.error(f"Error extracting template: {e}")
            raise
    
    def extract_recap(self, pdf_path: str) -> Dict:
        """Extract data from recap PDF"""
        try:
            doc = fitz.open(pdf_path)
            result = {
                "part_i": self._extract_part_i_filled(doc),
                "part_ii": self._extract_part_ii_filled(doc),
                "pages": doc.page_count,
                "metadata": doc.metadata
            }
            doc.close()
            return result
        except Exception as e:
            logger.error(f"Error extracting recap: {e}")
            raise
    
    def _extract_part_i_template(self, doc) -> Dict:
        """Extract Part I template structure"""
        part_i = {}
        full_text = ""
        
        for page in doc:
            full_text += page.get_text()
        
        lines = full_text.split('\n')
        for i, line in enumerate(lines):
            match = re.match(r'^(\d+)\.\s+(.+?)(?:\s+\(|$)', line)
            if match:
                field_num = int(match.group(1))
                field_label = match.group(2).strip()
                if 1 <= field_num <= 19:
                    part_i[field_num] = {
                        "label": field_label,
                        "value": "",
                        "line_index": i
                    }
        
        return part_i
    
    def _extract_part_i_filled(self, doc) -> Dict:
        part_i = {}
        full_text = ""

        for page in doc:
            full_text += page.get_text()

        lines = full_text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Stop extraction if reached Part II section
            if "Part II" in line:
                break

            match = re.match(r'^(\d+)\.\s+(.+?)$', line)
            if match:
                field_num = int(match.group(1))
                field_label = match.group(2).strip()

                i += 1
                value_lines = []
                while i < len(lines) and lines[i].strip():
                    next_line = lines[i].strip()
                    if re.match(r'^\d+\.\s+', next_line) or "Part II" in next_line:
                        i -= 1
                        break
                    value_lines.append(next_line)
                    i += 1

                if 1 <= field_num <= 19:
                    part_i[field_num] = {
                        "label": field_label,
                        "value": " ".join(value_lines).strip(),
                        "line_index": i
                    }

            i += 1

        return part_i

    def _extract_part_ii_template(self, doc) -> List[Dict]:
        """Extract Part II clauses from template"""
        clauses = []
        full_text = ""
        
        for page in doc:
            full_text += page.get_text()
        
        if "Part II" in full_text:
            part_ii_text = full_text.split("Part II")[1]
        else:
            part_ii_text = full_text
        
        lines = part_ii_text.split('\n')
        current_clause = None

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Match clause header like "Clause 1. Definitions"
            clause_header_match = re.match(r'^Clause\s*(\d+)\.\s*(.+)$', stripped)
            if clause_header_match:
                current_clause = {
                    "line": int(clause_header_match.group(1)),
                    "title": stripped,
                    "content": []
                }
                clauses.append(current_clause)
                continue

            # Match numbered lines like "1 Some clause text"
            numbered_line_match = re.match(r'^(\d+)\s+(.+)$', stripped)
            if numbered_line_match and current_clause is not None:
                current_clause["content"].append({
                    "line": int(numbered_line_match.group(1)),
                    "text": numbered_line_match.group(2).strip()
                })
                continue

            # Handle continuation or new lines without numbers
            if current_clause is not None:
                current_clause["content"].append({
                    "line": None,
                    "text": stripped
                })

        return clauses

        
    def _extract_part_ii_filled(self, doc) -> List[Dict]:
        """Extract Part II clauses from recap (with amendments)"""
        clauses = []
        full_text = ""
        
        for page in doc:
            full_text += page.get_text()
        
        if "Part II" in full_text:
            part_ii_text = full_text.split("Part II")[1]
        else:
            part_ii_text = full_text
        
        lines = part_ii_text.split('\n')
        current_clause = None
        
        for line in lines:
            # Match clause header like "Clause 1. Definitions"
            clause_header_match = re.match(r'^Clause\s*(\d+)\.\s*(.+)$', line)
            if clause_header_match:
                current_clause = {
                    "line": int(clause_header_match.group(1)),
                    "title": line.strip(),
                    "content": []
                }
                clauses.append(current_clause)
                continue
            
            # Match numbered lines like "1 Some clause text"
            numbered_line_match = re.match(r'^\s*(\d+)\s+(.+)$', line)
            if numbered_line_match and current_clause is not None:
                current_clause["content"].append({
                    "line": int(numbered_line_match.group(1)),
                    "text": numbered_line_match.group(2).strip()
                })
                continue
            
            # Handle continuation or new lines without numbers
            if current_clause and line.strip():
                current_clause["content"].append({
                    "line": None,
                    "text": line.strip()
                })
        if clauses is None:
            clauses = []
        return clauses
