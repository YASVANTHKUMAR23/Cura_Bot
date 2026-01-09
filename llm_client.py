import logging
import requests
from typing import Optional

from config import OLLAMA_MODEL, OLLAMA_BASE_URL

logger = logging.getLogger(__name__)


class OllamaLLM:
    """
    Ollama LLM client
    """
    
    def __init__(self, model: str = OLLAMA_MODEL, base_url: str = OLLAMA_BASE_URL):
        self.model = model
        self.base_url = base_url
        
        logger.info(f'Initialized Ollama LLM: {model}')
    
    def generate(self, prompt: str, temperature: float = 0.7, 
                max_tokens: int = 500) -> str:
        """
        Generate response from LLM
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
        
        Returns:
            Generated text
        """
        
        try:
            response = requests.post(
                f'{self.base_url}/api/generate',
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'temperature': temperature,
                    'max_tokens': max_tokens,
                    'stream': False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                logger.error(f'Ollama API error: {response.status_code}')
                return 'I am having trouble generating a response.'
        
        except Exception as e:
            logger.error(f'LLM generation error: {e}')
            return 'I am having trouble right now. Please try again.'


# Singleton instance
llm = OllamaLLM()
