class EmbeddingModel:
    """
    Base class for embedding models
    
    This abstract class defines the interface for embedding models.
    All embedding model implementations should inherit from this class.
    """
    
    def embed_text(self, text):
        """
        Convert a single text into an embedding vector
        
        Args:
            text (str): The text to embed
            
        Returns:
            list: The embedding vector
        """
        raise NotImplementedError("Subclasses must implement embed_text method")
    
    def embed_batch(self, texts):
        """
        Convert a batch of texts into embedding vectors
        
        Args:
            texts (list): List of texts to embed
            
        Returns:
            list: List of embedding vectors
        """
        # Default implementation calls embed_text for each text
        return [self.embed_text(text) for text in texts]
