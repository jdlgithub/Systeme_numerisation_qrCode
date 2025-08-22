"""
Script pour repartir sur une base propre
"""
import mysql.connector
import os
import shutil
import glob
from dotenv import load_dotenv
import logging
from pathlib import Path

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
        logger.info("Connexion à MySQL...")
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # 2. Supprimer complètement la base de données
        logger.info(f"Suppression complète de la base '{db_name}'...")
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        
        # 3. Recréer la base de données vide
        logger.info(f"Création d'une nouvelle base '{db_name}'...")
        cursor.execute(f"CREATE DATABASE {db_name}")
        cursor.execute(f"USE {db_name}")
        
        # 4. Créer les tables propres
        logger.info("Création des tables...")
        
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
        
        # Table qrcodes (structure hiérarchique complète)
        cursor.execute("""
        CREATE TABLE qrcodes (
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
        
        # 5. Tables créées avec succès - Base vide et propre
        logger.info("Structure de base de données créée (vide)")
        logger.info("Utilisez l'interface /admin pour créer vos catégories")
        
        connection.commit()
        
        # 6. Vérification finale
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        table_count = len(tables)
        
        logger.info("Base de données complètement réinitialisée !")
        logger.info(f"Base: {db_name} (PROPRE)")
        logger.info(f"{table_count} tables créées")
        logger.info(" 0 catégories (base vide)")
        logger.info(" 0 sous-catégories (base vide)")
        logger.info(" 0 documents (base vide)")
        logger.info(" 0 QR codes (base vide)")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur de nettoyage: {e}")
        return False

def clean_qr_images():
    """Nettoyer les images QR générées"""
    qr_folder = "qr_images"
    if os.path.exists(qr_folder):
        qr_files = glob.glob(f"{qr_folder}/*.png")
        deleted_count = 0
        for qr_file in qr_files:
            try:
                os.remove(qr_file)
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Impossible de supprimer {qr_file}: {e}")
        
        logger.info(f"Dossier {qr_folder}/ nettoyé ({deleted_count} fichiers supprimés)")
    else:
        logger.info(f"Dossier {qr_folder}/ n'existe pas")

def clean_archives_folder():
    """Nettoyer le dossier Archives (ATTENTION: supprime tous les PDFs !)"""
    archives_folder = "Archives"
    if os.path.exists(archives_folder):
        try:
            # Compter les fichiers avant suppression
            total_files = sum([len(files) for r, d, files in os.walk(archives_folder)])
            
            # Supprimer tout le contenu
            shutil.rmtree(archives_folder)
            
            # Recréer le dossier vide
            os.makedirs(archives_folder)
            
            logger.info(f"Dossier {archives_folder}/ complètement nettoyé ({total_files} fichiers supprimés)")
            logger.info(f"Dossier {archives_folder}/ recréé (vide)")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage de {archives_folder}/: {e}")
    else:
        # Créer le dossier s'il n'existe pas
        os.makedirs(archives_folder)
        logger.info(f"Dossier {archives_folder}/ créé")

def reset_complete_system():
    """Réinitialisation complète du système (base + fichiers)"""
    logger.info("Réinitialisation complète du système QR Archives...")
    
    success = True
    
    # 1. Réinitialiser la base de données
    if reset_database():
        logger.info("Base de données réinitialisée")
    else:
        logger.error("Échec de la réinitialisation de la base de données")
        success = False
    
    # 2. Nettoyer les images QR
    try:
        clean_qr_images()
        logger.info("Images QR nettoyées")
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des images QR: {e}")
        success = False
    
    return success

def reset_with_archives():
    """Réinitialisation complète incluant les Archives (DESTRUCTIF !)"""
    logger.info("Réinitialisation DESTRUCTIVE du système QR Archives...")
    logger.warning("ATTENTION: Cette opération va supprimer TOUS les fichiers PDF !")
    
    success = True
    
    # 1. Réinitialisation complète normale
    if not reset_complete_system():
        success = False
    
    # 2. Nettoyer aussi les Archives
    try:
        clean_archives_folder()
        logger.info("Dossier Archives nettoyé")
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des Archives: {e}")
        success = False
    
    return success

if __name__ == "__main__":
    logger.info("=== RÉINITIALISATION SYSTÈME QR ARCHIVES ===")
    logger.info("")
    logger.info("Options disponibles:")
    logger.info("1. Réinitialisation BASE SEULEMENT (conserve les PDFs)")
    logger.info("2. Réinitialisation COMPLÈTE (base + QR, conserve les PDFs)")
    logger.info("3. Réinitialisation DESTRUCTIVE (base + QR + PDFs)")
    logger.info("4. Annuler")
    logger.info("")
    
    try:
        choice = input("Choisissez une option (1-4): ").strip()
        
        if choice == "1":
            logger.warning("Réinitialisation de la base de données seulement")
            confirm = input("Tapez 'OUI' pour confirmer: ")
            if confirm.upper() == 'OUI':
                if reset_database():
                    logger.info("Base de données réinitialisée !")
                    logger.info("Relancez: python app.py")
                else:
                    logger.error("Échec de la réinitialisation")
            else:
                logger.info("Opération annulée")
                
        elif choice == "2":
            logger.warning("Réinitialisation complète (base + images QR)")
            confirm = input("Tapez 'OUI' pour confirmer: ")
            if confirm.upper() == 'OUI':
                if reset_complete_system():
                    logger.info("Système complètement réinitialisé !")
                    logger.info("Relancez: python app.py")
                else:
                    logger.error("Échec de la réinitialisation")
            else:
                logger.info("Opération annulée")
                
        elif choice == "3":
            logger.error("RÉINITIALISATION DESTRUCTIVE - SUPPRIME TOUS LES PDFs !")
            logger.warning("Cette opération est IRRÉVERSIBLE !")
            confirm1 = input("Tapez 'SUPPRIMER' pour confirmer: ")
            if confirm1.upper() == 'SUPPRIMER':
                confirm2 = input("Êtes-vous ABSOLUMENT sûr ? Tapez 'OUI': ")
                if confirm2.upper() == 'OUI':
                    if reset_with_archives():
                        logger.info("Système complètement réinitialisé (DESTRUCTIF) !")
                        logger.info("Relancez: python app.py")
                    else:
                        logger.error("Échec de la réinitialisation destructive")
                else:
                    logger.info("Opération annulée")
            else:
                logger.info("Opération annulée")
                
        elif choice == "4":
            logger.info("Opération annulée par l'utilisateur")
            
        else:
            logger.error("Option invalide")
            
    except KeyboardInterrupt:
        logger.info("\n Opération interrompue par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
