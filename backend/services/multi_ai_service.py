"""
Multi-AI Provider Service

Integrates multiple AI providers (OpenAI, Anthropic, Google, etc.) for enhanced
reasoning capabilities and fallback options.
"""

import os
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class MultiAIService:
    """Service for managing multiple AI providers"""
    
    def __init__(self):
        self.providers = {}
        self.default_provider = 'openai'
        self.fallback_chain = ['openai', 'anthropic', 'google']
        
        # Initialize available providers
        self._init_openai()
        self._init_anthropic()
        self._init_google()
        
        logger.info(f"✅ Multi-AI service initialized with providers: {list(self.providers.keys())}")
    
    def _init_openai(self):
        """Initialize OpenAI provider"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                from openai import OpenAI
                # Initialize with just the API key, no http_client
                self.providers['openai'] = {
                    'client': OpenAI(api_key=api_key),
                    'models': ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo'],
                    'default_model': 'gpt-3.5-turbo',
                    'max_tokens': 4096,
                    'available': True
                }
                logger.info("✅ OpenAI provider initialized")
            else:
                logger.warning("⚠️ OpenAI API key not found")
        except Exception as e:
            logger.error(f"❌ OpenAI initialization failed: {e}")
    
    def _init_anthropic(self):
        """Initialize Anthropic (Claude) provider"""
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                import anthropic
                self.providers['anthropic'] = {
                    'client': anthropic.Anthropic(api_key=api_key),
                    'models': ['claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
                    'default_model': 'claude-3-sonnet-20240229',
                    'max_tokens': 4096,
                    'available': True
                }
                logger.info("✅ Anthropic (Claude) provider initialized")
            else:
                logger.warning("⚠️ Anthropic API key not found")
        except ImportError:
            logger.warning("⚠️ Anthropic SDK not installed")
        except Exception as e:
            logger.error(f"❌ Anthropic initialization failed: {e}")
    
    def _init_google(self):
        """Initialize Google AI (Gemini) provider"""
        try:
            api_key = os.getenv('GOOGLE_AI_API_KEY')
            if api_key:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.providers['google'] = {
                    'client': genai,
                    'models': ['gemini-pro', 'gemini-pro-vision'],
                    'default_model': 'gemini-pro',
                    'max_tokens': 2048,
                    'available': True
                }
                logger.info("✅ Google AI (Gemini) provider initialized")
            else:
                logger.warning("⚠️ Google AI API key not found")
        except ImportError:
            logger.warning("⚠️ Google AI SDK not installed")
        except Exception as e:
            logger.error(f"❌ Google AI initialization failed: {e}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers"""
        return [name for name, config in self.providers.items() if config.get('available', False)]
    
    def get_reasoning_response(
        self, 
        user_input: str, 
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Get reasoning response from specified or best available provider"""
        
        # Use default provider if none specified
        if not provider:
            provider = self.default_provider
        
        # Try specified provider first
        if provider in self.providers and self.providers[provider]['available']:
            try:
                return self._call_provider(provider, user_input, model, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"⚠️ Provider {provider} failed: {e}")
        
        # Fallback to other providers
        for fallback_provider in self.fallback_chain:
            if fallback_provider != provider and fallback_provider in self.providers:
                if self.providers[fallback_provider]['available']:
                    try:
                        logger.info(f"🔄 Falling back to {fallback_provider}")
                        return self._call_provider(fallback_provider, user_input, model, temperature, max_tokens)
                    except Exception as e:
                        logger.warning(f"⚠️ Fallback provider {fallback_provider} failed: {e}")
                        continue
        
        raise Exception("All AI providers failed")
    
    def _call_provider(
        self, 
        provider: str, 
        user_input: str, 
        model: Optional[str] = None, 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Call specific AI provider"""
        
        config = self.providers[provider]
        selected_model = model or config['default_model']
        tokens = max_tokens or config['max_tokens']
        
        # Enhanced system prompt for reasoning
        system_prompt = """You are an advanced reasoning AI that thinks step by step and provides detailed analysis.

Format your response as:
<think>
[Your detailed step-by-step reasoning process, including:
- Problem analysis and understanding
- Key concepts and relationships identification
- Logical deduction and inference steps
- Consideration of multiple perspectives
- Validation of conclusions]
</think>
[Your clear, well-structured final answer]"""
        
        if provider == 'openai':
            return self._call_openai(config['client'], selected_model, user_input, system_prompt, temperature, tokens)
        elif provider == 'anthropic':
            return self._call_anthropic(config['client'], selected_model, user_input, system_prompt, temperature, tokens)
        elif provider == 'google':
            return self._call_google(config['client'], selected_model, user_input, system_prompt, temperature, tokens)
        else:
            raise Exception(f"Unknown provider: {provider}")
    
    def _call_openai(self, client, model: str, user_input: str, system_prompt: str, temperature: float, max_tokens: int) -> Tuple[str, str, Dict[str, Any]]:
        """Call OpenAI API"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        response_text = completion.choices[0].message.content
        thoughts, response = self._parse_thinking_response(response_text)
        
        metadata = {
            'provider': 'openai',
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'usage': {
                'prompt_tokens': completion.usage.prompt_tokens if completion.usage else 0,
                'completion_tokens': completion.usage.completion_tokens if completion.usage else 0,
                'total_tokens': completion.usage.total_tokens if completion.usage else 0
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return thoughts, response, metadata
    
    def _call_anthropic(self, client, model: str, user_input: str, system_prompt: str, temperature: float, max_tokens: int) -> Tuple[str, str, Dict[str, Any]]:
        """Call Anthropic (Claude) API"""
        try:
            message = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_input}
                ]
            )
            
            response_text = message.content[0].text
            thoughts, response = self._parse_thinking_response(response_text)
            
            metadata = {
                'provider': 'anthropic',
                'model': model,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'usage': {
                    'input_tokens': message.usage.input_tokens if hasattr(message, 'usage') else 0,
                    'output_tokens': message.usage.output_tokens if hasattr(message, 'usage') else 0,
                    'total_tokens': (message.usage.input_tokens + message.usage.output_tokens) if hasattr(message, 'usage') else 0
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return thoughts, response, metadata
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise
    
    def _call_google(self, client, model: str, user_input: str, system_prompt: str, temperature: float, max_tokens: int) -> Tuple[str, str, Dict[str, Any]]:
        """Call Google AI (Gemini) API"""
        try:
            model_instance = client.GenerativeModel(model)
            
            # Combine system prompt and user input for Gemini
            full_prompt = f"{system_prompt}\n\nUser: {user_input}"
            
            generation_config = client.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            response = model_instance.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            response_text = response.text
            thoughts, response_final = self._parse_thinking_response(response_text)
            
            metadata = {
                'provider': 'google',
                'model': model,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'usage': {
                    'prompt_tokens': response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                    'completion_tokens': response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                    'total_tokens': response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return thoughts, response_final, metadata
            
        except Exception as e:
            logger.error(f"Google AI API call failed: {e}")
            raise
    
    def _parse_thinking_response(self, response_text: str) -> Tuple[str, str]:
        """Parse AI response to extract thinking and final answer"""
        if "<think>" in response_text and "</think>" in response_text:
            parts = response_text.split("</think>")
            thoughts = parts[0].replace("<think>", "").strip()
            response = parts[1].strip() if len(parts) > 1 else ""
        else:
            # Fallback: treat first paragraph as thinking
            paragraphs = response_text.split("\n\n")
            if len(paragraphs) > 1:
                thoughts = paragraphs[0].strip()
                response = "\n\n".join(paragraphs[1:]).strip()
            else:
                thoughts = f"Processing query: {response_text[:100]}..."
                response = response_text.strip()
        
        return thoughts, response
    
    def compare_responses(self, user_input: str, providers: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get responses from multiple providers for comparison"""
        if not providers:
            providers = self.get_available_providers()
        
        results = {}
        for provider in providers:
            try:
                thoughts, response, metadata = self.get_reasoning_response(user_input, provider=provider)
                results[provider] = {
                    'thoughts': thoughts,
                    'response': response,
                    'metadata': metadata,
                    'success': True
                }
            except Exception as e:
                results[provider] = {
                    'error': str(e),
                    'success': False
                }
        
        return {
            'user_input': user_input,
            'timestamp': datetime.utcnow().isoformat(),
            'providers_compared': len(providers),
            'results': results
        }
    
    def get_best_response(self, user_input: str, providers: Optional[List[str]] = None) -> Tuple[str, str, Dict[str, Any]]:
        """Get the best response using ensemble method"""
        comparison = self.compare_responses(user_input, providers)
        
        # Simple scoring: prefer responses with longer thinking and fewer errors
        best_provider = None
        best_score = -1
        
        for provider, result in comparison['results'].items():
            if result['success']:
                score = len(result['thoughts'].split()) * 0.7 + len(result['response'].split()) * 0.3
                if score > best_score:
                    best_score = score
                    best_provider = provider
        
        if best_provider:
            best_result = comparison['results'][best_provider]
            metadata = best_result['metadata'].copy()
            metadata['ensemble_comparison'] = {
                'providers_compared': comparison['providers_compared'],
                'selected_provider': best_provider,
                'selection_score': best_score
            }
            
            return best_result['thoughts'], best_result['response'], metadata
        else:
            raise Exception("No providers returned successful responses")
    
    def health_check(self) -> Dict[str, Any]:
        """Check health status of all providers"""
        health = {
            'total_providers': len(self.providers),
            'available_providers': len(self.get_available_providers()),
            'default_provider': self.default_provider,
            'providers': {}
        }
        
        for name, config in self.providers.items():
            health['providers'][name] = {
                'available': config.get('available', False),
                'models': config.get('models', []),
                'default_model': config.get('default_model'),
                'max_tokens': config.get('max_tokens')
            }
        
        return health


# Global service instance
_multi_ai_service = None

def get_multi_ai_service() -> MultiAIService:
    """Get the global multi-AI service instance"""
    global _multi_ai_service
    if _multi_ai_service is None:
        _multi_ai_service = MultiAIService()
    return _multi_ai_service


# Export
__all__ = ['MultiAIService', 'get_multi_ai_service']