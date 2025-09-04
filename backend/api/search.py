"""
Graph Search API

Provides full-text search capabilities across the knowledge graph,
including nodes, relationships, and content.
"""

from flask import Blueprint, jsonify, request
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import re

# Create blueprint for search API
search_bp = Blueprint('search', __name__)
logger = logging.getLogger(__name__)


def create_search_indexes(driver):
    """Create full-text search indexes for the knowledge graph"""
    try:
        with driver.session() as session:
            # Create index for nodes - searching across names, content, and properties
            session.run("""
                CREATE FULLTEXT INDEX node_search_index IF NOT EXISTS
                FOR (n:Entity|Session|Thought|Tool) 
                ON EACH [n.name, n.content, n.definition, n.description]
            """)
            
            # Create index for relationships
            session.run("""
                CREATE FULLTEXT INDEX rel_search_index IF NOT EXISTS
                FOR ()-[r:MENTIONS|USES_TOOL|PART_OF|RELATES_TO]-()
                ON EACH [r.description, r.context]
            """)
            
            logger.info("Search indexes created successfully")
    except Exception as e:
        logger.error(f"Failed to create search indexes: {e}")


def format_search_results(results) -> Dict[str, Any]:
    """Format Neo4j search results into a structured response"""
    nodes = []
    relationships = []
    
    for record in results:
        if 'node' in record:
            node = record['node']
            nodes.append({
                'id': node.element_id,
                'name': node.get('name') or node.get('content', '')[:50] + '...',
                'type': list(node.labels)[0] if node.labels else 'unknown',
                'labels': list(node.labels),
                'confidence': node.get('confidence', 0.7),
                'score': record.get('score', 0.0),
                'properties': dict(node),
                'snippet': _extract_snippet(node, record.get('score', 0.0))
            })
        
        if 'relationship' in record:
            rel = record['relationship']
            start_node = record.get('startNode')
            end_node = record.get('endNode')
            
            relationships.append({
                'id': rel.element_id,
                'type': rel.type,
                'properties': dict(rel),
                'score': record.get('score', 0.0),
                'start_node': {
                    'id': start_node.element_id if start_node else None,
                    'name': start_node.get('name') if start_node else None
                },
                'end_node': {
                    'id': end_node.element_id if end_node else None,
                    'name': end_node.get('name') if end_node else None
                }
            })
    
    return {
        'nodes': nodes,
        'relationships': relationships,
        'total_results': len(nodes) + len(relationships)
    }


def _extract_snippet(node, score: float) -> str:
    """Extract a relevant snippet from node content for search results"""
    content = node.get('content', '') or node.get('definition', '') or node.get('name', '')
    if len(content) <= 100:
        return content
    
    # Simple snippet extraction - could be enhanced with more sophisticated algorithms
    words = content.split()
    if len(words) <= 20:
        return content
    
    # Take first 20 words and add ellipsis
    return ' '.join(words[:20]) + '...'


def register_search_routes(app, kg_system):
    """Register search routes with the Flask app"""
    
    @app.route('/api/search', methods=['POST'])
    def search_graph():
        """Search across nodes and relationships in the knowledge graph"""
        try:
            data = request.get_json()
            query = data.get('query', '').strip()
            search_type = data.get('type', 'all')  # 'nodes', 'relationships', 'all'
            limit = data.get('limit', 20)
            
            if not query:
                return jsonify({'error': 'Search query is required'}), 400
            
            if not kg_system:
                return jsonify({'error': 'Knowledge graph system not initialized'}), 500
            
            logger.debug(f"Performing search: query='{query}', type='{search_type}', limit={limit}")
            
            with kg_system.kg_builder.driver.session() as session:
                results = []
                
                if search_type in ['nodes', 'all']:
                    # Search nodes using full-text index
                    try:
                        node_results = session.run("""
                            CALL db.index.fulltext.queryNodes('node_search_index', $search_query)
                            YIELD node, score
                            RETURN node, score
                            ORDER BY score DESC
                            LIMIT $limit
                        """, search_query=f"{query}~", limit=limit)
                        
                        for record in node_results:
                            results.append({
                                'node': record['node'],
                                'score': record['score']
                            })
                    except Exception as e:
                        logger.warning(f"Full-text search failed, falling back to basic search: {e}")
                        # Fallback to basic text matching
                        fallback_results = session.run("""
                            MATCH (n)
                            WHERE toLower(coalesce(n.name, '')) CONTAINS toLower($search_query)
                               OR toLower(coalesce(n.content, '')) CONTAINS toLower($search_query)
                               OR toLower(coalesce(n.definition, '')) CONTAINS toLower($search_query)
                            RETURN n as node, 1.0 as score
                            ORDER BY n.name
                            LIMIT $limit
                        """, search_query=query, limit=limit)
                        
                        for record in fallback_results:
                            results.append({
                                'node': record['node'],
                                'score': record['score']
                            })
                
                if search_type in ['relationships', 'all'] and len(results) < limit:
                    # Search relationships
                    remaining_limit = limit - len(results)
                    try:
                        rel_results = session.run("""
                            CALL db.index.fulltext.queryRelationships('rel_search_index', $search_query)
                            YIELD relationship, score
                            MATCH (start)-[relationship]->(end)
                            RETURN relationship, score, start as startNode, end as endNode
                            ORDER BY score DESC
                            LIMIT $remaining_limit
                        """, search_query=f"{query}~", remaining_limit=remaining_limit)
                        
                        for record in rel_results:
                            results.append({
                                'relationship': record['relationship'],
                                'score': record['score'],
                                'startNode': record['startNode'],
                                'endNode': record['endNode']
                            })
                    except Exception as e:
                        logger.warning(f"Relationship search failed: {e}")
                
                # Format and return results
                formatted_results = format_search_results(results)
                
                logger.debug(f"Search completed: found {formatted_results['total_results']} results")
                return jsonify({
                    'success': True,
                    'query': query,
                    'search_type': search_type,
                    'results': formatted_results,
                    'metadata': {
                        'search_timestamp': datetime.now().isoformat(),
                        'total_results': formatted_results['total_results'],
                        'has_more': len(results) >= limit
                    }
                })
        
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return jsonify({'error': f'Search failed: {str(e)}'}), 500
    
    @app.route('/api/search/suggestions', methods=['GET'])
    def get_search_suggestions():
        """Get search suggestions based on existing node names and types"""
        try:
            query = request.args.get('q', '').strip()
            limit = request.args.get('limit', 10, type=int)
            
            if not kg_system:
                return jsonify({'error': 'Knowledge graph system not initialized'}), 500
            
            if len(query) < 2:
                return jsonify({'suggestions': []})
            
            with kg_system.kg_builder.driver.session() as session:
                # Get suggestions from node names and types
                result = session.run("""
                    MATCH (n)
                    WHERE toLower(coalesce(n.name, '')) STARTS WITH toLower($search_query)
                       OR toLower(coalesce(n.content, '')) CONTAINS toLower($search_query)
                    RETURN DISTINCT coalesce(n.name, n.content) as suggestion,
                           labels(n) as types,
                           count(*) as frequency
                    ORDER BY frequency DESC, suggestion
                    LIMIT $limit
                """, search_query=query, limit=limit)
                
                suggestions = []
                for record in result:
                    suggestion = record['suggestion']
                    if suggestion and len(suggestion.strip()) > 0:
                        suggestions.append({
                            'text': suggestion.strip(),
                            'types': record['types'],
                            'frequency': record['frequency']
                        })
                
                return jsonify({'suggestions': suggestions})
        
        except Exception as e:
            logger.error(f"Search suggestions error: {str(e)}")
            return jsonify({'error': f'Failed to get suggestions: {str(e)}'}), 500


# Initialize search indexes
def initialize_search_system(kg_system):
    """Initialize the search system with required indexes"""
    if kg_system and kg_system.kg_builder.driver:
        create_search_indexes(kg_system.kg_builder.driver)


# Export functions
__all__ = ['register_search_routes', 'initialize_search_system']