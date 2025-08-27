import qrcode
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

class QRGenerator:
    def __init__(self):
        """Initialiser le générateur avec le dossier de destination"""
        self.qr_folder = os.environ.get('QR_IMAGES_FOLDER', 'qr_images')
        # Créer le dossier s'il n'existe pas
        os.makedirs(self.qr_folder, exist_ok=True)
    
    def generate_qr_code(self, identifier, payload, filename=None):
        """
        Générer un QR code et sauvegarder l'image PNG
        
        Args:
            identifier (str): Identifiant unique du QR code
            payload (str): URL ou données à encoder
            filename (str): Nom du fichier (optionnel, par défaut: identifier.png)
        
        Returns:
            str: Chemin complet du fichier QR code généré
        """
        # Définir le nom du fichier
        if filename is None:
            filename = f"{identifier}.png"
        
        file_path = os.path.join(self.qr_folder, filename)
        
        # Configuration du QR code (taille optimale pour impression)
        qr = qrcode.QRCode(
            version=1,  # Taille automatique
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # Correction d'erreur faible
            box_size=10,  # Taille des pixels
            border=4,  # Bordure en pixels
        )
        
        # Ajouter les données et optimiser la taille
        qr.add_data(payload)
        qr.make(fit=True)
        
        # Créer l'image en noir et blanc
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarder l'image
        img.save(file_path)
        
        return file_path
    
    def generate_document_qr(self, document_code, base_url=None):
        """
        Générer un QR code pour un document spécifique
        
        Args:
            document_code (str): Code unique du document (ex: RH-CONTRATS-2025-0001)
            base_url (str): URL de base (optionnel, depuis .env par défaut)
        
        Returns:
            str: Chemin du fichier PNG généré
        """
        # Utiliser l'URL de base depuis .env ou valeur par défaut
        if base_url is None:
            base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
        
        # Créer l'URL de résolution du QR code
        payload = f"{base_url}/qr/{document_code}"
        
        return self.generate_qr_code(document_code, payload)
    
    def generate_subcategory_qr(self, subcategory_identifier, base_url=None):
        """
        Générer un QR code pour une sous-catégorie
        
        Args:
            subcategory_identifier (str): Identifiant de la sous-catégorie
            base_url (str): URL de base (optionnel, depuis .env par défaut)
        
        Returns:
            str: Chemin du fichier PNG généré
        """
        # Utiliser l'URL de base depuis .env ou valeur par défaut
        if base_url is None:
            base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
        
        # Créer l'URL de résolution du QR code
        payload = f"{base_url}/qr/{subcategory_identifier}"
        
        return self.generate_qr_code(subcategory_identifier, payload)

# Instance globale du générateur de QR codes
qr_generator = QRGenerator()
