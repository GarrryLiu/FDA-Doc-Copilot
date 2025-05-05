from langchain.text_splitter import RecursiveCharacterTextSplitter
from config.settings import VECTOR_STORE_CONFIG
import re

def load_and_chunk_text(file_path):
    """
    Load text from a file and split it into chunks
    
    Args:
        file_path (str): Path to the text file
        
    Returns:
        list: List of text chunks
    """
    # Import here to avoid circular imports
    from src.utils.text_extraction import extract_text_from_file
    
    # Extract text using the appropriate extractor based on file type
    text = extract_text_from_file(file_path)
    
    # Split into chunks
    return chunk_text(text)

def chunk_text(text):
    """
    Split text into chunks
    
    Args:
        text (str): The text to split
        
    Returns:
        list: List of text chunks
    """
    # Get chunk size and overlap from config
    chunk_size = VECTOR_STORE_CONFIG.get("chunk_size", 500)
    chunk_overlap = VECTOR_STORE_CONFIG.get("chunk_overlap", 100)
    
    # Create splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    # Split text
    return splitter.split_text(text)

def standardize_medical_terms(text):
    """
    Standardize medical terminology in the text
    
    Args:
        text (str): Input text
        
    Returns:
        str: Text with standardized terminology
    """
    # Map of common variations to standard terms
    term_mapping = {
        # Progression-Free Survival variations
        "progression free survival": "PFS",
        "progression-free-survival": "PFS",
        "progression-free survival": "PFS",
        
        # Overall Survival variations
        "overall survival": "OS",
        "overall-survival": "OS",
        
        # Adverse Event variations
        "adverse event": "AE",
        "adverse-event": "AE",
        "adverse events": "AEs",
        "adverse-events": "AEs",
        
        # Other oncology-specific terms
        "objective response rate": "ORR",
        "disease free survival": "DFS",
        "disease-free survival": "DFS",
        "complete response": "CR",
        "partial response": "PR",
        "stable disease": "SD",
        "progressive disease": "PD",
    }
    
    # Case-insensitive replacement
    for variation, standard in term_mapping.items():
        pattern = re.compile(re.escape(variation), re.IGNORECASE)
        text = pattern.sub(standard, text)
    
    return text

def validate_oncology_terms(text):
    """
    Validate that the text contains essential oncology terms
    
    Args:
        text (str): The text to validate
        
    Returns:
        tuple: (is_valid, missing_terms)
    """
    essential_terms = ["PFS", "OS", "AE"]
    missing_terms = [term for term in essential_terms if term not in text and term.lower() not in text.lower()]
    
    return len(missing_terms) == 0, missing_terms
