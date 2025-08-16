from flask import Flask, jsonify, request, render_template, send_from_directory
from database import db
from qr_generator import qr_generator
from config_local import Config  # Utiliser la configuration locale
import os
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

@app.route('/')
def index():
    """Page d'accueil de l'application"""
    return render_template('index.html')

@app.route('/qr/<identifier>')
def resolve_qr(identifier):
    """
    Résoudre un QR code et retourner les informations du document
    
    Args:
        identifier (str): Identifiant du QR code (code document ou sous-catégorie)
    
    Returns:
        JSON: Informations du document ou de la sous-catégorie
    """
    try:
        # Chercher d'abord dans les documents
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
        WHERE q.qr_identifier = %s
        """
        
        result = db.execute_query(query, (identifier,))
        
        if result:
            document = result[0]
            return jsonify({
                'success': True,
                'type': 'document',
                'data': document
            })
        
        # Si pas trouvé, chercher dans les sous-catégories
        query = """
        SELECT 
            q.qr_identifier,
            c.name as category_name,
            sc.name as subcategory_name,
            sc.description,
            q.qr_payload,
            'SUBCATEGORY' as type
        FROM qrcodes q
        JOIN subcategories sc ON q.subcategory_id = sc.id
        JOIN categories c ON sc.category_id = c.id
        WHERE q.qr_identifier = %s AND q.qr_type = 'SUBCATEGORY'
        """
        
        result = db.execute_query(query, (identifier,))
        
        if result:
            subcategory = result[0]
            return jsonify({
                'success': True,
                'type': 'subcategory',
                'data': subcategory
            })
        
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

@app.route('/api/documents', methods=['POST'])
def create_document():
    """
    Créer un nouveau document avec QR code
    
    Body JSON:
    {
        "category_name": "RH",
        "subcategory_name": "CONTRATS",
        "filename": "contrat_dupont.pdf",
        "file_path": "uploads/RH/CONTRATS/2025/contrat_dupont.pdf",
        "year": 2025,
        "title": "Contrat de travail Dupont",
        "description": "Contrat CDI pour M. Dupont"
    }
    """
    try:
        data = request.get_json()
        
        # Validation des données
        required_fields = ['category_name', 'subcategory_name', 'filename', 'file_path', 'year']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Champ requis manquant: {field}'
                }), 400
        
        # Appeler la procédure stockée
        params = (
            data['subcategory_name'],
            data['category_name'],
            data['filename'],
            data['file_path'],
            data['year'],
            data.get('title', ''),
            data.get('description', '')
        )
        
        result = db.execute_procedure('create_document_with_qr', params)
        
        if result:
            document_info = result[0]
            
            # Générer le QR code
            qr_path = qr_generator.generate_document_qr(document_info['document_code'])
            
            return jsonify({
                'success': True,
                'document_code': document_info['document_code'],
                'qr_identifier': document_info['qr_identifier'],
                'qr_payload': document_info['qr_payload'],
                'qr_image_path': qr_path
            })
        
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la création du document'
        }), 500
        
    except Exception as e:
        logger.error(f"Erreur lors de la création du document: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500

@app.route('/api/documents')
def list_documents():
    """Lister tous les documents"""
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
        JOIN qrcodes q ON d.id = q.document_id
        ORDER BY d.created_at DESC
        """
        
        documents = db.execute_query(query)
        
        return jsonify({
            'success': True,
            'documents': documents
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des documents: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500

@app.route('/qr_images/<filename>')
def serve_qr_image(filename):
    """Servir les images de QR codes"""
    return send_from_directory(Config.QR_IMAGES_FOLDER, filename)

@app.route('/uploads/<path:filename>')
def serve_document(filename):
    """Servir les documents PDF"""
    return send_from_directory(Config.UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
