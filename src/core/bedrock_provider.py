"""
AWS Bedrock Provider for Claude and Titan models.
"""

import json
import time
import boto3
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError

from ..utils import get_logger

logger = get_logger(__name__)


class BedrockProvider:
    """AWS Bedrock provider for text generation and embeddings."""
    
    def __init__(
        self,
        model_id: str,
        embedding_model_id: str = "amazon.titan-embed-text-v2:0",
        region: str = "us-east-1",
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        """
        Initialize Bedrock provider.
        
        Args:
            model_id: Claude model ID
            embedding_model_id: Embedding model ID
            region: AWS region
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries (seconds)
        """
        self.model_id = model_id
        self.embedding_model_id = embedding_model_id
        self.region = region
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize Bedrock client
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=region
        )
        
        logger.info(f"Initialized BedrockProvider: {model_id}")
    
    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text using Claude.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        response = self._invoke_with_retry(body)
        return self._extract_text_from_response(response)
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Titan.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        body = json.dumps({"inputText": text})
        
        try:
            response = self.client.invoke_model(
                modelId=self.embedding_model_id,
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            embedding = response_body.get('embedding', [])
            
            if not embedding:
                logger.warning("Empty embedding returned")
                return []
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts
            batch_size: Batch processing size
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            for text in batch:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
                time.sleep(0.1)  # Rate limiting
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    def _invoke_with_retry(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke model with retry logic.
        
        Args:
            body: Request body
            
        Returns:
            API response
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(body)
                )
                
                response_body = json.loads(response['body'].read())
                return response_body
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                last_error = e
                
                if error_code in ['ThrottlingException', 'ServiceUnavailableException']:
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.warning(
                            f"API throttled, retrying in {wait_time}s "
                            f"(attempt {attempt + 1}/{self.max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                
                logger.error(f"API call failed: {error_code}")
                raise
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise
        
        raise last_error
    
    def _extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """Extract text from Bedrock response."""
        try:
            content = response.get('content', [])
            
            if not content:
                logger.warning("No content in response")
                return ""
            
            text_parts = []
            for block in content:
                if block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
            
            return ''.join(text_parts)
            
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def __repr__(self) -> str:
        return f"BedrockProvider(model={self.model_id}, region={self.region})"
