"""
Galileo AI Integration for Thinking-Graph
Provides comprehensive monitoring, evaluation, and analytics for AI interactions
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

try:
    from galileo import galileo_context, log
    GALILEO_AVAILABLE = True
except ImportError:
    GALILEO_AVAILABLE = False
    print("Galileo SDK not available. Install with: pip install galileo")

class GalileoMonitor:
    """
    Galileo AI monitoring and evaluation service for thinking-graph
    """
    
    def __init__(self):
        self.galileo_api_key = os.getenv('GALILEO_API_KEY')
        self.galileo_console_url = os.getenv('GALILEO_CONSOLE_URL', 'https://app.galileo.ai')
        self.project_name = os.getenv('GALILEO_PROJECT', 'thinking-graph')
        self.run_name = f"thinking-graph-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Metrics storage for when Galileo is not available
        self.local_metrics = {
            'chat_interactions': [],
            'reasoning_evaluations': [],
            'knowledge_graph_updates': [],
            'system_metrics': {}
        }
        
        self.setup_logging()
        
        if GALILEO_AVAILABLE and self.galileo_api_key:
            self.initialize_galileo()
        else:
            print("Running in local metrics mode - Galileo integration disabled")
            self.galileo_initialized = False
    
    def setup_logging(self):
        """Setup logging for Galileo monitoring"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def initialize_galileo(self):
        """Initialize Galileo monitoring via SDK"""
        try:
            # Set environment variables for Galileo SDK
            os.environ['GALILEO_API_KEY'] = self.galileo_api_key
            os.environ['GALILEO_PROJECT'] = self.project_name
            
            # Initialize Galileo context
            galileo_context.init()
            
            self.logger.info(f"Galileo initialized for project: {self.project_name}")
            self.galileo_initialized = True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Galileo: {e}")
            self.galileo_initialized = False
    
    @log
    def log_interaction_to_galileo(self, user_input: str, ai_response: str, metadata: dict = None):
        """Log interaction using Galileo SDK decorator"""
        # This function will be automatically logged by the @log decorator
        return {
            'input': user_input,
            'output': ai_response,
            'metadata': metadata or {}
        }
    
    def log_chat_interaction(self, 
                           user_input: str, 
                           ai_response: str, 
                           reasoning: str,
                           session_id: str,
                           model_name: str = "gpt-3.5-turbo",
                           metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Log chat interaction with comprehensive metrics
        """
        interaction_data = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'user_input': user_input,
            'ai_response': ai_response,
            'reasoning': reasoning,
            'model_name': model_name,
            'input_length': len(user_input),
            'response_length': len(ai_response),
            'reasoning_length': len(reasoning),
            'metadata': metadata or {}
        }
        
        # Store locally
        self.local_metrics['chat_interactions'].append(interaction_data)
        
        if self.galileo_initialized:
            try:
                # Log to Galileo using SDK
                galileo_metadata = {
                    'session_id': session_id,
                    'model': model_name,
                    'reasoning': reasoning,
                    'reasoning_length': len(reasoning),
                    'input_length': len(user_input),
                    'response_length': len(ai_response),
                    'timestamp': interaction_data['timestamp'],
                    **metadata
                }
                
                # Use the Galileo decorator function to log the interaction
                self.log_interaction_to_galileo(user_input, ai_response, galileo_metadata)
                self.logger.info("Successfully logged interaction to Galileo")
                
                # Log reasoning quality metrics
                self._evaluate_reasoning_quality(reasoning, user_input, ai_response)
                
            except Exception as e:
                self.logger.error(f"Failed to log to Galileo: {e}")
        
        return interaction_data
    
    def _evaluate_reasoning_quality(self, reasoning: str, user_input: str, ai_response: str):
        """Evaluate reasoning quality using various metrics"""
        
        # Calculate reasoning metrics
        reasoning_metrics = {
            'coherence_score': self._calculate_coherence(reasoning),
            'completeness_score': self._calculate_completeness(reasoning, user_input),
            'clarity_score': self._calculate_clarity(reasoning),
            'relevance_score': self._calculate_relevance(reasoning, user_input),
            'reasoning_steps': self._count_reasoning_steps(reasoning)
        }
        
        # Store locally
        evaluation_data = {
            'timestamp': datetime.now().isoformat(),
            'reasoning': reasoning,
            'metrics': reasoning_metrics
        }
        self.local_metrics['reasoning_evaluations'].append(evaluation_data)
        
        # Note: Custom metrics logging can be enhanced with Galileo SDK's metric logging capabilities
        # For now, we store locally and the main interaction logging captures the quality assessment
    
    def _calculate_coherence(self, reasoning: str) -> float:
        """Calculate coherence score based on logical flow"""
        # Simple coherence calculation based on transition words and structure
        transition_words = ['therefore', 'because', 'since', 'thus', 'consequently', 
                          'however', 'moreover', 'furthermore', 'additionally']
        
        sentences = reasoning.split('.')
        if len(sentences) <= 1:
            return 0.5
        
        transition_count = sum(1 for word in transition_words 
                             if word.lower() in reasoning.lower())
        
        # Normalize by sentence count
        coherence = min(transition_count / max(len(sentences) - 1, 1), 1.0)
        return round(coherence, 2)
    
    def _calculate_completeness(self, reasoning: str, user_input: str) -> float:
        """Calculate completeness score based on coverage of input topics"""
        # Extract key terms from user input
        user_words = set(word.lower() for word in user_input.split() 
                        if len(word) > 3)
        reasoning_words = set(word.lower() for word in reasoning.split())
        
        if not user_words:
            return 1.0
        
        coverage = len(user_words & reasoning_words) / len(user_words)
        return round(coverage, 2)
    
    def _calculate_clarity(self, reasoning: str) -> float:
        """Calculate clarity score based on sentence structure and complexity"""
        sentences = [s.strip() for s in reasoning.split('.') if s.strip()]
        if not sentences:
            return 0.0
        
        # Average sentence length (shorter is clearer)
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        # Penalize very long or very short sentences
        clarity = max(0, 1 - abs(avg_length - 15) / 20)
        return round(clarity, 2)
    
    def _calculate_relevance(self, reasoning: str, user_input: str) -> float:
        """Calculate relevance score based on topic similarity"""
        # Simple relevance based on common words
        user_words = set(user_input.lower().split())
        reasoning_words = set(reasoning.lower().split())
        
        if not user_words:
            return 1.0
        
        common_words = user_words & reasoning_words
        relevance = len(common_words) / len(user_words | reasoning_words)
        return round(relevance, 2)
    
    def _count_reasoning_steps(self, reasoning: str) -> int:
        """Count number of reasoning steps"""
        # Count sentences as reasoning steps
        steps = len([s for s in reasoning.split('.') if s.strip()])
        return max(steps, 1)
    
    def log_knowledge_graph_update(self, 
                                 session_id: str,
                                 nodes_added: int,
                                 relationships_added: int,
                                 thinking_text: str,
                                 extraction_success: bool):
        """Log knowledge graph updates"""
        
        kg_data = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'nodes_added': nodes_added,
            'relationships_added': relationships_added,
            'thinking_text_length': len(thinking_text),
            'extraction_success': extraction_success
        }
        
        self.local_metrics['knowledge_graph_updates'].append(kg_data)
        
        # Knowledge graph metrics are stored locally for analysis
    
    def log_system_metrics(self, 
                          response_time: float,
                          model_name: str,
                          tokens_used: Optional[int] = None,
                          error_occurred: bool = False):
        """Log system performance metrics"""
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'response_time': response_time,
            'model_name': model_name,
            'tokens_used': tokens_used,
            'error_occurred': error_occurred
        }
        
        self.local_metrics['system_metrics'][datetime.now().isoformat()] = metrics
        
        # System metrics are stored locally for performance monitoring
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary"""
        
        total_interactions = len(self.local_metrics['chat_interactions'])
        total_kg_updates = len(self.local_metrics['knowledge_graph_updates'])
        
        # Calculate averages from local metrics
        avg_response_length = 0
        avg_reasoning_length = 0
        if total_interactions > 0:
            avg_response_length = sum(
                len(interaction['ai_response']) 
                for interaction in self.local_metrics['chat_interactions']
            ) / total_interactions
            
            avg_reasoning_length = sum(
                len(interaction['reasoning']) 
                for interaction in self.local_metrics['chat_interactions']
            ) / total_interactions
        
        # Reasoning quality averages
        avg_reasoning_quality = {}
        if self.local_metrics['reasoning_evaluations']:
            all_metrics = [eval_data['metrics'] for eval_data in self.local_metrics['reasoning_evaluations']]
            avg_reasoning_quality = {
                'avg_coherence': round(sum(m['coherence_score'] for m in all_metrics) / len(all_metrics), 2),
                'avg_completeness': round(sum(m['completeness_score'] for m in all_metrics) / len(all_metrics), 2),
                'avg_clarity': round(sum(m['clarity_score'] for m in all_metrics) / len(all_metrics), 2),
                'avg_relevance': round(sum(m['relevance_score'] for m in all_metrics) / len(all_metrics), 2),
                'avg_reasoning_steps': round(sum(m['reasoning_steps'] for m in all_metrics) / len(all_metrics), 2)
            }
        
        return {
            'total_interactions': total_interactions,
            'total_kg_updates': total_kg_updates,
            'avg_response_length': round(avg_response_length, 2),
            'avg_reasoning_length': round(avg_reasoning_length, 2),
            'reasoning_quality': avg_reasoning_quality,
            'galileo_enabled': self.galileo_initialized,
            'run_name': self.run_name,
            'console_url': f"{self.galileo_console_url}/project/{self.project_name}" if self.galileo_initialized else None
        }
    
    def finalize_session(self):
        """Finalize Galileo session"""
        if self.galileo_initialized:
            try:
                # Flush remaining logs to Galileo
                galileo_context.flush()
                self.logger.info("Galileo session finalized")
                    
            except Exception as e:
                self.logger.error(f"Failed to finalize Galileo session: {e}")

# Global Galileo monitor instance
galileo_monitor = None

def get_galileo_monitor() -> GalileoMonitor:
    """Get or create Galileo monitor instance"""
    global galileo_monitor
    if galileo_monitor is None:
        galileo_monitor = GalileoMonitor()
    return galileo_monitor
