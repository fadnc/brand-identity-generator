from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
import json
import logging
from datetime import datetime


class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents in the brand identity system.
    Provides common functionality and enforces interface contracts.
    """
    
    def __init__(self, openai_api_key: str, agent_name: str = "BaseAgent"):
        """
        Initialize the base agent.
        
        Args:
            openai_api_key: OpenAI API key for LLM access
            agent_name: Name identifier for this agent
        """
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.agent_name = agent_name
        self.logger = self._setup_logger()
        
        # Configuration
        self.default_model = "gpt-4-turbo-preview"
        self.fallback_model = "gpt-3.5-turbo"
        self.max_retries = 3
        self.temperature = 0.7
        
        # Execution tracking
        self.execution_history: List[Dict[str, Any]] = []
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for this agent."""
        logger = logging.getLogger(f"agent.{self.agent_name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.agent_name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Main execution method that each agent must implement.
        
        Returns:
            Dict containing the agent's output
        """
        pass
    
    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        json_response: bool = True,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Centralized LLM calling method with error handling and retries.
        
        Args:
            messages: List of message dictionaries for the LLM
            model: Model to use (defaults to self.default_model)
            temperature: Temperature for generation
            json_response: Whether to expect JSON response
            max_tokens: Maximum tokens in response
            
        Returns:
            Parsed response from LLM
        """
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.temperature
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"LLM call attempt {attempt + 1}/{self.max_retries}")
                
                # Prepare request parameters
                request_params = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature
                }
                
                if json_response:
                    request_params["response_format"] = {"type": "json_object"}
                
                if max_tokens:
                    request_params["max_tokens"] = max_tokens
                
                # Make API call
                response = await self.client.chat.completions.create(**request_params)
                
                content = response.choices[0].message.content
                
                # Track usage
                self._track_usage(response.usage, model)
                
                # Parse JSON if expected
                if json_response:
                    try:
                        parsed = json.loads(content)
                        self.logger.info("Successfully parsed JSON response")
                        return parsed
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"JSON parsing failed: {e}")
                        # Try to extract JSON from response
                        import re
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group())
                        raise
                else:
                    return {"content": content}
                    
            except Exception as e:
                self.logger.error(f"LLM call failed on attempt {attempt + 1}: {str(e)}")
                
                # Try fallback model on last retry
                if attempt == self.max_retries - 2 and model == self.default_model:
                    self.logger.info(f"Switching to fallback model: {self.fallback_model}")
                    model = self.fallback_model
                
                # Raise on final attempt
                if attempt == self.max_retries - 1:
                    self.logger.error("All retry attempts exhausted")
                    raise
                
                # Wait before retry (exponential backoff)
                import asyncio
                await asyncio.sleep(2 ** attempt)
        
        # This should never be reached due to raise in loop
        raise Exception("LLM call failed after all retries")
    
    def _track_usage(self, usage: Any, model: str) -> None:
        """
        Track API usage for monitoring and cost calculation.
        
        Args:
            usage: Usage object from OpenAI response
            model: Model that was used
        """
        usage_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.agent_name,
            "model": model,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens
        }
        
        self.execution_history.append(usage_data)
        
        # Log usage
        self.logger.info(
            f"Tokens used - Prompt: {usage.prompt_tokens}, "
            f"Completion: {usage.completion_tokens}, "
            f"Total: {usage.total_tokens}"
        )
    
    def get_total_usage(self) -> Dict[str, int]:
        """
        Get total token usage across all executions.
        
        Returns:
            Dictionary with token counts
        """
        total_prompt = sum(h.get("prompt_tokens", 0) for h in self.execution_history)
        total_completion = sum(h.get("completion_tokens", 0) for h in self.execution_history)
        
        return {
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
            "executions": len(self.execution_history)
        }
    
    def _validate_input(self, required_fields: List[str], **kwargs) -> None:
        """
        Validate that required input fields are present.
        
        Args:
            required_fields: List of required field names
            **kwargs: Input arguments to validate
            
        Raises:
            ValueError: If required fields are missing
        """
        missing_fields = [field for field in required_fields if not kwargs.get(field)]
        
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _create_system_prompt(self, role_description: str, guidelines: List[str]) -> str:
        """
        Create a standardized system prompt.
        
        Args:
            role_description: Description of the agent's role
            guidelines: List of guidelines for the agent
            
        Returns:
            Formatted system prompt
        """
        guidelines_text = "\n".join([f"- {g}" for g in guidelines])
        
        return f"""You are a {role_description}.

Guidelines:
{guidelines_text}

Always provide responses in JSON format when requested.
Be creative, professional, and strategic in your outputs."""
    
    async def _batch_process(
        self,
        items: List[Any],
        process_func,
        batch_size: int = 5
    ) -> List[Any]:
        """
        Process items in batches to avoid rate limits.
        
        Args:
            items: List of items to process
            process_func: Async function to process each item
            batch_size: Number of items per batch
            
        Returns:
            List of processed results
        """
        import asyncio
        
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            self.logger.info(f"Processing batch {i//batch_size + 1}")
            
            batch_results = await asyncio.gather(*[
                process_func(item) for item in batch
            ])
            
            results.extend(batch_results)
            
            # Small delay between batches
            if i + batch_size < len(items):
                await asyncio.sleep(1)
        
        return results
    
    def _sanitize_input(self, text: str) -> str:
        """
        Sanitize user input to prevent prompt injection.
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Sanitized text
        """
        # Remove any attempt to inject system prompts
        text = text.replace("System:", "").replace("system:", "")
        text = text.replace("Assistant:", "").replace("assistant:", "")
        
        # Limit length
        max_length = 2000
        if len(text) > max_length:
            self.logger.warning(f"Input truncated from {len(text)} to {max_length} chars")
            text = text[:max_length]
        
        return text.strip()
    
    def _extract_key_points(self, text: str, max_points: int = 5) -> List[str]:
        """
        Extract key points from text using simple heuristics.
        
        Args:
            text: Text to extract from
            max_points: Maximum number of points to extract
            
        Returns:
            List of key points
        """
        # Split by common delimiters
        sentences = text.replace('\n', '. ').split('. ')
        
        # Filter and clean
        points = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        return points[:max_points]
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get agent metadata and statistics.
        
        Returns:
            Dictionary with agent information
        """
        return {
            "agent_name": self.agent_name,
            "model": self.default_model,
            "fallback_model": self.fallback_model,
            "temperature": self.temperature,
            "total_executions": len(self.execution_history),
            "usage_stats": self.get_total_usage()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the agent.
        
        Returns:
            Health status
        """
        try:
            # Simple API call to verify connection
            test_response = await self._call_llm(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Respond with 'OK' in JSON format."}
                ],
                model=self.fallback_model,
                json_response=True
            )
            
            return {
                "status": "healthy",
                "agent": self.agent_name,
                "api_connection": "ok",
                "test_response": test_response
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "agent": self.agent_name,
                "error": str(e)
            }
    
    def __repr__(self) -> str:
        return f"<{self.agent_name} - Executions: {len(self.execution_history)}>"