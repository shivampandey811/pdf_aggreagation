import streamlit as st
import tempfile
import os
import sys
import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pdf_extractor import PDFExtractor
from src.field_mapper import FieldMapper
from src.amendment_parser import AmendmentParser
from src.pdf_generator import PDFGenerator


def setup_page():
    st.set_page_config(
        page_title="Charter Party Automation",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# Add these helper functions at top after imports

def safe_get_part_ii(data):
    if data and isinstance(data, dict):
        result = data.get("part_ii")
        if result is None:
            return []
        return result
    return []

def debug_session_state():
    st.write("DEBUG: Session State Keys", list(st.session_state.keys()))
    st.write("DEBUG: Template Data Type", type(st.session_state.get("template_data")))
    st.write("DEBUG: Recap Data Type", type(st.session_state.get("recap_data")))
    st.write("DEBUG: Template Keys", st.session_state.template_data.keys() if st.session_state.template_data else "None")
    st.write("DEBUG: Recap Keys", st.session_state.recap_data.keys() if st.session_state.recap_data else "None")

def main():
    setup_page()
    
    st.title("📄 Charter Party PDF Automation")
    st.markdown("**Intelligent PDF generation with automatic amendment tracking**")
    
    with st.sidebar:
        st.header("⚙️ Settings")
        show_debug = st.checkbox("Debug Mode", value=False)
    
    tab1, tab2, tab3 = st.tabs(["📤 Upload", "👁️ Preview", "📥 Generate"])
    
    if "template_data" not in st.session_state:
        st.session_state.template_data = None
    if "recap_data" not in st.session_state:
        st.session_state.recap_data = None
    if "amendments" not in st.session_state:
        st.session_state.amendments = None

    # TAB 1: UPLOAD
    with tab1:
        st.header("Upload PDFs")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Template PDF")
            template_file = st.file_uploader(
                "Upload template PDF",
                type="pdf",
                key="template_upload"
            )
            
            if template_file:
                st.success("✅ Template uploaded")
                with st.spinner("Extracting template..."):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(template_file.read())
                            tmp_path = tmp.name
                        
                        extractor = PDFExtractor()
                        st.session_state.template_data = extractor.extract_template(tmp_path)
                        os.unlink(tmp_path)
                        
                        st.info(f"Template: {st.session_state.template_data['pages']} page(s)")
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        with col2:
            st.subheader("Recap PDF")
            recap_file = st.file_uploader(
                "Upload recap PDF",
                type="pdf",
                key="recap_upload"
            )
            
            if recap_file:
                st.success("✅ Recap uploaded")
                with st.spinner("Extracting recap..."):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(recap_file.read())
                            tmp_path = tmp.name
                        
                        extractor = PDFExtractor()
                        st.session_state.recap_data = extractor.extract_recap(tmp_path)
                        os.unlink(tmp_path)
                        
                        st.info(f"Recap: {st.session_state.recap_data['pages']} page(s)")
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    # TAB 2: PREVIEW
    with tab2:
        st.header("Preview & Analysis")
        
        if st.session_state.template_data and st.session_state.recap_data:
            
            with st.expander("📋 Part I - Commercial Terms", expanded=True):
                mapper = FieldMapper()
                fields = mapper.extract_part_i_fields(st.session_state.recap_data)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("**Field #**")
                    for i in range(1, 20):
                        st.write(f"{i}")
                with col2:
                    st.write("**Label**")
                    for i in range(1, 20):
                        label = mapper.FIELD_LABELS.get(i, "")
                        st.write(label[:30])
                with col3:
                    st.write("**Value**")
                    for i in range(1, 20):
                        value = fields.get(i, {}).get("value", "")
                        st.write(value[:30] if value else "—")
            
            with st.expander("🔄 Amendment Analysis", expanded=True):
                parser = AmendmentParser()
                template_part_ii = safe_get_part_ii(st.session_state.template_data)
                recap_part_ii = safe_get_part_ii(st.session_state.recap_data)

                amendments = parser.detect_amendments(
                    template_part_ii,
                    recap_part_ii
                )
                st.session_state.amendments = amendments
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Deleted", len(amendments.get("deleted", [])))
                with col2:
                    st.metric("Added", len(amendments.get("added", [])))
                with col3:
                    st.metric("New Lines", len(amendments.get("new", [])))
                with col4:
                    st.metric("Modified", len(amendments.get("modified", [])))
        
        else:
            st.warning("⚠️ Please upload both PDFs first")
    
    # TAB 3: GENERATE
    with tab3:
        st.header("Generate Final PDF")
        
        if st.session_state.template_data and st.session_state.recap_data:
            
            if st.button("🚀 Generate Final PDF", use_container_width=True):
                with st.spinner("Generating PDF..."):
                    try:
                        mapper = FieldMapper()
                        fields = mapper.extract_part_i_fields(st.session_state.recap_data)
                        
                        parser = AmendmentParser()
                        template_part_ii = safe_get_part_ii(st.session_state.template_data)
                        recap_part_ii = safe_get_part_ii(st.session_state.recap_data)

                        amendments = parser.detect_amendments(
                            template_part_ii,
                            recap_part_ii
                        )
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            output_path = tmp.name
                        
                        generator = PDFGenerator()
                        print("Part I Fields sent to PDF Generator:")
                        for k, v in fields.items():
                            print(f"{k}: {v.get('label')} = {v.get('value')}")

                        success = generator.create_pdf(
                            st.session_state.template_data,
                            fields,
                            amendments,
                            output_path
                        )
                        
                        if success and os.path.exists(output_path):
                            with open(output_path, "rb") as f:
                                pdf_bytes = f.read()
                            
                            st.success("✅ PDF generated successfully!")
                            time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            st.download_button(
                                label="📥 Download Final_Filled.pdf",
                                data=pdf_bytes,
                                file_name=f"Final_Filled_{time}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            
                            os.unlink(output_path)
                        
                        else:
                            st.error("❌ Failed to generate PDF")
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        else:
            st.warning("⚠️ Please upload both PDFs first")


if __name__ == "__main__":
    main()
