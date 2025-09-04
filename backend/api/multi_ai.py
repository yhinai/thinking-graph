"""
Multi-AI Provider API endpoints
"""

from flask import Blueprint, request, jsonify
from services.multi_ai_service import get_multi_ai_service
from services.auth_service import require_auth
import logging

logger = logging.getLogger(__name__)

def register_multi_ai_routes(app):
    """Register multi-AI provider routes with the Flask app"""
    
    multi_ai_service = get_multi_ai_service()
    
    @app.route('/api/ai/providers', methods=['GET'])
    def get_providers():
        """Get list of available AI providers"""
        try:
            providers = multi_ai_service.get_available_providers()
            health = multi_ai_service.health_check()
            
            return jsonify({
                'success': True,
                'providers': providers,
                'health': health
            })
            
        except Exception as e:
            logger.error(f"Get providers error: {e}")
            return jsonify({'error': 'Failed to get providers'}), 500
    
    @app.route('/api/ai/chat', methods=['POST'])
    @require_auth
    def ai_chat():
        """Get AI response from specified provider"""
        try:
            data = request.get_json()
            
            user_input = data.get('message', '')
            provider = data.get('provider')  # Optional
            model = data.get('model')  # Optional
            temperature = data.get('temperature', 0.7)
            max_tokens = data.get('max_tokens')
            
            if not user_input:
                return jsonify({'error': 'message is required'}), 400
            
            thoughts, response, metadata = multi_ai_service.get_reasoning_response(
                user_input, provider, model, temperature, max_tokens
            )
            
            return jsonify({
                'success': True,
                'thoughts': thoughts,
                'response': response,
                'metadata': metadata
            })
            
        except Exception as e:
            logger.error(f"AI chat error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/ai/compare', methods=['POST'])
    @require_auth
    def compare_providers():
        """Compare responses from multiple AI providers"""
        try:
            data = request.get_json()
            
            user_input = data.get('message', '')
            providers = data.get('providers')  # Optional list
            
            if not user_input:
                return jsonify({'error': 'message is required'}), 400
            
            comparison = multi_ai_service.compare_responses(user_input, providers)
            
            return jsonify({
                'success': True,
                'comparison': comparison
            })
            
        except Exception as e:
            logger.error(f"Provider comparison error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/ai/best-response', methods=['POST'])
    @require_auth
    def get_best_response():
        """Get the best response using ensemble method"""
        try:
            data = request.get_json()
            
            user_input = data.get('message', '')
            providers = data.get('providers')  # Optional list
            
            if not user_input:
                return jsonify({'error': 'message is required'}), 400
            
            thoughts, response, metadata = multi_ai_service.get_best_response(user_input, providers)
            
            return jsonify({
                'success': True,
                'thoughts': thoughts,
                'response': response,
                'metadata': metadata
            })
            
        except Exception as e:
            logger.error(f"Best response error: {e}")
            return jsonify({'error': str(e)}), 500
    
    logger.info("✅ Multi-AI provider routes registered successfully")

# Export
__all__ = ['register_multi_ai_routes']