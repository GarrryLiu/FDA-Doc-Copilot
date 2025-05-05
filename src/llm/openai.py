from openai import OpenAI
import os
from .base import LLM
from config.settings import LLM_CONFIG

class OpenAILLM(LLM):
    """
    OpenAI language model implementation
    
    This class implements the LLM interface using OpenAI's API.
    """
    
    def __init__(self, model=None, temperature=None, api_key=None):
        """
        Initialize the OpenAI language model
        
        Args:
            model (str, optional): The model name to use. Defaults to the one in LLM_CONFIG.
            temperature (float, optional): The temperature to use. Defaults to the one in LLM_CONFIG.
            api_key (str, optional): The OpenAI API key. Defaults to the OPENAI_API_KEY environment variable.
        """
        self.model = model or LLM_CONFIG.get("model", "gpt-4o")
        self.temperature = temperature if temperature is not None else LLM_CONFIG.get("temperature", 0.3)
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    def generate(self, prompt):
        """
        Generate text based on a prompt using OpenAI's API
        
        Args:
            prompt (str): The prompt text
            
        Returns:
            str: The generated text
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature
        )
        return response.choices[0].message.content.strip()
