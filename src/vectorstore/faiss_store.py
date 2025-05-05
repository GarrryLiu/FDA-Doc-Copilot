import os
import pickle
import faiss
import numpy as np
from langchain.docstore.document import Document
from .base import VectorStore
from config.settings import VECTOR_STORE_CONFIG

class FaissStore(VectorStore):
    """
    FAISS vector store implementation
    
    This class implements the VectorStore interface using FAISS.
    """
    
    def __init__(self, embedding_model, index=None, documents=None):
        """
        Initialize the FAISS vector store
        
        Args:
            embedding_model: The embedding model to use
            index: The FAISS index (optional)
            documents: List of documents (optional)
        """
        self.embedding_model = embedding_model
        self.index = index or None
        self.documents = documents or []
    
    def add_texts(self, texts, metadatas=None):
        """
        Add texts to the vector store
        
        Args:
            texts (list): List of texts to add
            metadatas (list, optional): List of metadata dictionaries for each text
            
        Returns:
            list: List of IDs for the added texts
        """
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        # Create documents
        documents = [
            Document(page_content=text, metadata=metadata)
            for text, metadata in zip(texts, metadatas)
        ]
        
        # Get embeddings
        embeddings = self.embedding_model.embed_batch(texts)
        
        # Initialize index if it doesn't exist
        if self.index is None:
            dimension = len(embeddings[0])
            self.index = faiss.IndexFlatL2(dimension)
        
        # Add to index
        embeddings_np = np.array(embeddings, dtype=np.float32)
        start_id = len(self.documents)
        self.index.add(embeddings_np)
        
        # Store documents
        self.documents.extend(documents)
        
        # Return IDs
        return list(range(start_id, start_id + len(texts)))
    
    def similarity_search(self, query, k=3):
        """
        Search for similar documents
        
        Args:
            query (str): The query text
            k (int, optional): Number of results to return. Defaults to 3.
            
        Returns:
            list: List of documents with their content and metadata
        """
        # Get query embedding
        query_embedding = self.embedding_model.embed_text(query)
        query_embedding_np = np.array([query_embedding], dtype=np.float32)
        
        # Search
        distances, indices = self.index.search(query_embedding_np, k)
        
        # Return documents
        return [self.documents[i] for i in indices[0]]
    
    def filtered_similarity_search(self, query, k=3, filters=None):
        """
        Search for similar documents with metadata filtering
        
        Args:
            query (str): The query text
            k (int, optional): Number of results to return. Defaults to 3.
            filters (dict, optional): Metadata filters (e.g., {"disease_type": "NSCLC"})
            
        Returns:
            list: List of documents with their content and metadata
        """
        # If no filters, use regular similarity search
        if not filters:
            return self.similarity_search(query, k)
        
        # Get query embedding
        query_embedding = self.embedding_model.embed_text(query)
        query_embedding_np = np.array([query_embedding], dtype=np.float32)
        
        # Search for more results than needed to allow for filtering
        search_k = min(k * 3, len(self.documents))  # Get more results to filter from
        distances, indices = self.index.search(query_embedding_np, search_k)
        
        # Get all candidate documents
        candidate_docs = [self.documents[i] for i in indices[0]]
        
        # Filter results by metadata
        filtered_results = []
        for doc in candidate_docs:
            if all(doc.metadata.get(key) == value for key, value in filters.items()):
                filtered_results.append(doc)
                if len(filtered_results) >= k:
                    break
        
        # If not enough results after filtering, return what we have
        if not filtered_results:
            return candidate_docs[:k]  # Return top k unfiltered results if no matches
        
        return filtered_results[:k]
    
    def save(self, path):
        """
        Save the vector store to disk
        
        Args:
            path (str): Path to save the vector store
        """
        # Create directory if it doesn't exist
        os.makedirs(path, exist_ok=True)
        
        # Save index
        faiss.write_index(self.index, os.path.join(path, "index.faiss"))
        
        # Save documents
        with open(os.path.join(path, "documents.pkl"), "wb") as f:
            pickle.dump(self.documents, f)
    
    @classmethod
    def load(cls, path, embedding_model):
        """
        Load a vector store from disk
        
        Args:
            path (str): Path to load the vector store from
            embedding_model: The embedding model to use
            
        Returns:
            FaissStore: The loaded vector store
        """
        # Load index
        index = faiss.read_index(os.path.join(path, "index.faiss"))
        
        # Load documents
        with open(os.path.join(path, "documents.pkl"), "rb") as f:
            documents = pickle.load(f)
        
        # Create and return store
        return cls(embedding_model, index, documents)
    
    @classmethod
    def from_texts(cls, texts, embedding_model, metadatas=None):
        """
        Create a vector store from texts
        
        Args:
            texts (list): List of texts
            embedding_model: The embedding model to use
            metadatas (list, optional): List of metadata dictionaries for each text
            
        Returns:
            FaissStore: The created vector store
        """
        store = cls(embedding_model)
        store.add_texts(texts, metadatas)
        return store
