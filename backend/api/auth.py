"""
Authentication API endpoints
"""

from flask import Blueprint, request, jsonify
from services.auth_service import get_auth_service, require_auth, require_role
import logging

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__)

def register_auth_routes(app, kg_system):
    """Register authentication routes with the Flask app"""
    
    # Initialize auth service
    auth_service = get_auth_service(kg_system.kg_builder if kg_system else None)
    
    if not auth_service:
        logger.warning("⚠️ Authentication service not available - auth routes disabled")
        return
    
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        """Register a new user"""
        try:
            data = request.get_json()
            
            email = data.get('email', '').strip().lower()
            username = data.get('username', '').strip()
            password = data.get('password', '')
            role = data.get('role', 'user')  # Default to user role
            
            # Admin role can only be assigned by existing admin
            if role == 'admin':
                # Check if request has admin token
                token = request.headers.get('Authorization', '').replace('Bearer ', '')
                if token:
                    verification = auth_service.verify_token(token)
                    if not verification.get('valid') or verification.get('role') != 'admin':
                        role = 'user'  # Downgrade to user if not admin
                else:
                    role = 'user'
            
            result = auth_service.register_user(email, username, password, role)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': result['message'],
                    'user_id': result['user_id']
                })
            else:
                return jsonify({'error': result['error']}), 400
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return jsonify({'error': 'Registration failed'}), 500
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """Authenticate user and return JWT token"""
        try:
            data = request.get_json()
            
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            
            result = auth_service.authenticate_user(email, password)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'token': result['token'],
                    'user': result['user'],
                    'expires_in': result['expires_in']
                })
            else:
                return jsonify({'error': result['error']}), 401
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({'error': 'Authentication failed'}), 500
    
    @app.route('/api/auth/verify', methods=['GET'])
    @require_auth
    def verify_token():
        """Verify JWT token and return user info"""
        try:
            return jsonify({
                'valid': True,
                'user': {
                    'id': request.current_user['user_id'],
                    'email': request.current_user['email'],
                    'username': request.current_user['username'],
                    'role': request.current_user['role']
                }
            })
            
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return jsonify({'error': 'Token verification failed'}), 500
    
    @app.route('/api/auth/permissions', methods=['GET'])
    @require_auth
    def get_permissions():
        """Get user permissions for knowledge graphs"""
        try:
            user_id = request.current_user['user_id']
            permissions = auth_service.get_user_permissions(user_id)
            
            return jsonify({
                'success': True,
                'permissions': permissions
            })
            
        except Exception as e:
            logger.error(f"Permissions error: {e}")
            return jsonify({'error': 'Failed to get permissions'}), 500
    
    @app.route('/api/graphs', methods=['POST'])
    @require_auth
    def create_knowledge_graph():
        """Create a new shared knowledge graph"""
        try:
            data = request.get_json()
            
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            
            if not name:
                return jsonify({'error': 'Graph name is required'}), 400
            
            user_id = request.current_user['user_id']
            result = auth_service.create_shared_graph(user_id, name, description)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': result['message'],
                    'graph_id': result['graph_id']
                })
            else:
                return jsonify({'error': result['error']}), 500
                
        except Exception as e:
            logger.error(f"Graph creation error: {e}")
            return jsonify({'error': 'Failed to create knowledge graph'}), 500
    
    @app.route('/api/graphs/<graph_id>/access', methods=['POST'])
    @require_auth
    def grant_graph_access(graph_id):
        """Grant user access to a knowledge graph"""
        try:
            data = request.get_json()
            
            user_email = data.get('user_email', '').strip().lower()
            permission = data.get('permission', 'read')
            
            if not user_email:
                return jsonify({'error': 'User email is required'}), 400
            
            if permission not in ['read', 'write', 'admin']:
                return jsonify({'error': 'Invalid permission type'}), 400
            
            # Get user ID from email
            with kg_system.kg_builder.driver.session() as session:
                user_record = session.run("""
                    MATCH (u:User {email: $email})
                    RETURN u.id as user_id
                """, email=user_email).single()
                
                if not user_record:
                    return jsonify({'error': 'User not found'}), 404
                
                target_user_id = user_record['user_id']
            
            # Check if current user has admin access to this graph
            current_user_id = request.current_user['user_id']
            permissions = auth_service.get_user_permissions(current_user_id)
            
            if graph_id not in permissions['admin_access'] and '*' not in permissions['admin_access']:
                return jsonify({'error': 'You do not have admin access to this graph'}), 403
            
            result = auth_service.grant_graph_access(graph_id, target_user_id, permission)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': result['message']
                })
            else:
                return jsonify({'error': result['error']}), 500
                
        except Exception as e:
            logger.error(f"Access grant error: {e}")
            return jsonify({'error': 'Failed to grant access'}), 500
    
    @app.route('/api/graphs', methods=['GET'])
    @require_auth
    def list_accessible_graphs():
        """List all knowledge graphs accessible to the user"""
        try:
            user_id = request.current_user['user_id']
            user_role = request.current_user['role']
            
            with kg_system.kg_builder.driver.session() as session:
                if user_role == 'admin':
                    # Admin can see all graphs
                    graphs = session.run("""
                        MATCH (kg:KnowledgeGraph)
                        OPTIONAL MATCH (owner:User)-[:OWNS]->(kg)
                        RETURN kg.id as id, kg.name as name, kg.description as description,
                               kg.created_at as created_at, kg.is_public as is_public,
                               kg.node_count as node_count, kg.relationship_count as relationship_count,
                               owner.username as owner_username
                        ORDER BY kg.created_at DESC
                    """)
                else:
                    # Regular user sees only accessible graphs
                    graphs = session.run("""
                        MATCH (u:User {id: $user_id})
                        MATCH (kg:KnowledgeGraph)
                        WHERE (u)-[:OWNS]->(kg) OR (u)-[:HAS_ACCESS]->(kg) OR kg.is_public = true
                        OPTIONAL MATCH (owner:User)-[:OWNS]->(kg)
                        OPTIONAL MATCH (u)-[access:HAS_ACCESS]->(kg)
                        RETURN kg.id as id, kg.name as name, kg.description as description,
                               kg.created_at as created_at, kg.is_public as is_public,
                               kg.node_count as node_count, kg.relationship_count as relationship_count,
                               owner.username as owner_username,
                               CASE WHEN (u)-[:OWNS]->(kg) THEN 'owner'
                                    ELSE coalesce(access.permission, 'read') END as access_level
                        ORDER BY kg.created_at DESC
                    """, user_id=user_id)
                
                graph_list = []
                for record in graphs:
                    graph_list.append({
                        'id': record['id'],
                        'name': record['name'],
                        'description': record['description'],
                        'created_at': record['created_at'].isoformat() if record['created_at'] else None,
                        'is_public': record['is_public'],
                        'node_count': record['node_count'],
                        'relationship_count': record['relationship_count'],
                        'owner': record['owner_username'],
                        'access_level': record.get('access_level', 'read')
                    })
                
                return jsonify({
                    'success': True,
                    'graphs': graph_list
                })
                
        except Exception as e:
            logger.error(f"Graph listing error: {e}")
            return jsonify({'error': 'Failed to list graphs'}), 500
    
    logger.info("✅ Authentication routes registered successfully")

# Export
__all__ = ['register_auth_routes']