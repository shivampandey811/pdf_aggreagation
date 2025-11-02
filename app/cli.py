import argparse
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pdf_extractor import PDFExtractor
from src.field_mapper import FieldMapper
from src.amendment_parser import AmendmentParser
from src.pdf_generator import PDFGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_charter_party(template_path: str, recap_path: str, 
                         output_path: str, verbose: bool = False) -> bool:
    """Process charter party PDFs"""
    try:
        logger.info("=" * 60)
        logger.info("Charter Party PDF Automation - Processing Started")
        logger.info("=" * 60)
        
        template_file = Path(template_path)
        recap_file = Path(recap_path)
        
        if not template_file.exists():
            logger.error(f"Template file not found: {template_path}")
            return False
        if not recap_file.exists():
            logger.error(f"Recap file not found: {recap_path}")
            return False
        
        logger.info(f"Template: {template_file.name}")
        logger.info(f"Recap: {recap_file.name}")
        
        # Extract
        logger.info("\n[1/4] Extracting PDF content...")
        extractor = PDFExtractor()
        template_data = extractor.extract_template(str(template_file))
        recap_data = extractor.extract_recap(str(recap_file))
        logger.info("  ✓ PDFs extracted")
        
        # Map fields
        logger.info("\n[2/4] Mapping Part I fields...")
        mapper = FieldMapper()
        fields = mapper.extract_part_i_fields(recap_data)
        logger.info(f"  ✓ {len(fields)} fields extracted")
        
        # Detect amendments
        logger.info("\n[3/4] Detecting amendments...")
        parser = AmendmentParser()
        amendments = parser.detect_amendments(
            template_data.get("part_ii", []),
            recap_data.get("part_ii", [])
        )
        logger.info(f"  ✓ Deleted: {len(amendments['deleted'])}, Added: {len(amendments['added'])}")
        
        # Generate PDF
        logger.info("\n[4/4] Generating final PDF...")
        generator = PDFGenerator()
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        success = generator.create_pdf(
            template_data,
            fields,
            amendments,
            str(output_file)
        )
        
        if success:
            logger.info(f"  ✓ PDF created: {output_file.name}")
            logger.info("\n" + "=" * 60)
            logger.info("SUCCESS - Processing Complete")
            logger.info("=" * 60)
            return True
        else:
            logger.error("  ✗ Failed to generate PDF")
            return False
    
    except Exception as e:
        logger.error(f"ERROR: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Charter Party PDF Automation Tool"
    )
    
    parser.add_argument("--template", type=str, help="Path to template PDF", required=True)
    parser.add_argument("--recap", type=str, help="Path to recap PDF", required=True)
    parser.add_argument("-o", "--output", type=str, default="Final_Filled.pdf")
    parser.add_argument("-v", "--verbose", action="store_true")
    
    args = parser.parse_args()
    
    success = process_charter_party(
        args.template,
        args.recap,
        args.output,
        args.verbose
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
