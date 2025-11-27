"""
Dallama LLM Client Module

Handles communication with the Dallama LLM chat server.
"""

import requests
import uuid
import logging
from typing import Optional, Tuple

# Set up logger
logger = logging.getLogger(__name__)


class LLMAPIError(Exception):
    """Custom exception for LLM API errors."""
    pass


class DallamaLLM:
    def __init__(self, base_url="http://localhost:3000", timeout=30):
        """
        Initialize Dallama LLM client.
        
        Args:
            base_url: Base URL of the LLM chat server (default: http://localhost:3000)
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        logger.info(f"Initialized DallamaLLM client with base_url={self.base_url}, timeout={self.timeout}")
    
    def check_health(self) -> bool:
        """
        Check if the LLM server is ready to accept requests.
        
        Returns:
            True if server is ready, False otherwise
        """
        health_url = f"{self.base_url}/"
        logger.debug(f"Checking health at URL: {health_url}")
        
        try:
            response = requests.get(
                health_url,
                timeout=self.timeout
            )
            logger.debug(f"Health check response status: {response.status_code}")
            logger.debug(f"Health check response headers: {dict(response.headers)}")
            logger.debug(f"Health check response text: {response.text[:200]}")
            
            response.raise_for_status()
            
            try:
                data = response.json()
                logger.debug(f"Health check response JSON: {data}")
                status = data.get('status')
                is_ready = status == 'ready'
                
                if is_ready:
                    logger.info(f"LLM server health check passed: status={status}")
                else:
                    logger.warning(f"LLM server health check failed: expected 'ready', got '{status}'")
                
                return is_ready
            except ValueError as e:
                logger.error(f"Failed to parse health check response as JSON: {e}")
                logger.error(f"Response content: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error during health check to {health_url}: {e}")
            return False
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout during health check to {health_url} (timeout={self.timeout}s): {e}")
            return False
            
        except requests.exceptions.HTTPError as e:
            # response might not be defined if raise_for_status() fails
            if 'response' in locals():
                logger.error(f"HTTP error during health check: status={response.status_code}, error={e}")
                logger.error(f"Response text: {response.text[:200]}")
            else:
                logger.error(f"HTTP error during health check: {e}")
            return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception during health check: {type(e).__name__}: {e}")
            return False
    
    def chat(self, text: str, conversation_id: Optional[str] = None) -> Optional[str]:
        """
        Send a message to the LLM and receive a response.
        
        Args:
            text: The user's message text
            conversation_id: Optional conversation identifier for context
            
        Returns:
            LLM response text, or None if server is unavailable
            
        Raises:
            LLMAPIError: For API errors (400, 500, 502)
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Prepare request payload
        payload = {
            'text': text.strip()
        }
        if conversation_id:
            payload['conversationId'] = conversation_id
        
        chat_url = f"{self.base_url}/chat"
        logger.debug(f"Sending chat request to {chat_url} with payload: {payload}")
        
        try:
            response = requests.post(
                chat_url,
                json=payload,
                timeout=self.timeout
            )
            logger.debug(f"Chat response status: {response.status_code}")
            
            # Handle successful response
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Chat response data: {data}")
                message = data.get('message', '')
                logger.info(f"Chat request successful, response length: {len(message)} chars")
                return message
            
            # Handle error responses
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Bad request')
                    logger.error(f"Bad request (400): {error_msg}")
                except ValueError:
                    error_msg = f"Bad request: {response.text[:200]}"
                    logger.error(f"Bad request (400), non-JSON response: {error_msg}")
                raise LLMAPIError(f"Bad request: {error_msg}")
            
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Internal server error')
                    logger.error(f"Internal server error (500): {error_msg}")
                except ValueError:
                    error_msg = f"Internal server error: {response.text[:200]}"
                    logger.error(f"Internal server error (500), non-JSON response: {error_msg}")
                raise LLMAPIError(f"Internal server error: {error_msg}")
            
            elif response.status_code == 502:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Web search failed')
                    logger.error(f"Web search failed (502): {error_msg}")
                except ValueError:
                    error_msg = f"Web search failed: {response.text[:200]}"
                    logger.error(f"Web search failed (502), non-JSON response: {error_msg}")
                raise LLMAPIError(f"Web search failed: {error_msg}")
            
            else:
                logger.error(f"Unexpected status code: {response.status_code}, response: {response.text[:200]}")
                raise LLMAPIError(f"Unexpected status code: {response.status_code}")
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to {chat_url}: {e}")
            return None
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout connecting to {chat_url} (timeout={self.timeout}s): {e}")
            return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {type(e).__name__}: {e}")
            raise LLMAPIError(f"Request failed: {str(e)}")
    
    def get_conversation_id(self, text: str, conversation_id: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Send a message to the LLM and receive both response and conversation ID.
        
        Args:
            text: The user's message text
            conversation_id: Optional conversation identifier for context
            
        Returns:
            Tuple of (response_text, conversation_id) or (None, None) if unavailable
            
        Raises:
            LLMAPIError: For API errors (400, 500, 502)
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Prepare request payload
        payload = {
            'text': text.strip()
        }
        if conversation_id:
            payload['conversationId'] = conversation_id
        
        chat_url = f"{self.base_url}/chat"
        logger.debug(f"Sending chat request (with conversation_id) to {chat_url} with payload: {payload}")
        
        try:
            response = requests.post(
                chat_url,
                json=payload,
                timeout=self.timeout
            )
            logger.debug(f"Chat response status: {response.status_code}")
            
            # Handle successful response
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Chat response data: {data}")
                response_text = data.get('message', '')
                returned_conversation_id = data.get('conversationId', conversation_id or 'default')
                logger.info(f"Chat request successful, response length: {len(response_text)} chars, conversation_id: {returned_conversation_id}")
                return (response_text, returned_conversation_id)
            
            # Handle error responses
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Bad request')
                    logger.error(f"Bad request (400): {error_msg}")
                except ValueError:
                    error_msg = f"Bad request: {response.text[:200]}"
                    logger.error(f"Bad request (400), non-JSON response: {error_msg}")
                raise LLMAPIError(f"Bad request: {error_msg}")
            
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Internal server error')
                    logger.error(f"Internal server error (500): {error_msg}")
                except ValueError:
                    error_msg = f"Internal server error: {response.text[:200]}"
                    logger.error(f"Internal server error (500), non-JSON response: {error_msg}")
                raise LLMAPIError(f"Internal server error: {error_msg}")
            
            elif response.status_code == 502:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Web search failed')
                    logger.error(f"Web search failed (502): {error_msg}")
                except ValueError:
                    error_msg = f"Web search failed: {response.text[:200]}"
                    logger.error(f"Web search failed (502), non-JSON response: {error_msg}")
                raise LLMAPIError(f"Web search failed: {error_msg}")
            
            else:
                logger.error(f"Unexpected status code: {response.status_code}, response: {response.text[:200]}")
                raise LLMAPIError(f"Unexpected status code: {response.status_code}")
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to {chat_url}: {e}")
            return (None, None)
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout connecting to {chat_url} (timeout={self.timeout}s): {e}")
            return (None, None)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {type(e).__name__}: {e}")
            raise LLMAPIError(f"Request failed: {str(e)}")
    
    def cleanup(self):
        """Clean up resources."""
        # No persistent connections to clean up
        pass

