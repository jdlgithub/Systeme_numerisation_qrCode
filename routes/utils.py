import hashlib
import logging
from database import db

logger = logging.getLogger(__name__)

def hash_password(password):
    """Hasher un mot de passe avec SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_or_create_category(name):
    """Récupérer l'ID d'une catégorie ou la créer si elle n'existe pas"""
    try:
        result = db.execute_query_safe("SELECT id FROM categories WHERE name = %s", (name,))
        if result:
            return result[0]['id']
        
        # Créer la catégorie
        db.execute_query("INSERT INTO categories (name) VALUES (%s)", (name,))
        return db.execute_query("SELECT LAST_INSERT_ID() as id")[0]['id']
    except Exception as e:
        logger.error(f"Erreur lors de la création/récupération de la catégorie {name}: {e}")
        raise

def get_or_create_subcategory(category_id, name):
    """Récupérer l'ID d'une sous-catégorie ou la créer"""
    try:
        result = db.execute_query_safe("SELECT id FROM subcategories WHERE category_id = %s AND name = %s", (category_id, name))
        if result:
            return result[0]['id']
        
        # Créer la sous-catégorie
        db.execute_query("INSERT INTO subcategories (category_id, name) VALUES (%s, %s)", (category_id, name))
        return db.execute_query("SELECT LAST_INSERT_ID() as id")[0]['id']
    except Exception as e:
        logger.error(f"Erreur lors de la création/récupération de la sous-catégorie {name}: {e}")
        raise

def get_next_sequence(subcategory_id, year):
    """Obtenir le prochain numéro de séquence pour une sous-catégorie/année"""
    try:
        result = db.execute_query_safe("SELECT current_sequence FROM sequences WHERE subcategory_id = %s AND year = %s", (subcategory_id, year))
        
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
    except Exception as e:
        logger.error(f"Erreur lors de la gestion de la séquence pour subcategory_id={subcategory_id}, year={year}: {e}")
        raise

def create_document_simple(category_name, subcategory_name, filename, year, title="", description="", base_url=None):
    """Créer un document avec génération automatique du code et du chemin"""
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
        qr_payload = f"{base_url}/qr/{qr_identifier}"
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
