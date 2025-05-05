class Task:
    """
    Base class for tasks
    
    This abstract class defines the interface for tasks.
    All task implementations should inherit from this class.
    """
    
    def __init__(self, vector_store, llm):
        """
        Initialize the task
        
        Args:
            vector_store: The vector store to use for retrieval
            llm: The language model to use for generation
        """
        self.vector_store = vector_store
        self.llm = llm
    
    def process(self, input_text, **kwargs):
        """
        Process the input text and return the result
        
        Args:
            input_text (str): The input text to process
            **kwargs: Additional arguments for the task
            
        Returns:
            dict: The result of the task
        """
        raise NotImplementedError("Subclasses must implement process method")
