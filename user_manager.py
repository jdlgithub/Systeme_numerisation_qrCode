#!/usr/bin/env python3
"""
Gestionnaire d'utilisateurs pour l'application QR Archives
Permet de créer, modifier et supprimer des utilisateurs
"""

import mysql.connector
from mysql.connector import Error
import hashlib
import logging
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self):
        """Initialiser le gestionnaire d'utilisateurs"""
        self.connection = None
        self.connect()
    
    def connect(self):
        """Établir la connexion à la base de données"""
        try:
            self.connection = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USER', 'root'),
                password=os.environ.get('DB_PASSWORD', ''),
                database=os.environ.get('DB_NAME', 'qr_archives'),
                port=int(os.environ.get('DB_PORT', 3306))
            )
            if self.connection.is_connected():
                logger.info(" Connexion à la base de données réussie")
        except Error as e:
            logger.error(f" Erreur de connexion: {e}")
            raise
    
    def hash_password(self, password):
        """Hasher un mot de passe avec SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, password, full_name=None, email=None, role='user'):
        """Créer un nouvel utilisateur"""
        try:
            cursor = self.connection.cursor()
            
            # Vérifier si l'utilisateur existe déjà
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                logger.error(f" L'utilisateur '{username}' existe déjà")
                return False
            
            # Hasher le mot de passe
            password_hash = self.hash_password(password)
            
            # Insérer l'utilisateur
            query = """
            INSERT INTO users (username, password_hash, full_name, email, role, is_active)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            """
            cursor.execute(query, (username, password_hash, full_name, email, role))
            
            self.connection.commit()
            logger.info(f" Utilisateur '{username}' créé avec succès")
            return True
            
        except Error as e:
            logger.error(f" Erreur lors de la création de l'utilisateur: {e}")
            return False
        finally:
            cursor.close()
    
    def update_user(self, username, **kwargs):
        """Mettre à jour un utilisateur existant"""
        try:
            cursor = self.connection.cursor()
            
            # Vérifier si l'utilisateur existe
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if not cursor.fetchone():
                logger.error(f" L'utilisateur '{username}' n'existe pas")
                return False
            
            # Construire la requête de mise à jour
            updates = []
            values = []
            
            if 'password' in kwargs:
                updates.append("password_hash = %s")
                values.append(self.hash_password(kwargs['password']))
            
            if 'full_name' in kwargs:
                updates.append("full_name = %s")
                values.append(kwargs['full_name'])
            
            if 'email' in kwargs:
                updates.append("email = %s")
                values.append(kwargs['email'])
            
            if 'role' in kwargs:
                updates.append("role = %s")
                values.append(kwargs['role'])
            
            if 'is_active' in kwargs:
                updates.append("is_active = %s")
                values.append(kwargs['is_active'])
            
            if not updates:
                logger.warning(" Aucune modification à apporter")
                return False
            
            # Exécuter la mise à jour
            query = f"UPDATE users SET {', '.join(updates)} WHERE username = %s"
            values.append(username)
            cursor.execute(query, values)
            
            self.connection.commit()
            logger.info(f" Utilisateur '{username}' mis à jour avec succès")
            return True
            
        except Error as e:
            logger.error(f" Erreur lors de la mise à jour: {e}")
            return False
        finally:
            cursor.close()
    
    def delete_user(self, username):
        """Supprimer un utilisateur"""
        try:
            cursor = self.connection.cursor()
            
            # Vérifier si l'utilisateur existe
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if not cursor.fetchone():
                logger.error(f" L'utilisateur '{username}' n'existe pas")
                return False
            
            # Supprimer l'utilisateur
            cursor.execute("DELETE FROM users WHERE username = %s", (username,))
            
            self.connection.commit()
            logger.info(f"Utilisateur '{username}' supprimé avec succès")
            return True
            
        except Error as e:
            logger.error(f" Erreur lors de la suppression: {e}")
            return False
        finally:
            cursor.close()
    
    def list_users(self):
        """Lister tous les utilisateurs"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
            SELECT id, username, full_name, email, role, is_active, created_at, last_login
            FROM users
            ORDER BY username
            """
            cursor.execute(query)
            
            users = cursor.fetchall()
            
            logger.info(f" {len(users)} utilisateurs trouvés:")
            for user in users:
                status = "Actif" if user['is_active'] else "Inactif"
                last_login = user['last_login'].strftime('%Y-%m-%d %H:%M:%S') if user['last_login'] else "Jamais"
                logger.info(f"  - {user['username']} ({user['role']}) - {status} - Dernière connexion: {last_login}")
            
            return users
            
        except Error as e:
            logger.error(f" Erreur lors de la récupération des utilisateurs: {e}")
            return []
        finally:
            cursor.close()
    
    def get_user(self, username):
        """Récupérer les informations d'un utilisateur"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
            SELECT id, username, full_name, email, role, is_active, created_at, last_login
            FROM users
            WHERE username = %s
            """
            cursor.execute(query, (username,))
            
            user = cursor.fetchone()
            
            if user:
                logger.info(f" Utilisateur '{username}' trouvé:")
                logger.info(f"  - Nom complet: {user['full_name']}")
                logger.info(f"  - Email: {user['email']}")
                logger.info(f"  - Rôle: {user['role']}")
                logger.info(f"  - Statut: {'Actif' if user['is_active'] else 'Inactif'}")
                logger.info(f"  - Créé le: {user['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                if user['last_login']:
                    logger.info(f"  - Dernière connexion: {user['last_login'].strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    logger.info(f"  - Dernière connexion: Jamais")
            else:
                logger.error(f" L'utilisateur '{username}' n'existe pas")
            
            return user
            
        except Error as e:
            logger.error(f" Erreur lors de la récupération de l'utilisateur: {e}")
            return None
        finally:
            cursor.close()
    
    def close(self):
        """Fermer la connexion"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info(" Connexion fermée")

def main():
    """Interface en ligne de commande"""
    manager = UserManager()
    
    while True:
        print("\n=== Gestionnaire d'utilisateurs ===")
        print("1. Créer un utilisateur")
        print("2. Modifier un utilisateur")
        print("3. Supprimer un utilisateur")
        print("4. Lister tous les utilisateurs")
        print("5. Voir un utilisateur")
        print("6. Quitter")
        
        choice = input("\nVotre choix (1-6): ").strip()
        
        if choice == '1':
            username = input("Nom d'utilisateur: ").strip()
            password = input("Mot de passe: ").strip()
            full_name = input("Nom complet (optionnel): ").strip() or None
            email = input("Email (optionnel): ").strip() or None
            role = input("Rôle (admin/user, défaut: user): ").strip() or 'user'
            
            if manager.create_user(username, password, full_name, email, role):
                print("Utilisateur créé avec succès")
            else:
                print("Erreur lors de la création")
        
        elif choice == '2':
            username = input("Nom d'utilisateur à modifier: ").strip()
            print("Laissez vide pour ne pas modifier")
            
            password = input("Nouveau mot de passe: ").strip() or None
            full_name = input("Nouveau nom complet: ").strip() or None
            email = input("Nouvel email: ").strip() or None
            role = input("Nouveau rôle (admin/user): ").strip() or None
            
            updates = {}
            if password:
                updates['password'] = password
            if full_name:
                updates['full_name'] = full_name
            if email:
                updates['email'] = email
            if role:
                updates['role'] = role
            
            if manager.update_user(username, **updates):
                print("Utilisateur mis à jour avec succès")
            else:
                print("Erreur lors de la mise à jour")
        
        elif choice == '3':
            username = input("Nom d'utilisateur à supprimer: ").strip()
            confirm = input(f"Êtes-vous sûr de vouloir supprimer '{username}' ? (oui/non): ").strip().lower()
            
            if confirm == 'oui':
                if manager.delete_user(username):
                    print("Utilisateur supprimé avec succès")
                else:
                    print("Erreur lors de la suppression")
            else:
                print("Suppression annulée")
        
        elif choice == '4':
            users = manager.list_users()
            if not users:
                print("Aucun utilisateur trouvé")
        
        elif choice == '5':
            username = input("Nom d'utilisateur à voir: ").strip()
            user = manager.get_user(username)
            if not user:
                print("Utilisateur non trouvé")
        
        elif choice == '6':
            print("Au revoir!")
            break
        
        else:
            print("Choix invalide. Veuillez choisir 1-6.")
    
    manager.close()

if __name__ == "__main__":
    main()
