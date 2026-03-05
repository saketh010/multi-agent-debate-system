"""Utils package for debate system."""

from utils.bedrock_client import (
    BedrockClient,
    get_bedrock_client,
    generate_response
)

__all__ = [
    'BedrockClient',
    'get_bedrock_client',
    'generate_response'
]
