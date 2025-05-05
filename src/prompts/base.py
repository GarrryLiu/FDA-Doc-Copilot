class PromptTemplate:
    """
    Base class for prompt templates
    
    This class provides a template for creating prompts.
    """
    
    def __init__(self, template):
        """
        Initialize the prompt template
        
        Args:
            template (str): The template string with placeholders
        """
        self.template = template
    
    def format(self, **kwargs):
        """
        Format the template with the provided values
        
        Args:
            **kwargs: The values to fill in the template
            
        Returns:
            str: The formatted prompt
        """
        return self.template.format(**kwargs)
