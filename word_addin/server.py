from fastapi import FastAPI, Body, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import sys
import tempfile
import shutil

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import existing components
from src.embeddings.openai import OpenAIEmbedding
from src.vectorstore.faiss_store import FaissStore
from src.llm.openai import OpenAILLM
from src.tasks.summary import SummaryTask
from src.utils.data_discovery import discover_data_sources
from src.utils.text_extraction import extract_text_from_file, clean_extracted_text
from config.logging_config import setup_logging
from config.settings import AUTO_DISCOVER_CONFIG

# Set up logging
logger = setup_logging()

app = FastAPI(title="FDA Oncology Copilot Word Add-in API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
try:
    logger.info("Initializing components for Word add-in backend")
    embedding_model = OpenAIEmbedding()
    discovered_sources = discover_data_sources()
    vector_stores = {}
    
    for source_name, source_data in discovered_sources.items():
        index_path = source_data["config"]["index_path"]
        if os.path.exists(os.path.join(index_path, "index.faiss")):
            try:
                vector_store = FaissStore.load(index_path, embedding_model)
                vector_stores[source_name] = vector_store
                logger.info(f"Loaded vector store for source '{source_name}'")
            except Exception as e:
                logger.error(f"Error loading vector store for source '{source_name}': {str(e)}")
    
    llm = OpenAILLM()
    logger.info("Components initialized successfully")
except Exception as e:
    logger.error(f"Error initializing components: {str(e)}")
    vector_stores = {}

class SummaryRequest(BaseModel):
    text: str
    source: str
    filters: dict = None
    k: int = 3

@app.get("/api/sources")
async def get_sources():
    """Get all available data sources"""
    return [{"id": name, "name": name.replace("_", " ").title()} for name in vector_stores.keys()]

@app.get("/api/metadata")
async def get_metadata(source: str):
    """Get metadata options for the specified data source"""
    if source not in vector_stores:
        raise HTTPException(status_code=404, detail=f"Data source '{source}' not found")
    
    vector_store = vector_stores[source]
    options = {
        "disease_type": set(),
        "phase": set(),
        "section": set(),
        "filename": set()
    }
    
    # Extract unique values from document metadata
    for doc in vector_store.documents:
        for key in options:
            if key in doc.metadata:
                options[key].add(doc.metadata[key])
    
    # Convert to sorted lists
    return {k: sorted(list(v)) for k, v in options.items()}

@app.exception_handler(422)
async def validation_exception_handler(request, exc):
    """
    Handle validation errors and log them
    """
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.post("/api/summarize")
async def summarize(request: SummaryRequest):
    """Generate FDA-style summary"""
    logger.info(f"Received summary request: text length={len(request.text)}, source={request.source}, filters={request.filters}, k={request.k}")
    
    if not vector_stores:
        logger.error("No vector stores found")
        raise HTTPException(status_code=500, detail="No vector stores found. Please ensure indices are built.")
    
    # Use all available data sources regardless of the specified source
    logger.info(f"Using all available data sources instead of just '{request.source}'")
    
    # Ensure filters is None if it's an empty dict
    filters = request.filters if request.filters and len(request.filters) > 0 else None
    logger.info(f"Using filters: {filters}")
    
    try:
        # Collect results from all data sources
        all_references = []
        all_metadata = []
        
        # Get k/2 results from each source to ensure we don't get too many results
        results_per_source = max(1, request.k // len(vector_stores))
        remaining_results = request.k
        
        for source_name, vector_store in vector_stores.items():
            logger.info(f"Processing with source '{source_name}'")
            
            # Determine how many results to get from this source
            k_for_source = min(results_per_source, remaining_results)
            if k_for_source <= 0:
                break
                
            # Create a summary task for this source
            summary_task = SummaryTask(vector_store, llm)
            
            # Get results from this source
            source_result = summary_task.process(request.text, k=k_for_source, filters=filters)
            
            # Add references and metadata to the combined results
            all_references.extend(source_result["references"])
            all_metadata.extend(source_result["metadata"])
            
            # Update remaining results count
            remaining_results -= len(source_result["references"])
        
        # If we have no references, use the first data source as fallback
        if not all_references:
            logger.warning("No references found from any source, using first source as fallback")
            first_source_name = next(iter(vector_stores))
            vector_store = vector_stores[first_source_name]
            summary_task = SummaryTask(vector_store, llm)
            result = summary_task.process(request.text, k=request.k, filters=filters)
            return result
        
        # Generate a summary using all collected references
        # We'll use the first source's summary task for this
        first_source_name = next(iter(vector_stores))
        vector_store = vector_stores[first_source_name]
        summary_task = SummaryTask(vector_store, llm)
        
        # Get the prompt for summarization
        from src.prompts.summary import get_summary_prompt
        prompt = get_summary_prompt(request.text, all_references)
        
        # Generate summary
        summary = llm.generate(prompt)
        
        # Validate summary
        from src.utils.text_processing import validate_oncology_terms
        is_valid, missing_terms = validate_oncology_terms(summary)
        
        # Create combined result
        result = {
            "summary": summary,
            "references": all_references[:request.k],  # Limit to requested k
            "metadata": all_metadata[:request.k],      # Limit to requested k
            "validation": {
                "is_valid": is_valid,
                "missing_terms": missing_terms
            }
        }
        
        logger.info("Summary generated successfully using all data sources")
        return result
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), source: str = Form(...)):
    """
    Upload and process a file in various formats
    
    Args:
        file: The uploaded file
        source: The data source to use for summarization
    
    Returns:
        The extracted text from the file
    """
    if source not in vector_stores:
        raise HTTPException(status_code=404, detail=f"Data source '{source}' not found")
    
    # Get file extension
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    
    # Check if file type is supported
    supported_extensions = AUTO_DISCOVER_CONFIG.get("supported_extensions", [".txt"])
    if ext not in supported_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {ext}. Supported types: {', '.join(supported_extensions)}"
        )
    
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            # Copy uploaded file content to temporary file
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
        
        # Extract text from the file
        extracted_text = extract_text_from_file(temp_file_path)
        
        # Clean the extracted text
        cleaned_text = clean_extracted_text(extracted_text)
        
        # Remove the temporary file
        os.unlink(temp_file_path)
        
        return {"text": cleaned_text, "filename": file.filename}
    
    except Exception as e:
        logger.error(f"Error processing uploaded file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        file.file.close()

@app.get("/api/supported_formats")
async def get_supported_formats():
    """Get all supported file formats"""
    supported_extensions = AUTO_DISCOVER_CONFIG.get("supported_extensions", [".txt"])
    return {
        "formats": supported_extensions,
        "description": "Supported file formats for upload and processing"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "sources_available": len(vector_stores) > 0}

# Mount static files after all API routes are defined
static_dir = os.path.join(os.path.dirname(__file__), "web")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
