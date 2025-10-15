import aiohttp
import logging
import asyncio
from typing import Optional
from .models import EvaluationResponse

logger = logging.getLogger(__name__)

class EvaluationClient:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def submit_evaluation(self, eval_data: EvaluationResponse, evaluation_url: str) -> bool:
        """Submit evaluation data to evaluation service with retry logic"""
        max_retries = 5
        base_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                session = await self.get_session()
                
                async with session.post(
                    evaluation_url,
                    json=eval_data.dict(),
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    
                    if response.status == 200:
                        logger.info(f"Successfully submitted evaluation for {eval_data.task}")
                        return True
                    else:
                        logger.warning(f"Evaluation submission failed with status {response.status}")
                        
            except Exception as e:
                logger.warning(f"Evaluation submission attempt {attempt + 1} failed: {str(e)}")
            
            # Exponential backoff
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
        
        logger.error(f"Failed to submit evaluation after {max_retries} attempts")
        return False
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()