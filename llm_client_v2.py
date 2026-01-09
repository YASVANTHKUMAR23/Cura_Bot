import logging
import requests
from typing import Optional
import os

logger = logging.getLogger(__name__)

class LLMClientV2:
    def __init__(self):
        """Initialize Ollama LLM client"""
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        logger.info(f"✅ LLM Client V2 initialized: {self.model} at {self.base_url}")
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        """Generate response from LLM"""
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
                return 'Unable to process. Please try again.'
                
        except Exception as e:
            logger.error(f'LLM generation error: {e}')
            return 'I am having trouble right now. Please try again.'

# Global instance for Agent 2/3/4
llm_client = LLMClientV2()
