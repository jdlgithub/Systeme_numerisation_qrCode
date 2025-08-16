# Système de Numérisation QR Code - Application Flask

Une application Flask simple pour gérer des documents PDF avec des QR codes, utilisant MySQL comme base de données.

## 🚀 Installation

### Prérequis
- Python 3.7+
- MySQL 5.7+ ou MariaDB 10.2+
- pip (gestionnaire de paquets Python)

### 1. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 2. Configuration de la base de données

1. **Créer la base de données MySQL :**
   ```bash
   mysql -u root -p < schema_qr_archives.sql
   ```

2. **Configurer les variables d'environnement :**
   Créez un fichier `.env` à la racine du projet :
   ```
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=votre_mot_de_passe
   DB_NAME=qr_archives
   DB_PORT=3306
   FLASK_SECRET_KEY=votre_cle_secrete
   ```

### 3. Insertion des données de test

```bash
python test_data.py
```

Ce script va créer :
- 3 documents de test avec QR codes
- QR codes pour les sous-catégories
- Données de base (catégories RH et FACT)

## 🏃‍♂️ Démarrage de l'application

```bash
python app.py
```

L'application sera accessible à l'adresse : http://localhost:8000

## 📋 Fonctionnalités

### Interface Web
- **Création de documents** : Formulaire pour ajouter de nouveaux documents
- **Résolution de QR codes** : Tester la résolution des QR codes
- **Liste des documents** : Visualiser tous les documents enregistrés

### API REST
- `GET /qr/<identifier>` : Résoudre un QR code
- `POST /api/documents` : Créer un nouveau document
- `GET /api/documents` : Lister tous les documents

### Structure des QR Codes
- **Documents** : `CATEGORIE-SOUSCATEGORIE-ANNEE-NUMERO` (ex: `RH-CONTRATS-2025-0001`)
- **Sous-catégories** : `SUB-CATEGORIE-SOUSCATEGORIE` (ex: `SUB-RH-CONTRATS`)

## 🗂️ Structure du projet

```
qr_code_numarization/
├── app.py                 # Application Flask principale
├── config.py             # Configuration de l'application
├── database.py           # Gestion de la base de données
├── qr_generator.py       # Génération des QR codes
├── test_data.py          # Script de données de test
├── requirements.txt      # Dépendances Python
├── schema_qr_archives.sql # Schéma de base de données
├── templates/
│   └── index.html        # Interface web
├── uploads/              # Dossier des documents PDF
└── qr_images/            # Dossier des images QR codes
```

## 🧪 Tests

### Données de test créées
1. **Contrat de travail** : `RH-CONTRATS-2025-0001`
2. **Bulletin de paie** : `RH-PAYSLIPS-2025-0001`
3. **Facture** : `FACT-2025-0001`

### Test de résolution QR
1. Ouvrir http://localhost:8000
2. Dans la section "Résoudre un QR Code"
3. Entrer un des codes : `RH-CONTRATS-2025-0001`
4. Cliquer sur "Résoudre"

## 🔧 Configuration avancée

### Ajouter de nouvelles catégories
```sql
INSERT INTO categories (name, description) VALUES ('COMPTA', 'Comptabilité');
```

### Ajouter de nouvelles sous-catégories
```sql
INSERT INTO subcategories (category_id, name, description) 
VALUES (1, 'BILANS', 'Bilans annuels');
```

### Créer un document via API
```bash
curl -X POST http://localhost:8000/api/documents \
  -H "Content-Type: application/json" \
  -d '{
    "category_name": "RH",
    "subcategory_name": "CONTRATS",
    "filename": "nouveau_contrat.pdf",
    "file_path": "uploads/RH/CONTRATS/2025/nouveau_contrat.pdf",
    "year": 2025,
    "title": "Nouveau contrat",
    "description": "Description du contrat"
  }'
```

## 🛠️ Développement

### Structure de la base de données
- **categories** : Catégories principales (RH, FACT, etc.)
- **subcategories** : Sous-catégories (CONTRATS, PAYSLIPS, etc.)
- **documents** : Documents PDF avec métadonnées
- **qrcodes** : QR codes générés pour les documents et sous-catégories
- **sequences** : Gestion des numéros séquentiels par sous-catégorie/année

### Procédure stockée
La procédure `create_document_with_qr` gère automatiquement :
- Création des catégories/sous-catégories si elles n'existent pas
- Génération des codes de documents séquentiels
- Création des entrées dans la base de données
- Retour des informations pour génération du QR code

## 🔒 Sécurité

- L'application est configurée pour le développement local
- En production, configurer les variables d'environnement appropriées
- Restreindre l'accès à la base de données
- Utiliser HTTPS en production

## 📝 Notes

- Les QR codes sont générés au format PNG dans le dossier `qr_images/`
- Les documents PDF doivent être placés dans le dossier `uploads/`
- L'application utilise le port 8000 par défaut
- Les logs sont affichés dans la console pour le débogage
