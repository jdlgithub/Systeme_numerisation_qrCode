from flask import Blueprint, render_template, request, jsonify, current_app
from database import db
import logging

logger = logging.getLogger(__name__)

qr_bp = Blueprint('qr', __name__)

@qr_bp.route('/qr/<identifier>')
def resolve_qr(identifier):
    """Résoudre un QR code hiérarchique (catégorie, sous-catégorie ou document)"""
    try:
        # 1. Chercher dans les documents
        if not identifier.startswith('CAT-') and not identifier.startswith('SUBCAT-'):
            document_result = _resolve_document_qr(identifier)
            if document_result:
                return document_result
        
        # 2. Chercher dans les sous-catégories
        if identifier.startswith('SUBCAT-'):
            subcategory_result = _resolve_subcategory_qr(identifier)
            if subcategory_result:
                return subcategory_result
        
        # 3. Chercher dans les catégories
        if identifier.startswith('CAT-'):
            category_result = _resolve_category_qr(identifier)
            if category_result:
                return category_result
        
        return jsonify({
            'success': False,
            'error': 'QR code non trouvé'
        }), 404
        
    except Exception as e:
        logger.error(f"Erreur lors de la résolution du QR code {identifier}: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500

def _resolve_document_qr(identifier):
    """Résoudre un QR code de document"""
    try:
        query = """
        SELECT 
            d.document_code,
            d.filename,
            d.file_path,
            d.year,
            d.title,
            d.description,
            c.name as category_name,
            sc.name as subcategory_name,
            q.qr_payload,
            'DOCUMENT' as type
        FROM documents d
        JOIN subcategories sc ON d.subcategory_id = sc.id
        JOIN categories c ON sc.category_id = c.id
        JOIN qrcodes q ON d.id = q.document_id
        WHERE q.qr_identifier = %s AND q.qr_type = 'DOCUMENT'
        """
        
        result = db.execute_query_safe(query, (identifier,))
        
        if result:
            document = result[0]
            if request.headers.get('Accept', '').startswith('application/json'):
                return jsonify({
                    'success': True,
                    'type': 'document',
                    'data': document
                })
            else:
                return render_template('document_view.html', document=document)
        
        return None
    except Exception as e:
        logger.error(f"Erreur lors de la résolution du document QR {identifier}: {e}")
        return None

def _resolve_subcategory_qr(identifier):
    """Résoudre un QR code de sous-catégorie"""
    try:
        query = """
        SELECT 
            q.qr_identifier,
            c.name as category_name,
            sc.name as subcategory_name,
            sc.description,
            q.folder_path,
            q.qr_payload,
            'SUBCATEGORY' as type,
            COUNT(d.id) as document_count
        FROM qrcodes q
        JOIN subcategories sc ON q.subcategory_id = sc.id
        JOIN categories c ON sc.category_id = c.id
        LEFT JOIN documents d ON sc.id = d.subcategory_id
        WHERE q.qr_identifier = %s AND q.qr_type = 'SUBCATEGORY'
        GROUP BY q.id, c.name, sc.name, sc.description, q.folder_path, q.qr_payload
        """
        
        result = db.execute_query_safe(query, (identifier,))
        
        if result:
            subcategory = result[0]
            
            # Récupérer la liste des documents dans cette sous-catégorie
            docs_query = """
            SELECT d.document_code, d.filename, d.title, q.qr_identifier
            FROM documents d
            JOIN qrcodes q ON d.id = q.document_id
            JOIN subcategories sc ON d.subcategory_id = sc.id
            WHERE sc.name = %s AND sc.category_id = (
                SELECT category_id FROM subcategories WHERE id = (
                    SELECT subcategory_id FROM qrcodes WHERE qr_identifier = %s
                )
            )
            ORDER BY d.created_at DESC
            """
            
            documents = db.execute_query_safe(docs_query, (subcategory['subcategory_name'], identifier))
            subcategory['documents'] = documents or []
            
            if request.headers.get('Accept', '').startswith('application/json'):
                return jsonify({
                    'success': True,
                    'type': 'subcategory',
                    'data': subcategory
                })
            else:
                return render_template('subcategory_view.html', subcategory=subcategory)
        
        return None
    except Exception as e:
        logger.error(f"Erreur lors de la résolution de la sous-catégorie QR {identifier}: {e}")
        return None

def _resolve_category_qr(identifier):
    """Résoudre un QR code de catégorie"""
    try:
        query = """
        SELECT 
            q.qr_identifier,
            c.name as category_name,
            c.description,
            q.folder_path,
            q.qr_payload,
            'CATEGORY' as type,
            COUNT(DISTINCT sc.id) as subcategory_count,
            COUNT(DISTINCT d.id) as document_count
        FROM qrcodes q
        JOIN categories c ON q.category_id = c.id
        LEFT JOIN subcategories sc ON c.id = sc.category_id
        LEFT JOIN documents d ON sc.id = d.subcategory_id
        WHERE q.qr_identifier = %s AND q.qr_type = 'CATEGORY'
        GROUP BY q.id, c.name, c.description, q.folder_path, q.qr_payload
        """
        
        result = db.execute_query_safe(query, (identifier,))
        
        if result:
            category = result[0]
            
            # Récupérer les sous-catégories
            subcat_query = """
            SELECT 
                sc.name as subcategory_name,
                sc.description,
                q.qr_identifier,
                COUNT(d.id) as document_count
            FROM subcategories sc
            LEFT JOIN qrcodes q ON sc.id = q.subcategory_id AND q.qr_type = 'SUBCATEGORY'
            LEFT JOIN documents d ON sc.id = d.subcategory_id
            WHERE sc.category_id = (
                SELECT category_id FROM qrcodes WHERE qr_identifier = %s
            )
            GROUP BY sc.id, sc.name, sc.description, q.qr_identifier
            ORDER BY sc.name
            """
            
            subcategories = db.execute_query_safe(subcat_query, (identifier,))
            category['subcategories'] = subcategories or []
            
            if request.headers.get('Accept', '').startswith('application/json'):
                return jsonify({
                    'success': True,
                    'type': 'category',
                    'data': category
                })
            else:
                return render_template('category_view.html', category=category)
        
        return None
    except Exception as e:
        logger.error(f"Erreur lors de la résolution de la catégorie QR {identifier}: {e}")
        return None

@qr_bp.route('/download/<identifier>')
def download_document(identifier):
    """Télécharger directement un document via son identifiant QR"""
    try:
        query = """
        SELECT 
            d.filename,
            d.file_path
        FROM documents d
        JOIN qrcodes q ON d.id = q.document_id
        WHERE q.qr_identifier = %s
        """
        
        result = db.execute_query_safe(query, (identifier,))
        
        if result:
            document = result[0]
            file_path = document['file_path']
            filename = document['filename']
            
            # Vérifier si le fichier existe
            import os
            full_path = os.path.join(os.getcwd(), file_path)
            if os.path.exists(full_path):
                directory = os.path.dirname(file_path)
                from flask import send_from_directory
                return send_from_directory(directory, filename, as_attachment=True)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Fichier non trouvé sur le serveur'
                }), 404
        
        return jsonify({
            'success': False,
            'error': 'Document non trouvé'
        }), 404
        
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement du document {identifier}: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500
