#!/usr/bin/env python3
"""
Script d'initialisation simplifié de la base de données MySQL
"""

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
        logger.info("🔄 Connexion à MySQL...")
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # 2. Créer la base de données
        logger.info(f"🔄 Création de la base de données '{db_name}'...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.execute(f"USE {db_name}")
        
        # 3. Créer les tables
        logger.info("🔄 Création des tables...")
        
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
        
        # Table qrcodes
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS qrcodes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            qr_type ENUM('DOCUMENT', 'SUBCATEGORY') NOT NULL,
            qr_identifier VARCHAR(100) NOT NULL UNIQUE,
            qr_payload TEXT NOT NULL,
            document_id INT NULL,
            subcategory_id INT NULL,
            qr_image_path VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id),
            FOREIGN KEY (subcategory_id) REFERENCES subcategories(id)
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
        
        # 4. Insérer les données de base
        logger.info("🔄 Insertion des données de base...")
        
        # Catégories
        categories = [
            ('RH', 'Ressources Humaines'),
            ('FACT', 'Facturation'),
            ('CATALG', 'Catalogues')
        ]
        
        for name, desc in categories:
            cursor.execute("INSERT IGNORE INTO categories (name, description) VALUES (%s, %s)", (name, desc))
        
        # Sous-catégories
        subcategories = [
            (1, 'CONTRATS', 'Contrats de travail'),
            (1, 'PAYSLIPS', 'Bulletins de paie'),
            (2, '2023', 'Factures 2023'),
            (2, '2024', 'Factures 2024'),
            (2, '2025', 'Factures 2025'),
            (3, '2023', 'Catalogues 2023'),
            (3, '2024', 'Catalogues 2024'),
            (3, '2025', 'Catalogues 2025')
        ]
        
        for cat_id, name, desc in subcategories:
            cursor.execute("INSERT IGNORE INTO subcategories (category_id, name, description) VALUES (%s, %s, %s)", 
                          (cat_id, name, desc))
        
        connection.commit()
        
        # 5. Vérification
        cursor.execute("SELECT COUNT(*) as count FROM categories")
        cat_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as count FROM subcategories") 
        subcat_count = cursor.fetchone()[0]
        
        logger.info(f"✅ Base de données initialisée avec succès!")
        logger.info(f"   📊 {cat_count} catégories créées")
        logger.info(f"   📁 {subcat_count} sous-catégories créées")
        logger.info(f"   🗄️ Base: {db_name}")
        logger.info(f"   🌐 Host: {db_config['host']}:{db_config['port']}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur d'initialisation: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== Initialisation Base de Données QR Archives ===")
    if init_database():
        logger.info("🎉 Prêt à lancer l'application avec: python app.py")
    else:
        logger.error("💥 Échec de l'initialisation")
