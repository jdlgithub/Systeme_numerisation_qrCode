from flask import Blueprint, send_from_directory, current_app

files_bp = Blueprint('files', __name__)

@files_bp.route('/qr_images/<filename>')
def serve_qr_image(filename):
    """Servir les images de QR codes générées"""
    return send_from_directory(current_app.config['QR_IMAGES_FOLDER'], filename)

@files_bp.route('/archives/<path:filename>')
def serve_archive_document(filename):
    """Servir les documents PDF depuis le dossier Archives"""
    return send_from_directory(current_app.config['ARCHIVES_FOLDER'], filename)
