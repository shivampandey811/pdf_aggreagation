import re
from typing import Dict, List, Tuple
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class AmendmentParser:
    """Parses and detects amendments between template and recap clauses"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
    
    def detect_amendments(self, template_clauses: List[Dict], 
                         recap_clauses: List[Dict]) -> Dict:
        """Detect amendments by comparing template and recap clauses"""
        if not template_clauses:
            template_clauses = []
        if not recap_clauses:
            recap_clauses = []
            
        amendments = {
            "deleted": [],
            "added": [],
            "new": [],
            "modified": []
        }
        
        try:
            template_lines = self._extract_clause_lines(template_clauses)
            recap_lines = self._extract_clause_lines(recap_clauses)
            
            amendments = self._analyze_diff(template_lines, recap_lines)
            amendments["new"] = self._find_new_lines(template_clauses, recap_clauses)
            
            logger.info(f"Amendments detected: {len(amendments['deleted'])} deleted, "
                       f"{len(amendments['added'])} added, {len(amendments['new'])} new")
            
            return amendments
        except Exception as e:
            logger.error(f"Error detecting amendments: {e}")
            return amendments
    
    def _extract_clause_lines(self, clauses: List[Dict]) -> List[Dict]:
        """Extract all lines from clauses with metadata"""
        lines = []
        for clause in clauses:
            if "content" in clause:
                for item in clause["content"]:
                    lines.append({
                        "line": item.get("line"),
                        "text": item.get("text", ""),
                        "original": item.get("original", True),
                        "clause_title": clause.get("title", "")
                    })
        return lines
    
    def _analyze_diff(self, template_lines: List[Dict], 
                      recap_lines: List[Dict]) -> Dict:
        """Analyze differences between template and recap"""
        amendments = {
            "deleted": [],
            "added": [],
            "modified": []
        }
        
        template_texts = {item["text"]: item for item in template_lines}
        recap_texts = {item["text"]: item for item in recap_lines}
        
        # Find deleted text
        for text, item in template_texts.items():
            if text not in recap_texts:
                amendments["deleted"].append({
                    "text": item["text"],
                    "line": item.get("line"),
                    "clause": item.get("clause_title")
                })
        
        # Find added text
        for text, item in recap_texts.items():
            if text not in template_texts and not item.get("original", False):
                amendments["added"].append({
                    "text": text,
                    "line": item.get("line"),
                    "clause": item.get("clause_title")
                })
        
        return amendments
    
    def _find_new_lines(self, template_clauses: List[Dict], 
                        recap_clauses: List[Dict]) -> List[Dict]:
        """Find new lines that don't exist in template"""
        new_lines = []
        
        template_lines = set()
        for clause in template_clauses:
            if "content" in clause:
                for item in clause["content"]:
                    if item.get("line"):
                        template_lines.add(item["line"])
        
        for clause in recap_clauses:
            if "content" in clause:
                for item in clause["content"]:
                    if not item.get("original", False) and not item.get("line"):
                        new_lines.append({
                            "text": item.get("text", ""),
                            "clause": clause.get("title", ""),
                            "position": "after_clause"
                        })
        
        return new_lines
    
    def format_amendments_for_display(self, amendments: Dict) -> str:
        """Format amendments as readable text for preview"""
        result = []
        
        if amendments.get("deleted"):
            result.append("DELETED TEXT:")
            for item in amendments["deleted"]:
                result.append(f"  Line {item.get('line', 'N/A')}: ~~{item['text']}~~")
        
        if amendments.get("added"):
            result.append("\nADDED TEXT:")
            for item in amendments["added"]:
                result.append(f"  + {item['text']}")
        
        if amendments.get("new"):
            result.append("\nNEW LINES:")
            for item in amendments["new"]:
                result.append(f"  (new) {item['text']}")
        
        return "\n".join(result) if result else "No amendments detected"
