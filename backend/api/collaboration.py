"""
Collaboration API endpoints for real-time features
"""

from flask import Blueprint, request, jsonify
from services.collaboration_service import get_collaboration_service
from services.auth_service import require_auth
import logging

logger = logging.getLogger(__name__)

def register_collaboration_routes(app, socketio, kg_system):
    """Register collaboration routes with the Flask app"""
    
    # Initialize collaboration service
    collaboration_service = get_collaboration_service(socketio, kg_system.kg_builder if kg_system else None)
    
    if not collaboration_service:
        logger.warning("⚠️ Collaboration service not available - collaboration routes disabled")
        return
    
    @app.route('/api/collaboration/graphs/<graph_id>/active-users', methods=['GET'])
    @require_auth
    def get_active_users(graph_id):
        """Get list of active users for a graph"""
        try:
            active_users = collaboration_service.get_active_users(graph_id)
            
            return jsonify({
                'success': True,
                'graph_id': graph_id,
                'active_users': active_users,
                'count': len(active_users)
            })
            
        except Exception as e:
            logger.error(f"Get active users error: {e}")
            return jsonify({'error': 'Failed to get active users'}), 500
    
    @app.route('/api/collaboration/broadcast', methods=['POST'])
    @require_auth
    def broadcast_change():
        """Broadcast a graph change to all connected users"""
        try:
            data = request.get_json()
            
            graph_id = data.get('graph_id')
            change_type = data.get('change_type')
            change_data = data.get('change_data', {})
            
            if not graph_id or not change_type:
                return jsonify({'error': 'graph_id and change_type are required'}), 400
            
            collaboration_service.broadcast_graph_change(graph_id, change_type, change_data)
            
            return jsonify({
                'success': True,
                'message': 'Change broadcasted successfully'
            })
            
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            return jsonify({'error': 'Failed to broadcast change'}), 500
    
    logger.info("✅ Collaboration routes registered successfully")

# Export
__all__ = ['register_collaboration_routes']