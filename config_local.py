import os

class Config:
    SECRET_KEY = 'dev-secret-key-local'
    
    # Configuration MySQL pour développement local
    DB_HOST = 'localhost'
    DB_USER = 'Jdl'  # Remplacez par votre nom d'utilisateur MySQL
    DB_PASSWORD = 'Minecraft77jdl@.'  # Remplacez par votre mot de passe MySQL
    DB_NAME = 'qr_archives'
    DB_PORT = 3306
    
    # Configuration des fichiers
    UPLOAD_FOLDER = 'uploads'
    QR_IMAGES_FOLDER = 'qr_images'
    
    # Créer les dossiers s'ils n'existent pas
    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.QR_IMAGES_FOLDER, exist_ok=True)
