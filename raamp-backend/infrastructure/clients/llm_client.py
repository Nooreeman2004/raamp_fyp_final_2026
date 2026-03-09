
# Infrastructure Layer - LLM Client
import logging
import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class LLMClient:
    """Wrapper for OpenAI API calls with retry logic and JSON validation"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_GENERATION_MODEL", "gpt-4o") # Using gpt-4o as default for reasoning
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.error("OPENAI_API_KEY not found in environment")

    async def generate_structured_json(self, system_prompt: str, user_prompt: str, max_retries: int = 2) -> Optional[Dict[str, Any]]:
        """Call LLM and ensure response is valid JSON"""
        if not self.client:
            return None

        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7
                )
                
                content = response.choices[0].message.content
                return json.loads(content)
            except Exception as e:
                logger.error(f"LLM Call Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries:
                    raise e
        return None
