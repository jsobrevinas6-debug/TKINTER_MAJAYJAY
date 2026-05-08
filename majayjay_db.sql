-- ============================================================
--  majayjay_db  –  Full Database Schema
--  Run this file once in MySQL to set up the entire database.
--  Compatible with MySQL 8.0+
-- ============================================================

CREATE DATABASE IF NOT EXISTS majayjay_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE majayjay_db;

-- ============================================================
--  TABLE: users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    user_id       INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    email         VARCHAR(255)    NOT NULL UNIQUE,
    password      VARCHAR(512)    NOT NULL,
    first_name    VARCHAR(100)    NOT NULL,
    middle_name   VARCHAR(100)        NULL,
    last_name     VARCHAR(100)    NOT NULL,
    user_type     ENUM('student','mayor','admin')
                                  NOT NULL DEFAULT 'student',
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                           ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    INDEX idx_users_email (email),
    INDEX idx_users_type  (user_type)
) ENGINE=InnoDB;


-- ============================================================
--  TABLE: applications
-- ============================================================
CREATE TABLE IF NOT EXISTS applications (
    application_id  INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    user_id         INT UNSIGNED    NOT NULL,

    -- Personal Information
    first_name      VARCHAR(100)    NOT NULL,
    middle_name     VARCHAR(100)        NULL,
    last_name       VARCHAR(100)    NOT NULL,
    student_id      VARCHAR(50)     NOT NULL,
    contact_number  VARCHAR(20)     NOT NULL,

    -- Address
    municipality    VARCHAR(100)    NOT NULL,
    barangay        VARCHAR(100)    NOT NULL,

    -- Academic Information
    school_name     VARCHAR(200)    NOT NULL,
    course          VARCHAR(200)    NOT NULL,
    year_level      VARCHAR(20)     NOT NULL,
    gwa             DECIMAL(4,2)    NOT NULL,
    year_applied    YEAR            NOT NULL,

    -- Essay
    essay           TEXT            NOT NULL,

    -- Uploaded Documents
    doc_school_id   LONGBLOB            NULL,
    doc_id_picture  LONGBLOB            NULL,
    doc_birth_cert  LONGBLOB            NULL,
    doc_grades      LONGBLOB            NULL,
    doc_cor         LONGBLOB            NULL,

    -- Status & Timestamps
    status          ENUM('pending','approved','rejected','cancelled')
                                    NOT NULL DEFAULT 'pending',
    remarks         TEXT                NULL,
    reviewed_by     INT UNSIGNED        NULL,
    reviewed_at     DATETIME            NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                               ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (application_id),
    CONSTRAINT fk_app_user
        FOREIGN KEY (user_id)     REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_app_reviewer
        FOREIGN KEY (reviewed_by) REFERENCES users (user_id) ON DELETE SET NULL,
    INDEX idx_app_user_id (user_id),
    INDEX idx_app_status  (status),
    INDEX idx_app_year    (year_applied)
) ENGINE=InnoDB;


-- ============================================================
--  TABLE: renewals
-- ============================================================
CREATE TABLE IF NOT EXISTS renewals (
    renewal_id      INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    user_id         INT UNSIGNED    NOT NULL,
    application_id  INT UNSIGNED    NOT NULL,

    -- Personal Information
    first_name      VARCHAR(100)    NOT NULL,
    middle_name     VARCHAR(100)        NULL,
    last_name       VARCHAR(100)    NOT NULL,
    student_id      VARCHAR(50)     NOT NULL,
    contact_number  VARCHAR(20)     NOT NULL,

    -- Address
    municipality    VARCHAR(100)    NOT NULL,
    barangay        VARCHAR(100)    NOT NULL,

    -- Academic Information
    school_name     VARCHAR(200)    NOT NULL,
    course          VARCHAR(200)    NOT NULL,
    year_level      VARCHAR(20)     NOT NULL,
    gwa             DECIMAL(4,2)    NOT NULL,
    year_applied    YEAR            NOT NULL,

    -- Remarks & Documents
    remarks         TEXT                NULL,
    doc_school_id   LONGBLOB            NULL,
    doc_id_picture  LONGBLOB            NULL,
    doc_birth_cert  LONGBLOB            NULL,
    doc_grades      LONGBLOB            NULL,
    doc_cor         LONGBLOB            NULL,

    -- Status & Timestamps
    status          ENUM('pending','approved','rejected')
                                    NOT NULL DEFAULT 'pending',
    reviewed_by     INT UNSIGNED        NULL,
    reviewed_at     DATETIME            NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                               ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (renewal_id),
    CONSTRAINT fk_renewal_user
        FOREIGN KEY (user_id)        REFERENCES users        (user_id)        ON DELETE CASCADE,
    CONSTRAINT fk_renewal_app
        FOREIGN KEY (application_id) REFERENCES applications (application_id) ON DELETE CASCADE,
    CONSTRAINT fk_renewal_reviewer
        FOREIGN KEY (reviewed_by)    REFERENCES users        (user_id)        ON DELETE SET NULL,
    INDEX idx_renewal_user   (user_id),
    INDEX idx_renewal_app    (application_id),
    INDEX idx_renewal_status (status)
) ENGINE=InnoDB;


-- ============================================================
--  Seed: default admin + mayor accounts
--  Run setup_db.py instead of this block — it generates real
--  pbkdf2 hashes automatically.
-- ============================================================
INSERT IGNORE INTO users
    (email, password, first_name, middle_name, last_name, user_type)
VALUES
    ('admin@majayjay.gov.ph', 'REPLACE_WITH_HASHED_PASSWORD', 'System', NULL, 'Admin', 'admin'),
    ('mayor@majayjay.gov.ph', 'REPLACE_WITH_HASHED_PASSWORD', 'Mayor',  NULL, 'User',  'mayor');
