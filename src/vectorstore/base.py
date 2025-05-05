class VectorStore:
    """
    Base class for vector stores
    
    This abstract class defines the interface for vector stores.
    All vector store implementations should inherit from this class.
    """
    
    def add_texts(self, texts, metadatas=None):
        """
        Add texts to the vector store
        
        Args:
            texts (list): List of texts to add
            metadatas (list, optional): List of metadata dictionaries for each text
            
        Returns:
            list: List of IDs for the added texts
        """
        raise NotImplementedError("Subclasses must implement add_texts method")
    
    def similarity_search(self, query, k=3):
        """
        Search for similar documents
        
        Args:
            query (str): The query text
            k (int, optional): Number of results to return. Defaults to 3.
            
        Returns:
            list: List of documents with their content and metadata
        """
        raise NotImplementedError("Subclasses must implement similarity_search method")
    
    def save(self, path):
        """
        Save the vector store to disk
        
        Args:
            path (str): Path to save the vector store
        """
        raise NotImplementedError("Subclasses must implement save method")
    
    @classmethod
    def load(cls, path, embedding_model):
        """
        Load a vector store from disk
        
        Args:
            path (str): Path to load the vector store from
            embedding_model: The embedding model to use
            
        Returns:
            VectorStore: The loaded vector store
        """
        raise NotImplementedError("Subclasses must implement load method")
