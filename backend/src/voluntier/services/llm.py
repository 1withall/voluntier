"""LLM service for AI operations."""

import asyncio
import json
from typing import Any, Dict, List, Optional

import httpx
from temporalio import activity

from voluntier.config import settings
from voluntier.utils.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for interacting with LLM models."""
    
    def __init__(self):
        self.base_url = settings.llm.vllm_base_url
        self.default_model = settings.llm.default_model
        self.timeout = settings.llm.timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    async def analyze(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False,
    ) -> str:
        """
        Analyze a prompt and return LLM response.
        
        Args:
            prompt: The prompt to analyze
            model: Model to use (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            json_mode: Whether to force JSON output
            
        Returns:
            LLM response
        """
        try:
            response = await self._call_llm(
                prompt=prompt,
                model=model or self.default_model,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
            )
            return response
        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")
            raise
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False,
    ) -> str:
        """
        Generate content from a prompt.
        
        Args:
            prompt: The prompt to generate from
            model: Model to use (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            json_mode: Whether to force JSON output
            
        Returns:
            Generated content
        """
        try:
            response = await self._call_llm(
                prompt=prompt,
                model=model or self.default_model,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
            )
            return response
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            raise
    
    async def _call_llm(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
    ) -> str:
        """
        Make a call to the LLM service.
        
        Args:
            prompt: The prompt to send
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            json_mode: Whether to force JSON output
            
        Returns:
            LLM response text
        """
        # Prepare request payload
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant for the Voluntier platform."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        try:
            # Make the API call
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            if "choices" not in response_data or not response_data["choices"]:
                raise ValueError("No choices in LLM response")
            
            content = response_data["choices"][0]["message"]["content"]
            
            if json_mode:
                # Validate JSON if json_mode is enabled
                try:
                    json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"LLM returned invalid JSON: {str(e)}")
                    # Try to fix common JSON issues
                    content = self._fix_json_response(content)
            
            return content
            
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {str(e)}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling LLM: {str(e)}")
            raise
    
    def _fix_json_response(self, content: str) -> str:
        """
        Attempt to fix common JSON formatting issues.
        
        Args:
            content: The potentially malformed JSON content
            
        Returns:
            Fixed JSON content
        """
        try:
            # Try to parse as-is first
            json.loads(content)
            return content
        except json.JSONDecodeError:
            pass
        
        # Common fixes
        fixes = [
            # Remove markdown code blocks
            lambda x: x.replace("```json\n", "").replace("\n```", "").replace("```", ""),
            # Remove leading/trailing whitespace
            lambda x: x.strip(),
            # Fix trailing commas
            lambda x: x.replace(",}", "}").replace(",]", "]"),
        ]
        
        for fix in fixes:
            try:
                fixed_content = fix(content)
                json.loads(fixed_content)
                return fixed_content
            except json.JSONDecodeError:
                continue
        
        # If all fixes fail, return a minimal valid JSON
        logger.warning("Could not fix JSON response, returning error JSON")
        return '{"error": "Invalid JSON response from LLM", "original_content": "' + content.replace('"', '\\"')[:500] + '"}'
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()