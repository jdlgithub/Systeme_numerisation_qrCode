"""
Gestionnaire d'Utilisateurs - QR Archives System """

import mysql.connector
import hashlib
import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import getpass

# Charger les variables d'environnement
load_dotenv()

class UserManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.connect_db()
    
    def connect_db(self):
        """Connexion à la base de données"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'qr_archives'),
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            self.cursor = self.connection.cursor(buffered=True)
            print("Connexion à la base de données réussie")
        except mysql.connector.Error as e:
            print(f"Erreur de connexion à la base de données : {e}")
            sys.exit(1)
    
    def close_db(self):
        """Fermeture de la connexion"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def hash_password(self, password):
        """Hash du mot de passe en SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def user_exists(self, username):
        """Vérifier si un utilisateur existe"""
        query = "SELECT id FROM users WHERE username = %s"
        self.cursor.execute(query, (username,))
        return self.cursor.fetchone() is not None
    
    def add_user(self, username, password, role='user', is_active=True):
        """Ajouter un nouvel utilisateur"""
        try:
            if self.user_exists(username):
                print(f"L'utilisateur '{username}' existe déjà")
                return False
            
            if role not in ['admin', 'user']:
                print("Le rôle doit être 'admin' ou 'user'")
                return False
            
            password_hash = self.hash_password(password)
            
            query = """
            INSERT INTO users (username, password_hash, role, created_at, is_active) 
            VALUES (%s, %s, %s, %s, %s)
            """
            
            self.cursor.execute(query, (
                username, 
                password_hash, 
                role, 
                datetime.now(), 
                1 if is_active else 0
            ))
            self.connection.commit()
            
            print(f"Utilisateur '{username}' ajouté avec succès (rôle: {role})")
            return True
            
        except mysql.connector.Error as e:
            print(f"Erreur lors de l'ajout : {e}")
            return False
    
    def update_password(self, username, new_password):
        """Modifier le mot de passe d'un utilisateur"""
        try:
            if not self.user_exists(username):
                print(f"L'utilisateur '{username}' n'existe pas")
                return False
            
            password_hash = self.hash_password(new_password)
            
            query = "UPDATE users SET password_hash = %s WHERE username = %s"
            self.cursor.execute(query, (password_hash, username))
            self.connection.commit()
            
            print(f"Mot de passe mis à jour pour '{username}'")
            return True
            
        except mysql.connector.Error as e:
            print(f"Erreur lors de la mise à jour : {e}")
            return False
    
    def update_role(self, username, new_role):
        """Modifier le rôle d'un utilisateur"""
        try:
            if not self.user_exists(username):
                print(f"L'utilisateur '{username}' n'existe pas")
                return False
            
            if new_role not in ['admin', 'user']:
                print("Le rôle doit être 'admin' ou 'user'")
                return False
            
            query = "UPDATE users SET role = %s WHERE username = %s"
            self.cursor.execute(query, (new_role, username))
            self.connection.commit()
            
            print(f"Rôle mis à jour pour '{username}' : {new_role}")
            return True
            
        except mysql.connector.Error as e:
            print(f"Erreur lors de la mise à jour : {e}")
            return False
    
    def toggle_user_status(self, username, activate=True):
        """Activer/Désactiver un utilisateur"""
        try:
            if not self.user_exists(username):
                print(f"L'utilisateur '{username}' n'existe pas")
                return False
            
            status = 1 if activate else 0
            action = "activé" if activate else "désactivé"
            
            query = "UPDATE users SET is_active = %s WHERE username = %s"
            self.cursor.execute(query, (status, username))
            self.connection.commit()
            
            print(f"Utilisateur '{username}' {action}")
            return True
            
        except mysql.connector.Error as e:
            print(f"Erreur lors de la mise à jour : {e}")
            return False
    
    def delete_user(self, username, soft_delete=True):
        """Supprimer un utilisateur (soft ou hard delete)"""
        try:
            if not self.user_exists(username):
                print(f"L'utilisateur '{username}' n'existe pas")
                return False
            
            if soft_delete:
                # Soft delete : désactiver et renommer
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_username = f"{username}_DELETED_{timestamp}"
                
                query = """
                UPDATE users 
                SET is_active = 0, username = %s 
                WHERE username = %s
                """
                self.cursor.execute(query, (new_username, username))
                print(f"Utilisateur '{username}' désactivé (soft delete)")
            else:
                # Hard delete : suppression définitive
                query = "DELETE FROM users WHERE username = %s"
                self.cursor.execute(query, (username,))
                print(f"Utilisateur '{username}' supprimé définitivement")
            
            self.connection.commit()
            return True
            
        except mysql.connector.Error as e:
            print(f"Erreur lors de la suppression : {e}")
            return False
    
    def get_user_info(self, username):
        """Obtenir les informations d'un utilisateur"""
        try:
            query = """
            SELECT id, username, role, created_at, last_login, is_active 
            FROM users 
            WHERE username = %s
            """
            self.cursor.execute(query, (username,))
            user = self.cursor.fetchone()
            
            if not user:
                print(f"Utilisateur '{username}' introuvable")
                return None
            
            return {
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'created_at': user[3],
                'last_login': user[4],
                'is_active': bool(user[5])
            }
            
        except mysql.connector.Error as e:
            print(f"Erreur lors de la recherche : {e}")
            return None
    
    def list_users(self, active_only=False, role_filter=None):
        """Lister tous les utilisateurs"""
        try:
            query = """
            SELECT id, username, role, created_at, last_login, is_active 
            FROM users
            """
            conditions = []
            params = []
            
            if active_only:
                conditions.append("is_active = 1")
            
            if role_filter in ['admin', 'user']:
                conditions.append("role = %s")
                params.append(role_filter)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC"
            
            self.cursor.execute(query, params)
            users = self.cursor.fetchall()
            
            if not users:
                print("Aucun utilisateur trouvé")
                return []
            
            # Affichage simple en colonnes
            print("\n" + "="*100)
            print("                              LISTE DES UTILISATEURS")
            print("="*100)
            
            # En-têtes
            print(f"{'ID':<4} {'Username':<20} {'Rôle':<8} {'Créé le':<17} {'Dernière connexion':<17} {'Actif':<6}")
            print("-" * 100)
            
            for user in users:
                created = user[3].strftime("%Y-%m-%d %H:%M") if user[3] else "N/A"
                last_login = user[4].strftime("%Y-%m-%d %H:%M") if user[4] else "Jamais"
                status = "Oui" if user[5] else "Non"
                
                print(f"{user[0]:<4} {user[1]:<20} {user[2]:<8} {created:<17} {last_login:<17} {status:<6}")
            
            print("-" * 100)
            print(f"Total : {len(users)} utilisateur(s)")
            
            return users
            
        except mysql.connector.Error as e:
            print(f"Erreur lors de la liste : {e}")
            return []
    
    def get_statistics(self):
        """Obtenir les statistiques des utilisateurs"""
        try:
            stats = {}
            
            # Total utilisateurs
            self.cursor.execute("SELECT COUNT(*) FROM users")
            stats['total'] = self.cursor.fetchone()[0]
            
            # Utilisateurs actifs
            self.cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
            stats['active'] = self.cursor.fetchone()[0]
            
            # Utilisateurs inactifs
            stats['inactive'] = stats['total'] - stats['active']
            
            # Par rôle
            self.cursor.execute("SELECT role, COUNT(*) FROM users WHERE is_active = 1 GROUP BY role")
            role_stats = dict(self.cursor.fetchall())
            stats['admins'] = role_stats.get('admin', 0)
            stats['users'] = role_stats.get('user', 0)
            
            # Connexions récentes (7 derniers jours)
            week_ago = datetime.now() - timedelta(days=7)
            self.cursor.execute(
                "SELECT COUNT(*) FROM users WHERE last_login >= %s", 
                (week_ago,)
            )
            stats['recent_logins'] = self.cursor.fetchone()[0]
            
            return stats
            
        except mysql.connector.Error as e:
            print(f"Erreur lors du calcul des statistiques : {e}")
            return {}
    
    def display_statistics(self):
        """Afficher les statistiques"""
        stats = self.get_statistics()
        if not stats:
            return
        
        print("\n" + "="*60)
        print("                    STATISTIQUES UTILISATEURS")
        print("="*60)
        print(f"Total utilisateurs      : {stats['total']}")
        print(f"Utilisateurs actifs     : {stats['active']}")
        print(f"Utilisateurs inactifs   : {stats['inactive']}")
        print(f"Administrateurs         : {stats['admins']}")
        print(f"Utilisateurs standard   : {stats['users']}")
        print(f"Connexions récentes     : {stats['recent_logins']} (7 derniers jours)")
        print("="*60)
    
    def backup_users(self, filename=None):
        """Sauvegarder les utilisateurs en JSON"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"users_backup_{timestamp}.json"
            
            query = """
            SELECT id, username, password_hash, role, created_at, last_login, is_active 
            FROM users 
            ORDER BY id
            """
            self.cursor.execute(query)
            users = self.cursor.fetchall()
            
            backup_data = []
            for user in users:
                backup_data.append({
                    'id': user[0],
                    'username': user[1],
                    'password_hash': user[2],
                    'role': user[3],
                    'created_at': user[4].isoformat() if user[4] else None,
                    'last_login': user[5].isoformat() if user[5] else None,
                    'is_active': bool(user[6])
                })
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            print(f"Sauvegarde créée : {filename} ({len(users)} utilisateurs)")
            return filename
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde : {e}")
            return None
    
    def restore_users(self, filename):
        """Restaurer les utilisateurs depuis un fichier JSON"""
        try:
            if not os.path.exists(filename):
                print(f"Fichier de sauvegarde introuvable : {filename}")
                return False
            
            with open(filename, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            restored = 0
            skipped = 0
            
            for user_data in backup_data:
                if self.user_exists(user_data['username']):
                    print(f"Utilisateur '{user_data['username']}' existe déjà - ignoré")
                    skipped += 1
                    continue
                
                query = """
                INSERT INTO users (username, password_hash, role, created_at, last_login, is_active) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                created_at = datetime.fromisoformat(user_data['created_at']) if user_data['created_at'] else datetime.now()
                last_login = datetime.fromisoformat(user_data['last_login']) if user_data['last_login'] else None
                
                self.cursor.execute(query, (
                    user_data['username'],
                    user_data['password_hash'],
                    user_data['role'],
                    created_at,
                    last_login,
                    1 if user_data['is_active'] else 0
                ))
                restored += 1
            
            self.connection.commit()
            print(f"Restauration terminée : {restored} utilisateurs restaurés, {skipped} ignorés")
            return True
            
        except Exception as e:
            print(f"Erreur lors de la restauration : {e}")
            return False

def clear_screen():
    """Effacer l'écran"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_menu():
    """Afficher le menu principal"""
    print("\n" + "="*80)
    print("                        GESTIONNAIRE D'UTILISATEURS")
    print("                             QR Archives System")
    print("="*80)
    print("1. Ajouter un utilisateur")
    print("2. Modifier le mot de passe")
    print("3. Modifier le rôle")
    print("4. Activer un utilisateur")
    print("5. Désactiver un utilisateur")
    print("6. Supprimer un utilisateur (soft delete)")
    print("7. Supprimer définitivement")
    print("8. Rechercher un utilisateur")
    print("9. Lister tous les utilisateurs")
    print("10. Afficher les statistiques")
    print("11. Sauvegarder les utilisateurs")
    print("12. Restaurer les utilisateurs")
    print("13. Rafraîchir l'écran")
    print("0. Quitter")
    print("="*80)

def get_secure_password(prompt="Mot de passe : "):
    """Saisie sécurisée du mot de passe"""
    return getpass.getpass(prompt)

def main():
    """Fonction principale"""
    user_manager = UserManager()
    
    try:
        while True:
            display_menu()
            choice = input("\n Votre choix : ").strip()
            
            if choice == '0':
                print("\n Au revoir !")
                break
            
            elif choice == '1':
                print("\n AJOUT D'UTILISATEUR")
                print("-" * 30)
                username = input("Nom d'utilisateur : ").strip()
                if not username:
                    print("Le nom d'utilisateur ne peut pas être vide")
                    continue
                
                password = get_secure_password()
                if not password:
                    print("Le mot de passe ne peut pas être vide")
                    continue
                
                role = input("Rôle (admin/user) [user] : ").strip().lower() or 'user'
                user_manager.add_user(username, password, role)
            
            elif choice == '2':
                print("\n MODIFICATION MOT DE PASSE")
                print("-" * 35)
                username = input("Nom d'utilisateur : ").strip()
                if not username:
                    print("Le nom d'utilisateur ne peut pas être vide")
                    continue
                
                new_password = get_secure_password("Nouveau mot de passe : ")
                if not new_password:
                    print("Le mot de passe ne peut pas être vide")
                    continue
                
                user_manager.update_password(username, new_password)
            
            elif choice == '3':
                print("\n MODIFICATION RÔLE")
                print("-" * 25)
                username = input("Nom d'utilisateur : ").strip()
                if not username:
                    print("Le nom d'utilisateur ne peut pas être vide")
                    continue
                
                new_role = input("Nouveau rôle (admin/user) : ").strip().lower()
                if new_role not in ['admin', 'user']:
                    print("Le rôle doit être 'admin' ou 'user'")
                    continue
                
                user_manager.update_role(username, new_role)
            
            elif choice == '4':
                print("\n ACTIVATION UTILISATEUR")
                print("-" * 30)
                username = input("Nom d'utilisateur : ").strip()
                if username:
                    user_manager.toggle_user_status(username, activate=True)
            
            elif choice == '5':
                print("\n DÉSACTIVATION UTILISATEUR")
                print("-" * 35)
                username = input("Nom d'utilisateur : ").strip()
                if username:
                    user_manager.toggle_user_status(username, activate=False)
            
            elif choice == '6':
                print("\n SUPPRESSION UTILISATEUR (SOFT DELETE)")
                print("-" * 45)
                username = input("Nom d'utilisateur : ").strip()
                if username:
                    confirm = input(f"⚠️ Confirmer la désactivation de '{username}' ? (oui/non) : ").strip().lower()
                    if confirm in ['oui', 'o', 'yes', 'y']:
                        user_manager.delete_user(username, soft_delete=True)
            
            elif choice == '7':
                print("\n SUPPRESSION DÉFINITIVE")
                print("-" * 30)
                username = input("Nom d'utilisateur : ").strip()
                if username:
                    print("ATTENTION : Cette action est IRRÉVERSIBLE !")
                    confirm1 = input(f"Confirmer la suppression définitive de '{username}' ? (oui/non) : ").strip().lower()
                    if confirm1 in ['oui', 'o', 'yes', 'y']:
                        confirm2 = input("Êtes-vous ABSOLUMENT sûr ? (SUPPRIMER/annuler) : ").strip()
                        if confirm2 == 'SUPPRIMER':
                            user_manager.delete_user(username, soft_delete=False)
                        else:
                            print("Suppression annulée")
            
            elif choice == '8':
                print("\n RECHERCHE UTILISATEUR")
                print("-" * 30)
                username = input("Nom d'utilisateur : ").strip()
                if username:
                    user_info = user_manager.get_user_info(username)
                    if user_info:
                        print("\n INFORMATIONS UTILISATEUR")
                        print("-" * 35)
                        print(f"ID           : {user_info['id']}")
                        print(f"Username     : {user_info['username']}")
                        print(f"Rôle         : {user_info['role']}")
                        print(f"Créé le      : {user_info['created_at']}")
                        print(f"Dernière co. : {user_info['last_login'] or 'Jamais'}")
                        print(f"Actif        : {'Oui' if user_info['is_active'] else 'Non'}")
            
            elif choice == '9':
                print("\n LISTE DES UTILISATEURS")
                print("-" * 30)
                filter_choice = input("Filtre (1=Tous, 2=Actifs, 3=Admins, 4=Users) [1] : ").strip() or '1'
                
                if filter_choice == '1':
                    user_manager.list_users()
                elif filter_choice == '2':
                    user_manager.list_users(active_only=True)
                elif filter_choice == '3':
                    user_manager.list_users(active_only=True, role_filter='admin')
                elif filter_choice == '4':
                    user_manager.list_users(active_only=True, role_filter='user')
                else:
                    print("Choix invalide")
            
            elif choice == '10':
                user_manager.display_statistics()
            
            elif choice == '11':
                print("\n SAUVEGARDE UTILISATEURS")
                print("-" * 35)
                filename = input("Nom du fichier [auto] : ").strip() or None
                user_manager.backup_users(filename)
            
            elif choice == '12':
                print("\n RESTAURATION UTILISATEURS")
                print("-" * 40)
                filename = input("Nom du fichier de sauvegarde : ").strip()
                if filename:
                    user_manager.restore_users(filename)
            
            elif choice == '13':
                clear_screen()
                continue
            
            else:
                print("Choix invalide")
            
            input("\n Appuyez sur Entrée pour continuer...")
    
    except KeyboardInterrupt:
        print("\n\n Interruption détectée")
    except Exception as e:
        print(f"\n Erreur inattendue : {e}")
    finally:
        user_manager.close_db()
        print("Connexion fermée")

if __name__ == "__main__":
    main()
