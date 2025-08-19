# Système de Numérisation avec QR Codes

Application Flask pour la numérisation et gestion de documents PDF avec génération automatique de QR codes et base de données MySQL locale.

## Architecture

- **Base de données** : MySQL locale
- **Backend** : Flask (Python)
- **Structure des fichiers** : `Archives/CATEGORIE/SOUS-CATEGORIE/ANNEE/fichier.pdf`
- **QR Codes** : Génération automatique pointant vers `/qr/{identifier}`

## Catégories Supportées

- **RH** : Ressources Humaines (CONTRATS, PAYSLIPS)
- **FACT** : Facturation (2023, 2024, 2025)
- **CATALG** : Catalogues (2023, 2024, 2025)

## Installation

### 1. Prérequis

- Python 3.8+
- MySQL Server 8.0+
- Git

### 2. Installation MySQL (Windows)

1. Télécharger MySQL Community Server depuis [mysql.com](https://dev.mysql.com/downloads/mysql/)
2. Installer avec les paramètres par défaut
3. Retenir le mot de passe root
4. Démarrer le service MySQL

### 3. Configuration du Projet

```bash
# Naviguer vers le dossier du projet
cd "c:\Users\minec\Downloads\Documents\Projet_stage\Qr_code numarization"

# Activer l'environnement virtuel
.venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### 4. Configuration de la Base de Données

1. **Modifier le fichier `.env`** (déjà créé) :
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=votre_mot_de_passe_mysql
DB_NAME=qr_archives
DB_PORT=3306
BASE_URL=http://localhost:5000
```

2. **Initialiser la base de données** :
```bash
python setup_database.py
```

### 5. Lancement de l'Application

```bash
python app.py
```

L'application sera accessible sur : `http://localhost:5000`

##  Fonctionnalités

### Interface Web
- **Création de documents** : Formulaire pour ajouter de nouveaux documents
- **Résolution de QR codes** : Tester la résolution des QR codes
- **Liste des documents** : Visualiser tous les documents enregistrés

### API REST
- `GET /qr/<identifier>` : Résoudre un QR code
- `GET /download/<identifier>` : Téléchargement direct d'un document
- `POST /api/documents` : Créer un nouveau document
- `GET /api/documents` : Lister tous les documents

### Structure des QR Codes
- **Documents** : `CATEGORIE-SOUSCATEGORIE-ANNEE-NUMERO` (ex: `RH-CONTRATS-2025-0001`)

## Structure du Projet

```
Qr_code_numarization/
├── app.py                    # Application Flask principale
├── config.py                # Configuration de l'application
├── database.py              # Gestion de la base de données MySQL
├── qr_generator.py          # Génération des QR codes
├── setup_database.py        # Script d'initialisation de la BD
├── migrate_to_archives.py   # Migration vers Archives/
├── requirements.txt         # Dépendances Python
├── schema_qr_archives.sql   # Schéma de base de données
├── .env                     # Variables d'environnement
├── templates/               # Templates HTML
│   ├── index.html
│   ├── document_view.html
│   └── subcategory_view.html
├── Archives/                # Documents organisés
│   ├── RH/
│   ├── FACT/
│   └── CATALG/
├── uploads/                 # Dossier temporaire
└── qr_images/              # Images QR codes générées
```

## Test de l'Application

### Créer un Document via API
```bash
curl -X POST http://localhost:5000/api/documents \
  -H "Content-Type: application/json" \
  -d '{
    "category_name": "RH",
    "subcategory_name": "CONTRATS",
    "filename": "contrat_dupont.pdf",
    "year": 2025,
    "title": "Contrat de travail Dupont",
    "description": "Contrat CDI pour M. Dupont"
  }'
```

### Tester la Résolution QR
1. Ouvrir `http://localhost:5000`
2. Utiliser un code généré (ex: `RH-CONTRATS-2025-0001`)
3. Accéder via `/qr/{code}` pour voir le document

## Configuration Avancée

### Variables d'Environnement (.env)
```env
# Base de données
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=votre_mot_de_passe
DB_NAME=qr_archives
DB_PORT=3306

# Application
BASE_URL=http://localhost:5000
SERVER_HOST=localhost
SERVER_PORT=5000
FLASK_DEBUG=true
```

## Dépannage

### Erreurs Communes

1. **Erreur de connexion MySQL** :
   - Vérifier que MySQL est démarré
   - Vérifier le mot de passe dans `.env`
   - Tester : `python setup_database.py`

2. **Erreur de permissions** :
   ```sql
   GRANT ALL PRIVILEGES ON qr_archives.* TO 'root'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Port déjà utilisé** :
   - Modifier `SERVER_PORT` dans `.env`
   - Redémarrer l'application
