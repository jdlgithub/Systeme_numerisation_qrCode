#!/usr/bin/env python3
"""
Script pour tester la connexion à la base de données MySQL
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db

def test_connection():
    """Tester la connexion à la base de données"""
    try:
        print("🔍 Test de connexion à la base de données...")
        
        # Test de connexion simple
        result = db.execute_query("SELECT 1 as test")
        if result:
            print("✅ Connexion réussie!")
        
        # Vérifier que la base de données existe
        result = db.execute_query("SELECT DATABASE() as current_db")
        if result:
            print(f"📊 Base de données active: {result[0]['current_db']}")
        
        # Vérifier les tables
        result = db.execute_query("SHOW TABLES")
        if result:
            print("📋 Tables trouvées:")
            for table in result:
                table_name = list(table.values())[0]
                print(f"   • {table_name}")
        
        # Vérifier les données de test
        result = db.execute_query("SELECT COUNT(*) as count FROM categories")
        if result:
            print(f"📄 Catégories: {result[0]['count']}")
        
        result = db.execute_query("SELECT COUNT(*) as count FROM subcategories")
        if result:
            print(f"📁 Sous-catégories: {result[0]['count']}")
        
        print("\n🎉 Test de connexion réussi!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("\n🔧 Vérifiez:")
        print("   1. MySQL est démarré")
        print("   2. Les paramètres dans config_local.py sont corrects")
        print("   3. La base de données 'qr_archives' existe")
        return False

if __name__ == "__main__":
    try:
        success = test_connection()
        if success:
            print("\n✅ Vous pouvez maintenant démarrer l'application avec: python app.py")
        else:
            sys.exit(1)
    finally:
        db.close()
