from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import os
import json
from datetime import datetime
from kgbuilder import AgentThinkingKG
from services.galileo_service import get_galileo_service
from services.cache_service import cache_service
from services.auth_service import get_auth_service
from services.collaboration_service import get_collaboration_service
from services.multi_ai_service import get_multi_ai_service
from services.export_import_service import get_export_import_service
from api.node_details import register_node_details_routes
from api.search import register_search_routes, initialize_search_system
from api.analytics import register_analytics_routes
from api.auth import register_auth_routes
from api.collaboration import register_collaboration_routes
from api.multi_ai import register_multi_ai_routes
from api.export_import import register_export_import_routes
from dotenv import load_dotenv

# Load environment variables from parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize SocketIO for real-time collaboration
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize the knowledge graph system
kg_system = None

def init_kg_system():
    """Initialize the knowledge graph system"""
    global kg_system
    try:
        kg_system = AgentThinkingKG()
        print("Knowledge graph system initialized successfully")
    except Exception as e:
        print(f"Failed to initialize knowledge graph system: {e}")
        print("Running in simplified mode without knowledge graph")
        kg_system = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Get Galileo service health
    galileo_service = get_galileo_service()
    galileo_health = galileo_service.health_check()
    
    # Get cache service health
    cache_health = cache_service.health_check()
    cache_stats = cache_service.get_stats()
    
    # Get auth service health
    auth_service = get_auth_service()
    auth_health = auth_service.health_check() if auth_service else {'available': False}
    
    # Get multi-AI service health
    multi_ai_service = get_multi_ai_service()
    ai_health = multi_ai_service.health_check()
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'kg_system_initialized': kg_system is not None,
        'phase_3_features': {
            'authentication': auth_service is not None,
            'collaboration': get_collaboration_service() is not None,
            'multi_ai': True,
            'export_import': get_export_import_service() is not None
        },
        'galileo_service': galileo_health,
        'cache_service': {
            'health': cache_health,
            'stats': cache_stats
        },
        'auth_service': auth_health,
        'multi_ai_service': ai_health
    })

@app.route('/api/chat', methods=['POST'])
def chat_with_agent():
    """Chat with the agent and process the response"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id')
        
        if not user_message:
            return jsonify({'error': 'message is required'}), 400
        
        # Get response from the agent with Galileo evaluation
        galileo_service = get_galileo_service()
        thoughts, response, evaluation_metadata = galileo_service.get_reasoning_response_with_evaluation(
            user_message, session_id
        )
        
        # Process the agent's thinking into the knowledge graph (if available)
        result_session_id = session_id
        if kg_system:
            try:
                result_session_id = kg_system.process_thinking(thoughts, session_id)
                
                # Invalidate relevant caches when graph changes
                cache_service.delete('graph_data*')
                cache_service.delete(f'node_details:*')
                cache_service.delete('sessions*')
                cache_service.delete('patterns*')
            except Exception as e:
                print(f"Warning: Failed to process thinking in KG: {e}")
                # Continue without KG processing
        
        return jsonify({
            'success': True,
            'session_id': result_session_id,
            'thoughts': thoughts,
            'response': response,
            'message': 'Chat processed successfully',
            'kg_enabled': kg_system is not None,
            'evaluation': {
                'galileo_enabled': evaluation_metadata.get('galileo_enabled', False),
                'evaluation_scores': evaluation_metadata.get('evaluation_scores', {}),
                'evaluation_feedback': evaluation_metadata.get('evaluation_feedback', {}),
                'self_evaluation': evaluation_metadata.get('self_evaluation', {}),
                'galileo_trace_id': evaluation_metadata.get('galileo_trace_id'),
                'service_version': evaluation_metadata.get('service_version', '1.0.0')
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-thinking', methods=['POST'])
def process_thinking():
    """Process thinking text and add to knowledge graph"""
    try:
        data = request.get_json()
        thinking_text = data.get('thinking_text', '')
        session_id = data.get('session_id')
        
        if not thinking_text:
            return jsonify({'error': 'thinking_text is required'}), 400
        
        if not kg_system:
            return jsonify({'error': 'Knowledge graph system not initialized'}), 500
        
        # Process the thinking text
        result_session_id = kg_system.process_thinking(thinking_text, session_id)
        
        return jsonify({
            'success': True,
            'session_id': result_session_id,
            'message': 'Thinking processed successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/graph-data', methods=['GET'])
def get_graph_data():
    """Get knowledge graph data for visualization with caching"""
    try:
        if not kg_system:
            return jsonify({'error': 'Knowledge graph system not initialized'}), 500
        
        # Check cache first
        cache_key = cache_service.generate_key('graph_data')
        cached_data = cache_service.get(cache_key)
        if cached_data:
            return jsonify(cached_data)
        
        # Get fresh data
        graph_data = kg_system.get_full_graph_data()
        
        # Transform the data for 3d-force-graph format
        nodes = []
        links = []
        
        for node in graph_data['nodes']:
            nodes.append({
                'id': node['id'],
                'name': node['label'],
                'type': node['type'],
                'val': 10 if node['type'] == 'Session' else 5,  # Size based on type
                'color': get_node_color(node['type'])
            })
        
        for link in graph_data['links']:
            links.append({
                'source': link['source'],
                'target': link['target'],
                'type': link['type'],
                'value': link.get('strength', 1.0)
            })
        
        response_data = {
            'nodes': nodes,
            'links': links
        }
        
        # Cache the processed data for 5 minutes
        cache_service.set(cache_key, response_data, ttl=300)
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get all sessions in the knowledge graph with caching"""
    try:
        if not kg_system:
            return jsonify({'error': 'Knowledge graph system not initialized'}), 500
        
        # Check cache first
        cache_key = cache_service.generate_key('sessions')
        cached_sessions = cache_service.get(cache_key)
        if cached_sessions:
            return jsonify({'sessions': cached_sessions})
        
        sessions = kg_system.get_session_info()
        
        # Cache sessions for 10 minutes
        cache_service.set(cache_key, sessions, ttl=600)
        
        return jsonify({'sessions': sessions})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<session_id>', methods=['GET'])
def get_session_details(session_id):
    """Get detailed information about a specific session"""
    try:
        if not kg_system:
            return jsonify({'error': 'Knowledge graph system not initialized'}), 500
        
        session_info = kg_system.get_session_info(session_id)
        return jsonify({'session': session_info})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/patterns', methods=['GET'])
def get_patterns():
    """Get reasoning patterns analysis with caching"""
    try:
        if not kg_system:
            return jsonify({'error': 'Knowledge graph system not initialized'}), 500
        
        # Check cache first
        cache_key = cache_service.generate_key('patterns')
        cached_patterns = cache_service.get(cache_key)
        if cached_patterns:
            return jsonify(cached_patterns)
        
        patterns = kg_system.analyze_patterns()
        
        # Cache patterns for 15 minutes (expensive operation)
        cache_service.set(cache_key, patterns, ttl=900)
        
        return jsonify(patterns)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-database', methods=['DELETE'])
def clear_database():
    """Clear all data from the knowledge graph (use with caution)"""
    try:
        if not kg_system:
            return jsonify({'error': 'Knowledge graph system not initialized'}), 500
        
        kg_system.clear_database()
        return jsonify({'success': True, 'message': 'Database cleared successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_node_color(node_type):
    """Get color for different node types"""
    color_map = {
        'Session': '#4A90E2',
        'Thought': '#357ABD', 
        'Entity': '#50C878',
        'Tool': '#FF6B6B',
        'unknown': '#888888'
    }
    return color_map.get(node_type, '#888888')

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize the knowledge graph system
    init_kg_system()
    
    # Set up context-aware conversations
    if kg_system:
        galileo_service = get_galileo_service()
        galileo_service.set_knowledge_graph(kg_system)
    
    # Initialize Phase 3 services
    auth_service = get_auth_service(kg_system.kg_builder if kg_system else None)
    collaboration_service = get_collaboration_service(socketio, kg_system.kg_builder if kg_system else None)
    multi_ai_service = get_multi_ai_service()
    export_import_service = get_export_import_service(kg_system.kg_builder if kg_system else None)
    
    print("✅ Phase 3 services initialized:")
    print(f"  - Authentication: {'✅' if auth_service else '❌'}")
    print(f"  - Real-time Collaboration: {'✅' if collaboration_service else '❌'}")
    print(f"  - Multi-AI Providers: {'✅' if multi_ai_service else '❌'}")
    print(f"  - Export/Import: {'✅' if export_import_service else '❌'}")
    
    # Register all API routes
    register_node_details_routes(app, kg_system)
    register_search_routes(app, kg_system)
    register_analytics_routes(app, kg_system)
    
    # Phase 3 routes
    register_auth_routes(app, kg_system)
    register_collaboration_routes(app, socketio, kg_system)
    register_multi_ai_routes(app)
    register_export_import_routes(app, kg_system)
    
    # Initialize search system
    initialize_search_system(kg_system)
    
    # Get port from environment variable or default to 8000
    port = int(os.environ.get('BACKEND_PORT', os.environ.get('PORT', 8000)))
    
    # Use SocketIO server for real-time features
    print(f" * VizBrain Knowledge Graph Server")
    print(f" * Phase 3 Features: Multi-user, Collaboration, Advanced AI")
    print(f" * Running on all addresses (0.0.0.0)")
    print(f" * Running on http://127.0.0.1:{port}")
    print(f" * Running on http://192.0.0.2:{port}")
    print(f" * WebSocket support enabled for real-time collaboration")
    print(f" * Server starting on port {port}")
    
    # Use SocketIO's run method which handles both HTTP and WebSocket
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)