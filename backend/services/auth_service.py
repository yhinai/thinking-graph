"""
Authentication Service for Multi-User Knowledge Graph

Provides secure user authentication, authorization, and session management
for collaborative knowledge graph access.
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
from flask import request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication and authorization service"""
    
    def __init__(self, kg_builder):
        self.kg_builder = kg_builder
        self.secret_key = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
        self.token_expiry_hours = int(os.getenv('JWT_EXPIRY_HOURS', '24'))
        
        # Initialize user management in Neo4j
        self._init_user_schema()
    
    def _init_user_schema(self):
        """Initialize user management schema in Neo4j"""
        try:
            with self.kg_builder.driver.session() as session:
                # Create user nodes and indexes
                session.run("""
                    CREATE CONSTRAINT user_email_unique IF NOT EXISTS
                    FOR (u:User) REQUIRE u.email IS UNIQUE
                """)
                
                session.run("""
                    CREATE CONSTRAINT user_id_unique IF NOT EXISTS
                    FOR (u:User) REQUIRE u.id IS UNIQUE
                """)
                
                # Create default admin user if none exists
                admin_exists = session.run("""
                    MATCH (u:User {role: 'admin'})
                    RETURN count(u) as admin_count
                """).single()['admin_count']
                
                if admin_exists == 0:
                    admin_password = self._hash_password('admin123')
                    session.run("""
                        CREATE (u:User {
                            id: $user_id,
                            email: 'admin@vizbrain.ai',
                            username: 'admin',
                            password_hash: $password_hash,
                            role: 'admin',
                            created_at: datetime(),
                            last_login: null,
                            is_active: true
                        })
                    """, user_id=f"user_{secrets.token_hex(8)}", password_hash=admin_password)
                    
                    logger.info("✅ Default admin user created (email: admin@vizbrain.ai, password: admin123)")
                
        except Exception as e:
            logger.error(f"Failed to initialize user schema: {e}")
    
    def register_user(self, email: str, username: str, password: str, role: str = 'user') -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Validate input
            if not email or not username or not password:
                return {'success': False, 'error': 'Email, username, and password are required'}
            
            if len(password) < 6:
                return {'success': False, 'error': 'Password must be at least 6 characters'}
            
            # Hash password
            password_hash = self._hash_password(password)
            user_id = f"user_{secrets.token_hex(8)}"
            
            with self.kg_builder.driver.session() as session:
                # Check if user exists
                existing = session.run("""
                    MATCH (u:User) 
                    WHERE u.email = $email OR u.username = $username
                    RETURN u.email as email, u.username as username
                """, email=email, username=username).single()
                
                if existing:
                    return {'success': False, 'error': 'User with this email or username already exists'}
                
                # Create user
                session.run("""
                    CREATE (u:User {
                        id: $user_id,
                        email: $email,
                        username: $username,
                        password_hash: $password_hash,
                        role: $role,
                        created_at: datetime(),
                        last_login: null,
                        is_active: true
                    })
                """, user_id=user_id, email=email, username=username, 
                    password_hash=password_hash, role=role)
                
                logger.info(f"✅ New user registered: {email} ({username})")
                
                return {
                    'success': True,
                    'user_id': user_id,
                    'message': 'User registered successfully'
                }
                
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            return {'success': False, 'error': 'Registration failed'}
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return JWT token"""
        try:
            password_hash = self._hash_password(password)
            
            with self.kg_builder.driver.session() as session:
                user_record = session.run("""
                    MATCH (u:User {email: $email, password_hash: $password_hash})
                    WHERE u.is_active = true
                    SET u.last_login = datetime()
                    RETURN u.id as user_id, u.email as email, u.username as username, 
                           u.role as role, u.created_at as created_at
                """, email=email, password_hash=password_hash).single()
                
                if not user_record:
                    return {'success': False, 'error': 'Invalid email or password'}
                
                # Generate JWT token
                token_data = {
                    'user_id': user_record['user_id'],
                    'email': user_record['email'],
                    'username': user_record['username'],
                    'role': user_record['role'],
                    'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
                    'iat': datetime.utcnow()
                }
                
                token = jwt.encode(token_data, self.secret_key, algorithm='HS256')
                
                logger.info(f"✅ User authenticated: {email}")
                
                return {
                    'success': True,
                    'token': token,
                    'user': {
                        'id': user_record['user_id'],
                        'email': user_record['email'],
                        'username': user_record['username'],
                        'role': user_record['role']
                    },
                    'expires_in': self.token_expiry_hours * 3600
                }
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return {'success': False, 'error': 'Authentication failed'}
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return user data"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Check if user is still active
            with self.kg_builder.driver.session() as session:
                user_active = session.run("""
                    MATCH (u:User {id: $user_id})
                    RETURN u.is_active as is_active
                """, user_id=payload['user_id']).single()
                
                if not user_active or not user_active['is_active']:
                    return {'valid': False, 'error': 'User account is inactive'}
            
            return {
                'valid': True,
                'user_id': payload['user_id'],
                'email': payload['email'],
                'username': payload['username'],
                'role': payload['role']
            }
            
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token has expired'}
        except jwt.InvalidTokenError:
            return {'valid': False, 'error': 'Invalid token'}
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return {'valid': False, 'error': 'Token verification failed'}
    
    def get_user_permissions(self, user_id: str) -> Dict[str, List[str]]:
        """Get user permissions for knowledge graph access"""
        try:
            with self.kg_builder.driver.session() as session:
                user_data = session.run("""
                    MATCH (u:User {id: $user_id})
                    OPTIONAL MATCH (u)-[:HAS_ACCESS]->(kg:KnowledgeGraph)
                    OPTIONAL MATCH (u)-[:OWNS]->(owned_kg:KnowledgeGraph)
                    RETURN u.role as role,
                           collect(DISTINCT kg.id) as accessible_graphs,
                           collect(DISTINCT owned_kg.id) as owned_graphs
                """, user_id=user_id).single()
                
                if not user_data:
                    return {'read_access': [], 'write_access': [], 'admin_access': []}
                
                role = user_data['role']
                accessible = user_data['accessible_graphs'] or []
                owned = user_data['owned_graphs'] or []
                
                if role == 'admin':
                    return {
                        'read_access': ['*'],  # Access to all graphs
                        'write_access': ['*'],
                        'admin_access': ['*']
                    }
                else:
                    return {
                        'read_access': accessible + owned,
                        'write_access': owned,
                        'admin_access': owned
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get user permissions: {e}")
            return {'read_access': [], 'write_access': [], 'admin_access': []}
    
    def create_shared_graph(self, owner_id: str, name: str, description: str = '') -> Dict[str, Any]:
        """Create a new shared knowledge graph"""
        try:
            graph_id = f"kg_{secrets.token_hex(8)}"
            
            with self.kg_builder.driver.session() as session:
                session.run("""
                    MATCH (u:User {id: $owner_id})
                    CREATE (kg:KnowledgeGraph {
                        id: $graph_id,
                        name: $name,
                        description: $description,
                        created_at: datetime(),
                        is_public: false,
                        node_count: 0,
                        relationship_count: 0
                    })
                    CREATE (u)-[:OWNS]->(kg)
                """, owner_id=owner_id, graph_id=graph_id, name=name, description=description)
                
                logger.info(f"✅ Shared knowledge graph created: {name} ({graph_id})")
                
                return {
                    'success': True,
                    'graph_id': graph_id,
                    'message': 'Knowledge graph created successfully'
                }
                
        except Exception as e:
            logger.error(f"Failed to create shared graph: {e}")
            return {'success': False, 'error': 'Failed to create knowledge graph'}
    
    def grant_graph_access(self, graph_id: str, user_id: str, permission: str = 'read') -> Dict[str, Any]:
        """Grant user access to a knowledge graph"""
        try:
            with self.kg_builder.driver.session() as session:
                # Check if graph exists and user has admin rights
                result = session.run("""
                    MATCH (kg:KnowledgeGraph {id: $graph_id})
                    OPTIONAL MATCH (u:User {id: $user_id})
                    RETURN kg IS NOT NULL as graph_exists, u IS NOT NULL as user_exists
                """, graph_id=graph_id, user_id=user_id).single()
                
                if not result['graph_exists']:
                    return {'success': False, 'error': 'Knowledge graph not found'}
                if not result['user_exists']:
                    return {'success': False, 'error': 'User not found'}
                
                # Grant access
                session.run("""
                    MATCH (u:User {id: $user_id}), (kg:KnowledgeGraph {id: $graph_id})
                    MERGE (u)-[r:HAS_ACCESS]->(kg)
                    SET r.permission = $permission,
                        r.granted_at = datetime()
                """, user_id=user_id, graph_id=graph_id, permission=permission)
                
                logger.info(f"✅ Access granted: user {user_id} -> graph {graph_id} ({permission})")
                
                return {'success': True, 'message': 'Access granted successfully'}
                
        except Exception as e:
            logger.error(f"Failed to grant graph access: {e}")
            return {'success': False, 'error': 'Failed to grant access'}
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = os.getenv('PASSWORD_SALT', 'vizbrain_default_salt')
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def health_check(self) -> Dict[str, Any]:
        """Check health status of authentication service"""
        try:
            # Test database connectivity
            with self.kg_builder.driver.session() as session:
                result = session.run("MATCH (u:User) RETURN count(u) as user_count").single()
                user_count = result['user_count'] if result else 0
            
            return {
                'available': True,
                'database_connected': True,
                'user_count': user_count,
                'jwt_configured': bool(self.secret_key),
                'status': 'healthy'
            }
        except Exception as e:
            return {
                'available': False,
                'database_connected': False,
                'error': str(e),
                'status': 'unhealthy'
            }


# Authentication decorators
def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                pass
        
        # Get token from query parameter (fallback)
        if not token:
            token = request.args.get('token')
        
        if not token:
            return jsonify({'error': 'Authentication token is required'}), 401
        
        # Verify token
        auth_service = get_auth_service()
        verification = auth_service.verify_token(token)
        
        if not verification['valid']:
            return jsonify({'error': verification['error']}), 401
        
        # Add user info to request context
        request.current_user = verification
        return f(*args, **kwargs)
    
    return decorated_function


def require_role(required_role: str):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user_role = request.current_user.get('role')
            
            if required_role == 'admin' and user_role != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Global service instance
_auth_service = None

def get_auth_service(kg_builder=None):
    """Get the global authentication service instance"""
    global _auth_service
    if _auth_service is None and kg_builder:
        _auth_service = AuthService(kg_builder)
    return _auth_service


# Export
__all__ = ['AuthService', 'get_auth_service', 'require_auth', 'require_role']