"""
Galileo AI Evaluation Service - Minimal Integration with Graceful Fallback

This service wraps OpenAI API calls with Galileo evaluation, providing:
- Quality metrics for AI responses
- Graceful fallback when Galileo unavailable
- Backward compatibility with existing systems
"""

import os
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import httpx

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

# Setup logging
logger = logging.getLogger(__name__)

# Galileo imports with fallback
GALILEO_AVAILABLE = False
try:
    import galileo
    # Modern Galileo SDK uses direct logging functions
    GALILEO_AVAILABLE = True
    logger.info("✅ Galileo SDK imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Galileo SDK not available: {e}")
    logger.warning("⚠️ Will use basic evaluation instead")


class GalileoService:
    """
    Service for integrating Galileo AI evaluation with OpenAI calls.
    Falls back gracefully to standard OpenAI when Galileo unavailable.
    """
    
    def __init__(self):
        # Initialize OpenAI client
        try:
            http_client = httpx.Client()
            self.openai_client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                http_client=http_client
            )
            logger.info("✅ OpenAI client initialized")
        except Exception as e:
            logger.error(f"❌ OpenAI initialization failed: {e}")
            # Fallback initialization
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Initialize Galileo logger if available
        self.galileo_logger = None
        self.galileo_enabled = False
        
        if GALILEO_AVAILABLE and os.getenv("GALILEO_API_KEY"):
            try:
                # Initialize Galileo logger with project and log stream
                project = os.getenv("GALILEO_PROJECT", "vizbrain-thinking-graph")
                log_stream = os.getenv("GALILEO_LOG_STREAM", "vizbrain-chat-logs")
                
                self.galileo_logger = galileo.GalileoLogger(
                    project=project,
                    log_stream=log_stream
                )
                self.galileo_enabled = True
                logger.info(f"✅ Galileo logger initialized for project '{project}' and stream '{log_stream}'")
            except Exception as e:
                logger.warning(f"⚠️ Galileo logger initialization failed: {e}")
                logger.warning("⚠️ Continuing with basic evaluation")
                self.galileo_enabled = False
        else:
            logger.info("ℹ️ Galileo not configured - using basic evaluation")
    
    def get_reasoning_response_with_evaluation(
        self, 
        user_input: str, 
        session_id: Optional[str] = None
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Get AI response with optional Galileo evaluation.
        
        Args:
            user_input: User's question/prompt
            session_id: Optional session identifier
            
        Returns:
            Tuple of (thoughts, response, metadata)
            - thoughts: AI's step-by-step reasoning
            - response: Final answer to user
            - metadata: Evaluation scores and system info
        """
        if not session_id:
            session_id = f"vizbrain_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Standard system prompt for reasoning
        system_prompt = """You are a reasoning agent that thinks step by step.
Format your response as follows:
<think>
[Your step-by-step reasoning process here]
</think>
[Your final answer here]"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        # Initialize metadata
        metadata = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "galileo_enabled": self.galileo_enabled,
            "evaluation_scores": {},
            "evaluation_feedback": {},
            "galileo_trace_id": None,
            "service_version": "1.0.0"
        }
        
        # Try Galileo logging if available
        if self.galileo_enabled and self.galileo_logger:
            try:
                logger.info(f"📊 Running OpenAI call with Galileo logging for session {session_id}")
                
                # Make standard OpenAI call
                completion = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1200
                )
                
                # Log to Galileo using single LLM span trace
                response_content = completion.choices[0].message.content
                
                try:
                    logger.info(f"🔬 Starting Galileo logging for session {session_id}")
                    
                    # Create a trace with LLM span for Galileo
                    trace = self.galileo_logger.start_trace(
                        input=user_input,
                        name=f"VizBrain Chat - {session_id[-8:]}"
                    )
                    logger.info(f"✅ Trace created with ID: {trace.id if hasattr(trace, 'id') else 'Unknown'}")
                    
                    # Add LLM span
                    llm_span = self.galileo_logger.add_llm_span(
                        input=user_input,
                        output=response_content,
                        model="gpt-3.5-turbo",
                        temperature=0.7,
                        num_input_tokens=completion.usage.prompt_tokens if completion.usage else None,
                        num_output_tokens=completion.usage.completion_tokens if completion.usage else None,
                        total_tokens=completion.usage.total_tokens if completion.usage else None
                    )
                    logger.info(f"✅ LLM span added")
                    
                    # Conclude the trace
                    self.galileo_logger.conclude(output=response_content)
                    logger.info(f"✅ Trace concluded")
                    
                    # Flush to send to Galileo
                    logger.info(f"📤 Flushing to Galileo...")
                    flush_result = self.galileo_logger.flush()
                    logger.info(f"📤 Flush completed: {len(flush_result)} traces sent")
                    
                    metadata["galileo_logged"] = True
                    metadata["galileo_trace_id"] = str(trace.id) if hasattr(trace, 'id') else None
                    metadata["traces_sent"] = len(flush_result)
                    logger.info(f"✅ Galileo logging completed: {len(flush_result)} traces sent for session {session_id}")
                    
                except Exception as log_error:
                    logger.error(f"❌ Galileo logging failed: {log_error}")
                    logger.error(f"❌ Error details: {type(log_error).__name__}: {str(log_error)}")
                    import traceback
                    logger.error(f"❌ Full traceback: {traceback.format_exc()}")
                    metadata["galileo_logged"] = False
                
            except Exception as e:
                logger.warning(f"⚠️ Galileo evaluation failed: {e}")
                logger.info("🔄 Falling back to standard OpenAI call")
                
                # Fallback to standard OpenAI call
                completion = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1200
                )
                metadata["galileo_fallback"] = True
        else:
            # Standard OpenAI call when Galileo not available
            logger.info(f"🤖 Standard OpenAI call for session {session_id}")
            completion = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1200
            )
        
        # Parse response text
        response_text = completion.choices[0].message.content
        thoughts, response = self._parse_thinking_response(response_text)
        
        # Add basic self-evaluation if no Galileo scores
        if not metadata["evaluation_scores"]:
            metadata["self_evaluation"] = self._create_basic_evaluation(
                user_input, thoughts, response
            )
            logger.info("📝 Added basic self-evaluation metrics")
        
        logger.info(f"✅ Response generated for session {session_id}")
        return thoughts, response, metadata
    
    def _parse_thinking_response(self, response_text: str) -> Tuple[str, str]:
        """
        Parse AI response to extract thinking and final answer.
        
        Args:
            response_text: Raw AI response
            
        Returns:
            Tuple of (thoughts, response)
        """
        if "<think>" in response_text and "</think>" in response_text:
            parts = response_text.split("</think>")
            thoughts = parts[0].replace("<think>", "").strip()
            response = parts[1].strip() if len(parts) > 1 else ""
        else:
            # Fallback: create basic reasoning note
            thoughts = f"Processing user query: {response_text[:100]}..."
            response = response_text.strip()
        
        return thoughts, response
    
    def _create_basic_evaluation(
        self, 
        user_input: str, 
        thoughts: str, 
        response: str
    ) -> Dict[str, Any]:
        """
        Create basic evaluation metrics when Galileo unavailable.
        
        Args:
            user_input: Original user question
            thoughts: AI reasoning process
            response: Final AI response
            
        Returns:
            Dictionary of basic evaluation metrics
        """
        # Simple heuristic-based evaluation
        reasoning_words = len(thoughts.split())
        response_words = len(response.split())
        
        # Check for step-by-step reasoning indicators
        has_step_by_step = any(indicator in thoughts.lower() for indicator in [
            "step", "first", "then", "next", "finally", "therefore"
        ])
        
        # Check if response addresses the query
        query_words = set(user_input.lower().split()[:5])  # First 5 words of query
        response_words_set = set(response.lower().split())
        addresses_query = len(query_words.intersection(response_words_set)) > 0
        
        # Estimate quality based on length and structure
        quality_score = 0.5  # baseline
        if reasoning_words > 50:
            quality_score += 0.2
        if has_step_by_step:
            quality_score += 0.15
        if addresses_query:
            quality_score += 0.15
        quality_score = min(1.0, quality_score)
        
        return {
            "reasoning_words": reasoning_words,
            "response_words": response_words,
            "has_step_by_step": has_step_by_step,
            "addresses_query": addresses_query,
            "estimated_quality": "high" if quality_score > 0.8 else "medium" if quality_score > 0.6 else "low",
            "quality_score": quality_score,
            "evaluation_method": "basic_heuristics",
            "complexity_score": min(1.0, reasoning_words / 100.0)
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health status of all service components.
        
        Returns:
            Dictionary with health status information
        """
        health = {
            "openai_available": bool(self.openai_client),
            "galileo_available": GALILEO_AVAILABLE,
            "galileo_configured": self.galileo_enabled,
            "api_keys_present": {
                "openai": bool(os.getenv("OPENAI_API_KEY")),
                "galileo": bool(os.getenv("GALILEO_API_KEY"))
            },
            "service_ready": bool(self.openai_client),
            "evaluation_mode": "galileo" if self.galileo_enabled else "basic",
            "timestamp": datetime.now().isoformat()
        }
        
        return health


# Global service instance
_galileo_service = None

def get_galileo_service() -> GalileoService:
    """
    Get the global Galileo service instance (singleton pattern).
    
    Returns:
        GalileoService instance
    """
    global _galileo_service
    if _galileo_service is None:
        _galileo_service = GalileoService()
    return _galileo_service


# Backward compatibility function
def get_reasoning_response(user_input: str) -> Tuple[str, str]:
    """
    Backward compatible function matching the original deepseek.py interface.
    
    Args:
        user_input: User's question
        
    Returns:
        Tuple of (thoughts, response)
    """
    service = get_galileo_service()
    thoughts, response, metadata = service.get_reasoning_response_with_evaluation(user_input)
    return thoughts, response


if __name__ == "__main__":
    # Test the service
    service = get_galileo_service()
    
    print("🧪 Testing Galileo Service")
    print("=" * 50)
    
    # Health check
    health = service.health_check()
    print("Health Status:")
    for key, value in health.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 50)
    
    # Test evaluation
    test_input = "What is machine learning?"
    print(f"Test Input: {test_input}")
    
    thoughts, response, metadata = service.get_reasoning_response_with_evaluation(test_input)
    
    print(f"\nThoughts: {thoughts[:100]}...")
    print(f"Response: {response[:100]}...")
    print(f"Galileo Enabled: {metadata['galileo_enabled']}")
    print(f"Evaluation Scores: {len(metadata.get('evaluation_scores', {}))}")