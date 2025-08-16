import qrcode
import os
from config_local import Config  # Utiliser la configuration locale

class QRGenerator:
    def __init__(self):
        self.qr_folder = Config.QR_IMAGES_FOLDER
    
    def generate_qr_code(self, identifier, payload, filename=None):
        """
        Générer un QR code et le sauvegarder
        
        Args:
            identifier (str): Identifiant unique du QR code
            payload (str): Contenu du QR code (URL ou données)
            filename (str): Nom du fichier (optionnel)
        
        Returns:
            str: Chemin du fichier QR code généré
        """
        if filename is None:
            filename = f"{identifier}.png"
        
        file_path = os.path.join(self.qr_folder, filename)
        
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
        img.save(file_path)
        
        return file_path
    
    def generate_document_qr(self, document_code, base_url="http://localhost:8000"):
        """
        Générer un QR code pour un document
        
        Args:
            document_code (str): Code du document
            base_url (str): URL de base de l'application
        
        Returns:
            str: Chemin du fichier QR code généré
        """
        payload = f"{base_url}/qr/{document_code}"
        return self.generate_qr_code(document_code, payload)
    
    def generate_subcategory_qr(self, subcategory_identifier, base_url="http://localhost:8000"):
        """
        Générer un QR code pour une sous-catégorie
        
        Args:
            subcategory_identifier (str): Identifiant de la sous-catégorie
            base_url (str): URL de base de l'application
        
        Returns:
            str: Chemin du fichier QR code généré
        """
        payload = f"{base_url}/qr/{subcategory_identifier}"
        return self.generate_qr_code(subcategory_identifier, payload)

# Instance globale du générateur de QR codes
qr_generator = QRGenerator()
