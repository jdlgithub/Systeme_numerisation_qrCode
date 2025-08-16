import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-key'
    
    # Configuration MySQL
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'qr_archives')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    
    # Configuration des fichiers
    UPLOAD_FOLDER = 'uploads'
    QR_IMAGES_FOLDER = 'qr_images'
    
    # Créer les dossiers s'ils n'existent pas
    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.QR_IMAGES_FOLDER, exist_ok=True)
