"""
Gestion de la base de données MySQL pour l'application QR Archives
"""
import mysql.connector
from mysql.connector import Error
import logging
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Database:
    def __init__(self):
        """Initialiser la connexion à MySQL"""
        self.connection = None
        self.connect()
    
    def connect(self):
        """Établir la connexion à la base de données MySQL locale"""
        try:
            # Paramètres de connexion depuis les variables d'environnement
            self.connection = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USER', 'root'),
                password=os.environ.get('DB_PASSWORD', ''),
                database=os.environ.get('DB_NAME', 'qr_archives'),
                port=int(os.environ.get('DB_PORT', 3306)),
                autocommit=True,  # Auto-commit pour simplifier
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            if self.connection.is_connected():
                logging.info(" Connexion à MySQL réussie")
        except Error as e:
            logging.error(f" Erreur de connexion à MySQL: {e}")
            raise
    
    def is_connected(self):
        """Vérifier si la connexion est active"""
        try:
            return self.connection and self.connection.is_connected()
        except:
            return False
    
    def get_cursor(self):
        """Obtenir un curseur MySQL avec résultats en dictionnaire"""
        if not self.is_connected():
            self.connect()
        return self.connection.cursor(dictionary=True)
    
    def execute_procedure(self, procedure_name, params):
        """Exécuter une procédure stockée MySQL"""
        cursor = self.get_cursor()
        try:
            # Appeler la procédure stockée
            cursor.callproc(procedure_name, params)
            
            # Récupérer tous les résultats
            results = []
            for result in cursor.stored_results():
                results.extend(result.fetchall())
            return results
        except Error as e:
            logging.error(f" Erreur procédure {procedure_name}: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_query(self, query, params=None):
        """Exécuter une requête SQL (SELECT, INSERT, UPDATE, DELETE)"""
        cursor = self.get_cursor()
        try:
            cursor.execute(query, params or ())
            
            # Retourner les résultats pour SELECT, nombre de lignes affectées sinon
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                return cursor.rowcount
        except Error as e:
            logging.error(f" Erreur requête SQL: {e}")
            logging.error(f" Query: {query}")
            logging.error(f" Params: {params}")
            raise
        finally:
            cursor.close()
    
    def execute_query_safe(self, query, params=None):
        """Exécuter une requête SQL avec gestion d'erreur silencieuse"""
        try:
            return self.execute_query(query, params)
        except Exception as e:
            logging.warning(f" Requête échouée (ignorée): {e}")
            return []
    
    def close(self):
        """Fermer proprement la connexion MySQL"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info(" Connexion MySQL fermée")

# Instance globale de la base de données
db = Database()
