from flask import Flask
import os
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Factory function pour créer l'application Flask"""
    app = Flask(__name__)
    
    # Configuration depuis les variables d'environnement
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'change-this-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Dossiers
    app.config['ARCHIVES_FOLDER'] = os.environ.get('ARCHIVES_FOLDER', 'Archives')
    app.config['QR_IMAGES_FOLDER'] = os.environ.get('QR_IMAGES_FOLDER', 'qr_images')
    
    # Serveur
    app.config['BASE_URL'] = os.environ.get('BASE_URL', 'http://localhost:5000')
    app.config['SERVER_HOST'] = os.environ.get('SERVER_HOST', 'localhost')
    app.config['SERVER_PORT'] = int(os.environ.get('SERVER_PORT', 5000))
    
    # Créer les dossiers nécessaires
    os.makedirs(app.config['ARCHIVES_FOLDER'], exist_ok=True)
    os.makedirs(app.config['QR_IMAGES_FOLDER'], exist_ok=True)
    
    # Enregistrer les blueprints
    from routes.auth import auth_bp
    from routes.qr import qr_bp
    from routes.admin import admin_bp
    from routes.api import api_bp
    from routes.files import files_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(qr_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(files_bp)
    
    return app

# Créer l'application
app = create_app()

if __name__ == '__main__':
    app.run(
        debug=app.config['DEBUG'], 
        host=app.config['SERVER_HOST'], 
        port=app.config['SERVER_PORT']
    )
