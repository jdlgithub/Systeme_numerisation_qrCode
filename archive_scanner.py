
""" Génère les QR codes hiérarchiques
Scanne tous les dossiers, sous-dossiers et fichiers pour créer les QR codes correspondants
"""

import os
import logging
from pathlib import Path
from database import db
from qr_generator import qr_generator
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration
ARCHIVES_FOLDER = os.environ.get('ARCHIVES_FOLDER', 'Archives')
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArchiveScanner:
    def __init__(self):
        self.archives_path = Path(ARCHIVES_FOLDER)
        self.base_url = BASE_URL
        
    def scan_and_register_all(self):
        """Scanner complètement la structure Archives/ et enregistrer tout en base"""
        logger.info("=== Début du scan de la structure Archives/ ===")
        
        if not self.archives_path.exists():
            logger.error(f"Le dossier {ARCHIVES_FOLDER} n'existe pas")
            return False
            
        try:
            # 1. Scanner et enregistrer les catégories (dossiers racine)
            categories = self._scan_categories()
            
            # 2. Scanner et enregistrer les sous-catégories
            subcategories = self._scan_subcategories(categories)
            
            # 3. Scanner et enregistrer tous les fichiers
            files = self._scan_files(subcategories)
            
            # Compter les nouveaux vs existants
            new_files = [f for f in files if f and f.get('status') == 'new']
            existing_files = [f for f in files if f and f.get('status') == 'existing']
            
            logger.info(f"=== Scan terminé ===")
            logger.info(f"{len(categories)} catégories")
            logger.info(f"{len(subcategories)} sous-catégories") 
            logger.info(f"{len(new_files)} nouveaux fichiers ajoutés")
            logger.info(f"{len(existing_files)} fichiers existants ignorés")
            logger.info(f"{len(files)} fichiers traités au total")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du scan: {e}")
            return False
    
    def _scan_categories(self):
        """Scanner et enregistrer toutes les catégories (dossiers racine)"""
        logger.info("Scan des catégories...")
        categories = {}
        
        for item in self.archives_path.iterdir():
            if item.is_dir():
                category_name = item.name
                logger.info(f"Traitement catégorie: {category_name}")
                
                # Créer ou récupérer la catégorie en base
                category_id = self._get_or_create_category(category_name)
                categories[category_name] = {
                    'id': category_id,
                    'path': item,
                    'name': category_name
                }
                
                # Créer le QR code pour la catégorie
                self._create_category_qr(category_id, category_name)
        
        return categories
    
    def _scan_subcategories(self, categories):
        """Scanner et enregistrer toutes les sous-catégories"""
        logger.info("Scan des sous-catégories...")
        subcategories = {}
        
        for cat_name, cat_info in categories.items():
            cat_path = cat_info['path']
            category_id = cat_info['id']
            
            for item in cat_path.iterdir():
                if item.is_dir():
                    subcat_name = item.name
                    logger.info(f"   Traitement sous-catégorie: {cat_name}/{subcat_name}")
                    
                    # Créer ou récupérer la sous-catégorie
                    subcat_id = self._get_or_create_subcategory(category_id, subcat_name)
                    
                    subcat_key = f"{cat_name}/{subcat_name}"
                    subcategories[subcat_key] = {
                        'id': subcat_id,
                        'path': item,
                        'category_name': cat_name,
                        'subcategory_name': subcat_name,
                        'category_id': category_id
                    }
                    
                    # Créer le QR code pour la sous-catégorie
                    self._create_subcategory_qr(subcat_id, cat_name, subcat_name)
        
        return subcategories
    
    def _scan_files(self, subcategories):
        """Scanner et enregistrer tous les fichiers"""
        logger.info("Scan des fichiers...")
        files = []
        
        # Scanner les fichiers dans les sous-catégories
        for subcat_key, subcat_info in subcategories.items():
            subcat_path = subcat_info['path']
            files.extend(self._scan_files_in_directory(subcat_path, subcat_info))
        
        # Scanner les fichiers directement dans les catégories
        for item in self.archives_path.iterdir():
            if item.is_file() and item.suffix.lower() == '.pdf':
                logger.info(f"   Fichier racine: {item.name}")
                file_info = self._register_root_file(item)
                if file_info:
                    files.append(file_info)
        
        return files
    
    def _scan_files_in_directory(self, directory_path, subcat_info):
        """Scanner récursivement les fichiers dans un répertoire"""
        files = []
        
        for item in directory_path.rglob('*.pdf'):
            if item.is_file():
                logger.info(f"   Fichier: {item.relative_to(self.archives_path)}")
                
                # Extraire l'année du chemin si possible
                year = self._extract_year_from_path(item)
                
                file_info = self._register_file(item, subcat_info, year)
                if file_info:
                    files.append(file_info)
        
        return files
    
    def _register_file(self, file_path, subcat_info, year):
        """Enregistrer un fichier en base avec son QR code"""
        try:
            filename = file_path.name
            relative_path = str(file_path).replace('\\', '/')
            
            # Vérifier si le document existe déjà (même nom et même chemin)
            existing_doc = db.execute_query(
                "SELECT id, document_code FROM documents WHERE filename = %s AND file_path = %s", 
                (filename, str(relative_path))
            )
            
            if existing_doc:
                logger.info(f"   Document {filename} existe déjà dans {relative_path} - ignoré")
                return {
                    'document_id': existing_doc[0]['id'],
                    'document_code': existing_doc[0]['document_code'],
                    'filename': filename,
                    'status': 'existing'
                }
            
            # Générer le code document
            sequence_num = self._get_next_sequence(subcat_info['id'], year)
            document_code = f"{subcat_info['category_name']}-{subcat_info['subcategory_name']}-{year}-{sequence_num:04d}"
            
            # Insérer le document
            insert_query = """
            INSERT INTO documents (subcategory_id, document_code, filename, file_path, year, title, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            db.execute_query(insert_query, (
                subcat_info['id'], 
                document_code, 
                filename, 
                str(relative_path), 
                year, 
                filename.replace('.pdf', ''), 
                f"Document {filename}"
            ))
            
            # Récupérer l'ID du document
            document_id = db.execute_query("SELECT LAST_INSERT_ID() as id")[0]['id']
            
            # Créer le QR code
            self._create_document_qr(document_id, document_code)
            
            logger.info(f"   Nouveau document ajouté: {document_code}")
            
            return {
                'document_id': document_id,
                'document_code': document_code,
                'filename': filename,
                'status': 'new'
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du fichier {file_path}: {e}")
            return None
    
    def _register_root_file(self, file_path):
        """Enregistrer un fichier à la racine d'Archives/"""
        try:
            filename = file_path.name
            relative_path = str(file_path).replace('\\', '/')
            year = 2025  # Année par défaut pour les fichiers racine
            
            # Vérifier si le document existe déjà (même nom et même chemin)
            existing_doc = db.execute_query(
                "SELECT id, document_code FROM documents WHERE filename = %s AND file_path = %s", 
                (filename, str(relative_path))
            )
            
            if existing_doc:
                logger.info(f"   Document racine {filename} existe déjà dans {relative_path} - ignoré")
                return {
                    'document_id': existing_doc[0]['id'],
                    'document_code': existing_doc[0]['document_code'],
                    'filename': filename,
                    'status': 'existing'
                }
            
            # Créer une catégorie "GENERAL" si nécessaire
            general_cat_id = self._get_or_create_category("GENERAL")
            general_subcat_id = self._get_or_create_subcategory(general_cat_id, "DIVERS")
            
            # Générer le code document
            sequence_num = self._get_next_sequence(general_subcat_id, year)
            document_code = f"GENERAL-DIVERS-{year}-{sequence_num:04d}"
            
            # Insérer le document
            insert_query = """
            INSERT INTO documents (subcategory_id, document_code, filename, file_path, year, title, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            db.execute_query(insert_query, (
                general_subcat_id,
                document_code,
                filename,
                str(relative_path),
                year,
                filename.replace('.pdf', ''),
                f"Document racine {filename}"
            ))
            
            # Récupérer l'ID du document
            document_id = db.execute_query("SELECT LAST_INSERT_ID() as id")[0]['id']
            
            # Créer le QR code
            self._create_document_qr(document_id, document_code)
            
            logger.info(f"   Nouveau document racine ajouté: {document_code}")
            
            return {
                'document_id': document_id,
                'document_code': document_code,
                'filename': filename,
                'status': 'new'
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du fichier racine {file_path}: {e}")
            return None
    
    def _create_category_qr(self, category_id, category_name):
        """Créer un QR code pour une catégorie"""
        try:
            qr_identifier = f"CAT-{category_name}"
            qr_payload = f"{self.base_url}/qr/{qr_identifier}"
            qr_image_path = f"qr_images/{qr_identifier}.png"
            folder_path = f"Archives/{category_name}"
            
            # Vérifier si le QR existe déjà
            existing = db.execute_query("SELECT id FROM qrcodes WHERE qr_identifier = %s", (qr_identifier,))
            if existing:
                logger.info(f"   QR catégorie {category_name} existe déjà")
                return
            
            # Insérer en base
            qr_query = """
            INSERT INTO qrcodes (qr_type, qr_identifier, qr_payload, category_id, folder_path, qr_image_path)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            db.execute_query(qr_query, ('CATEGORY', qr_identifier, qr_payload, category_id, folder_path, qr_image_path))
            
            # Générer l'image QR
            qr_generator.generate_qr_code(qr_identifier, qr_payload)
            logger.info(f"QR créé pour catégorie: {category_name}")
            
        except Exception as e:
            logger.error(f"Erreur création QR catégorie {category_name}: {e}")
    
    def _create_subcategory_qr(self, subcategory_id, category_name, subcategory_name):
        """Créer un QR code pour une sous-catégorie"""
        try:
            qr_identifier = f"SUBCAT-{category_name}-{subcategory_name}"
            qr_payload = f"{self.base_url}/qr/{qr_identifier}"
            qr_image_path = f"qr_images/{qr_identifier}.png"
            folder_path = f"Archives/{category_name}/{subcategory_name}"
            
            # Vérifier si le QR existe déjà
            existing = db.execute_query("SELECT id FROM qrcodes WHERE qr_identifier = %s", (qr_identifier,))
            if existing:
                logger.info(f"   QR sous-catégorie {category_name}/{subcategory_name} existe déjà")
                return
            
            # Insérer en base
            qr_query = """
            INSERT INTO qrcodes (qr_type, qr_identifier, qr_payload, subcategory_id, folder_path, qr_image_path)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            db.execute_query(qr_query, ('SUBCATEGORY', qr_identifier, qr_payload, subcategory_id, folder_path, qr_image_path))
            
            # Générer l'image QR
            qr_generator.generate_qr_code(qr_identifier, qr_payload)
            logger.info(f"QR créé pour sous-catégorie: {category_name}/{subcategory_name}")
            
        except Exception as e:
            logger.error(f"Erreur création QR sous-catégorie {category_name}/{subcategory_name}: {e}")
    
    def _create_document_qr(self, document_id, document_code):
        """Créer un QR code pour un document"""
        try:
            qr_identifier = document_code
            qr_payload = f"{self.base_url}/qr/{qr_identifier}"
            qr_image_path = f"qr_images/{qr_identifier}.png"
            
            # Vérifier si le QR existe déjà
            existing = db.execute_query("SELECT id FROM qrcodes WHERE qr_identifier = %s", (qr_identifier,))
            if existing:
                logger.info(f"   QR document {document_code} existe déjà")
                return
            
            # Insérer en base
            qr_query = """
            INSERT INTO qrcodes (qr_type, qr_identifier, qr_payload, document_id, qr_image_path)
            VALUES (%s, %s, %s, %s, %s)
            """
            db.execute_query(qr_query, ('DOCUMENT', qr_identifier, qr_payload, document_id, qr_image_path))
            
            # Générer l'image QR
            qr_generator.generate_qr_code(qr_identifier, qr_payload)
            logger.info(f"QR créé pour document: {document_code}")
            
        except Exception as e:
            logger.error(f"Erreur création QR document {document_code}: {e}")
    
    def _get_or_create_category(self, name):
        """Récupérer ou créer une catégorie"""
        result = db.execute_query("SELECT id FROM categories WHERE name = %s", (name,))
        if result:
            return result[0]['id']
        
        db.execute_query("INSERT INTO categories (name, description) VALUES (%s, %s)", (name, f"Catégorie {name}"))
        return db.execute_query("SELECT LAST_INSERT_ID() as id")[0]['id']
    
    def _get_or_create_subcategory(self, category_id, name):
        """Récupérer ou créer une sous-catégorie"""
        result = db.execute_query("SELECT id FROM subcategories WHERE category_id = %s AND name = %s", (category_id, name))
        if result:
            return result[0]['id']
        
        db.execute_query("INSERT INTO subcategories (category_id, name, description) VALUES (%s, %s, %s)", 
                        (category_id, name, f"Sous-catégorie {name}"))
        return db.execute_query("SELECT LAST_INSERT_ID() as id")[0]['id']
    
    def _get_next_sequence(self, subcategory_id, year):
        """Obtenir le prochain numéro de séquence"""
        result = db.execute_query("SELECT current_sequence FROM sequences WHERE subcategory_id = %s AND year = %s", 
                                 (subcategory_id, year))
        
        if result:
            new_sequence = result[0]['current_sequence'] + 1
            db.execute_query("UPDATE sequences SET current_sequence = %s WHERE subcategory_id = %s AND year = %s", 
                           (new_sequence, subcategory_id, year))
            return new_sequence
        else:
            db.execute_query("INSERT INTO sequences (subcategory_id, year, current_sequence) VALUES (%s, %s, 1)", 
                           (subcategory_id, year))
            return 1
    
    def _extract_year_from_path(self, file_path):
        """Extraire l'année du chemin du fichier"""
        path_parts = file_path.parts
        
        # Chercher une année dans le chemin (2020-2030)
        for part in path_parts:
            if part.isdigit() and 2020 <= int(part) <= 2030:
                return int(part)
        
        # Année par défaut
        return 2025

def main():
    """Fonction principale pour scanner et enregistrer toute la structure"""
    scanner = ArchiveScanner()
    
    logger.info("Démarrage du scan complet de la structure Archives/")
    
    if scanner.scan_and_register_all():
        logger.info("Scan terminé avec succès!")
        logger.info("Tous les QR codes ont été générés")
        logger.info("Vous pouvez maintenant scanner n'importe quel QR code")
    else:
        logger.error("Erreur lors du scan")

if __name__ == "__main__":
    main()
