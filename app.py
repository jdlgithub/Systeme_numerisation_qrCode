from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, url_for
from database import db
from qr_generator import qr_generator
import os
import logging
from dotenv import load_dotenv
from functools import wraps
import hashlib

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

# Décorateurs d'authentification
def login_required(f):
    """Décorateur pour vérifier que l'utilisateur est connecté"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.headers.get('Accept', '').startswith('application/json'):
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Décorateur pour vérifier que l'utilisateur est admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.headers.get('Accept', '').startswith('application/json'):
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            return redirect(url_for('login'))
        
        if session.get('user_role') != 'admin':
            if request.headers.get('Accept', '').startswith('application/json'):
                return jsonify({'success': False, 'error': 'Accès admin requis'}), 403
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def hash_password(password):
    """Hasher un mot de passe avec SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

#  Fontions utilitaires pour la création de documents 

def create_document_simple(category_name, subcategory_name, filename, year, title="", description=""):
    """
    Créer un document avec génération automatique du code et du chemin

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

# Routes d'authentification

@app.route('/login')
def login():
    """Page de connexion"""
    if 'user_id' in session:
        if session.get('user_role') == 'admin':
            return redirect(url_for('index'))
        else:
            return redirect(url_for('user_dashboard'))
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """API: Authentification utilisateur"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Nom d\'utilisateur et mot de passe requis'
            }), 400
        
        # Vérifier les identifiants
        password_hash = hash_password(password)
        query = """
        SELECT id, username, full_name, role, is_active
        FROM users 
        WHERE username = %s AND password_hash = %s AND is_active = TRUE
        """
        
        result = db.execute_query(query, (username, password_hash))
        
        if result:
            user = result[0]
            
            # Créer la session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user.get('full_name')
            session['user_role'] = user['role']
            
            # Mettre à jour la dernière connexion
            db.execute_query(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                (user['id'],)
            )
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'full_name': user.get('full_name'),
                    'role': user['role']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Identifiants incorrects'
            }), 401
            
    except Exception as e:
        logger.error(f"Erreur lors de la connexion: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500

@app.route('/api/logout')
def api_logout():
    """API: Déconnexion"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/user-info')
@login_required
def api_user_info():
    """API: Informations utilisateur connecté"""
    return jsonify({
        'success': True,
        'user': {
            'id': session['user_id'],
            'username': session['username'],
            'full_name': session.get('full_name'),
            'role': session['user_role']
        }
    })

@app.route('/user-dashboard')
@login_required
def user_dashboard():
    """Tableau de bord utilisateur"""
    if session.get('user_role') == 'admin':
        return redirect(url_for('index'))
    return render_template('user_dashboard.html')

# Routes web 

@app.route('/')
@login_required
def index():
    """Page d'accueil de l'application (admin seulement)"""
    if session.get('user_role') != 'admin':
        return redirect(url_for('user_dashboard'))
    return render_template('index.html')

@app.route('/qr/<identifier>')
def resolve_qr(identifier):
    """
    Résoudre un QR code hiérarchique (catégorie, sous-catégorie ou document)
    
    Args:
        identifier (str): Identifiant du QR code
    
    Returns:
        HTML: Page de visualisation ou JSON pour API
    """
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
    
    result = db.execute_query(query, (identifier,))
    
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

def _resolve_subcategory_qr(identifier):
    """Résoudre un QR code de sous-catégorie"""
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
    
    result = db.execute_query(query, (identifier,))
    
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
        
        documents = db.execute_query(docs_query, (subcategory['subcategory_name'], identifier))
        subcategory['documents'] = documents
        
        if request.headers.get('Accept', '').startswith('application/json'):
            return jsonify({
                'success': True,
                'type': 'subcategory',
                'data': subcategory
            })
        else:
            return render_template('subcategory_view.html', subcategory=subcategory)
    
    return None

def _resolve_category_qr(identifier):
    """Résoudre un QR code de catégorie"""
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
    
    result = db.execute_query(query, (identifier,))
    
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
        
        subcategories = db.execute_query(subcat_query, (identifier,))
        category['subcategories'] = subcategories
        
        if request.headers.get('Accept', '').startswith('application/json'):
            return jsonify({
                'success': True,
                'type': 'category',
                'data': category
            })
        else:
            return render_template('category_view.html', category=category)
    
    return None

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

@app.route('/api/scan-archives', methods=['POST'])
@admin_required
def scan_archives():
    """
    API: Scanner la structure Archives/ et créer tous les QR codes
    """
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

@app.route('/api/categories', methods=['GET'])
def list_categories():
    """API: Lister toutes les catégories"""
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
            'categories': categories
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des catégories: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500

@app.route('/api/categories', methods=['POST'])
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
        existing = db.execute_query("SELECT id FROM categories WHERE name = %s", (name,))
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
        qr_payload = f"{BASE_URL}/qr/{qr_identifier}"
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
        os.makedirs(os.path.join(ARCHIVES_FOLDER, name), exist_ok=True)
        
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

@app.route('/api/subcategories', methods=['POST'])
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
        category = db.execute_query("SELECT name FROM categories WHERE id = %s", (category_id,))
        if not category:
            return jsonify({
                'success': False,
                'error': 'Catégorie non trouvée'
            }), 404
        
        category_name = category[0]['name']
        
        # Vérifier si la sous-catégorie existe déjà
        existing = db.execute_query(
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
        qr_payload = f"{BASE_URL}/qr/{qr_identifier}"
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
        os.makedirs(os.path.join(ARCHIVES_FOLDER, category_name, name), exist_ok=True)
        
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

@app.route('/api/subcategories/<int:category_id>')
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
        
        subcategories = db.execute_query(query, (category_id,))
        
        return jsonify({
            'success': True,
            'subcategories': subcategories
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des sous-catégories: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500

@app.route('/admin')
@admin_required
def admin_panel():
    """Page d'administration pour gérer les catégories et sous-catégories"""
    return render_template('admin.html')

@app.route('/api/documents', methods=['POST'])
@admin_required
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
        
        # Créer le document 
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

# API endspoints

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
        LEFT JOIN qrcodes q ON d.id = q.document_id
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

#  Fichiers statiques et images QR 

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
