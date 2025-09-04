"""
Node Details API Endpoint

This module provides detailed information about specific nodes in the knowledge graph,
including their properties, connections, related conversations, and metadata.
"""

from flask import Blueprint, jsonify, request
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json

# Create blueprint for node details API
node_details_bp = Blueprint('node_details', __name__)
logger = logging.getLogger(__name__)


def serialize_neo4j_datetime(obj):
    """Convert Neo4j DateTime objects to ISO format strings"""
    if hasattr(obj, 'to_native'):
        # Neo4j DateTime object
        return obj.to_native().isoformat()
    return obj

def format_node_details(query_result: Any) -> Dict[str, Any]:
    """Format Neo4j query results into a structured node details response"""
    
    if not query_result:
        return None
    
    record = query_result.single()
    if not record:
        return None
    
    node = record['n']
    relationships = record.get('relationships', [])
    connected_nodes = record.get('connected_nodes', [])
    conversations = record.get('conversations', [])
    
    # Extract basic node properties
    node_data = {
        'id': node.element_id,
        'name': node.get('name') or node.get('content') or node.element_id,
        'type': list(node.labels)[0] if node.labels else 'unknown',
        'labels': list(node.labels),
        'properties': {k: serialize_neo4j_datetime(v) for k, v in dict(node).items()},
        'created_at': serialize_neo4j_datetime(node.get('timestamp')),
        'last_updated': serialize_neo4j_datetime(node.get('timestamp'))
    }
    
    # Add confidence if available (from enhanced entity extraction)
    if 'confidence' in node:
        node_data['confidence'] = node['confidence']
    elif 'entity_confidence' in node:
        node_data['confidence'] = node['entity_confidence']
    else:
        node_data['confidence'] = 0.7  # Default confidence
    
    # Process connections
    connections = []
    for i, rel in enumerate(relationships):
        if i < len(connected_nodes):
            connected_node = connected_nodes[i]
            connection = {
                'id': connected_node.element_id,
                'name': connected_node.get('name') or connected_node.get('content') or connected_node.element_id,
                'type': list(connected_node.labels)[0] if connected_node.labels else 'unknown',
                'relationship_type': rel.type,
                'relationship_properties': {k: serialize_neo4j_datetime(v) for k, v in dict(rel).items()},
                'strength': rel.get('strength', 1.0)
            }
            connections.append(connection)
    
    # Process related conversations
    related_conversations = []
    processed_sessions = set()
    
    for conv in conversations:
        session = conv.get('session')
        thought = conv.get('thought')
        
        if session and session.element_id not in processed_sessions:
            conversation = {
                'session_id': session.get('id', session.element_id),
                'reasoning_strategy': session.get('reasoning_strategy', 'unknown'),
                'domain': session.get('domain', 'general'),
                'timestamp': serialize_neo4j_datetime(session.get('timestamp')),
                'thought_content': thought.get('content', '') if thought else '',
                'thought_type': thought.get('type', '') if thought else '',
                'thought_confidence': thought.get('confidence', 0.0) if thought else 0.0
            }
            related_conversations.append(conversation)
            processed_sessions.add(session.element_id)
    
    # Sort conversations by timestamp (most recent first)
    related_conversations.sort(key=lambda x: x.get('timestamp') or datetime.min, reverse=True)
    
    # Build final response
    response = {
        **node_data,
        'connections': connections,
        'connection_count': len(connections),
        'related_conversations': related_conversations[:10],  # Limit to 10 most recent
        'conversation_count': len(related_conversations),
        'metadata': {
            'retrieval_timestamp': datetime.now().isoformat(),
            'total_relationships': len(relationships),
            'has_definition': 'definition' in node_data['properties'],
            'node_centrality': len(connections)  # Simple centrality measure
        }
    }
    
    # Add definition if it exists
    if node_data['properties'].get('definition'):
        response['definition'] = node_data['properties']['definition']
    
    return response


def register_node_details_routes(app, kg_system):
    """Register node details routes with the Flask app"""
    
    @app.route('/api/node/<node_id>/details', methods=['GET'])
    def get_node_details(node_id: str):
        """Get comprehensive details about a specific node"""
        try:
            logger.debug(f"Fetching details for node: {node_id}")
            
            if not kg_system:
                return jsonify({'error': 'Knowledge graph system not initialized'}), 500
            
            with kg_system.kg_builder.driver.session() as session:
                # Comprehensive query to get all node information
                result = session.run("""
                    MATCH (n) WHERE elementId(n) = $node_id
                    OPTIONAL MATCH (n)-[r]-(connected)
                    OPTIONAL MATCH (n)<-[:MENTIONS]-(t:Thought)-[:PART_OF]->(s:Session)
                    OPTIONAL MATCH (n)<-[:USES_TOOL]-(t2:Thought)-[:PART_OF]->(s2:Session)
                    WITH n, 
                         collect(DISTINCT r) as relationships,
                         collect(DISTINCT connected) as connected_nodes,
                         collect(DISTINCT {session: s, thought: t}) + 
                         collect(DISTINCT {session: s2, thought: t2}) as conversations
                    RETURN n, relationships, connected_nodes, conversations
                """, node_id=node_id)
                
                # Format the results
                node_details = format_node_details(result)
                
                if not node_details:
                    return jsonify({'error': f'Node with id {node_id} not found'}), 404
                
                logger.debug(f"Successfully retrieved details for node: {node_id}")
                return jsonify(node_details)
        
        except Exception as e:
            logger.error(f"Error fetching node details for {node_id}: {str(e)}")
            return jsonify({'error': f'Failed to fetch node details: {str(e)}'}), 500
    
    @app.route('/api/node/<node_id>/connections', methods=['GET'])
    def get_node_connections(node_id: str):
        """Get just the connections for a specific node"""
        try:
            limit = request.args.get('limit', 20, type=int)
            relationship_type = request.args.get('type', None)
            
            if not kg_system:
                return jsonify({'error': 'Knowledge graph system not initialized'}), 500
            
            with kg_system.kg_builder.driver.session() as session:
                # Build query based on parameters
                if relationship_type:
                    query = """
                        MATCH (n)-[r]->(connected) 
                        WHERE elementId(n) = $node_id AND type(r) = $rel_type
                        RETURN connected, r
                        ORDER BY r.strength DESC, connected.name
                        LIMIT $limit
                    """
                    params = {'node_id': node_id, 'rel_type': relationship_type, 'limit': limit}
                else:
                    query = """
                        MATCH (n)-[r]-(connected) 
                        WHERE elementId(n) = $node_id
                        RETURN connected, r, 
                               CASE WHEN startNode(r) = n THEN 'outgoing' ELSE 'incoming' END as direction
                        ORDER BY r.strength DESC, connected.name
                        LIMIT $limit
                    """
                    params = {'node_id': node_id, 'limit': limit}
                
                result = session.run(query, **params)
                
                connections = []
                for record in result:
                    connected_node = record['connected']
                    relationship = record['r']
                    
                    connection = {
                        'id': connected_node.element_id,
                        'name': connected_node.get('name') or connected_node.get('content'),
                        'type': list(connected_node.labels)[0] if connected_node.labels else 'unknown',
                        'relationship_type': relationship.type,
                        'strength': relationship.get('strength', 1.0),
                        'direction': record.get('direction', 'bidirectional')
                    }
                    connections.append(connection)
                
                return jsonify({
                    'node_id': node_id,
                    'connections': connections,
                    'total_connections': len(connections),
                    'filtered_by': relationship_type,
                    'limit_applied': limit
                })
        
        except Exception as e:
            logger.error(f"Error fetching connections for {node_id}: {str(e)}")
            return jsonify({'error': f'Failed to fetch connections: {str(e)}'}), 500
    
    @app.route('/api/node/<node_id>/timeline', methods=['GET'])
    def get_node_timeline(node_id: str):
        """Get timeline of when this node was mentioned or used"""
        try:
            if not kg_system:
                return jsonify({'error': 'Knowledge graph system not initialized'}), 500
            
            with kg_system.kg_builder.driver.session() as session:
                result = session.run("""
                    MATCH (n) WHERE elementId(n) = $node_id
                    OPTIONAL MATCH (n)<-[:MENTIONS|USES_TOOL]-(t:Thought)-[:PART_OF]->(s:Session)
                    WITH n, s, t, s.timestamp as session_time
                    WHERE session_time IS NOT NULL
                    RETURN s.id as session_id,
                           s.reasoning_strategy as strategy,
                           s.domain as domain,
                           session_time,
                           collect({
                               content: t.content,
                               type: t.type,
                               confidence: t.confidence
                           }) as thoughts
                    ORDER BY session_time DESC
                    LIMIT 50
                """, node_id=node_id)
                
                timeline = []
                for record in result:
                    timeline_entry = {
                        'session_id': record['session_id'],
                        'strategy': record['strategy'],
                        'domain': record['domain'],
                        'timestamp': serialize_neo4j_datetime(record['session_time']),
                        'thoughts': record['thoughts']
                    }
                    timeline.append(timeline_entry)
                
                return jsonify({
                    'node_id': node_id,
                    'timeline': timeline,
                    'total_entries': len(timeline)
                })
        
        except Exception as e:
            logger.error(f"Error fetching timeline for {node_id}: {str(e)}")
            return jsonify({'error': f'Failed to fetch timeline: {str(e)}'}), 500
    
    @app.route('/api/node/<node_id>/statistics', methods=['GET'])
    def get_node_statistics(node_id: str):
        """Get statistical information about a node"""
        try:
            if not kg_system:
                return jsonify({'error': 'Knowledge graph system not initialized'}), 500
            
            with kg_system.kg_builder.driver.session() as session:
                result = session.run("""
                    MATCH (n) WHERE elementId(n) = $node_id
                    OPTIONAL MATCH (n)-[r]-(connected)
                    WITH n, 
                         count(connected) as total_connections,
                         collect(type(r)) as relationship_types,
                         collect(labels(connected)) as connected_types
                    OPTIONAL MATCH (n)<-[:MENTIONS|USES_TOOL]-(t:Thought)
                    WITH n, total_connections, relationship_types, connected_types,
                         count(t) as mention_count,
                         avg(t.confidence) as avg_confidence
                    RETURN n,
                           total_connections,
                           relationship_types,
                           connected_types,
                           mention_count,
                           avg_confidence
                """, node_id=node_id)
                
                record = result.single()
                if not record:
                    return jsonify({'error': f'Node with id {node_id} not found'}), 404
                
                # Process relationship type frequencies
                rel_types = record['relationship_types']
                rel_type_counts = {}
                for rel_type in rel_types:
                    if rel_type:
                        rel_type_counts[rel_type] = rel_type_counts.get(rel_type, 0) + 1
                
                # Process connected node type frequencies
                connected_types = []
                for type_list in record['connected_types']:
                    if type_list:
                        connected_types.extend(type_list)
                
                connected_type_counts = {}
                for node_type in connected_types:
                    connected_type_counts[node_type] = connected_type_counts.get(node_type, 0) + 1
                
                statistics = {
                    'node_id': node_id,
                    'total_connections': record['total_connections'] or 0,
                    'mention_count': record['mention_count'] or 0,
                    'average_confidence': record['avg_confidence'] or 0.0,
                    'relationship_types': rel_type_counts,
                    'connected_node_types': connected_type_counts,
                    'centrality_score': record['total_connections'] or 0,  # Simple centrality
                    'activity_score': (record['mention_count'] or 0) * (record['avg_confidence'] or 0.5)
                }
                
                return jsonify(statistics)
        
        except Exception as e:
            logger.error(f"Error fetching statistics for {node_id}: {str(e)}")
            return jsonify({'error': f'Failed to fetch statistics: {str(e)}'}), 500


# Export the registration function
__all__ = ['register_node_details_routes']