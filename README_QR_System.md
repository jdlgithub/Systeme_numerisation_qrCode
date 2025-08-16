
# Feuille de route — Système de Numérisation par QR Code (MySQL)

## Étape 0 — Préparer
- Installer MySQL et créer un utilisateur dédié (lecture/écriture).
- Définir l'emplacement des PDF (partage réseau).
- Installer Python + `mysql-connector-python`, `qrcode[pil]`, `python-dotenv`, `flask`.

## Étape 1 — Modèle de données
- Exécuter `schema_qr_archives.sql` pour créer la base `qr_archives` (tables: categories, subcategories, documents, qrcodes, sequences).

## Étape 2 — Taxonomie
- Remplir `categories` (ex: RH, FACT).
- Remplir `subcategories` (ex: RH/CONTRATS, FACT/2025).

## Étape 3 — Numérisation
- Scanner en PDF/A, 300 dpi, OCR activé.
- Ranger les fichiers: \\Serveur\<CAT>\<SUB>\<YYYY>\<DOC_CODE>.pdf

## Étape 4 — Enregistrement + QR
- Compléter `documents_template.csv`.
- Lancer: `python make_qr_images.py documents_template.csv`.
- Les entrées sont insérées via la procédure `create_document_with_qr(...)`.
- Les QR PNG sont générés dans `qr_images/` : un par document.

## Étape 5 — QR de Sous-catégorie (option)
- Insérer une ligne `qrcodes` avec `qr_type='SUBCATEGORY'`, `subcategory_id` ciblé,
  `qr_identifier` ex: `SUB-RH-CONTRATS-2025`, `qr_payload` ex: `http://intranet:8000/qr/SUB-RH-CONTRATS-2025`.

## Étape 6 — Service de résolution
- Démarrer `python app.py` (port 8000).
- Scanner `RH-CONTRATS-2025-0001` -> JSON avec métadonnées + chemin du PDF.

## Étape 7 — Opérations
- Coller les étiquettes QR sur les dossiers papier.
- Former le personnel (scan avec smartphone via navigateur intranet).
- Sauvegardes quotidiennes MySQL + fichiers.

## Sécurité
- Comptes MySQL distincts (lecture seule pour l'app, admin pour scripts).
- Journaliser l'accès aux endpoints.
- Restreindre l'app au réseau local.
