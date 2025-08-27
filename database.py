#!/usr/bin/env python3
"""
Gestion de la base de données MySQL pour l'application QR Archives
Connexion et exécution de requêtes/procédures stockées
"""

import mysql.connector
from mysql.connector import Error
import logging
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

class Database:
    def __init__(self):
        """Initialiser la connexion à MySQL"""
        self.connection = None
        self.connect()
    
    def connect(self):
        """Établir la connexion à la base de données MySQL locale"""
        try:
            # Paramètres de connexion depuis .env
            self.connection = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USER', 'root'),
                password=os.environ.get('DB_PASSWORD', ''),
                database=os.environ.get('DB_NAME', 'qr_archives'),
                port=int(os.environ.get('DB_PORT', 3306)),
                autocommit=True  # Auto-commit pour simplifier
            )
            if self.connection.is_connected():
                logging.info(" Connexion à MySQL réussie")
        except Error as e:
            logging.error(f" Erreur de connexion à MySQL: {e}")
            raise
    
    def get_cursor(self):
        """Obtenir un curseur MySQL avec résultats en dictionnaire"""
        if not self.connection or not self.connection.is_connected():
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
            raise
        finally:
            cursor.close()
    
    def close(self):
        """Fermer proprement la connexion MySQL"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info(" Connexion MySQL fermée")

# Instance globale de la base de données
db = Database()
