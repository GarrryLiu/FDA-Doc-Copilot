import os
from dotenv import load_dotenv

load_dotenv()

# Model configuration
LLM_CONFIG = {
    "model": os.getenv("LLM_MODEL", "gpt-4o"),
    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3")),
}

# Embedding model configuration
EMBEDDING_CONFIG = {
    "model": os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002"),
}

# Vector store configuration
VECTOR_STORE_CONFIG = {
    "type": os.getenv("VECTOR_STORE_TYPE", "faiss"),
    "chunk_size": int(os.getenv("CHUNK_SIZE", "500")),
    "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "100")),
}

# Data sources configuration
DATA_SOURCES = {
    "fda_documents": {
        "path": os.path.join("data", "sources", "fda_documents"),
        "index_path": os.path.join("data", "indices", "fda_documents"),
    },
    # Add more data sources here
}

# Auto-discovery configuration
AUTO_DISCOVER_CONFIG = {
    "enabled": True,
    "source_dir": os.path.join("data", "sources"),
    "supported_extensions": [
        # Text formats
        ".txt", 
        # Office document formats
        ".pdf", ".docx", ".doc", 
        # Spreadsheet formats
        ".csv", ".tsv", ".xlsx", ".xls",
        # Web formats
        ".html", ".htm", ".xml", ".json",
        # Markdown
        ".md", ".markdown"
    ],
    "exclude_patterns": ["temp_*", "draft_*", "*.tmp"],
    "batch_size": int(os.getenv("BATCH_SIZE", "1000")),  # For batch processing
    "parallel_processes": int(os.getenv("PARALLEL_PROCESSES", "4")),  # For parallel processing
}

# Metadata extraction configuration
METADATA_CONFIG = {
    "disease_types": {
        "nsclc": "NSCLC",
        "lung": "NSCLC",
        "breast": "Breast Cancer", 
        "colorectal": "Colorectal Cancer",
        "colon": "Colorectal Cancer",
        "melanoma": "Melanoma",
        "skin": "Melanoma",
    },
    "phases": {
        "phase 1": "Phase 1",
        "phase i": "Phase 1",
        "phase 2": "Phase 2", 
        "phase ii": "Phase 2",
        "phase 3": "Phase 3",
        "phase iii": "Phase 3",
        "phase 4": "Phase 4",
        "phase iv": "Phase 4",
    },
    "sections": {
        "efficacy": "Efficacy",
        "effective": "Efficacy",
        "survival": "Efficacy",
        "response": "Efficacy",
        "safety": "Safety",
        "adverse": "Safety",
        "toxicity": "Safety",
        "pharmacokinetics": "Pharmacokinetics",
        "pk": "Pharmacokinetics",
        "pharmacology": "Clinical Pharmacology",
    }
}
