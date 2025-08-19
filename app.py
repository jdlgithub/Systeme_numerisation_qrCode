#!/usr/bin/env python3
"""
Application Flask pour la numérisation de documents avec QR codes
Utilise MySQL local et stockage dans Archives/
"""

from flask import Flask, jsonify, request, render_template, send_from_directory
from database import db
from qr_generator import qr_generator
import os
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration Flask depuis variables d'environnement
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'change-this-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite: 16MB par fichier
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# Variables de configuration depuis .env
ARCHIVES_FOLDER = os.environ.get('ARCHIVES_FOLDER', 'Archives')
QR_IMAGES_FOLDER = os.environ.get('QR_IMAGES_FOLDER', 'qr_images')
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
SERVER_HOST = os.environ.get('SERVER_HOST', 'localhost')
SERVER_PORT = int(os.environ.get('SERVER_PORT', 5000))
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# Créer les dossiers nécessaires
os.makedirs(ARCHIVES_FOLDER, exist_ok=True)
os.makedirs(QR_IMAGES_FOLDER, exist_ok=True)

# ==================== FONCTIONS UTILITAIRES ====================

def create_document_simple(category_name, subcategory_name, filename, year, title="", description=""):
    """
    Créer un document avec génération automatique du code et du chemin
    Remplace la procédure stockée par de la logique Python simple
    """
    try:
        # 1. Récupérer ou créer la catégorie
        category_id = get_or_create_category(category_name)
        
        # 2. Récupérer ou créer la sous-catégorie  
        subcategory_id = get_or_create_subcategory(category_id, subcategory_name)
        
        # 3. Générer le numéro de séquence
        sequence_num = get_next_sequence(subcategory_id, year)
        
        # 4. Générer le code document
        document_code = f"{category_name}-{subcategory_name}-{year}-{sequence_num:04d}"
        
        # 5. Générer le chemin dans Archives
        file_path = f"Archives/{category_name}/{subcategory_name}/{year}/{filename}"
        
        # 6. Insérer le document
        insert_query = """
        INSERT INTO documents (subcategory_id, document_code, filename, file_path, year, title, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        db.execute_query(insert_query, (subcategory_id, document_code, filename, file_path, year, title, description))
        
        # 7. Récupérer l'ID du document créé
        document_id = db.execute_query("SELECT LAST_INSERT_ID() as id")[0]['id']
        
        # 8. Créer le QR code en base
        qr_identifier = document_code
        qr_payload = f"{BASE_URL}/qr/{qr_identifier}"
        qr_image_path = f"qr_images/{qr_identifier}.png"
        
        qr_query = """
        INSERT INTO qrcodes (qr_type, qr_identifier, qr_payload, document_id, qr_image_path)
        VALUES (%s, %s, %s, %s, %s)
        """
        db.execute_query(qr_query, ('DOCUMENT', qr_identifier, qr_payload, document_id, qr_image_path))
        
        # 9. Retourner les informations
        return [{
            'document_code': document_code,
            'qr_identifier': qr_identifier,
            'qr_payload': qr_payload
        }]
        
    except Exception as e:
        logger.error(f"Erreur création document: {e}")
        return None

def get_or_create_category(name):
    """Récupérer l'ID d'une catégorie ou la créer si elle n'existe pas"""
    result = db.execute_query("SELECT id FROM categories WHERE name = %s", (name,))
    if result:
        return result[0]['id']
    
    # Créer la catégorie
    db.execute_query("INSERT INTO categories (name) VALUES (%s)", (name,))
    return db.execute_query("SELECT LAST_INSERT_ID() as id")[0]['id']

def get_or_create_subcategory(category_id, name):
    """Récupérer l'ID d'une sous-catégorie ou la créer"""
    result = db.execute_query("SELECT id FROM subcategories WHERE category_id = %s AND name = %s", (category_id, name))
    if result:
        return result[0]['id']
    
    # Créer la sous-catégorie
    db.execute_query("INSERT INTO subcategories (category_id, name) VALUES (%s, %s)", (category_id, name))
    return db.execute_query("SELECT LAST_INSERT_ID() as id")[0]['id']

def get_next_sequence(subcategory_id, year):
    """Obtenir le prochain numéro de séquence pour une sous-catégorie/année"""
    result = db.execute_query("SELECT current_sequence FROM sequences WHERE subcategory_id = %s AND year = %s", (subcategory_id, year))
    
    if result:
        # Incrémenter la séquence existante
        new_sequence = result[0]['current_sequence'] + 1
        db.execute_query("UPDATE sequences SET current_sequence = %s WHERE subcategory_id = %s AND year = %s", 
                        (new_sequence, subcategory_id, year))
        return new_sequence
    else:
        # Créer une nouvelle séquence
        db.execute_query("INSERT INTO sequences (subcategory_id, year, current_sequence) VALUES (%s, %s, 1)", 
                        (subcategory_id, year))
        return 1

# ==================== ROUTES WEB ====================

@app.route('/')
def index():
    """Page d'accueil de l'application"""
    return render_template('index.html')

@app.route('/qr/<identifier>')
def resolve_qr(identifier):
    """
    Résoudre un QR code et afficher la page du document avec option de téléchargement
    
    Args:
        identifier (str): Identifiant du QR code (code document ou sous-catégorie)
    
    Returns:
        HTML: Page de visualisation du document ou JSON pour API
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
            # Vérifier si c'est une requête API ou une navigation web
            if request.headers.get('Accept', '').startswith('application/json'):
                return jsonify({
                    'success': True,
                    'type': 'document',
                    'data': document
                })
            else:
                # Afficher la page de visualisation du document
                return render_template('document_view.html', document=document)
        
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
            if request.headers.get('Accept', '').startswith('application/json'):
                return jsonify({
                    'success': True,
                    'type': 'subcategory',
                    'data': subcategory
                })
            else:
                return render_template('subcategory_view.html', subcategory=subcategory)
        
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

@app.route('/download/<identifier>')
def download_document(identifier):
    """
    Télécharger directement un document via son identifiant QR
    
    Args:
        identifier (str): Identifiant du QR code du document
    
    Returns:
        File: Fichier PDF à télécharger
    """
    try:
        query = """
        SELECT 
            d.filename,
            d.file_path
        FROM documents d
        JOIN qrcodes q ON d.id = q.document_id
        WHERE q.qr_identifier = %s
        """
        
        result = db.execute_query(query, (identifier,))
        
        if result:
            document = result[0]
            file_path = document['file_path']
            filename = document['filename']
            
            # Vérifier si le fichier existe
            full_path = os.path.join(os.getcwd(), file_path)
            if os.path.exists(full_path):
                directory = os.path.dirname(file_path)
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

@app.route('/api/documents', methods=['POST'])
def create_document():
    """
    API: Créer un nouveau document avec génération automatique du QR code
    
    Body JSON:
    {
        "category_name": "RH",
        "subcategory_name": "CONTRATS", 
        "filename": "contrat_dupont.pdf",
        "year": 2025,
        "title": "Contrat de travail Dupont",
        "description": "Contrat CDI pour M. Dupont"
    }
    
    Le chemin sera automatiquement: Archives/RH/CONTRATS/2025/contrat_dupont.pdf
    """
    try:
        data = request.get_json()
        
        # Validation des champs obligatoires
        required_fields = ['category_name', 'subcategory_name', 'filename', 'year']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Champ requis manquant: {field}'
                }), 400
        
        # Créer le document avec logique simplifiée
        result = create_document_simple(
            data['category_name'],
            data['subcategory_name'], 
            data['filename'],
            data['year'],
            data.get('title', ''),
            data.get('description', '')
        )
        
        if result:
            document_info = result[0]
            
            # Générer l'image QR code physique
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
            'error': 'Impossible de créer le document'
        }), 500
        
    except Exception as e:
        logger.error(f"Erreur lors de la création du document: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500

# ==================== API ENDPOINTS ====================

@app.route('/api/documents')
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

# ==================== FICHIERS STATIQUES ====================

@app.route('/qr_images/<filename>')
def serve_qr_image(filename):
    """Servir les images de QR codes générées"""
    return send_from_directory(QR_IMAGES_FOLDER, filename)

@app.route('/archives/<path:filename>')
def serve_archive_document(filename):
    """Servir les documents PDF depuis le dossier Archives"""
    return send_from_directory(ARCHIVES_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=DEBUG, host=SERVER_HOST, port=SERVER_PORT)
