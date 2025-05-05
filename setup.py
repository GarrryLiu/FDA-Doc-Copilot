import os
import sys
import logging

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config.logging_config import setup_logging
from scripts.data_processing import process_all_data
from scripts.build_indices import build_all_indices
from src.utils.data_discovery import discover_data_sources

# Set up logging
logger = setup_logging()

def setup():
    """
    Set up the FDA Oncology Copilot
    """
    logger.info("Setting up FDA Oncology Copilot...")
    
    # Create necessary directories
    os.makedirs(os.path.join("data", "sources"), exist_ok=True)
    os.makedirs(os.path.join("data", "indices"), exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Process all data
    logger.info("Processing data...")
    process_all_data()
    
    # Discover data sources
    logger.info("Discovering data sources...")
    discovered_sources = discover_data_sources()
    
    if not discovered_sources:
        logger.warning("No data sources discovered. Please add data files to the data/sources directory.")
        return
    
    logger.info(f"Discovered {len(discovered_sources)} data sources")
    
    # Build all indices
    logger.info("Building indices...")
    build_all_indices()
    
    logger.info("Setup complete. All data has been processed and indices have been built.")
    print("Setup complete. All data has been processed and indices have been built.")

if __name__ == "__main__":
    setup()
