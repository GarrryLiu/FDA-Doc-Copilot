from .base import Task
from src.prompts.summary import get_summary_prompt
from src.utils.text_processing import standardize_medical_terms, validate_oncology_terms

class SummaryTask(Task):
    """
    Task for summarizing text in FDA oncology style
    """
    
    def process(self, input_text, k=3, filters=None):
        """
        Process the input text and return a summary
        
        Args:
            input_text (str): The input text to summarize
            k (int, optional): Number of reference documents to retrieve. Defaults to 3.
            filters (dict, optional): Metadata filters (e.g., {"disease_type": "NSCLC"})
            
        Returns:
            dict: The result containing the summary, references, and validation info
        """
        # Preprocess input text
        processed_text = standardize_medical_terms(input_text)
        
        # Retrieve similar documents with filtering if available
        if hasattr(self.vector_store, 'filtered_similarity_search') and filters:
            retrieved_docs = self.vector_store.filtered_similarity_search(processed_text, k=k, filters=filters)
        else:
            retrieved_docs = self.vector_store.similarity_search(processed_text, k=k)
        
        retrieved_texts = [doc.page_content for doc in retrieved_docs]
        retrieved_metadata = [doc.metadata for doc in retrieved_docs]
        
        # Generate prompt
        prompt = get_summary_prompt(processed_text, retrieved_texts)
        
        # Generate summary
        summary = self.llm.generate(prompt)
        
        # Validate summary
        is_valid, missing_terms = validate_oncology_terms(summary)
        
        # Return result
        return {
            "summary": summary,
            "references": retrieved_texts,
            "metadata": retrieved_metadata,
            "validation": {
                "is_valid": is_valid,
                "missing_terms": missing_terms
            }
        }
