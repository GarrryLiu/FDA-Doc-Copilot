class LLM:
    """
    Base class for language models
    
    This abstract class defines the interface for language models.
    All language model implementations should inherit from this class.
    """
    
    def generate(self, prompt):
        """
        Generate text based on a prompt
        
        Args:
            prompt (str): The prompt text
            
        Returns:
            str: The generated text
        """
        raise NotImplementedError("Subclasses must implement generate method")
    
    def generate_batch(self, prompts):
        """
        Generate text for multiple prompts
        
        Args:
            prompts (list): List of prompt texts
            
        Returns:
            list: List of generated texts
        """
        # Default implementation calls generate for each prompt
        return [self.generate(prompt) for prompt in prompts]
