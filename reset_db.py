#!/usr/bin/env python3
"""
Script de nettoyage complet de la base de données MySQL
Supprime tout et repart sur une base propre
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

def reset_database():
    """Nettoyer complètement la base de données et la recréer"""
    
    # Paramètres de connexion depuis .env
    db_config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWORD', ''),
        'port': int(os.environ.get('DB_PORT', 3306))
    }
    
    db_name = os.environ.get('DB_NAME', 'qr_archives')
    
    try:
        # 1. Connexion sans base de données
        logger.info("🔄 Connexion à MySQL...")
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # 2. Supprimer complètement la base de données
        logger.info(f"🗑️ Suppression complète de la base '{db_name}'...")
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        
        # 3. Recréer la base de données vide
        logger.info(f"🆕 Création d'une nouvelle base '{db_name}'...")
        cursor.execute(f"CREATE DATABASE {db_name}")
        cursor.execute(f"USE {db_name}")
        
        # 4. Créer les tables propres
        logger.info("📋 Création des tables...")
        
        # Table categories
        cursor.execute("""
        CREATE TABLE categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Table subcategories
        cursor.execute("""
        CREATE TABLE subcategories (
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
        CREATE TABLE documents (
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
        CREATE TABLE qrcodes (
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
        CREATE TABLE sequences (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subcategory_id INT NOT NULL,
            year INT NOT NULL,
            current_sequence INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subcategory_id) REFERENCES subcategories(id),
            UNIQUE KEY unique_sequence (subcategory_id, year)
        )
        """)
        
        # 5. Insérer les données de base propres
        logger.info("📊 Insertion des données de base...")
        
        # Catégories
        categories = [
            ('RH', 'Ressources Humaines'),
            ('FACT', 'Facturation'),
            ('CATALG', 'Catalogues')
        ]
        
        for name, desc in categories:
            cursor.execute("INSERT INTO categories (name, description) VALUES (%s, %s)", (name, desc))
        
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
            cursor.execute("INSERT INTO subcategories (category_id, name, description) VALUES (%s, %s, %s)", 
                          (cat_id, name, desc))
        
        connection.commit()
        
        # 6. Vérification finale
        cursor.execute("SELECT COUNT(*) as count FROM categories")
        cat_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as count FROM subcategories") 
        subcat_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as count FROM documents")
        doc_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as count FROM qrcodes")
        qr_count = cursor.fetchone()[0]
        
        logger.info("✅ Base de données complètement nettoyée et réinitialisée !")
        logger.info(f"   📊 {cat_count} catégories")
        logger.info(f"   📁 {subcat_count} sous-catégories")
        logger.info(f"   📄 {doc_count} documents")
        logger.info(f"   🔲 {qr_count} QR codes")
        logger.info(f"   🗄️ Base: {db_name} (PROPRE)")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur de nettoyage: {e}")
        return False

def clean_qr_images():
    """Nettoyer aussi les images QR générées"""
    qr_folder = "qr_images"
    if os.path.exists(qr_folder):
        import glob
        qr_files = glob.glob(f"{qr_folder}/*.png")
        for qr_file in qr_files:
            try:
                os.remove(qr_file)
                logger.info(f"🗑️ Supprimé: {qr_file}")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de supprimer {qr_file}: {e}")
        
        logger.info(f"🧹 Dossier {qr_folder}/ nettoyé")

if __name__ == "__main__":
    logger.info("=== NETTOYAGE COMPLET BASE DE DONNÉES ===")
    logger.warning("⚠️ ATTENTION: Cette opération va SUPPRIMER toutes les données !")
    
    # Demander confirmation
    response = input("Êtes-vous sûr de vouloir tout supprimer ? (tapez 'OUI' pour confirmer): ")
    
    if response.upper() == 'OUI':
        logger.info("🚀 Démarrage du nettoyage...")
        
        # Nettoyer la base de données
        if reset_database():
            # Nettoyer les images QR
            clean_qr_images()
            logger.info("🎉 Nettoyage terminé ! Base de données propre et prête.")
            logger.info("💡 Vous pouvez maintenant relancer: python app.py")
        else:
            logger.error("💥 Échec du nettoyage")
    else:
        logger.info("❌ Nettoyage annulé par l'utilisateur")
