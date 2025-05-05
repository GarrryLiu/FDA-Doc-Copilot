from .base import PromptTemplate

# Define the summary prompt template
SUMMARY_TEMPLATE = """You are an FDA oncology regulatory writing assistant specializing in executive summaries.

Use the following reference paragraphs from previous FDA oncology submissions to guide your summary:

{context}

Now, summarize the following draft paragraph into an FDA-style executive summary for oncology:

{text}

Your summary should:
1. Maintain precise medical terminology (PFS, OS, AE)
2. Focus on statistical significance and clinical relevance
3. Present data objectively without exaggeration
4. Follow standard FDA regulatory language conventions
5. Be concise and focused on key outcomes
6. Include appropriate qualifiers when discussing efficacy or safety
7. Use consistent terminology for the study drug and comparators

Summary:"""

class SummaryPrompt(PromptTemplate):
    """
    Prompt template for summarization task
    """
    
    def __init__(self):
        """
        Initialize the summary prompt template
        """
        super().__init__(SUMMARY_TEMPLATE)
    
    def format_with_references(self, text, references):
        """
        Format the template with the input text and references
        
        Args:
            text (str): The input text to summarize
            references (list): List of reference texts
            
        Returns:
            str: The formatted prompt
        """
        context = "\n".join(references) if references else ""
        return self.format(context=context, text=text)


def get_summary_prompt(text, references=None):
    """
    Get a formatted summary prompt
    
    Args:
        text (str): The input text to summarize
        references (list, optional): List of reference texts
        
    Returns:
        str: The formatted prompt
    """
    prompt = SummaryPrompt()
    return prompt.format_with_references(text, references)
