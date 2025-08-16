-- Création de la base de données
CREATE DATABASE IF NOT EXISTS qr_archives;
USE qr_archives;

-- Table des catégories principales
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des sous-catégories
CREATE TABLE subcategories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    UNIQUE KEY unique_subcategory (category_id, name)
);

-- Table des documents
CREATE TABLE documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subcategory_id INT NOT NULL,
    document_code VARCHAR(50) NOT NULL UNIQUE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    year INT NOT NULL,
    title VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subcategory_id) REFERENCES subcategories(id)
);

-- Table des QR codes
CREATE TABLE qrcodes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qr_type ENUM('DOCUMENT', 'SUBCATEGORY') NOT NULL,
    qr_identifier VARCHAR(100) NOT NULL UNIQUE,
    qr_payload TEXT NOT NULL,
    document_id INT NULL,
    subcategory_id INT NULL,
    qr_image_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (subcategory_id) REFERENCES subcategories(id)
);

-- Table des séquences pour les codes de documents
CREATE TABLE sequences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subcategory_id INT NOT NULL,
    year INT NOT NULL,
    current_sequence INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subcategory_id) REFERENCES subcategories(id),
    UNIQUE KEY unique_sequence (subcategory_id, year)
);

-- Procédure pour créer un document avec QR code
DELIMITER //
CREATE PROCEDURE create_document_with_qr(
    IN p_subcategory_name VARCHAR(100),
    IN p_category_name VARCHAR(50),
    IN p_filename VARCHAR(255),
    IN p_file_path VARCHAR(500),
    IN p_year INT,
    IN p_title VARCHAR(255),
    IN p_description TEXT
)
BEGIN
    DECLARE v_subcategory_id INT;
    DECLARE v_category_id INT;
    DECLARE v_document_id INT;
    DECLARE v_document_code VARCHAR(50);
    DECLARE v_current_sequence INT;
    DECLARE v_qr_identifier VARCHAR(100);
    DECLARE v_qr_payload TEXT;
    
    -- Récupérer ou créer la catégorie
    SELECT id INTO v_category_id FROM categories WHERE name = p_category_name;
    IF v_category_id IS NULL THEN
        INSERT INTO categories (name) VALUES (p_category_name);
        SET v_category_id = LAST_INSERT_ID();
    END IF;
    
    -- Récupérer ou créer la sous-catégorie
    SELECT id INTO v_subcategory_id FROM subcategories WHERE name = p_subcategory_name AND category_id = v_category_id;
    IF v_subcategory_id IS NULL THEN
        INSERT INTO subcategories (category_id, name) VALUES (v_category_id, p_subcategory_name);
        SET v_subcategory_id = LAST_INSERT_ID();
    END IF;
    
    -- Gérer la séquence pour le code de document
    SELECT current_sequence INTO v_current_sequence FROM sequences WHERE subcategory_id = v_subcategory_id AND year = p_year;
    IF v_current_sequence IS NULL THEN
        INSERT INTO sequences (subcategory_id, year, current_sequence) VALUES (v_subcategory_id, p_year, 1);
        SET v_current_sequence = 1;
    ELSE
        UPDATE sequences SET current_sequence = current_sequence + 1 WHERE subcategory_id = v_subcategory_id AND year = p_year;
        SET v_current_sequence = v_current_sequence + 1;
    END IF;
    
    -- Générer le code de document
    SET v_document_code = CONCAT(p_category_name, '-', p_subcategory_name, '-', p_year, '-', LPAD(v_current_sequence, 4, '0'));
    
    -- Insérer le document
    INSERT INTO documents (subcategory_id, document_code, filename, file_path, year, title, description)
    VALUES (v_subcategory_id, v_document_code, p_filename, p_file_path, p_year, p_title, p_description);
    SET v_document_id = LAST_INSERT_ID();
    
    -- Générer le QR code
    SET v_qr_identifier = v_document_code;
    SET v_qr_payload = CONCAT('http://localhost:8000/qr/', v_qr_identifier);
    
    -- Insérer le QR code
    INSERT INTO qrcodes (qr_type, qr_identifier, qr_payload, document_id, qr_image_path)
    VALUES ('DOCUMENT', v_qr_identifier, v_qr_payload, v_document_id, CONCAT('qr_images/', v_qr_identifier, '.png'));
    
    -- Retourner les informations créées
    SELECT v_document_code as document_code, v_qr_identifier as qr_identifier, v_qr_payload as qr_payload;
END //
DELIMITER ;

-- Insertion de données de test
INSERT INTO categories (name, description) VALUES 
('RH', 'Ressources Humaines'),
('FACT', 'Facturation');

INSERT INTO subcategories (category_id, name, description) VALUES 
(1, 'CONTRATS', 'Contrats de travail'),
(1, 'PAYSLIPS', 'Bulletins de paie'),
(2, '2025', 'Factures 2025');
