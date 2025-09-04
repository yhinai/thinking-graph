"""
Export and Import Service for Knowledge Graphs

Provides comprehensive export and import capabilities for knowledge graphs
in various formats (JSON, GraphML, CSV, RDF, etc.)
"""

import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Any, Optional, BinaryIO, TextIO
import zipfile
import io
import logging

logger = logging.getLogger(__name__)

class ExportImportService:
    """Service for exporting and importing knowledge graphs"""
    
    def __init__(self, kg_builder):
        self.kg_builder = kg_builder
    
    def export_graph_json(self, graph_id: Optional[str] = None, include_metadata: bool = True) -> Dict[str, Any]:
        """Export knowledge graph to JSON format"""
        try:
            with self.kg_builder.driver.session() as session:
                # Query for nodes
                if graph_id:
                    nodes_query = """
                        MATCH (kg:KnowledgeGraph {id: $graph_id})
                        MATCH (kg)-[:CONTAINS]->(n)
                        RETURN n, labels(n) as node_labels, id(n) as neo4j_id
                        ORDER BY n.timestamp
                    """
                    nodes_result = session.run(nodes_query, graph_id=graph_id)
                else:
                    nodes_query = """
                        MATCH (n)
                        WHERE NOT 'KnowledgeGraph' IN labels(n) AND NOT 'User' IN labels(n)
                        RETURN n, labels(n) as node_labels, id(n) as neo4j_id
                        ORDER BY n.timestamp
                    """
                    nodes_result = session.run(nodes_query)
                
                # Process nodes
                nodes = []
                node_id_mapping = {}
                
                for record in nodes_result:
                    node = record['n']
                    node_labels = record['node_labels']
                    neo4j_id = record['neo4j_id']
                    
                    # Convert node properties
                    node_data = dict(node)
                    
                    # Handle datetime serialization
                    for key, value in node_data.items():
                        if hasattr(value, 'isoformat'):  # DateTime objects
                            node_data[key] = value.isoformat()
                    
                    node_export = {
                        'id': node_data.get('id', f'node_{neo4j_id}'),
                        'labels': node_labels,
                        'properties': node_data
                    }
                    
                    nodes.append(node_export)
                    node_id_mapping[neo4j_id] = node_export['id']
                
                # Query for relationships
                if graph_id:
                    rels_query = """
                        MATCH (kg:KnowledgeGraph {id: $graph_id})
                        MATCH (kg)-[:CONTAINS]->(n1)-[r]->(n2)<-[:CONTAINS]-(kg)
                        RETURN r, type(r) as rel_type, id(startNode(r)) as start_id, id(endNode(r)) as end_id
                    """
                    rels_result = session.run(rels_query, graph_id=graph_id)
                else:
                    rels_query = """
                        MATCH (n1)-[r]->(n2)
                        WHERE NOT 'KnowledgeGraph' IN labels(n1) AND NOT 'User' IN labels(n1)
                          AND NOT 'KnowledgeGraph' IN labels(n2) AND NOT 'User' IN labels(n2)
                        RETURN r, type(r) as rel_type, id(startNode(r)) as start_id, id(endNode(r)) as end_id
                    """
                    rels_result = session.run(rels_query)
                
                # Process relationships
                relationships = []
                for record in rels_result:
                    rel = record['r']
                    rel_type = record['rel_type']
                    start_neo4j_id = record['start_id']
                    end_neo4j_id = record['end_id']
                    
                    # Convert relationship properties
                    rel_data = dict(rel)
                    for key, value in rel_data.items():
                        if hasattr(value, 'isoformat'):
                            rel_data[key] = value.isoformat()
                    
                    rel_export = {
                        'type': rel_type,
                        'source': node_id_mapping.get(start_neo4j_id),
                        'target': node_id_mapping.get(end_neo4j_id),
                        'properties': rel_data
                    }
                    
                    if rel_export['source'] and rel_export['target']:
                        relationships.append(rel_export)
                
                # Build export data
                export_data = {
                    'format_version': '1.0',
                    'export_timestamp': datetime.utcnow().isoformat(),
                    'graph_id': graph_id,
                    'nodes': nodes,
                    'relationships': relationships,
                    'statistics': {
                        'node_count': len(nodes),
                        'relationship_count': len(relationships),
                        'node_types': list(set(label for node in nodes for label in node['labels'])),
                        'relationship_types': list(set(rel['type'] for rel in relationships))
                    }
                }
                
                if include_metadata:
                    # Add graph metadata if available
                    if graph_id:
                        graph_meta = session.run("""
                            MATCH (kg:KnowledgeGraph {id: $graph_id})
                            OPTIONAL MATCH (owner:User)-[:OWNS]->(kg)
                            RETURN kg.name as name, kg.description as description,
                                   kg.created_at as created_at, owner.username as owner
                        """, graph_id=graph_id).single()
                        
                        if graph_meta:
                            export_data['metadata'] = {
                                'name': graph_meta['name'],
                                'description': graph_meta['description'],
                                'created_at': graph_meta['created_at'].isoformat() if graph_meta['created_at'] else None,
                                'owner': graph_meta['owner']
                            }
                
                logger.info(f"✅ Graph exported to JSON: {len(nodes)} nodes, {len(relationships)} relationships")
                return export_data
                
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            raise
    
    def export_graph_csv(self, graph_id: Optional[str] = None) -> Dict[str, str]:
        """Export knowledge graph to CSV format (nodes and edges files)"""
        try:
            json_data = self.export_graph_json(graph_id, include_metadata=False)
            
            # Create nodes CSV
            nodes_csv = io.StringIO()
            if json_data['nodes']:
                # Get all possible node properties
                all_node_props = set()
                for node in json_data['nodes']:
                    all_node_props.update(node['properties'].keys())
                    all_node_props.add('labels')
                
                fieldnames = ['id'] + sorted(all_node_props)
                writer = csv.DictWriter(nodes_csv, fieldnames=fieldnames)
                writer.writeheader()
                
                for node in json_data['nodes']:
                    row = {'id': node['id'], 'labels': '|'.join(node['labels'])}
                    row.update(node['properties'])
                    writer.writerow(row)
            
            # Create edges CSV  
            edges_csv = io.StringIO()
            if json_data['relationships']:
                all_rel_props = set()
                for rel in json_data['relationships']:
                    all_rel_props.update(rel['properties'].keys())
                
                fieldnames = ['source', 'target', 'type'] + sorted(all_rel_props)
                writer = csv.DictWriter(edges_csv, fieldnames=fieldnames)
                writer.writeheader()
                
                for rel in json_data['relationships']:
                    row = {
                        'source': rel['source'],
                        'target': rel['target'],
                        'type': rel['type']
                    }
                    row.update(rel['properties'])
                    writer.writerow(row)
            
            logger.info(f"✅ Graph exported to CSV format")
            return {
                'nodes_csv': nodes_csv.getvalue(),
                'edges_csv': edges_csv.getvalue()
            }
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            raise
    
    def export_graph_graphml(self, graph_id: Optional[str] = None) -> str:
        """Export knowledge graph to GraphML format"""
        try:
            json_data = self.export_graph_json(graph_id, include_metadata=False)
            
            # Create GraphML XML structure
            root = ET.Element("graphml", xmlns="http://graphml.graphdrawing.org/xmlns")
            
            # Define keys for node and edge attributes
            key_counter = 0
            keys = {}
            
            # Analyze all properties to create key definitions
            all_node_props = set()
            all_edge_props = set()
            
            for node in json_data['nodes']:
                all_node_props.update(node['properties'].keys())
            
            for rel in json_data['relationships']:
                all_edge_props.update(rel['properties'].keys())
            
            # Create key elements for node properties
            for prop in sorted(all_node_props):
                key_elem = ET.SubElement(root, "key", id=f"d{key_counter}", 
                                       **{"for": "node", "attr.name": prop, "attr.type": "string"})
                keys[f"node_{prop}"] = f"d{key_counter}"
                key_counter += 1
            
            # Create key elements for edge properties
            for prop in sorted(all_edge_props):
                key_elem = ET.SubElement(root, "key", id=f"d{key_counter}",
                                       **{"for": "edge", "attr.name": prop, "attr.type": "string"})
                keys[f"edge_{prop}"] = f"d{key_counter}"
                key_counter += 1
            
            # Create graph element
            graph = ET.SubElement(root, "graph", id="G", edgedefault="directed")
            
            # Add nodes
            for node in json_data['nodes']:
                node_elem = ET.SubElement(graph, "node", id=str(node['id']))
                
                # Add node properties as data elements
                for prop, value in node['properties'].items():
                    data_elem = ET.SubElement(node_elem, "data", key=keys[f"node_{prop}"])
                    data_elem.text = str(value)
                
                # Add labels as a special property
                if f"node_labels" in keys:
                    data_elem = ET.SubElement(node_elem, "data", key=keys[f"node_labels"])
                    data_elem.text = "|".join(node['labels'])
            
            # Add edges
            edge_counter = 0
            for rel in json_data['relationships']:
                edge_elem = ET.SubElement(graph, "edge", id=f"e{edge_counter}",
                                        source=str(rel['source']), target=str(rel['target']))
                edge_counter += 1
                
                # Add edge type as data
                if f"edge_type" in keys:
                    data_elem = ET.SubElement(edge_elem, "data", key=keys[f"edge_type"])
                    data_elem.text = rel['type']
                
                # Add edge properties
                for prop, value in rel['properties'].items():
                    if f"edge_{prop}" in keys:
                        data_elem = ET.SubElement(edge_elem, "data", key=keys[f"edge_{prop}"])
                        data_elem.text = str(value)
            
            # Convert to string
            tree = ET.ElementTree(root)
            output = io.StringIO()
            tree.write(output, encoding='unicode', xml_declaration=True)
            
            logger.info(f"✅ Graph exported to GraphML format")
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"GraphML export failed: {e}")
            raise
    
    def create_export_bundle(self, graph_id: Optional[str] = None) -> bytes:
        """Create a ZIP bundle with multiple export formats"""
        try:
            # Get exports in different formats
            json_export = self.export_graph_json(graph_id)
            csv_exports = self.export_graph_csv(graph_id)
            graphml_export = self.export_graph_graphml(graph_id)
            
            # Create ZIP file in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add JSON export
                zip_file.writestr('knowledge_graph.json', json.dumps(json_export, indent=2))
                
                # Add CSV exports
                zip_file.writestr('nodes.csv', csv_exports['nodes_csv'])
                zip_file.writestr('edges.csv', csv_exports['edges_csv'])
                
                # Add GraphML export
                zip_file.writestr('knowledge_graph.graphml', graphml_export)
                
                # Add metadata file
                metadata = {
                    'export_timestamp': datetime.utcnow().isoformat(),
                    'graph_id': graph_id,
                    'formats_included': ['json', 'csv', 'graphml'],
                    'statistics': json_export['statistics']
                }
                zip_file.writestr('export_metadata.json', json.dumps(metadata, indent=2))
            
            zip_buffer.seek(0)
            logger.info(f"✅ Export bundle created successfully")
            return zip_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Export bundle creation failed: {e}")
            raise
    
    def import_graph_json(self, json_data: Dict[str, Any], graph_id: Optional[str] = None, merge: bool = False) -> Dict[str, Any]:
        """Import knowledge graph from JSON format"""
        try:
            # Validate JSON structure
            required_fields = ['nodes', 'relationships']
            for field in required_fields:
                if field not in json_data:
                    raise ValueError(f"Missing required field: {field}")
            
            imported_nodes = 0
            imported_relationships = 0
            errors = []
            
            with self.kg_builder.driver.session() as session:
                # Create graph container if specified
                if graph_id:
                    session.run("""
                        MERGE (kg:KnowledgeGraph {id: $graph_id})
                        ON CREATE SET kg.created_at = datetime(),
                                     kg.imported_at = datetime()
                        ON MATCH SET kg.imported_at = datetime()
                    """, graph_id=graph_id)
                
                # Clear existing data if not merging
                if not merge and graph_id:
                    session.run("""
                        MATCH (kg:KnowledgeGraph {id: $graph_id})-[:CONTAINS]->(n)
                        DETACH DELETE n
                    """, graph_id=graph_id)
                
                # Import nodes
                for node_data in json_data['nodes']:
                    try:
                        node_id = node_data['id']
                        labels = node_data.get('labels', [])
                        properties = node_data.get('properties', {})
                        
                        # Build Cypher query for node creation
                        label_str = ':'.join(labels) if labels else 'Node'
                        
                        create_query = f"""
                            MERGE (n:{label_str} {{id: $node_id}})
                            SET n += $properties,
                                n.imported_at = datetime()
                        """
                        
                        session.run(create_query, node_id=node_id, properties=properties)
                        
                        # Link to knowledge graph if specified
                        if graph_id:
                            session.run("""
                                MATCH (kg:KnowledgeGraph {id: $graph_id})
                                MATCH (n {id: $node_id})
                                MERGE (kg)-[:CONTAINS]->(n)
                            """, graph_id=graph_id, node_id=node_id)
                        
                        imported_nodes += 1
                        
                    except Exception as e:
                        errors.append(f"Node import error ({node_data.get('id', 'unknown')}): {e}")
                
                # Import relationships
                for rel_data in json_data['relationships']:
                    try:
                        source_id = rel_data['source']
                        target_id = rel_data['target']
                        rel_type = rel_data['type']
                        properties = rel_data.get('properties', {})
                        
                        create_rel_query = f"""
                            MATCH (source {{id: $source_id}})
                            MATCH (target {{id: $target_id}})
                            MERGE (source)-[r:{rel_type}]->(target)
                            SET r += $properties,
                                r.imported_at = datetime()
                        """
                        
                        session.run(create_rel_query, 
                                   source_id=source_id, 
                                   target_id=target_id, 
                                   properties=properties)
                        
                        imported_relationships += 1
                        
                    except Exception as e:
                        errors.append(f"Relationship import error ({rel_data.get('source', 'unknown')} -> {rel_data.get('target', 'unknown')}): {e}")
            
            result = {
                'success': True,
                'imported_nodes': imported_nodes,
                'imported_relationships': imported_relationships,
                'total_nodes': len(json_data['nodes']),
                'total_relationships': len(json_data['relationships']),
                'errors': errors,
                'error_count': len(errors)
            }
            
            logger.info(f"✅ JSON import completed: {imported_nodes} nodes, {imported_relationships} relationships")
            if errors:
                logger.warning(f"⚠️ Import completed with {len(errors)} errors")
            
            return result
            
        except Exception as e:
            logger.error(f"JSON import failed: {e}")
            raise
    
    def import_from_bundle(self, zip_data: bytes, graph_id: Optional[str] = None, merge: bool = False) -> Dict[str, Any]:
        """Import knowledge graph from ZIP bundle"""
        try:
            results = {}
            
            with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zip_file:
                # Check for JSON file
                json_files = [f for f in zip_file.namelist() if f.endswith('.json') and 'metadata' not in f]
                
                if json_files:
                    json_filename = json_files[0]
                    with zip_file.open(json_filename) as json_file:
                        json_data = json.load(json_file)
                        results['json_import'] = self.import_graph_json(json_data, graph_id, merge)
                else:
                    raise ValueError("No JSON file found in bundle")
                
                # Read metadata if available
                if 'export_metadata.json' in zip_file.namelist():
                    with zip_file.open('export_metadata.json') as meta_file:
                        metadata = json.load(meta_file)
                        results['original_metadata'] = metadata
            
            logger.info(f"✅ Bundle import completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Bundle import failed: {e}")
            raise


# Global service instance
_export_import_service = None

def get_export_import_service(kg_builder=None):
    """Get the global export/import service instance"""
    global _export_import_service
    if _export_import_service is None and kg_builder:
        _export_import_service = ExportImportService(kg_builder)
    return _export_import_service


# Export
__all__ = ['ExportImportService', 'get_export_import_service']