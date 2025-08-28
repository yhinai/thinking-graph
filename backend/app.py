from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
from kgbuilder import AgentThinkingKG
from services.galileo_service import get_galileo_service
from dotenv import load_dotenv

# Load environment variables from parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'kg_system_initialized': kg_system is not None,
        'galileo_service': galileo_health
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
    """Get knowledge graph data for visualization"""
    try:
        if not kg_system:
            return jsonify({'error': 'Knowledge graph system not initialized'}), 500
        
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
        
        return jsonify({
            'nodes': nodes,
            'links': links
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get all sessions in the knowledge graph"""
    try:
        if not kg_system:
            return jsonify({'error': 'Knowledge graph system not initialized'}), 500
        
        sessions = kg_system.get_session_info()
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
    """Get reasoning patterns analysis"""
    try:
        if not kg_system:
            return jsonify({'error': 'Knowledge graph system not initialized'}), 500
        
        patterns = kg_system.analyze_patterns()
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
    
    # Get port from environment variable or default to 8000
    port = int(os.environ.get('BACKEND_PORT', os.environ.get('PORT', 8000)))
    
    # Use Waitress production server
    try:
        from waitress import serve
        print(f" * Running on all addresses (0.0.0.0)")
        print(f" * Running on http://127.0.0.1:{port}")
        print(f" * Running on http://192.0.0.2:{port}")
        print(f" * Production server starting on port {port}")
        serve(app, host='0.0.0.0', port=port)
    except ImportError:
        print("Waitress not installed, falling back to Flask dev server")
        app.run(debug=False, host='0.0.0.0', port=port)