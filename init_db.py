"""
Script d'initialisation de la base de données MySQL
Crée la base de données et toutes les tables nécessaires
"""

import mysql.connector
from mysql.connector import Error
import logging
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database():
    """Créer la base de données si elle n'existe pas"""
    try:
        # Connexion sans spécifier de base de données
        connection = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD', ''),
            port=int(os.environ.get('DB_PORT', 3306))
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Créer la base de données
            db_name = os.environ.get('DB_NAME', 'qr_archives')
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f" Base de données '{db_name}' créée ou déjà existante")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        logger.error(f" Erreur lors de la création de la base de données: {e}")
        raise

def create_tables():
    """Créer toutes les tables nécessaires"""
    try:
        # Connexion à la base de données
        connection = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'qr_archives'),
            port=int(os.environ.get('DB_PORT', 3306))
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Table des utilisateurs
            create_users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                email VARCHAR(100),
                role ENUM('admin', 'user') DEFAULT 'user',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_users_table)
            logger.info(" Table 'users' créée")
            
            # Table des catégories
            create_categories_table = """
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_categories_table)
            logger.info(" Table 'categories' créée")
            
            # Table des sous-catégories
            create_subcategories_table = """
            CREATE TABLE IF NOT EXISTS subcategories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category_id INT NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
                UNIQUE KEY unique_subcategory (category_id, name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_subcategories_table)
            logger.info(" Table 'subcategories' créée")
            
            # Table des séquences
            create_sequences_table = """
            CREATE TABLE IF NOT EXISTS sequences (
                id INT AUTO_INCREMENT PRIMARY KEY,
                subcategory_id INT NOT NULL,
                year INT NOT NULL,
                current_sequence INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (subcategory_id) REFERENCES subcategories(id) ON DELETE CASCADE,
                UNIQUE KEY unique_sequence (subcategory_id, year)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_sequences_table)
            logger.info(" Table 'sequences' créée")
            
            # Table des documents
            create_documents_table = """
            CREATE TABLE IF NOT EXISTS documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                subcategory_id INT NOT NULL,
                document_code VARCHAR(100) UNIQUE NOT NULL,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                year INT NOT NULL,
                title VARCHAR(255),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (subcategory_id) REFERENCES subcategories(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_documents_table)
            logger.info(" Table 'documents' créée")
            
            # Table des QR codes
            create_qrcodes_table = """
            CREATE TABLE IF NOT EXISTS qrcodes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                qr_type ENUM('CATEGORY', 'SUBCATEGORY', 'DOCUMENT') NOT NULL,
                qr_identifier VARCHAR(100) UNIQUE NOT NULL,
                qr_payload TEXT NOT NULL,
                qr_image_path VARCHAR(255),
                folder_path VARCHAR(500),
                category_id INT NULL,
                subcategory_id INT NULL,
                document_id INT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
                FOREIGN KEY (subcategory_id) REFERENCES subcategories(id) ON DELETE CASCADE,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_qrcodes_table)
            logger.info(" Table 'qrcodes' créée")
            
            # Valider les changements
            connection.commit()
            
            cursor.close()
            connection.close()
            
            logger.info(" Toutes les tables ont été créées avec succès")
            
    except Error as e:
        logger.error(f" Erreur lors de la création des tables: {e}")
        raise

def main():
    """Fonction principale d'initialisation"""
    logger.info("=== Initialisation de la base de données ===")
    
    try:
        # Créer la base de données
        create_database()
        
        # Créer les tables
        create_tables()
        
        logger.info("Initialisation terminée avec succès")
        logger.info("Vous pouvez maintenant lancer l'application avec: python app.py")
        
    except Exception as e:
        logger.error(f"Échec de l'initialisation: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
