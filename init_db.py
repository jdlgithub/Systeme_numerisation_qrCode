import mysql.connector
import os
from dotenv import load_dotenv
import logging

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialiser complètement la base de données"""
    
    # Paramètres de connexion depuis .env
    db_config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWORD', ''),
        'port': int(os.environ.get('DB_PORT', 3306))
    }
    
    db_name = os.environ.get('DB_NAME', 'qr_archives')
    
    try:
        # 1. Connexion sans base de données pour la créer
        logger.info(" Connexion à MySQL...")
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # 2. Créer la base de données
        logger.info(f" Création de la base de données '{db_name}'...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.execute(f"USE {db_name}")
        
        # 3. Créer les tables
        logger.info(" Création des tables...")
        
        # Table categories
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Table subcategories
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS subcategories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id),
            UNIQUE KEY unique_subcategory (category_id, name)
        )
        """)
        
        # Table documents
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subcategory_id INT NOT NULL,
            document_code VARCHAR(50) NOT NULL UNIQUE,
            filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            year INT NOT NULL,
            title VARCHAR(255),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subcategory_id) REFERENCES subcategories(id)
        )
        """)
        
        # Table qrcodes - Support pour hiérarchie complète
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS qrcodes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            qr_type ENUM('DOCUMENT', 'SUBCATEGORY', 'CATEGORY') NOT NULL,
            qr_identifier VARCHAR(100) NOT NULL UNIQUE,
            qr_payload TEXT NOT NULL,
            document_id INT NULL,
            subcategory_id INT NULL,
            category_id INT NULL,
            folder_path VARCHAR(500) NULL,
            qr_image_path VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id),
            FOREIGN KEY (subcategory_id) REFERENCES subcategories(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
        """)
        
        # Table sequences
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sequences (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subcategory_id INT NOT NULL,
            year INT NOT NULL,
            current_sequence INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subcategory_id) REFERENCES subcategories(id),
            UNIQUE KEY unique_sequence (subcategory_id, year)
        )
        """)
        
        # Table users pour l'authentification
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
            email VARCHAR(100),
            full_name VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL
        )
        """)
        
        
        connection.commit()
        
        # 4. Vérification
        logger.info(f" Base de données initialisée avec succès!")
        logger.info(f"    Tables créées et prêtes à recevoir des données")
        logger.info(f"    Base: {db_name}")
        logger.info(f"    Host: {db_config['host']}:{db_config['port']}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        logger.error(f" Erreur d'initialisation: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== Initialisation Base de Données QR Archives ===")
    if init_database():
        logger.info(" Prêt à lancer l'application avec: python app.py")
    else:
        logger.error(" Échec de l'initialisation")
