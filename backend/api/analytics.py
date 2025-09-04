"""
Analytics API for Knowledge Graph

Provides comprehensive analytics about the knowledge graph including:
- Growth metrics
- Topic clusters
- Connection patterns
- Learning insights
"""

from flask import Blueprint, jsonify, request
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import json

# Create blueprint for analytics API
analytics_bp = Blueprint('analytics', __name__)
logger = logging.getLogger(__name__)


def calculate_knowledge_metrics(session, time_range: str = 'week') -> Dict[str, Any]:
    """Calculate comprehensive knowledge graph metrics"""
    
    # Determine time filter
    now = datetime.now()
    if time_range == 'day':
        cutoff = now - timedelta(days=1)
    elif time_range == 'week':
        cutoff = now - timedelta(weeks=1)
    elif time_range == 'month':
        cutoff = now - timedelta(days=30)
    else:
        cutoff = datetime.min
    
    # Query 1: Basic counts
    basic_counts = session.run("""
        MATCH (n)
        WITH count(n) as total_nodes
        MATCH ()-[r]-()
        WITH total_nodes, count(r) as total_relationships
        MATCH (s:Session)
        WITH total_nodes, total_relationships, count(s) as total_sessions
        RETURN total_nodes, total_relationships, total_sessions
    """).single()
    
    # Query 2: Growth metrics
    growth_query = """
        MATCH (n) 
        WHERE n.timestamp >= $cutoff
        WITH labels(n) as node_labels, date(n.timestamp) as creation_date
        RETURN node_labels[0] as node_type, 
               creation_date,
               count(*) as count
        ORDER BY creation_date
    """
    
    growth_results = session.run(growth_query, cutoff=cutoff)
    growth_data = []
    for record in growth_results:
        growth_data.append({
            'date': record['creation_date'].isoformat() if record['creation_date'] else None,
            'type': record['node_type'],
            'count': record['count']
        })
    
    # Query 3: Topic clusters (most connected entities)
    topic_clusters = session.run("""
        MATCH (e:Entity)-[r]-(related)
        WITH e, count(DISTINCT related) as connection_count,
             collect(DISTINCT labels(related)[0]) as related_types
        WHERE connection_count >= 3
        RETURN e.name as topic,
               labels(e) as types,
               connection_count,
               related_types,
               e.definition as definition
        ORDER BY connection_count DESC
        LIMIT 10
    """)
    
    clusters = []
    for record in topic_clusters:
        clusters.append({
            'name': record['topic'],
            'types': record['types'],
            'connections': record['connection_count'],
            'related_types': record['related_types'],
            'definition': record.get('definition'),
            'cluster_size': record['connection_count']
        })
    
    # Query 4: Most connected concepts
    connected_concepts = session.run("""
        MATCH (n)-[r]-(connected)
        WITH n, count(DISTINCT connected) as connections,
             avg(r.strength) as avg_strength
        WHERE connections >= 2
        RETURN n.name as name,
               labels(n) as types,
               connections,
               avg_strength,
               n.confidence as confidence
        ORDER BY connections DESC, avg_strength DESC
        LIMIT 15
    """)
    
    concepts = []
    for record in connected_concepts:
        concepts.append({
            'name': record['name'],
            'types': record['types'],
            'connections': record['connections'],
            'avg_strength': record.get('avg_strength', 1.0),
            'confidence': record.get('confidence', 0.7)
        })
    
    # Query 5: Session insights
    session_insights = session.run("""
        MATCH (s:Session)-[:CONTAINS]->(t:Thought)
        WITH s, count(t) as thought_count,
             collect(t.type) as thought_types
        OPTIONAL MATCH (s)-[:CONTAINS]->(t2:Thought)-[:MENTIONS]->(e:Entity)
        WITH s, thought_count, thought_types,
             count(DISTINCT e) as entities_discussed
        RETURN s.id as session_id,
               s.reasoning_strategy as strategy,
               s.domain as domain,
               s.timestamp as timestamp,
               thought_count,
               thought_types,
               entities_discussed
        ORDER BY s.timestamp DESC
        LIMIT 20
    """)
    
    insights = []
    for record in session_insights:
        thought_type_counts = {}
        for thought_type in record.get('thought_types', []):
            thought_type_counts[thought_type] = thought_type_counts.get(thought_type, 0) + 1
        
        insights.append({
            'session_id': record['session_id'],
            'strategy': record.get('strategy', 'unknown'),
            'domain': record.get('domain', 'general'),
            'timestamp': record['timestamp'].isoformat() if record['timestamp'] else None,
            'thought_count': record['thought_count'],
            'thought_types': thought_type_counts,
            'entities_discussed': record.get('entities_discussed', 0)
        })
    
    # Calculate derived metrics
    total_nodes = basic_counts['total_nodes'] or 0
    total_relationships = basic_counts['total_relationships'] or 0
    total_sessions = basic_counts['total_sessions'] or 0
    
    # Knowledge depth (average connections per node)
    knowledge_depth = (total_relationships / total_nodes) if total_nodes > 0 else 0
    
    # Growth rate (nodes added in time period vs total)
    recent_nodes = sum(item['count'] for item in growth_data)
    growth_rate = (recent_nodes / total_nodes * 100) if total_nodes > 0 else 0
    
    return {
        'total_nodes': total_nodes,
        'total_connections': total_relationships,
        'total_sessions': total_sessions,
        'knowledge_depth': round(knowledge_depth, 2),
        'growth_rate': round(growth_rate, 2),
        'topic_clusters': clusters,
        'most_connected_concepts': concepts,
        'session_insights': insights,
        'growth_data': growth_data,
        'time_range': time_range,
        'generated_at': datetime.now().isoformat()
    }


def register_analytics_routes(app, kg_system):
    """Register analytics routes with the Flask app"""
    
    @app.route('/api/analytics', methods=['GET'])
    def get_knowledge_analytics():
        """Get comprehensive knowledge graph analytics"""
        try:
            time_range = request.args.get('range', 'week')
            
            if not kg_system:
                return jsonify({'error': 'Knowledge graph system not initialized'}), 500
            
            logger.debug(f"Fetching analytics for time range: {time_range}")
            
            with kg_system.kg_builder.driver.session() as session:
                analytics = calculate_knowledge_metrics(session, time_range)
                
            logger.debug(f"Analytics generated successfully: {analytics['total_nodes']} nodes, {analytics['total_connections']} connections")
            return jsonify({
                'success': True,
                'analytics': analytics,
                'metadata': {
                    'time_range': time_range,
                    'generated_at': analytics['generated_at']
                }
            })
        
        except Exception as e:
            logger.error(f"Analytics error: {str(e)}")
            return jsonify({'error': f'Analytics generation failed: {str(e)}'}), 500
    
    @app.route('/api/analytics/growth', methods=['GET'])
    def get_growth_analytics():
        """Get detailed growth analytics"""
        try:
            days = request.args.get('days', 30, type=int)
            
            if not kg_system:
                return jsonify({'error': 'Knowledge graph system not initialized'}), 500
            
            with kg_system.kg_builder.driver.session() as session:
                # Daily growth over specified period
                cutoff = datetime.now() - timedelta(days=days)
                
                growth_results = session.run("""
                    MATCH (n) 
                    WHERE n.timestamp >= $cutoff
                    WITH date(n.timestamp) as creation_date, labels(n)[0] as node_type
                    RETURN creation_date, node_type, count(*) as count
                    ORDER BY creation_date, node_type
                """, cutoff=cutoff)
                
                # Organize by date and type
                growth_by_date = {}
                node_types = set()
                
                for record in growth_results:
                    date_str = record['creation_date'].isoformat() if record['creation_date'] else 'unknown'
                    node_type = record['node_type'] or 'Unknown'
                    node_types.add(node_type)
                    
                    if date_str not in growth_by_date:
                        growth_by_date[date_str] = {}
                    
                    growth_by_date[date_str][node_type] = record['count']
                
                return jsonify({
                    'success': True,
                    'growth_data': growth_by_date,
                    'node_types': list(node_types),
                    'time_period': f'{days} days',
                    'start_date': (datetime.now() - timedelta(days=days)).isoformat(),
                    'end_date': datetime.now().isoformat()
                })
        
        except Exception as e:
            logger.error(f"Growth analytics error: {str(e)}")
            return jsonify({'error': f'Growth analytics failed: {str(e)}'}), 500
    
    @app.route('/api/analytics/relationships', methods=['GET'])
    def get_relationship_analytics():
        """Get relationship pattern analytics"""
        try:
            if not kg_system:
                return jsonify({'error': 'Knowledge graph system not initialized'}), 500
            
            with kg_system.kg_builder.driver.session() as session:
                # Relationship type distribution
                rel_distribution = session.run("""
                    MATCH ()-[r]-()
                    WITH type(r) as rel_type, count(*) as count
                    RETURN rel_type, count
                    ORDER BY count DESC
                """)
                
                # Node type connections matrix
                connection_matrix = session.run("""
                    MATCH (n1)-[r]-(n2)
                    WITH labels(n1)[0] as type1, labels(n2)[0] as type2, count(*) as connections
                    RETURN type1, type2, connections
                    ORDER BY connections DESC
                """)
                
                # Strongest connections
                strongest_connections = session.run("""
                    MATCH (n1)-[r]-(n2)
                    WHERE r.strength IS NOT NULL
                    RETURN n1.name as source,
                           n2.name as target,
                           type(r) as relationship,
                           r.strength as strength
                    ORDER BY r.strength DESC
                    LIMIT 20
                """)
                
                return jsonify({
                    'success': True,
                    'relationship_distribution': [
                        {'type': record['rel_type'], 'count': record['count']}
                        for record in rel_distribution
                    ],
                    'connection_matrix': [
                        {
                            'source_type': record['type1'],
                            'target_type': record['type2'],
                            'connections': record['connections']
                        }
                        for record in connection_matrix
                    ],
                    'strongest_connections': [
                        {
                            'source': record['source'],
                            'target': record['target'],
                            'relationship': record['relationship'],
                            'strength': record['strength']
                        }
                        for record in strongest_connections
                    ]
                })
        
        except Exception as e:
            logger.error(f"Relationship analytics error: {str(e)}")
            return jsonify({'error': f'Relationship analytics failed: {str(e)}'}), 500


# Export the registration function
__all__ = ['register_analytics_routes']