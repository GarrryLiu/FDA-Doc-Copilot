from openai import OpenAI
import os
from .base import EmbeddingModel
from config.settings import EMBEDDING_CONFIG

class OpenAIEmbedding(EmbeddingModel):
    """
    OpenAI embedding model implementation
    
    This class implements the EmbeddingModel interface using OpenAI's embedding API.
    """
    
    def __init__(self, model=None, api_key=None):
        """
        Initialize the OpenAI embedding model
        
        Args:
            model (str, optional): The model name to use. Defaults to the one in EMBEDDING_CONFIG.
            api_key (str, optional): The OpenAI API key. Defaults to the OPENAI_API_KEY environment variable.
        """
        self.model = model or EMBEDDING_CONFIG.get("model", "text-embedding-ada-002")
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    def embed_text(self, text):
        """
        Convert a single text into an embedding vector using OpenAI's API
        
        Args:
            text (str): The text to embed
            
        Returns:
            list: The embedding vector
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    def embed_batch(self, texts):
        """
        Convert a batch of texts into embedding vectors using OpenAI's API
        
        Args:
            texts (list): List of texts to embed
            
        Returns:
            list: List of embedding vectors
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]
