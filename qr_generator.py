"""
Générateur de QR codes pour l'application QR Archives
"""

import qrcode
import os
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class QRGenerator:
    def __init__(self):
        """Initialiser le générateur de QR codes"""
        self.qr_folder = os.environ.get('QR_IMAGES_FOLDER', 'qr_images')
        self.base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
        
        # Créer le dossier QR s'il n'existe pas
        if not os.path.exists(self.qr_folder):
            os.makedirs(self.qr_folder, exist_ok=True)
            logging.info(f"Dossier QR créé: {self.qr_folder}")
    
    def generate_qr_code(self, identifier, payload):
        """Générer un QR code PNG"""
        try:
            # Créer le QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(payload)
            qr.make(fit=True)
            
            # Créer l'image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Sauvegarder l'image
            filename = f"{identifier}.png"
            filepath = os.path.join(self.qr_folder, filename)
            img.save(filepath)
            
            logging.info(f"QR code généré: {filepath}")
            return filepath
            
        except Exception as e:
            logging.error(f"Erreur génération QR code {identifier}: {e}")
            return None
    
    def generate_document_qr(self, document_code):
        """Générer un QR code pour un document"""
        payload = f"{self.base_url}/qr/{document_code}"
        return self.generate_qr_code(document_code, payload)
    
    def generate_category_qr(self, category_name):
        """Générer un QR code pour une catégorie"""
        identifier = f"CAT-{category_name}"
        payload = f"{self.base_url}/qr/{identifier}"
        return self.generate_qr_code(identifier, payload)
    
    def generate_subcategory_qr(self, category_name, subcategory_name):
        """Générer un QR code pour une sous-catégorie"""
        identifier = f"SUBCAT-{category_name}-{subcategory_name}"
        payload = f"{self.base_url}/qr/{identifier}"
        return self.generate_qr_code(identifier, payload)

# Instance globale du générateur de QR codes
qr_generator = QRGenerator()
