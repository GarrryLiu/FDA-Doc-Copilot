"""
Data discovery utilities for automatically finding and processing data sources
"""

import os
import glob
import fnmatch
import re
import sys

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from config.settings import DATA_SOURCES, AUTO_DISCOVER_CONFIG, METADATA_CONFIG
from config.logging_config import setup_logging

logger = setup_logging()

def discover_data_sources():
    """
    Automatically discover all data sources in the data directory
    
    Returns:
        dict: Discovered data sources mapping {source_name: {files: [file_paths], config: {...}}}
    """
    discovered_sources = {}
    
    # 1. Process configured data sources
    for source_name, config in DATA_SOURCES.items():
        source_path = config.get("path")
        if not os.path.exists(source_path):
            logger.warning(f"Configured source path does not exist: {source_path}")
            continue
        
        # Get all supported files in this directory
        files = []
        for ext in AUTO_DISCOVER_CONFIG.get("supported_extensions", [".txt"]):
            pattern = f"*{ext}"
            files.extend(glob.glob(os.path.join(source_path, pattern)))
        
        # Apply exclusion patterns
        exclude_patterns = AUTO_DISCOVER_CONFIG.get("exclude_patterns", [])
        for exclude in exclude_patterns:
            files = [f for f in files if not fnmatch.fnmatch(os.path.basename(f), exclude)]
        
        if files:
            discovered_sources[source_name] = {
                "files": files,
                "config": config
            }
            logger.info(f"Discovered {len(files)} files for source '{source_name}'")
        else:
            logger.warning(f"No files found for source '{source_name}'")
    
    # 2. Auto-discover additional sources if enabled
    if AUTO_DISCOVER_CONFIG.get("enabled", False):
        source_dir = AUTO_DISCOVER_CONFIG.get("source_dir", os.path.join("data", "sources"))
        
        if os.path.exists(source_dir):
            # Get all subdirectories (each subdirectory as a data source)
            for subdir in [d for d in os.listdir(source_dir) 
                          if os.path.isdir(os.path.join(source_dir, d))
                          and d not in DATA_SOURCES]:  # Exclude already configured sources
                
                subdir_path = os.path.join(source_dir, subdir)
                
                # Get all supported files in this subdirectory
                files = []
                for ext in AUTO_DISCOVER_CONFIG.get("supported_extensions", [".txt"]):
                    pattern = f"*{ext}"
                    files.extend(glob.glob(os.path.join(subdir_path, pattern)))
                
                # Apply exclusion patterns
                exclude_patterns = AUTO_DISCOVER_CONFIG.get("exclude_patterns", [])
                for exclude in exclude_patterns:
                    files = [f for f in files if not fnmatch.fnmatch(os.path.basename(f), exclude)]
                
                if files:
                    # Create configuration for auto-discovered source
                    auto_config = {
                        "path": subdir_path,
                        "index_path": os.path.join("data", "indices", subdir),
                    }
                    
                    discovered_sources[subdir] = {
                        "files": files,
                        "config": auto_config
                    }
                    logger.info(f"Auto-discovered source '{subdir}' with {len(files)} files")
    
    return discovered_sources

def get_file_metadata(file_path):
    """
    Extract metadata from file name and path
    
    Args:
        file_path (str): File path
        
    Returns:
        dict: Extracted metadata
    """
    filename = os.path.basename(file_path)
    parent_dir = os.path.basename(os.path.dirname(file_path))
    
    metadata = {
        "filename": filename,
        "source_dir": parent_dir,
    }
    
    # Extract more metadata from filename (adjust based on your naming convention)
    name_parts = os.path.splitext(filename)[0].split('_')
    
    # Example: extract disease type, phase, etc. from filename
    # e.g., nsclc_phase3_efficacy_001.txt
    if len(name_parts) >= 3:
        disease_types = METADATA_CONFIG.get("disease_types", {})
        
        # Try to extract disease type from first part
        if name_parts[0].lower() in disease_types:
            metadata["disease_type"] = disease_types[name_parts[0].lower()]
        
        # Try to extract trial phase from second part
        if "phase" in name_parts[1].lower():
            phase_key = name_parts[1].lower()
            phases = METADATA_CONFIG.get("phases", {})
            for key, value in phases.items():
                if key in phase_key:
                    metadata["phase"] = value
                    break
        
        # Try to extract document section from third part
        section_key = name_parts[2].lower()
        sections = METADATA_CONFIG.get("sections", {})
        for key, value in sections.items():
            if key in section_key:
                metadata["section"] = value
                break
    
    return metadata

def extract_content_metadata(chunk):
    """
    Extract metadata from chunk content
    
    Args:
        chunk (str): Text chunk
        
    Returns:
        dict: Extracted metadata
    """
    metadata = {}
    chunk_lower = chunk.lower()
    
    # Extract disease type based on content keywords
    disease_types = METADATA_CONFIG.get("disease_types", {})
    for key, value in disease_types.items():
        if key in chunk_lower:
            metadata["disease_type"] = value
            break
    
    if "disease_type" not in metadata:
        metadata["disease_type"] = "Other"
    
    # Extract phase based on content keywords
    phases = METADATA_CONFIG.get("phases", {})
    phase_found = False
    for key, value in phases.items():
        if key in chunk_lower:
            metadata["phase"] = value
            phase_found = True
            break
    
    if not phase_found:
        # Default to Phase 3 if not specified
        metadata["phase"] = "Phase 3"
    
    # Extract section based on content keywords
    sections = METADATA_CONFIG.get("sections", {})
    section_found = False
    for key, value in sections.items():
        if key in chunk_lower:
            metadata["section"] = value
            section_found = True
            break
    
    if not section_found:
        metadata["section"] = "Efficacy"  # Default
    
    return metadata

def clean_text_file(file_path):
    """
    Clean a text file (example preprocessing)
    
    Args:
        file_path (str): File path
    """
    # Only process text files
    if not file_path.endswith('.txt'):
        return
    
    try:
        # Import here to avoid circular imports
        from src.utils.text_extraction import clean_extracted_text
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Use the more comprehensive cleaning function
        cleaned_content = clean_extracted_text(content)
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
    except Exception as e:
        logger.error(f"Error cleaning file {file_path}: {str(e)}")
        raise
