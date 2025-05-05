import os
import sys
import subprocess
import logging

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.utils.data_discovery import discover_data_sources
from config.logging_config import setup_logging

# Set up logging
logger = setup_logging()

def check_and_prepare_data():
    """
    Check data sources and indices, prepare data if necessary
    """
    # Discover data sources
    discovered_sources = discover_data_sources()
    
    if not discovered_sources:
        logger.warning("No data sources discovered. Please add data files to the data/sources directory.")
        return
    
    # Check each data source's index
    indices_to_build = []
    
    for source_name, source_data in discovered_sources.items():
        index_path = source_data["config"]["index_path"]
        index_file = os.path.join(index_path, "index.faiss")
        
        # Check if index exists
        if not os.path.exists(index_file):
            logger.info(f"Index not found for source '{source_name}'. Will build index.")
            indices_to_build.append(source_name)
        else:
            # Check for new files that need to be indexed
            processed_files_path = os.path.join(index_path, "processed_files.txt")
            if os.path.exists(processed_files_path):
                with open(processed_files_path, "r") as f:
                    processed_files = set(line.strip() for line in f)
                
                current_files = set(source_data["files"])
                new_files = current_files - processed_files
                
                if new_files:
                    logger.info(f"Found {len(new_files)} new files for source '{source_name}'. Will update index.")
                    indices_to_build.append(source_name)
   
    # Build or update indices if needed
    if indices_to_build:
        logger.info(f"Building/updating indices for {len(indices_to_build)} sources...")
        
        # Process data first
        subprocess.run([sys.executable, "scripts/data_processing.py"])
        
        # Build indices
        for source_name in indices_to_build:
            subprocess.run([sys.executable, "scripts/build_indices.py", source_name])

def run_app():
    """
    Run the Streamlit application
    """
    logger.info("Starting FDA Oncology Copilot...")
    
    # Check and prepare data
    check_and_prepare_data()
    
    # Run the Streamlit app
    subprocess.run(["streamlit", "run", "ui/app.py"])

if __name__ == "__main__":
    run_app()
