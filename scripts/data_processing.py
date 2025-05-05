import os
import sys
import shutil
import glob
import concurrent.futures

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import DATA_SOURCES, AUTO_DISCOVER_CONFIG
from config.logging_config import setup_logging
from src.utils.data_discovery import discover_data_sources, clean_text_file
from src.utils.text_extraction import extract_text_from_file, clean_extracted_text

# Set up logging
logger = setup_logging()

def copy_example_data():
    """
    Copy example data to the data sources directory
    """
    for source_name, source_config in DATA_SOURCES.items():
        if "original_path" in source_config:
            original_path = source_config.get("original_path")
            source_path = source_config.get("path")
            
            # Check if the original file exists
            if not os.path.exists(original_path):
                logger.error(f"Original file '{original_path}' not found")
                continue
            
            # Create the source directory if it doesn't exist
            os.makedirs(source_path, exist_ok=True)
            
            # Copy the file
            destination_path = os.path.join(source_path, os.path.basename(original_path))
            shutil.copy2(original_path, destination_path)
            logger.info(f"Copied {original_path} to {destination_path}")

def process_data_source(source_name, files):
    """
    Process files for a data source
    
    Args:
        source_name (str): Name of the data source
        files (list): List of file paths
    """
    logger.info(f"Processing {len(files)} files for source '{source_name}'")
    
    # Process files in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_file = {
            executor.submit(process_file, file_path): file_path 
            for file_path in files
        }
        
        for future in concurrent.futures.as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                future.result()
                logger.info(f"Processed {file_path}")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")

def process_file(file_path):
    """
    Process a single file
    
    Args:
        file_path (str): Path to the file
    """
    # Determine file type
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    # Get supported extensions from config
    supported_extensions = AUTO_DISCOVER_CONFIG.get("supported_extensions", [".txt"])
    
    if ext not in supported_extensions:
        logger.warning(f"Unsupported file type: {file_path}")
        return
    
    if ext == '.txt':
        # For text files, use the existing clean_text_file function
        clean_text_file(file_path)
    else:
        # For other file types, extract text and save as .txt
        try:
            # Extract text from the file
            extracted_text = extract_text_from_file(file_path)
            
            # Clean the extracted text
            cleaned_text = clean_extracted_text(extracted_text)
            
            # Save as a text file with the same base name
            base_name = os.path.splitext(file_path)[0]
            txt_file_path = f"{base_name}.txt"
            
            with open(txt_file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            
            logger.info(f"Extracted and saved text from {file_path} to {txt_file_path}")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")

def process_all_data():
    """
    Process all discovered data sources
    """
    # First, copy example data
    copy_example_data()
    
    # Discover all data sources
    discovered_sources = discover_data_sources()
    
    if not discovered_sources:
        logger.warning("No data sources discovered")
        return
    
    logger.info(f"Processing {len(discovered_sources)} discovered sources")
    
    # Process each data source
    for source_name, source_data in discovered_sources.items():
        process_data_source(
            source_name=source_name,
            files=source_data["files"]
        )

if __name__ == "__main__":
    process_all_data()
