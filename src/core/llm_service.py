"""
Basic LLM Service - Phase 1 with Gemini Support
Simple LLM client that supports multiple providers including Google Gemini
"""
import logging
from typing import Optional, Dict, Any
from enum import Enum
import json

from ..config import settings

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    GEMINI_FLASH = "gemini-1.5-flash"
    GEMINI_PRO = "gemini-1.5-pro"
    GEMINI_FLASH_8B = "gemini-1.5-flash-8b"
    GEMINI_2_FLASH = "gemini-2.0-flash-exp"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    GPT_4 = "gpt-4"

# Gemini model configurations
GEMINI_MODELS = {
    "gemini-1.5-flash": {
        "name": "Gemini 1.5 Flash",
        "description": "Fast and efficient model for general tasks",
        "input_tokens": 1000000,
        "output_tokens": 8192
    },
    "gemini-1.5-pro": {
        "name": "Gemini 1.5 Pro", 
        "description": "Most capable model for complex reasoning",
        "input_tokens": 2000000,
        "output_tokens": 8192
    },
    "gemini-1.5-flash-8b": {
        "name": "Gemini 1.5 Flash-8B",
        "description": "Smaller, faster model for simple tasks",
        "input_tokens": 1000000,
        "output_tokens": 8192
    },
    "gemini-2.0-flash-exp": {
        "name": "Gemini 2.0 Flash (Experimental)",
        "description": "Latest experimental model with enhanced capabilities",
        "input_tokens": 1000000,
        "output_tokens": 8192
    }
}

# Claude model configurations (using confirmed working model IDs from Anthropic docs)
CLAUDE_MODELS = {
    "claude-sonnet-4-20250514": {
        "name": "Claude 4 Sonnet",
        "description": "Latest Claude 4 Sonnet with enhanced reasoning capabilities",
        "input_tokens": 200000,
        "output_tokens": 8192
    },
    "claude-opus-4-1-20250805": {
        "name": "Claude 4.1 Opus",
        "description": "Most advanced Claude model with extended thinking",
        "input_tokens": 200000,
        "output_tokens": 8192
    },
    "claude-opus-4-20250514": {
        "name": "Claude 4 Opus",
        "description": "Highly capable Claude 4 model for complex reasoning",
        "input_tokens": 200000,
        "output_tokens": 8192
    },
    "claude-3-5-sonnet-20241022": {
        "name": "Claude 3.5 Sonnet",
        "description": "Most intelligent Claude 3.5 model, excellent at complex reasoning",
        "input_tokens": 200000,
        "output_tokens": 8192
    },
    "claude-3-5-haiku-20241022": {
        "name": "Claude 3.5 Haiku",
        "description": "Fast and efficient Claude 3.5 model",
        "input_tokens": 200000,
        "output_tokens": 8192
    },
    "claude-3-haiku-20240307": {
        "name": "Claude 3 Haiku",
        "description": "Fastest and most cost-effective Claude model",
        "input_tokens": 200000,
        "output_tokens": 4096
    },
    "claude-3-opus-20240229": {
        "name": "Claude 3 Opus",
        "description": "Most powerful Claude 3 model for complex tasks",
        "input_tokens": 200000,
        "output_tokens": 4096
    }
}

class SimpleLLMClient:
    """
    Simple LLM client with multiple provider support
    Phase 1: Basic implementation for JSON refactoring
    Team Member 1 will enhance with advanced routing and caching
    """
    
    def __init__(self, api_keys=None):
        self.available_providers = []
        self.preferred_model = None
        self.api_keys = api_keys or {}
        self._initialize_clients()
        # Set Claude Sonnet 4 as default preferred model if no preference set
        if not self.preferred_model and "claude-sonnet-4-20250514" in CLAUDE_MODELS:
            self.preferred_model = "claude-sonnet-4-20250514"
    
    def set_preferred_model(self, model_id: str):
        """Set preferred model for analysis"""
        if model_id in GEMINI_MODELS or model_id in CLAUDE_MODELS:
            self.preferred_model = model_id
            logger.info(f"Preferred model set to: {model_id}")
        else:
            logger.warning(f"Unknown model: {model_id}")
    
    def update_api_keys(self, api_keys: dict):
        """Update API keys and reinitialize clients"""
        self.api_keys = api_keys
        self.available_providers = []
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize available LLM clients based on API keys"""
        
        # Use user-provided API keys first, fallback to environment variables
        google_key = self.api_keys.get('google') or settings.google_api_key
        anthropic_key = self.api_keys.get('anthropic') or settings.anthropic_api_key
        openai_key = self.api_keys.get('openai') or settings.openai_api_key
        
        # Google Gemini
        if google_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_key)
                self.genai = genai  # Store genai module for dynamic model creation
                # Add all Gemini models to available providers
                self.available_providers.extend([
                    LLMProvider.GEMINI_FLASH,
                    LLMProvider.GEMINI_PRO, 
                    LLMProvider.GEMINI_FLASH_8B,
                    LLMProvider.GEMINI_2_FLASH
                ])
                logger.info("✅ Google Gemini clients initialized (all models available)")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")
        
        # Anthropic Claude
        if anthropic_key:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(
                    api_key=anthropic_key
                )
                # Add all Claude models to available providers  
                for model_id in CLAUDE_MODELS.keys():
                    # Create enum-like providers for each model
                    self.available_providers.append(type('Provider', (), {'value': model_id})())
                logger.info("✅ Anthropic Claude client initialized with all models")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")
        
        # OpenAI GPT
        if openai_key:
            try:
                import openai
                self.openai_client = openai.OpenAI(
                    api_key=openai_key
                )
                self.available_providers.append(LLMProvider.GPT_4)
                logger.info("✅ OpenAI GPT client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        if not self.available_providers:
            logger.error("❌ No LLM providers available! Please provide API keys.")
        else:
            logger.info(f"🎯 Available LLM providers: {[getattr(p, 'value', p) for p in self.available_providers]}")
    
    async def complete(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Generate completion using preferred model or fallback chain
        """
        
        if not self.available_providers:
            raise Exception("No LLM providers available. Please configure API keys.")
        
        # If we have a preferred model, try it first
        if self.preferred_model:
            try:
                if self.preferred_model in GEMINI_MODELS:
                    return await self._complete_gemini(prompt, max_tokens, temperature, self.preferred_model)
                elif self.preferred_model in CLAUDE_MODELS:
                    return await self._complete_claude(prompt, max_tokens, temperature, self.preferred_model)
            except Exception as e:
                logger.warning(f"Preferred model {self.preferred_model} failed: {e}")
                # Fall back to provider chain
        
        # Fallback: Try providers in order of availability
        for provider in self.available_providers:
            try:
                if provider in [LLMProvider.GEMINI_FLASH, LLMProvider.GEMINI_PRO, 
                               LLMProvider.GEMINI_FLASH_8B, LLMProvider.GEMINI_2_FLASH]:
                    return await self._complete_gemini(prompt, max_tokens, temperature, provider.value)
                elif hasattr(provider, 'value') and provider.value in CLAUDE_MODELS:
                    return await self._complete_claude(prompt, max_tokens, temperature, provider.value)
                elif provider == LLMProvider.GPT_4:
                    return await self._complete_openai(prompt, max_tokens, temperature)
                    
            except Exception as e:
                logger.warning(f"LLM provider {getattr(provider, 'value', provider)} failed: {e}")
                continue
        
        raise Exception("All LLM providers failed")
    
    async def stream(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1):
        """
        Generate streaming completion using the first available provider
        Yields tokens as they come from the LLM
        """
        
        if not self.available_providers:
            raise Exception("No LLM providers available. Please configure API keys.")
        
        # Try providers in order of preference
        for provider in self.available_providers:
            try:
                if provider in [LLMProvider.GEMINI_FLASH, LLMProvider.GEMINI_PRO, 
                               LLMProvider.GEMINI_FLASH_8B, LLMProvider.GEMINI_2_FLASH]:
                    async for chunk in self._stream_gemini(prompt, max_tokens, temperature, provider.value):
                        yield chunk
                    return
                elif hasattr(provider, 'value') and provider.value in CLAUDE_MODELS:
                    async for chunk in self._stream_claude(prompt, max_tokens, temperature, provider.value):
                        yield chunk
                    return
                elif provider == LLMProvider.GPT_4:
                    async for chunk in self._stream_openai(prompt, max_tokens, temperature):
                        yield chunk
                    return
                    
            except Exception as e:
                logger.warning(f"LLM provider {provider.value} streaming failed: {e}")
                continue
        
        raise Exception("All LLM providers failed for streaming")
    
    async def _complete_gemini(self, prompt: str, max_tokens: int, temperature: float, model_id: str = None) -> Dict[str, Any]:
        """Complete using Google Gemini with specified model"""
        
        try:
            # Use preferred model if set, otherwise use the passed model_id or default
            if self.preferred_model:
                model_to_use = self.preferred_model
            elif model_id:
                model_to_use = model_id
            else:
                model_to_use = "gemini-1.5-flash"
            
            # Create model client dynamically
            gemini_client = self.genai.GenerativeModel(model_to_use)
            
            # Configure generation parameters
            generation_config = {
                'max_output_tokens': max_tokens,
                'temperature': temperature,
                'top_p': 0.8,
                'top_k': 40
            }
            
            response = gemini_client.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return {
                "content": response.text,
                "model": model_to_use,
                "tokens_used": len(response.text.split()) * 1.3  # Rough estimate
            }
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    async def _stream_gemini(self, prompt: str, max_tokens: int, temperature: float, model_id: str = None):
        """Stream using Google Gemini with specified model"""
        
        try:
            # Use preferred model if set, otherwise use the passed model_id or default
            if self.preferred_model:
                model_to_use = self.preferred_model
            elif model_id:
                model_to_use = model_id
            else:
                model_to_use = "gemini-1.5-flash"
            
            # Create model client dynamically
            gemini_client = self.genai.GenerativeModel(model_to_use)
            
            # Configure generation parameters
            generation_config = {
                'max_output_tokens': max_tokens,
                'temperature': temperature,
                'top_p': 0.8,
                'top_k': 40
            }
            
            response = gemini_client.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True  # Enable streaming
            )
            
            for chunk in response:
                if chunk.text:
                    yield {
                        "content": chunk.text,
                        "model": model_to_use,
                        "done": False
                    }
            
            # Final chunk to indicate completion
            yield {
                "content": "",
                "model": model_to_use,
                "done": True
            }
            
        except Exception as e:
            logger.error(f"Gemini streaming API error: {e}")
            raise
    
    async def _complete_claude(self, prompt: str, max_tokens: int, temperature: float, model_id: str = None) -> Dict[str, Any]:
        """Complete using Anthropic Claude with specified model"""
        
        try:
            # Use preferred model if set, otherwise use the passed model_id or default
            if self.preferred_model and self.preferred_model in CLAUDE_MODELS:
                model_to_use = self.preferred_model
            elif model_id and model_id in CLAUDE_MODELS:
                model_to_use = model_id
            else:
                model_to_use = "claude-sonnet-4-20250514"
            
            response = self.anthropic_client.messages.create(
                model=model_to_use,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                "content": response.content[0].text,
                "model": model_to_use,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens
            }
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
    
    async def _stream_claude(self, prompt: str, max_tokens: int, temperature: float, model_id: str = None):
        """Stream using Anthropic Claude with specified model"""
        
        try:
            # Use preferred model if set, otherwise use the passed model_id or default
            if self.preferred_model and self.preferred_model in CLAUDE_MODELS:
                model_to_use = self.preferred_model
            elif model_id and model_id in CLAUDE_MODELS:
                model_to_use = model_id
            else:
                model_to_use = "claude-sonnet-4-20250514"
            
            with self.anthropic_client.messages.stream(
                model=model_to_use,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for text in stream.text_stream:
                    yield {
                        "content": text,
                        "model": model_to_use,
                        "done": False
                    }
            
            # Final chunk to indicate completion
            yield {
                "content": "",
                "model": model_to_use,
                "done": True
            }
            
        except Exception as e:
            logger.error(f"Claude streaming API error: {e}")
            raise
    
    async def _complete_openai(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Complete using OpenAI GPT"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                "content": response.choices[0].message.content,
                "model": "gpt-4",
                "tokens_used": response.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _stream_openai(self, prompt: str, max_tokens: int, temperature: float):
        """Stream using OpenAI GPT"""
        
        try:
            stream = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "model": "gpt-4",
                        "done": False
                    }
            
            # Final chunk to indicate completion
            yield {
                "content": "",
                "model": "gpt-4",
                "done": True
            }
            
        except Exception as e:
            logger.error(f"OpenAI streaming API error: {e}")
            raise

# Global LLM client instance (with fallback to environment variables)
llm_client = SimpleLLMClient()

def create_llm_client(api_keys: dict) -> SimpleLLMClient:
    """Create LLM client with user-provided API keys"""
    return SimpleLLMClient(api_keys=api_keys)

# TODO: Team Member 1 - Enhanced LLM router with advanced features
# class EnhancedLLMRouter(SimpleLLMClient):
#     """Enhanced LLM router with caching, load balancing, and cost optimization"""
#     
#     def __init__(self, cache_manager=None):
#         super().__init__()
#         self.cache = cache_manager
#     
#     async def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
#         # TODO: Team Member 1 - Add advanced features
#         # 1. Check cache for identical prompts
#         # 2. Load balance across providers
#         # 3. Cost optimization (prefer cheaper models)
#         # 4. Rate limiting and retry logic
#         # 5. Token usage tracking and limits
#         pass