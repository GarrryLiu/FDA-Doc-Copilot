import streamlit as st
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.embeddings.openai import OpenAIEmbedding
from src.vectorstore.faiss_store import FaissStore
from src.llm.openai import OpenAILLM
from src.tasks.summary import SummaryTask
from src.utils.data_discovery import discover_data_sources
from config.logging_config import setup_logging

# Set up logging
logger = setup_logging()

# Set page title and configuration
st.set_page_config(
    page_title="FDA Oncology Copilot",
    page_icon="📄",
    layout="wide"
)

# ----------- Page Title -----------
st.title("FDA Oncology Copilot")

st.markdown("""
Paste a draft paragraph from your oncology clinical or regulatory document.
Click **Summarize** to get an FDA-style executive summary optimized for oncology submissions.
""")

# ----------- Initialize Components -----------
@st.cache_resource
def initialize_components():
    """
    Initialize the components needed for the application
    
    Returns:
        tuple: (embedding_model, vector_stores, llm)
    """
    # Create embedding model
    embedding_model = OpenAIEmbedding()
    
    # Discover data sources
    discovered_sources = discover_data_sources()
    
    # Load vector stores for all discovered sources
    vector_stores = {}
    for source_name, source_data in discovered_sources.items():
        index_path = source_data["config"]["index_path"]
        
        # Check if index exists
        if os.path.exists(os.path.join(index_path, "index.faiss")):
            try:
                # Load vector store
                vector_store = FaissStore.load(index_path, embedding_model)
                vector_stores[source_name] = vector_store
                logger.info(f"Loaded vector store for source '{source_name}'")
            except Exception as e:
                logger.error(f"Error loading vector store for source '{source_name}': {str(e)}")
    
    # Create language model
    llm = OpenAILLM()
    
    return embedding_model, vector_stores, llm

# ----------- Get Metadata Options -----------
@st.cache_data
def get_metadata_options(_vector_store):
    """
    Get all available metadata options from the vector store
    
    Args:
        _vector_store: The vector store to extract options from (underscore prevents hashing)
        
    Returns:
        dict: Dictionary of metadata options
    """
    options = {
        "disease_type": set(),
        "phase": set(),
        "section": set(),
        "filename": set()
    }
    
    # Extract unique values from document metadata
    for doc in _vector_store.documents:
        for key in options:
            if key in doc.metadata:
                options[key].add(doc.metadata[key])
    
    # Convert to sorted lists with "All" option
    return {k: ["All"] + sorted(list(v)) for k, v in options.items()}

# Initialize components
try:
    embedding_model, vector_stores, llm = initialize_components()
    
    if not vector_stores:
        st.error("No vector stores found. Please add data files and build indices.")
        st.info("Run `python scripts/data_processing.py` and `python scripts/build_indices.py` to prepare data.")
        st.stop()
    
    # ----------- Sidebar Data Source Selection -----------
    st.sidebar.header("Data Source")
    
    # Format source names for display
    def format_source_name(name):
        return name.replace("_", " ").title()
    
    selected_source = st.sidebar.selectbox(
        "Select Data Source",
        list(vector_stores.keys()),
        format_func=format_source_name
    )
    
    # Use selected vector store
    vector_store = vector_stores[selected_source]
    
    # Create summary task
    summary_task = SummaryTask(vector_store, llm)
    
    # ----------- Sidebar Filters -----------
    st.sidebar.header("Filters")
    st.sidebar.markdown("Filter reference documents by metadata")
    
    # Get metadata options for the selected source
    metadata_options = get_metadata_options(vector_store)
    
    # Add filters based on available metadata
    filters = {}
    
    if metadata_options["disease_type"]:
        disease_type = st.sidebar.selectbox(
            "Disease Type",
            metadata_options["disease_type"]
        )
        if disease_type != "All":
            filters["disease_type"] = disease_type
    
    if metadata_options["phase"]:
        trial_phase = st.sidebar.selectbox(
            "Trial Phase",
            metadata_options["phase"]
        )
        if trial_phase != "All":
            filters["phase"] = trial_phase
    
    if metadata_options["section"]:
        document_section = st.sidebar.selectbox(
            "Document Section",
            metadata_options["section"]
        )
        if document_section != "All":
            filters["section"] = document_section
    
    # Advanced filters in expander
    with st.sidebar.expander("Advanced Filters"):
        if metadata_options["filename"]:
            filename = st.selectbox(
                "Source File",
                metadata_options["filename"]
            )
            if filename != "All":
                filters["filename"] = filename
    
    # ----------- User Input -----------
    input_text = st.text_area("Draft Paragraph", height=200)
    
    # ----------- Process Input -----------
    if st.button("Summarize"):
        if input_text.strip():
            with st.spinner("Retrieving similar content and generating summary..."):
                # Process the input with filters
                result = summary_task.process(input_text, k=3, filters=filters if filters else None)
                
                # Display references
                st.markdown("**Retrieved Reference Paragraphs:**")
                for idx, chunk in enumerate(result["references"], 1):
                    with st.expander(f"Reference {idx}", expanded=True):
                        st.markdown(chunk)
                        
                        # Show metadata for this reference
                        if "metadata" in result and len(result["metadata"]) >= idx:
                            st.caption("Metadata:")
                            metadata = result["metadata"][idx-1]
                            for key, value in metadata.items():
                                if key not in ["chunk_id", "source"]:
                                    st.caption(f"**{key}**: {value}")
                
                # Display validation results if there are missing terms
                if not result["validation"]["is_valid"]:
                    st.warning(f"⚠️ The summary may be missing important oncology terms: {', '.join(result['validation']['missing_terms'])}")
                
                # Display summary
                st.subheader("Generated Executive Summary:")
                st.write(result["summary"])
                
                # Add copy button
                st.button("Copy to Clipboard", 
                          on_click=lambda: st.write('<script>navigator.clipboard.writeText(`' + result["summary"] + '`);</script>', unsafe_allow_html=True))
        else:
            st.warning("Please paste a draft paragraph before summarizing.")
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.info("Make sure you have built the FAISS index by running `python scripts/build_indices.py`")
