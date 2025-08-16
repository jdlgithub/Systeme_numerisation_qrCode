import mysql.connector
from mysql.connector import Error
from config_local import Config  # Utiliser la configuration locale
import logging

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Établir la connexion à la base de données MySQL"""
        try:
            self.connection = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                port=Config.DB_PORT,
                autocommit=True
            )
            if self.connection.is_connected():
                logging.info("Connexion à MySQL réussie")
        except Error as e:
            logging.error(f"Erreur de connexion à MySQL: {e}")
            raise
    
    def get_cursor(self):
        """Obtenir un curseur pour exécuter des requêtes"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        return self.connection.cursor(dictionary=True)
    
    def execute_procedure(self, procedure_name, params):
        """Exécuter une procédure stockée"""
        cursor = self.get_cursor()
        try:
            cursor.callproc(procedure_name, params)
            results = []
            for result in cursor.stored_results():
                results.extend(result.fetchall())
            return results
        except Error as e:
            logging.error(f"Erreur lors de l'exécution de la procédure {procedure_name}: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_query(self, query, params=None):
        """Exécuter une requête SQL"""
        cursor = self.get_cursor()
        try:
            cursor.execute(query, params or ())
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                return cursor.rowcount
        except Error as e:
            logging.error(f"Erreur lors de l'exécution de la requête: {e}")
            raise
        finally:
            cursor.close()
    
    def close(self):
        """Fermer la connexion à la base de données"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info("Connexion MySQL fermée")

# Instance globale de la base de données
db = Database()
