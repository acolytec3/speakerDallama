"""
Dallama LLM Client Module

Handles communication with the Dallama LLM chat server.
Supports Server-Sent Events (SSE) streaming.
"""

import requests
import uuid
import logging
import json
from typing import Optional, Tuple, Callable

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
        Send a message to the LLM via SSE streaming and receive a response.
        
        Args:
            text: The user's message text
            conversation_id: Optional conversation identifier for context
            
        Returns:
            LLM response text, or None if server is unavailable
            
        Raises:
            LLMAPIError: For API errors (400, 500, 502)
        """
        # Use get_conversation_id and return just the response text
        response_text, _ = self.get_conversation_id(text, conversation_id)
        return response_text
    
    def _parse_sse_line(self, line: str) -> Optional[dict]:
        """
        Parse a single SSE line.
        
        SSE format: "data: {...}\n" or "event: type\ndata: {...}\n"
        
        Returns:
            Parsed data dict or None if line doesn't contain data
        """
        line = line.strip()
        if not line:
            return None
        
        # Handle data lines
        if line.startswith('data: '):
            data_str = line[6:]  # Remove 'data: ' prefix
            try:
                return json.loads(data_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse SSE data as JSON: {data_str[:100]}, error: {e}")
                return None
        
        return None
    
    def _stream_sse(self, response: requests.Response, 
                    on_tool_call: Optional[Callable[[dict], None]] = None,
                    on_chunk: Optional[Callable[[str], None]] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse SSE stream from response.
        
        SSE format: Each event is separated by \n\n
        Example:
            data: {"type":"chunk","text":"Hello"}\n
            \n
            data: {"type":"done","conversationId":"123"}\n
            \n
        
        Args:
            response: Streaming response object
            on_tool_call: Optional callback for tool_call events
            on_chunk: Optional callback for chunk events
            
        Returns:
            Tuple of (full_response_text, conversation_id)
        """
        full_response = ""
        conversation_id = None
        done = False
        
        try:
            # Use iter_lines for SSE (line-based protocol)
            # SSE events are separated by blank lines (\n\n)
            event_lines = []
            
            for line in response.iter_lines(decode_unicode=True):
                if line is None:
                    continue
                
                line = line.strip()
                
                if not line:
                    # Empty line indicates end of SSE event block - process accumulated lines
                    if event_lines:
                        # Parse the event block
                        event_data = None
                        for event_line in event_lines:
                            data = self._parse_sse_line(event_line)
                            if data:
                                event_data = data
                                break
                        
                        if event_data:
                            event_type = event_data.get('type')
                            
                            if event_type == 'tool_call':
                                logger.debug("Received tool_call event")
                                if on_tool_call:
                                    on_tool_call(event_data)
                            
                            elif event_type == 'chunk':
                                chunk_text = event_data.get('text', '')
                                if chunk_text:
                                    full_response += chunk_text
                                    logger.debug(f"Received chunk: {chunk_text[:50]}...")
                                    if on_chunk:
                                        on_chunk(chunk_text)
                            
                            elif event_type == 'done':
                                logger.debug("Received done event")
                                # Extract conversation_id if present
                                if 'conversationId' in event_data:
                                    conversation_id = event_data.get('conversationId')
                                done = True
                                break
                            
                            else:
                                logger.debug(f"Unknown event type: {event_type}")
                        
                        # Clear event lines for next event
                        event_lines = []
                else:
                    # Accumulate lines for current event
                    event_lines.append(line)
                
                if done:
                    break
            
            # Process any remaining event lines (in case stream ends without blank line)
            if not done and event_lines:
                event_data = None
                for event_line in event_lines:
                    data = self._parse_sse_line(event_line)
                    if data:
                        event_data = data
                        break
                
                if event_data:
                    event_type = event_data.get('type')
                    if event_type == 'chunk':
                        chunk_text = event_data.get('text', '')
                        if chunk_text:
                            full_response += chunk_text
                            if on_chunk:
                                on_chunk(chunk_text)
                    elif event_type == 'done':
                        if 'conversationId' in event_data:
                            conversation_id = event_data.get('conversationId')
        
        except Exception as e:
            logger.error(f"Error parsing SSE stream: {e}")
            raise
        
        return (full_response if full_response else None, conversation_id)
    
    def get_conversation_id(self, text: str, conversation_id: Optional[str] = None,
                           on_tool_call: Optional[Callable[[dict], None]] = None,
                           on_chunk: Optional[Callable[[str], None]] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Send a message to the LLM via SSE streaming and receive both response and conversation ID.
        
        Args:
            text: The user's message text
            conversation_id: Optional conversation identifier for context
            on_tool_call: Optional callback function called when tool_call events are received
            on_chunk: Optional callback function called when chunk events are received
            
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
        
        chat_url = f"{self.base_url}/voice"
        logger.debug(f"Sending SSE chat request (with conversation_id) to {chat_url} with payload: {payload}")
        
        try:
            # Make POST request with streaming enabled
            response = requests.post(
                chat_url,
                json=payload,
                timeout=self.timeout,
                stream=True,
                headers={
                    'Accept': 'text/event-stream',
                    'Cache-Control': 'no-cache'
                }
            )
            logger.debug(f"Chat response status: {response.status_code}")
            
            # Handle successful response
            if response.status_code == 200:
                # Parse SSE stream
                response_text, returned_conversation_id = self._stream_sse(
                    response,
                    on_tool_call=on_tool_call,
                    on_chunk=on_chunk
                )
                
                # Use provided conversation_id if not returned
                if not returned_conversation_id:
                    returned_conversation_id = conversation_id
                
                logger.info(f"SSE chat request successful, response length: {len(response_text or '')} chars, conversation_id: {returned_conversation_id}")
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

