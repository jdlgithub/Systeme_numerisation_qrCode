from flask import Blueprint, render_template, request, jsonify, current_app
from database import db
from routes.decorators import admin_required
from routes.utils import create_document_simple
from qr_generator import qr_generator
import os
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@admin_required
def index():
    """Page d'accueil de l'application (admin seulement)"""
    return render_template('index.html')

@admin_bp.route('/admin')
@admin_required
def admin_panel():
    """Page d'administration pour gérer les catégories et sous-catégories"""
    return render_template('admin.html')

@admin_bp.route('/api/scan-archives', methods=['POST'])
@admin_required
def scan_archives():
    """API: Scanner la structure Archives/ et créer tous les QR codes"""
    try:
        from archive_scanner import ArchiveScanner
        
        scanner = ArchiveScanner()
        success = scanner.scan_and_register_all()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Structure Archives/ scannée et QR codes générés avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors du scan de la structure'
            }), 500
            
    except Exception as e:
        logger.error(f"Erreur lors du scan des archives: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500

@admin_bp.route('/api/categories', methods=['GET'])
def list_categories():
    """API: Lister toutes les catégories"""
    try:
        # Vérifier si la table existe
        try:
            query = """
            SELECT 
                c.id,
                c.name,
                c.description,
                COUNT(DISTINCT sc.id) as subcategory_count,
                COUNT(DISTINCT d.id) as document_count,
                q.qr_identifier
            FROM categories c
            LEFT JOIN subcategories sc ON c.id = sc.category_id
            LEFT JOIN documents d ON sc.id = d.subcategory_id
            LEFT JOIN qrcodes q ON c.id = q.category_id AND q.qr_type = 'CATEGORY'
            GROUP BY c.id, c.name, c.description, q.qr_identifier
            ORDER BY c.name
            """
            
            categories = db.execute_query(query)
            
            return jsonify({
                'success': True,
                'categories': categories or []
            })
        except Exception as table_error:
            logger.warning(f"Table categories non trouvée: {table_error}")
            return jsonify({
                'success': True,
                'categories': []
            })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des catégories: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500

@admin_bp.route('/api/categories', methods=['POST'])
@admin_required
def create_category():
    """API: Créer une nouvelle catégorie avec QR code"""
    try:
        data = request.get_json()
        
        # Validation
        if 'name' not in data:
            return jsonify({
                'success': False,
                'error': 'Le nom de la catégorie est requis'
            }), 400
        
        name = data['name'].upper().strip()
        description = data.get('description', f'Catégorie {name}')
        
        # Vérifier si la catégorie existe déjà
        existing = db.execute_query_safe("SELECT id FROM categories WHERE name = %s", (name,))
        if existing:
            return jsonify({
                'success': False,
                'error': 'Cette catégorie existe déjà'
            }), 400
        
        # Créer la catégorie
        db.execute_query("INSERT INTO categories (name, description) VALUES (%s, %s)", (name, description))
        category_id = db.execute_query("SELECT LAST_INSERT_ID() as id")[0]['id']
        
        # Créer le QR code
        qr_identifier = f"CAT-{name}"
        qr_payload = f"{current_app.config['BASE_URL']}/qr/{qr_identifier}"
        qr_image_path = f"qr_images/{qr_identifier}.png"
        folder_path = f"Archives/{name}"
        
        qr_query = """
        INSERT INTO qrcodes (qr_type, qr_identifier, qr_payload, category_id, folder_path, qr_image_path)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        db.execute_query(qr_query, ('CATEGORY', qr_identifier, qr_payload, category_id, folder_path, qr_image_path))
        
        # Générer l'image QR
        qr_generator.generate_qr_code(qr_identifier, qr_payload)
        
        # Créer le dossier physique
        os.makedirs(os.path.join(current_app.config['ARCHIVES_FOLDER'], name), exist_ok=True)
        
        return jsonify({
            'success': True,
            'category': {
                'id': category_id,
                'name': name,
                'description': description,
                'qr_identifier': qr_identifier,
                'folder_path': folder_path
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de la catégorie: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500

@admin_bp.route('/api/subcategories', methods=['POST'])
@admin_required
def create_subcategory():
    """API: Créer une nouvelle sous-catégorie avec QR code"""
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['category_id', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Champ requis manquant: {field}'
                }), 400
        
        category_id = data['category_id']
        name = data['name'].upper().strip()
        description = data.get('description', f'Sous-catégorie {name}')
        
        # Vérifier que la catégorie existe
        category = db.execute_query_safe("SELECT name FROM categories WHERE id = %s", (category_id,))
        if not category:
            return jsonify({
                'success': False,
                'error': 'Catégorie non trouvée'
            }), 404
        
        category_name = category[0]['name']
        
        # Vérifier si la sous-catégorie existe déjà
        existing = db.execute_query_safe(
            "SELECT id FROM subcategories WHERE category_id = %s AND name = %s", 
            (category_id, name)
        )
        if existing:
            return jsonify({
                'success': False,
                'error': 'Cette sous-catégorie existe déjà dans cette catégorie'
            }), 400
        
        # Créer la sous-catégorie
        db.execute_query(
            "INSERT INTO subcategories (category_id, name, description) VALUES (%s, %s, %s)", 
            (category_id, name, description)
        )
        subcategory_id = db.execute_query("SELECT LAST_INSERT_ID() as id")[0]['id']
        
        # Créer le QR code
        qr_identifier = f"SUBCAT-{category_name}-{name}"
        qr_payload = f"{current_app.config['BASE_URL']}/qr/{qr_identifier}"
        qr_image_path = f"qr_images/{qr_identifier}.png"
        folder_path = f"Archives/{category_name}/{name}"
        
        qr_query = """
        INSERT INTO qrcodes (qr_type, qr_identifier, qr_payload, subcategory_id, folder_path, qr_image_path)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        db.execute_query(qr_query, ('SUBCATEGORY', qr_identifier, qr_payload, subcategory_id, folder_path, qr_image_path))
        
        # Générer l'image QR
        qr_generator.generate_qr_code(qr_identifier, qr_payload)
        
        # Créer le dossier physique
        os.makedirs(os.path.join(current_app.config['ARCHIVES_FOLDER'], category_name, name), exist_ok=True)
        
        return jsonify({
            'success': True,
            'subcategory': {
                'id': subcategory_id,
                'name': name,
                'description': description,
                'category_name': category_name,
                'qr_identifier': qr_identifier,
                'folder_path': folder_path
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de la sous-catégorie: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500

@admin_bp.route('/api/subcategories/<int:category_id>')
def list_subcategories(category_id):
    """API: Lister les sous-catégories d'une catégorie"""
    try:
        query = """
        SELECT 
            sc.id,
            sc.name,
            sc.description,
            COUNT(d.id) as document_count,
            q.qr_identifier
        FROM subcategories sc
        LEFT JOIN documents d ON sc.id = d.subcategory_id
        LEFT JOIN qrcodes q ON sc.id = q.subcategory_id AND q.qr_type = 'SUBCATEGORY'
        WHERE sc.category_id = %s
        GROUP BY sc.id, sc.name, sc.description, q.qr_identifier
        ORDER BY sc.name
        """
        
        subcategories = db.execute_query_safe(query, (category_id,))
        
        return jsonify({
            'success': True,
            'subcategories': subcategories or []
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des sous-catégories: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500

@admin_bp.route('/api/documents', methods=['POST'])
@admin_required
def create_document():
    """API: Créer un nouveau document avec génération automatique du QR code"""
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
        
        # Créer le document 
        result = create_document_simple(
            data['category_name'],
            data['subcategory_name'], 
            data['filename'],
            data['year'],
            data.get('title', ''),
            data.get('description', ''),
            current_app.config['BASE_URL']
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
