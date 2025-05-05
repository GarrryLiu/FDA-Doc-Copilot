import os
import sys
import shutil
import concurrent.futures
import numpy as np

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.embeddings.openai import OpenAIEmbedding
from src.vectorstore.faiss_store import FaissStore
from src.utils.text_processing import load_and_chunk_text
from src.utils.data_discovery import discover_data_sources, get_file_metadata, extract_content_metadata
from config.settings import DATA_SOURCES
from config.logging_config import setup_logging

# Set up logging
logger = setup_logging()

def process_file(file_path, source_name):
    """
    Process a single file and return its chunks and metadata
    
    Args:
        file_path (str): Path to the file
        source_name (str): Name of the data source
        
    Returns:
        tuple: (chunks, metadatas)
    """
    try:
        # Load and chunk the text
        chunks = load_and_chunk_text(file_path)
        
        # Get file metadata
        file_metadata = get_file_metadata(file_path)
        
        # Create metadata for each chunk
        metadatas = []
        for i, chunk in enumerate(chunks):
            # Start with file metadata
            metadata = file_metadata.copy()
            
            # Add chunk-specific metadata
            metadata.update({
                "source": source_name,
                "chunk_id": i,
            })
            
            # Extract content-based metadata if not already present
            content_metadata = extract_content_metadata(chunk)
            for key, value in content_metadata.items():
                if key not in metadata:
                    metadata[key] = value
            
            metadatas.append(metadata)
        
        return chunks, metadatas
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return [], []

def build_index_for_files(source_name, files, index_path):
    """
    Build a FAISS index for a set of files
    
    Args:
        source_name (str): Name of the data source
        files (list): List of file paths
        index_path (str): Path to save the index
    """
    logger.info(f"Building index for '{source_name}' with {len(files)} files")
    
    all_chunks = []
    all_metadatas = []
    
    # Process files in parallel
    with concurrent.futures.ProcessPoolExecutor() as executor:
        future_to_file = {
            executor.submit(process_file, file_path, source_name): file_path 
            for file_path in files
        }
        
        for future in concurrent.futures.as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                chunks, metadatas = future.result()
                all_chunks.extend(chunks)
                all_metadatas.extend(metadatas)
                logger.info(f"Processed {file_path}: {len(chunks)} chunks")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
    
    if not all_chunks:
        logger.warning(f"No chunks extracted from files for source '{source_name}'")
        return
    
    # Create embedding model
    embedding_model = OpenAIEmbedding()
    
    # Process in batches to avoid memory issues
    batch_size = 1000  # Adjust based on available memory
    faiss_store = None
    
    for i in range(0, len(all_chunks), batch_size):
        batch_chunks = all_chunks[i:i+batch_size]
        batch_metadatas = all_metadatas[i:i+batch_size]
        
        if faiss_store is None:
            # Create new store
            faiss_store = FaissStore.from_texts(batch_chunks, embedding_model, metadatas=batch_metadatas)
        else:
            # Add to existing store
            faiss_store.add_texts(batch_chunks, metadatas=batch_metadatas)
        
        logger.info(f"Indexed batch {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}")
    
    # Save the index
    os.makedirs(index_path, exist_ok=True)
    faiss_store.save(index_path)
    
    # Save processed files list for incremental updates
    with open(os.path.join(index_path, "processed_files.txt"), "w") as f:
        for file_path in files:
            f.write(f"{file_path}\n")
    
    logger.info(f"Index saved to {index_path} with {len(all_chunks)} total chunks")

def update_index_with_files(source_name, files, index_path):
    """
    Update an existing FAISS index with new files
    
    Args:
        source_name (str): Name of the data source
        files (list): List of new file paths
        index_path (str): Path to the existing index
    """
    logger.info(f"Updating index for '{source_name}' with {len(files)} new files")
    
    # Load existing index
    embedding_model = OpenAIEmbedding()
    faiss_store = FaissStore.load(index_path, embedding_model)
    
    # Process each new file
    for file_path in files:
        try:
            chunks, metadatas = process_file(file_path, source_name)
            
            if chunks:
                # Add to index
                faiss_store.add_texts(chunks, metadatas)
                logger.info(f"Added {file_path} to index: {len(chunks)} chunks")
            else:
                logger.warning(f"No chunks extracted from {file_path}")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
    
    # Save updated index
    faiss_store.save(index_path)
    
    # Update processed files list
    processed_files = set()
    if os.path.exists(os.path.join(index_path, "processed_files.txt")):
        with open(os.path.join(index_path, "processed_files.txt"), "r") as f:
            processed_files = set(line.strip() for line in f)
    
    processed_files.update(files)
    
    with open(os.path.join(index_path, "processed_files.txt"), "w") as f:
        for file_path in processed_files:
            f.write(f"{file_path}\n")
    
    logger.info(f"Updated index at {index_path}")

def build_index(source_name):
    """
    Build a FAISS index for a data source
    
    Args:
        source_name (str): Name of the data source in DATA_SOURCES
    """
    # Discover data sources
    discovered_sources = discover_data_sources()
    
    # Check if the source exists
    if source_name not in discovered_sources:
        logger.error(f"Data source '{source_name}' not found")
        return
    
    # Get source data
    source_data = discovered_sources[source_name]
    files = source_data["files"]
    index_path = source_data["config"]["index_path"]
    
    # Build index
    build_index_for_files(source_name, files, index_path)

def build_all_indices():
    """
    Build indices for all discovered data sources
    """
    # Discover data sources
    discovered_sources = discover_data_sources()
    
    if not discovered_sources:
        logger.warning("No data sources discovered")
        return
    
    logger.info(f"Building indices for {len(discovered_sources)} discovered sources")
    
    # Build index for each source
    for source_name, source_data in discovered_sources.items():
        build_index_for_files(
            source_name=source_name,
            files=source_data["files"],
            index_path=source_data["config"]["index_path"]
        )

if __name__ == "__main__":
    # Check if a specific source was specified
    if len(sys.argv) > 1:
        source_name = sys.argv[1]
        build_index(source_name)
    else:
        # Build all indices
        build_all_indices()
