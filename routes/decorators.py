from functools import wraps
from flask import session, redirect, url_for, jsonify, request

def login_required(f):
    """Décorateur pour vérifier que l'utilisateur est connecté"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.headers.get('Accept', '').startswith('application/json'):
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Décorateur pour vérifier que l'utilisateur est admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.headers.get('Accept', '').startswith('application/json'):
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            return redirect(url_for('auth.login'))
        
        if session.get('user_role') != 'admin':
            if request.headers.get('Accept', '').startswith('application/json'):
                return jsonify({'success': False, 'error': 'Accès admin requis'}), 403
            return redirect(url_for('auth.user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function
