#!/usr/bin/env python3
"""
Script pour insérer des données de test dans la base de données
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db
from qr_generator import qr_generator

def create_test_documents():
    """Créer des documents de test avec QR codes"""
    
    # Données de test
    test_documents = [
        {
            'category_name': 'RH',
            'subcategory_name': 'CONTRATS',
            'filename': 'contrat_dupont_2025.pdf',
            'file_path': 'uploads/RH/CONTRATS/2025/contrat_dupont_2025.pdf',
            'year': 2025,
            'title': 'Contrat de travail - M. Dupont Jean',
            'description': 'Contrat CDI pour M. Jean Dupont, poste de développeur'
        },
        {
            'category_name': 'RH',
            'subcategory_name': 'PAYSLIPS',
            'filename': 'bulletin_dupont_janvier_2025.pdf',
            'file_path': 'uploads/RH/PAYSLIPS/2025/bulletin_dupont_janvier_2025.pdf',
            'year': 2025,
            'title': 'Bulletin de paie - M. Dupont Jean - Janvier 2025',
            'description': 'Bulletin de paie de janvier 2025 pour M. Jean Dupont'
        },
        {
            'category_name': 'FACT',
            'subcategory_name': '2025',
            'filename': 'facture_client_abc_001_2025.pdf',
            'file_path': 'uploads/FACT/2025/facture_client_abc_001_2025.pdf',
            'year': 2025,
            'title': 'Facture Client ABC - Référence 001/2025',
            'description': 'Facture pour prestations de développement web - Client ABC'
        }
    ]
    
    print("🔧 Création des documents de test...")
    
    for i, doc_data in enumerate(test_documents, 1):
        try:
            print(f"\n📄 Document {i}: {doc_data['title']}")
            
            # Appeler la procédure stockée
            params = (
                doc_data['subcategory_name'],
                doc_data['category_name'],
                doc_data['filename'],
                doc_data['file_path'],
                doc_data['year'],
                doc_data['title'],
                doc_data['description']
            )
            
            result = db.execute_procedure('create_document_with_qr', params)
            
            if result:
                document_info = result[0]
                print(f"   ✅ Code document: {document_info['document_code']}")
                print(f"   ✅ QR Identifier: {document_info['qr_identifier']}")
                
                # Générer le QR code
                qr_path = qr_generator.generate_document_qr(document_info['document_code'])
                print(f"   ✅ QR Code généré: {qr_path}")
            else:
                print(f"   ❌ Erreur lors de la création du document {i}")
                
        except Exception as e:
            print(f"   ❌ Erreur pour le document {i}: {e}")
    
    print("\n🎉 Création des documents de test terminée!")

def create_test_subcategory_qr():
    """Créer des QR codes pour les sous-catégories"""
    
    print("\n🔧 Création des QR codes de sous-catégories...")
    
    # Récupérer les sous-catégories existantes
    query = """
    SELECT sc.id, sc.name, c.name as category_name
    FROM subcategories sc
    JOIN categories c ON sc.category_id = c.id
    """
    
    subcategories = db.execute_query(query)
    
    for sub in subcategories:
        try:
            qr_identifier = f"SUB-{sub['category_name']}-{sub['name']}"
            qr_payload = f"http://localhost:8000/qr/{qr_identifier}"
            
            # Vérifier si le QR code existe déjà
            check_query = "SELECT id FROM qrcodes WHERE qr_identifier = %s"
            existing = db.execute_query(check_query, (qr_identifier,))
            
            if not existing:
                # Insérer le QR code
                insert_query = """
                INSERT INTO qrcodes (qr_type, qr_identifier, qr_payload, subcategory_id, qr_image_path)
                VALUES ('SUBCATEGORY', %s, %s, %s, %s)
                """
                qr_image_path = f"qr_images/{qr_identifier}.png"
                
                db.execute_query(insert_query, (qr_identifier, qr_payload, sub['id'], qr_image_path))
                
                # Générer l'image QR
                qr_generator.generate_qr_code(qr_identifier, qr_payload)
                
                print(f"   ✅ QR Code créé pour {sub['category_name']}/{sub['name']}: {qr_identifier}")
            else:
                print(f"   ⚠️  QR Code déjà existant pour {sub['category_name']}/{sub['name']}")
                
        except Exception as e:
            print(f"   ❌ Erreur pour {sub['category_name']}/{sub['name']}: {e}")

def show_test_results():
    """Afficher les résultats des tests"""
    
    print("\n📊 Résultats des tests:")
    
    # Compter les documents
    doc_count = db.execute_query("SELECT COUNT(*) as count FROM documents")
    print(f"   📄 Documents créés: {doc_count[0]['count']}")
    
    # Compter les QR codes
    qr_count = db.execute_query("SELECT COUNT(*) as count FROM qrcodes")
    print(f"   🔍 QR codes créés: {qr_count[0]['count']}")
    
    # Lister les documents
    documents = db.execute_query("""
        SELECT d.document_code, d.title, c.name as category, sc.name as subcategory
        FROM documents d
        JOIN subcategories sc ON d.subcategory_id = sc.id
        JOIN categories c ON sc.category_id = c.id
        ORDER BY d.created_at DESC
    """)
    
    print("\n📋 Liste des documents:")
    for doc in documents:
        print(f"   • {doc['document_code']} - {doc['title']} ({doc['category']}/{doc['subcategory']})")

if __name__ == "__main__":
    try:
        print("🚀 Démarrage des tests du système QR Code")
        print("=" * 50)
        
        # Créer les documents de test
        create_test_documents()
        
        # Créer les QR codes de sous-catégories
        create_test_subcategory_qr()
        
        # Afficher les résultats
        show_test_results()
        
        print("\n" + "=" * 50)
        print("✅ Tests terminés avec succès!")
        print("\n🌐 Pour tester l'application:")
        print("   1. Démarrer l'application: python app.py")
        print("   2. Ouvrir http://localhost:8000")
        print("   3. Tester la résolution des QR codes")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        sys.exit(1)
    finally:
        db.close()
