"""
Export and Import API endpoints
"""

from flask import Blueprint, request, jsonify, send_file
from services.export_import_service import get_export_import_service
from services.auth_service import require_auth, get_auth_service
import io
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def register_export_import_routes(app, kg_system):
    """Register export/import routes with the Flask app"""
    
    # Initialize export/import service
    export_import_service = get_export_import_service(kg_system.kg_builder if kg_system else None)
    auth_service = get_auth_service()
    
    if not export_import_service:
        logger.warning("⚠️ Export/Import service not available")
        return
    
    @app.route('/api/export/<graph_id>/json', methods=['GET'])
    @require_auth
    def export_graph_json(graph_id):
        """Export knowledge graph to JSON format"""
        try:
            # Check permissions
            user_id = request.current_user['user_id']
            permissions = auth_service.get_user_permissions(user_id)
            
            if graph_id not in permissions['read_access'] and '*' not in permissions['read_access']:
                return jsonify({'error': 'Access denied to this graph'}), 403
            
            include_metadata = request.args.get('include_metadata', 'true').lower() == 'true'
            export_data = export_import_service.export_graph_json(graph_id, include_metadata)
            
            return jsonify({
                'success': True,
                'export_data': export_data
            })
            
        except Exception as e:
            logger.error(f"JSON export error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/export/<graph_id>/csv', methods=['GET'])
    @require_auth
    def export_graph_csv(graph_id):
        """Export knowledge graph to CSV format"""
        try:
            # Check permissions
            user_id = request.current_user['user_id']
            permissions = auth_service.get_user_permissions(user_id)
            
            if graph_id not in permissions['read_access'] and '*' not in permissions['read_access']:
                return jsonify({'error': 'Access denied to this graph'}), 403
            
            csv_data = export_import_service.export_graph_csv(graph_id)
            
            return jsonify({
                'success': True,
                'nodes_csv': csv_data['nodes_csv'],
                'edges_csv': csv_data['edges_csv']
            })
            
        except Exception as e:
            logger.error(f"CSV export error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/export/<graph_id>/graphml', methods=['GET'])
    @require_auth
    def export_graph_graphml(graph_id):
        """Export knowledge graph to GraphML format"""
        try:
            # Check permissions
            user_id = request.current_user['user_id']
            permissions = auth_service.get_user_permissions(user_id)
            
            if graph_id not in permissions['read_access'] and '*' not in permissions['read_access']:
                return jsonify({'error': 'Access denied to this graph'}), 403
            
            graphml_data = export_import_service.export_graph_graphml(graph_id)
            
            return jsonify({
                'success': True,
                'graphml_data': graphml_data
            })
            
        except Exception as e:
            logger.error(f"GraphML export error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/export/<graph_id>/bundle', methods=['GET'])
    @require_auth
    def export_graph_bundle(graph_id):
        """Export knowledge graph as ZIP bundle with multiple formats"""
        try:
            # Check permissions
            user_id = request.current_user['user_id']
            permissions = auth_service.get_user_permissions(user_id)
            
            if graph_id not in permissions['read_access'] and '*' not in permissions['read_access']:
                return jsonify({'error': 'Access denied to this graph'}), 403
            
            bundle_data = export_import_service.create_export_bundle(graph_id)
            
            # Create file-like object for sending
            bundle_io = io.BytesIO(bundle_data)
            bundle_io.seek(0)
            
            filename = f"knowledge_graph_{graph_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            return send_file(
                bundle_io,
                as_attachment=True,
                download_name=filename,
                mimetype='application/zip'
            )
            
        except Exception as e:
            logger.error(f"Bundle export error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/import/<graph_id>/json', methods=['POST'])
    @require_auth
    def import_graph_json(graph_id):
        """Import knowledge graph from JSON format"""
        try:
            # Check permissions
            user_id = request.current_user['user_id']
            permissions = auth_service.get_user_permissions(user_id)
            
            if graph_id not in permissions['write_access'] and '*' not in permissions['write_access']:
                return jsonify({'error': 'Write access denied to this graph'}), 403
            
            # Get JSON data from request
            if request.content_type == 'application/json':
                json_data = request.get_json()
            else:
                # Handle file upload
                if 'file' not in request.files:
                    return jsonify({'error': 'No file provided'}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400
                
                json_data = json.load(file)
            
            merge = request.args.get('merge', 'false').lower() == 'true'
            
            result = export_import_service.import_graph_json(json_data, graph_id, merge)
            
            return jsonify({
                'success': True,
                'import_result': result
            })
            
        except Exception as e:
            logger.error(f"JSON import error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/import/<graph_id>/bundle', methods=['POST'])
    @require_auth
    def import_graph_bundle(graph_id):
        """Import knowledge graph from ZIP bundle"""
        try:
            # Check permissions
            user_id = request.current_user['user_id']
            permissions = auth_service.get_user_permissions(user_id)
            
            if graph_id not in permissions['write_access'] and '*' not in permissions['write_access']:
                return jsonify({'error': 'Write access denied to this graph'}), 403
            
            # Handle file upload
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            zip_data = file.read()
            merge = request.args.get('merge', 'false').lower() == 'true'
            
            result = export_import_service.import_from_bundle(zip_data, graph_id, merge)
            
            return jsonify({
                'success': True,
                'import_result': result
            })
            
        except Exception as e:
            logger.error(f"Bundle import error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/export/full/json', methods=['GET'])
    @require_auth
    def export_full_graph_json():
        """Export entire knowledge graph (admin only)"""
        try:
            user_role = request.current_user['role']
            if user_role != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            
            include_metadata = request.args.get('include_metadata', 'true').lower() == 'true'
            export_data = export_import_service.export_graph_json(None, include_metadata)
            
            return jsonify({
                'success': True,
                'export_data': export_data
            })
            
        except Exception as e:
            logger.error(f"Full JSON export error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/export/full/bundle', methods=['GET'])
    @require_auth
    def export_full_graph_bundle():
        """Export entire knowledge graph as bundle (admin only)"""
        try:
            user_role = request.current_user['role']
            if user_role != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            
            bundle_data = export_import_service.create_export_bundle(None)
            
            # Create file-like object for sending
            bundle_io = io.BytesIO(bundle_data)
            bundle_io.seek(0)
            
            filename = f"full_knowledge_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            return send_file(
                bundle_io,
                as_attachment=True,
                download_name=filename,
                mimetype='application/zip'
            )
            
        except Exception as e:
            logger.error(f"Full bundle export error: {e}")
            return jsonify({'error': str(e)}), 500
    
    logger.info("✅ Export/Import routes registered successfully")

# Export
__all__ = ['register_export_import_routes']