"""
AWS Bedrock Client Module

Provides a client interface for interacting with AWS Bedrock runtime
to generate responses using Claude models.
"""

import json
import os
from typing import Optional, Dict, Any
import boto3
from botocore.config import Config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BedrockClient:
    """
    AWS Bedrock client for generating LLM responses.
    
    This client initializes a boto3 Bedrock runtime client and provides
    methods to generate text responses using Claude models.
    """
    
    def __init__(
        self,
        model_id: Optional[str] = None,
        region: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        """
        Initialize the Bedrock client.
        
        Args:
            model_id: Bedrock model ID (default: from env or claude-3-sonnet)
            region: AWS region (default: from env or us-east-1)
            aws_access_key_id: AWS access key (default: from env)
            aws_secret_access_key: AWS secret key (default: from env)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature for response generation
        """
        self.model_id = model_id or os.getenv(
            "BEDROCK_MODEL_ID",
            "anthropic.claude-3-sonnet-20240229-v1:0"  # Default to Claude 3 Sonnet (on-demand compatible)
        )
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize boto3 client
        config = Config(
            region_name=self.region,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        session_kwargs = {}
        if aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"):
            session_kwargs['aws_access_key_id'] = (
                aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
            )
        if aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"):
            session_kwargs['aws_secret_access_key'] = (
                aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
            )
        
        session = boto3.Session(**session_kwargs)
        self.client = session.client(
            service_name='bedrock-runtime',
            config=config
        )
    
    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate a response from the Bedrock model.
        
        Args:
            prompt: The user prompt/question
            system_prompt: Optional system prompt for context
            max_tokens: Override default max tokens
            temperature: Override default temperature
        
        Returns:
            str: Generated response text
        
        Raises:
            Exception: If API call fails
        """
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        
        # Prepare request body for Claude 3
        messages = [{"role": "user", "content": prompt}]
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        if system_prompt:
            request_body["system"] = system_prompt
        
        try:
            # Invoke the model
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract text from Claude 3 response format
            if 'content' in response_body:
                return response_body['content'][0]['text']
            else:
                raise ValueError(f"Unexpected response format: {response_body}")
                
        except Exception as e:
            raise Exception(f"Bedrock API call failed: {str(e)}")
    
    def generate_structured_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        expected_format: Optional[str] = None
    ) -> str:
        """
        Generate a structured response with format guidance.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            expected_format: Description of expected output format
        
        Returns:
            str: Generated structured response
        """
        if expected_format:
            enhanced_prompt = f"{prompt}\n\nPlease format your response as follows:\n{expected_format}"
        else:
            enhanced_prompt = prompt
        
        return self.generate_response(enhanced_prompt, system_prompt)


# Global client instance (initialized lazily)
_bedrock_client: Optional[BedrockClient] = None


def get_bedrock_client() -> BedrockClient:
    """
    Get or create a global Bedrock client instance.
    
    Returns:
        BedrockClient: Singleton Bedrock client
    """
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client


def generate_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7
) -> str:
    """
    Convenience function to generate a response using the global client.
    
    Args:
        prompt: The user prompt
        system_prompt: Optional system prompt
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
    
    Returns:
        str: Generated response text
    """
    client = get_bedrock_client()
    return client.generate_response(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature
    )

