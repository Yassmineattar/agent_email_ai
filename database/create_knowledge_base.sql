CREATE TABLE knowledge_base (
    id INT AUTO_INCREMENT PRIMARY KEY,
    logiciel VARCHAR(100) NOT NULL,                -- Ex: SAP, AGIRH, Docubase
    question TEXT NOT NULL,                        -- Description du problème ou question fréquente
    reponse TEXT NOT NULL,                         -- Solution ou réponse fournie
    mots_cles TEXT,                                -- Mots-clés ou tags utiles
    source_email_id VARCHAR(255),                  -- Identifiant ou sujet du mail
    image_paths TEXT,                              -- Chemins vers les images liés (séparés par virgule si plusieurs)
    source_folder VARCHAR(100),                    -- Nom du dossier Gmail (SAP, AGIRH, etc.)
    date_reception DATETIME,                       -- Date réelle du mail
    date_insertion TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Date d’enregistrement dans la base
);
