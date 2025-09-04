"""
Real-Time Collaboration Service

Enables real-time collaborative editing of knowledge graphs using WebSocket connections.
Handles concurrent editing, conflict resolution, and live updates.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from flask_socketio import SocketIO, emit, join_room, leave_room
from services.auth_service import get_auth_service
import uuid

logger = logging.getLogger(__name__)

class CollaborationService:
    """Real-time collaboration service for knowledge graphs"""
    
    def __init__(self, socketio: SocketIO, kg_builder):
        self.socketio = socketio
        self.kg_builder = kg_builder
        self.auth_service = get_auth_service()
        
        # Track active sessions and users
        self.active_sessions: Dict[str, Set[str]] = {}  # graph_id -> set of user_ids
        self.user_sessions: Dict[str, str] = {}  # socket_id -> user_id
        self.graph_locks: Dict[str, Dict[str, Any]] = {}  # node_id -> lock_info
        
        # Register SocketIO handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect(auth):
            """Handle client connection"""
            try:
                # Authenticate user
                token = auth.get('token') if auth else None
                if not token:
                    return False  # Reject connection
                
                verification = self.auth_service.verify_token(token)
                if not verification['valid']:
                    return False
                
                user_id = verification['user_id']
                self.user_sessions[request.sid] = user_id
                
                logger.info(f"✅ User {verification['username']} connected via WebSocket")
                return True
                
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                return False
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            try:
                socket_id = request.sid
                if socket_id in self.user_sessions:
                    user_id = self.user_sessions[socket_id]
                    
                    # Remove user from all graph sessions
                    graphs_to_update = []
                    for graph_id, users in self.active_sessions.items():
                        if user_id in users:
                            users.remove(user_id)
                            graphs_to_update.append(graph_id)
                    
                    # Release any locks held by this user
                    locks_to_release = []
                    for node_id, lock_info in self.graph_locks.items():
                        if lock_info.get('user_id') == user_id:
                            locks_to_release.append(node_id)
                    
                    for node_id in locks_to_release:
                        del self.graph_locks[node_id]
                        # Notify others about lock release
                        for graph_id in graphs_to_update:
                            self.socketio.emit('node_unlocked', {
                                'node_id': node_id,
                                'user_id': user_id
                            }, room=f"graph_{graph_id}")
                    
                    del self.user_sessions[socket_id]
                    
                    # Notify remaining users about disconnection
                    for graph_id in graphs_to_update:
                        self.socketio.emit('user_left', {
                            'user_id': user_id,
                            'active_users': len(self.active_sessions[graph_id])
                        }, room=f"graph_{graph_id}")
                    
                    logger.info(f"🔌 User {user_id} disconnected")
                
            except Exception as e:
                logger.error(f"WebSocket disconnection error: {e}")
        
        @self.socketio.on('join_graph')
        def handle_join_graph(data):
            """Handle user joining a knowledge graph session"""
            try:
                socket_id = request.sid
                if socket_id not in self.user_sessions:
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                user_id = self.user_sessions[socket_id]
                graph_id = data.get('graph_id')
                
                if not graph_id:
                    emit('error', {'message': 'Graph ID required'})
                    return
                
                # Check user permissions
                permissions = self.auth_service.get_user_permissions(user_id)
                if graph_id not in permissions['read_access'] and '*' not in permissions['read_access']:
                    emit('error', {'message': 'Access denied to this graph'})
                    return
                
                # Add user to graph session
                if graph_id not in self.active_sessions:
                    self.active_sessions[graph_id] = set()
                
                self.active_sessions[graph_id].add(user_id)
                join_room(f"graph_{graph_id}")
                
                # Get user info
                with self.kg_builder.driver.session() as session:
                    user_info = session.run("""
                        MATCH (u:User {id: $user_id})
                        RETURN u.username as username, u.email as email
                    """, user_id=user_id).single()
                
                # Notify others about new user
                emit('user_joined', {
                    'user_id': user_id,
                    'username': user_info['username'] if user_info else 'Unknown',
                    'active_users': len(self.active_sessions[graph_id])
                }, room=f"graph_{graph_id}", include_self=False)
                
                # Send current active users to new user
                active_users = []
                for active_user_id in self.active_sessions[graph_id]:
                    if active_user_id != user_id:
                        with self.kg_builder.driver.session() as session:
                            user_data = session.run("""
                                MATCH (u:User {id: $user_id})
                                RETURN u.username as username
                            """, user_id=active_user_id).single()
                            
                            if user_data:
                                active_users.append({
                                    'user_id': active_user_id,
                                    'username': user_data['username']
                                })
                
                emit('graph_joined', {
                    'graph_id': graph_id,
                    'active_users': active_users,
                    'current_locks': [
                        {'node_id': node_id, 'user_id': lock_info['user_id'], 'locked_at': lock_info['locked_at']}
                        for node_id, lock_info in self.graph_locks.items()
                    ]
                })
                
                logger.info(f"👥 User {user_id} joined graph {graph_id}")
                
            except Exception as e:
                logger.error(f"Join graph error: {e}")
                emit('error', {'message': 'Failed to join graph'})
        
        @self.socketio.on('leave_graph')
        def handle_leave_graph(data):
            """Handle user leaving a knowledge graph session"""
            try:
                socket_id = request.sid
                if socket_id not in self.user_sessions:
                    return
                
                user_id = self.user_sessions[socket_id]
                graph_id = data.get('graph_id')
                
                if graph_id in self.active_sessions and user_id in self.active_sessions[graph_id]:
                    self.active_sessions[graph_id].remove(user_id)
                    leave_room(f"graph_{graph_id}")
                    
                    # Release any locks
                    locks_to_release = [
                        node_id for node_id, lock_info in self.graph_locks.items()
                        if lock_info.get('user_id') == user_id
                    ]
                    
                    for node_id in locks_to_release:
                        del self.graph_locks[node_id]
                        emit('node_unlocked', {
                            'node_id': node_id,
                            'user_id': user_id
                        }, room=f"graph_{graph_id}")
                    
                    # Notify others
                    emit('user_left', {
                        'user_id': user_id,
                        'active_users': len(self.active_sessions[graph_id])
                    }, room=f"graph_{graph_id}")
                
                logger.info(f"👋 User {user_id} left graph {graph_id}")
                
            except Exception as e:
                logger.error(f"Leave graph error: {e}")
        
        @self.socketio.on('lock_node')
        def handle_lock_node(data):
            """Handle node locking for editing"""
            try:
                socket_id = request.sid
                if socket_id not in self.user_sessions:
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                user_id = self.user_sessions[socket_id]
                node_id = data.get('node_id')
                graph_id = data.get('graph_id')
                
                if not node_id or not graph_id:
                    emit('error', {'message': 'Node ID and Graph ID required'})
                    return
                
                # Check write permissions
                permissions = self.auth_service.get_user_permissions(user_id)
                if graph_id not in permissions['write_access'] and '*' not in permissions['write_access']:
                    emit('error', {'message': 'Write access denied'})
                    return
                
                # Check if node is already locked
                if node_id in self.graph_locks:
                    existing_lock = self.graph_locks[node_id]
                    if existing_lock['user_id'] != user_id:
                        emit('lock_failed', {
                            'node_id': node_id,
                            'locked_by': existing_lock['user_id'],
                            'locked_at': existing_lock['locked_at']
                        })
                        return
                
                # Lock the node
                self.graph_locks[node_id] = {
                    'user_id': user_id,
                    'graph_id': graph_id,
                    'locked_at': datetime.utcnow().isoformat()
                }
                
                # Notify all users in the graph
                emit('node_locked', {
                    'node_id': node_id,
                    'user_id': user_id,
                    'locked_at': self.graph_locks[node_id]['locked_at']
                }, room=f"graph_{graph_id}")
                
                logger.info(f"🔒 Node {node_id} locked by user {user_id}")
                
            except Exception as e:
                logger.error(f"Node lock error: {e}")
                emit('error', {'message': 'Failed to lock node'})
        
        @self.socketio.on('unlock_node')
        def handle_unlock_node(data):
            """Handle node unlocking"""
            try:
                socket_id = request.sid
                if socket_id not in self.user_sessions:
                    return
                
                user_id = self.user_sessions[socket_id]
                node_id = data.get('node_id')
                graph_id = data.get('graph_id')
                
                # Check if user owns the lock
                if node_id in self.graph_locks and self.graph_locks[node_id]['user_id'] == user_id:
                    del self.graph_locks[node_id]
                    
                    # Notify all users
                    emit('node_unlocked', {
                        'node_id': node_id,
                        'user_id': user_id
                    }, room=f"graph_{graph_id}")
                    
                    logger.info(f"🔓 Node {node_id} unlocked by user {user_id}")
                
            except Exception as e:
                logger.error(f"Node unlock error: {e}")
        
        @self.socketio.on('node_update')
        def handle_node_update(data):
            """Handle real-time node updates"""
            try:
                socket_id = request.sid
                if socket_id not in self.user_sessions:
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                user_id = self.user_sessions[socket_id]
                node_id = data.get('node_id')
                graph_id = data.get('graph_id')
                updates = data.get('updates', {})
                
                # Check if user has the node locked
                if node_id not in self.graph_locks or self.graph_locks[node_id]['user_id'] != user_id:
                    emit('error', {'message': 'Node not locked by current user'})
                    return
                
                # Apply updates to database
                with self.kg_builder.driver.session() as session:
                    # Build update query
                    set_clauses = []
                    params = {'node_id': node_id}
                    
                    for key, value in updates.items():
                        if key in ['name', 'label', 'definition', 'confidence']:
                            set_clauses.append(f"n.{key} = ${key}")
                            params[key] = value
                    
                    if set_clauses:
                        query = f"""
                            MATCH (n) WHERE n.id = $node_id
                            SET {', '.join(set_clauses)},
                                n.last_modified = datetime(),
                                n.last_modified_by = $user_id
                            RETURN n
                        """
                        params['user_id'] = user_id
                        
                        result = session.run(query, params).single()
                        
                        if result:
                            # Broadcast update to all users except sender
                            emit('node_updated', {
                                'node_id': node_id,
                                'updates': updates,
                                'updated_by': user_id,
                                'timestamp': datetime.utcnow().isoformat()
                            }, room=f"graph_{graph_id}", include_self=False)
                            
                            logger.info(f"📝 Node {node_id} updated by user {user_id}")
                
            except Exception as e:
                logger.error(f"Node update error: {e}")
                emit('error', {'message': 'Failed to update node'})
        
        @self.socketio.on('cursor_position')
        def handle_cursor_position(data):
            """Handle cursor position sharing"""
            try:
                socket_id = request.sid
                if socket_id not in self.user_sessions:
                    return
                
                user_id = self.user_sessions[socket_id]
                graph_id = data.get('graph_id')
                position = data.get('position', {})
                
                # Broadcast cursor position to other users
                emit('cursor_moved', {
                    'user_id': user_id,
                    'position': position,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=f"graph_{graph_id}", include_self=False)
                
            except Exception as e:
                logger.error(f"Cursor position error: {e}")
    
    def broadcast_graph_change(self, graph_id: str, change_type: str, change_data: Dict[str, Any]):
        """Broadcast graph changes to all connected users"""
        try:
            self.socketio.emit('graph_changed', {
                'graph_id': graph_id,
                'change_type': change_type,  # 'node_added', 'node_deleted', 'relationship_added', etc.
                'change_data': change_data,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"graph_{graph_id}")
            
            logger.info(f"📡 Graph change broadcast: {change_type} in {graph_id}")
            
        except Exception as e:
            logger.error(f"Graph change broadcast error: {e}")
    
    def get_active_users(self, graph_id: str) -> List[Dict[str, Any]]:
        """Get list of active users for a graph"""
        try:
            if graph_id not in self.active_sessions:
                return []
            
            active_users = []
            for user_id in self.active_sessions[graph_id]:
                with self.kg_builder.driver.session() as session:
                    user_info = session.run("""
                        MATCH (u:User {id: $user_id})
                        RETURN u.username as username, u.email as email
                    """, user_id=user_id).single()
                    
                    if user_info:
                        active_users.append({
                            'user_id': user_id,
                            'username': user_info['username'],
                            'email': user_info['email']
                        })
            
            return active_users
            
        except Exception as e:
            logger.error(f"Get active users error: {e}")
            return []


# Global service instance
_collaboration_service = None

def get_collaboration_service(socketio=None, kg_builder=None):
    """Get the global collaboration service instance"""
    global _collaboration_service
    if _collaboration_service is None and socketio and kg_builder:
        _collaboration_service = CollaborationService(socketio, kg_builder)
    return _collaboration_service


# Export
__all__ = ['CollaborationService', 'get_collaboration_service']