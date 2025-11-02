import re
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class FieldMapper:
    """Maps Part I fields between template and filled values"""
    
    FIELD_LABELS = {
        1: "Charter Party Form",
        2: "Vessel Name",
        3: "Flag / Class",
        4: "Owners",
        5: "Charterers",
        6: "Brokers / Commission",
        7: "Date & Place of Fixture",
        8: "Laycan",
        9: "Cargo Description",
        10: "Quantity",
        11: "Load Port(s)",
        12: "Discharge Port(s)",
        13: "Freight / Rate / Basis",
        14: "Payment Terms",
        15: "Laytime",
        16: "Demurrage / Despatch",
        17: "NOR / Notice / Time Counting",
        18: "Law & Arbitration",
        19: "Special Provisions"
    }
    
    FIELD_VALIDATORS = {
        1: r"^(VOY\d+|BALTIME|NYPE|GENCON).*",
        2: r"^(MV|MS|MT|SS)\s+\w+",
        3: r"^\w+\s*/\s*\w+",
    }
    
    def __init__(self):
        self.mapped_fields = {}
        self.validation_errors = []
    
    def extract_part_i_fields(self, recap_data: Dict) -> Dict:
        """Extract Part I fields from recap PDF data"""
        fields = {}
        part_i_data = recap_data.get("part_i", {})
        
        if isinstance(part_i_data, dict):
            for field_num in range(1, 20):
                if field_num in part_i_data:
                    fields[field_num] = {
                        "label": self.FIELD_LABELS.get(field_num, ""),
                        "value": part_i_data[field_num].get("value", ""),
                        "original_label": part_i_data[field_num].get("label", "")
                    }
                else:
                    fields[field_num] = {
                        "label": self.FIELD_LABELS.get(field_num, ""),
                        "value": ""
                    }
        
        return fields
    
    def validate_fields(self, fields: Dict) -> Tuple[bool, Dict]:
        """Validate extracted field values"""
        errors = {}
        required_fields = [1, 2, 4, 5, 8, 9, 10, 11, 12, 13, 15]
        
        for field_num in required_fields:
            if field_num not in fields or not fields[field_num].get("value", "").strip():
                errors[field_num] = f"Field {field_num} ({self.FIELD_LABELS.get(field_num)}) is required"
        
        for field_num, validator in self.FIELD_VALIDATORS.items():
            if field_num in fields and fields[field_num].get("value"):
                value = fields[field_num]["value"]
                if not re.match(validator, value, re.IGNORECASE):
                    errors[field_num] = f"Field {field_num} format invalid: {value}"
        
        is_valid = len(errors) == 0
        self.validation_errors = errors
        return is_valid, errors
    
    def normalize_field_value(self, field_num: int, value: str) -> str:
        """Normalize field value based on field type"""
        if not value:
            return value
        
        if field_num == 10:
            if not re.search(r'(MT|tonnes|TEU)', value, re.IGNORECASE):
                value += " MT"
        
        elif field_num == 13:
            value = value.replace("USD", "USD").replace("$", "USD ")
        
        elif field_num == 15:
            value = value.upper()
            value = value.replace("SHEC", "SHEX")
        
        return value.strip()
    
    def get_field_statistics(self, fields: Dict) -> Dict:
        """Get statistics about extracted fields"""
        total = len([f for f in fields.values() if f.get("label")])
        filled = len([f for f in fields.values() if f.get("value")])
        empty = total - filled
        
        return {
            "total_fields": total,
            "filled_fields": filled,
            "empty_fields": empty,
            "completion_percentage": (filled / total * 100) if total > 0 else 0
        }
