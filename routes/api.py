from flask import Blueprint, jsonify
from database import db
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/documents')
def list_documents():
    """API: Lister tous les documents enregistrés"""
    try:
        query = """
        SELECT 
            d.document_code,
            d.filename,
            d.year,
            d.title,
            c.name as category_name,
            sc.name as subcategory_name,
            q.qr_identifier
        FROM documents d
        JOIN subcategories sc ON d.subcategory_id = sc.id
        JOIN categories c ON sc.category_id = c.id
        LEFT JOIN qrcodes q ON d.id = q.document_id
        ORDER BY d.created_at DESC
        """
        
        documents = db.execute_query_safe(query)
        
        return jsonify({
            'success': True,
            'documents': documents or []
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des documents: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500
