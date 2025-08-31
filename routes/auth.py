from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database import db
from routes.decorators import login_required
from routes.utils import hash_password
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    """Page de connexion"""
    if 'user_id' in session:
        if session.get('user_role') == 'admin':
            return redirect(url_for('admin.index'))
        else:
            return redirect(url_for('auth.user_dashboard'))
    return render_template('login.html')

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """API: Authentification utilisateur"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Nom d\'utilisateur et mot de passe requis'
            }), 400
        
        # Vérifier les identifiants
        password_hash = hash_password(password)
        query = """
        SELECT id, username, full_name, role, is_active
        FROM users 
        WHERE username = %s AND password_hash = %s AND is_active = TRUE
        """
        
        result = db.execute_query(query, (username, password_hash))
        
        if result:
            user = result[0]
            
            # Créer la session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user.get('full_name')
            session['user_role'] = user['role']
            
            # Mettre à jour la dernière connexion
            db.execute_query(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                (user['id'],)
            )
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'full_name': user.get('full_name'),
                    'role': user['role']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Identifiants incorrects'
            }), 401
            
    except Exception as e:
        logger.error(f"Erreur lors de la connexion: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500

@auth_bp.route('/api/logout')
def api_logout():
    """API: Déconnexion"""
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/api/user-info')
@login_required
def api_user_info():
    """API: Informations utilisateur connecté"""
    try:
        # Récupérer les informations utilisateur depuis la base de données
        query = """
        SELECT id, username, full_name, email, role, is_active, created_at, last_login
        FROM users 
        WHERE id = %s
        """
        
        result = db.execute_query(query, (session['user_id'],))
        
        if result:
            user = result[0]
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'full_name': user.get('full_name'),
                    'email': user.get('email'),
                    'role': user['role'],
                    'is_active': user['is_active'],
                    'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                    'last_login': user['last_login'].isoformat() if user['last_login'] else None
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Utilisateur non trouvé'
            }), 404
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des informations utilisateur: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur interne du serveur'
        }), 500

@auth_bp.route('/user-dashboard')
@login_required
def user_dashboard():
    """Tableau de bord utilisateur"""
    if session.get('user_role') == 'admin':
        return redirect(url_for('admin.index'))
    return render_template('user_dashboard.html')
