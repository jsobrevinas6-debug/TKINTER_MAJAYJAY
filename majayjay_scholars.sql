-- ============================================
-- MySQL Database Schema for Majayjay Scholars
-- ============================================

CREATE DATABASE IF NOT EXISTS majayjay_scholars;
USE majayjay_scholars;

DROP TABLE IF EXISTS renew;
DROP TABLE IF EXISTS application;
DROP TABLE IF EXISTS renewal_settings;
DROP TABLE IF EXISTS users;

-- ============================================
-- Create users table
-- ============================================
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    contact_number VARCHAR(20),
    password VARCHAR(255),
    user_type ENUM('student', 'admin', 'mayor') DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    auth_user_id VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Create application table
-- ============================================
CREATE TABLE application (
    application_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    student_id VARCHAR(100),
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    last_name VARCHAR(50) NOT NULL,
    contact_number VARCHAR(50),
    address VARCHAR(500),
    municipality VARCHAR(50),
    baranggay VARCHAR(45),
    school_name VARCHAR(255),
    course VARCHAR(255),
    year_level VARCHAR(50),
    gwa DECIMAL(3,2),
    year_applied INT NOT NULL,
    reason TEXT,
    scholarship_type VARCHAR(45),
    school_id_path VARCHAR(255),
    id_picture_path VARCHAR(255),
    birth_certificate_path VARCHAR(255),
    grades_path VARCHAR(255),
    cor_path VARCHAR(255),
    status ENUM('pending', 'approved', 'rejected', 'renewal') DEFAULT 'pending' NOT NULL,
    archived BOOLEAN DEFAULT FALSE,
    submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_archived (archived)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Create renew table
-- ============================================
CREATE TABLE renew (
    renewal_id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    user_id INT,
    student_id VARCHAR(100),
    first_name VARCHAR(50),
    middle_name VARCHAR(50),
    last_name VARCHAR(50),
    contact_number VARCHAR(50),
    address VARCHAR(500),
    municipality VARCHAR(50),
    baranggay VARCHAR(45),
    course VARCHAR(255),
    year_level VARCHAR(50),
    gwa DECIMAL(3,2),
    reason TEXT,
    school_id_path VARCHAR(255),
    id_picture_path VARCHAR(255),
    birth_certificate_path VARCHAR(255),
    grades_path VARCHAR(255),
    cor_path VARCHAR(255),
    status VARCHAR(50) DEFAULT 'Pending',
    archived BOOLEAN DEFAULT FALSE,
    submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES application(application_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_archived (archived)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Create renewal_settings table
-- ============================================
CREATE TABLE renewal_settings (
    id INT PRIMARY KEY DEFAULT 1,
    is_open BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO renewal_settings (id, is_open) VALUES (1, FALSE);

-- ============================================
-- Insert all users in ONE single INSERT
-- ✅ Fixed: removed duplicate INSERT INTO, fixed semicolons on 101 & 102
-- ============================================
INSERT INTO users (email, first_name, middle_name, last_name, contact_number, password, user_type) VALUES
('admin@gmail.com', 'Admin', 'System', 'Administrator', '09171234567', 'asdfgh', 'admin'),
('mayor@gmail.com', 'Mayor', 'Municipal', 'Official', '09181234567', 'asdfgh', 'mayor'),
('user1@gmail.com', 'John', 'Michael', 'Smith', '09191234567', 'asdfgh', 'student'),
('user2@gmail.com', 'Maria', 'Elena', 'Garcia', '09201234567', 'asdfgh', 'student'),
('user3@gmail.com', 'Jose', 'Antonio', 'Rodriguez', '09211234567', 'asdfgh', 'student'),
('user4@gmail.com', 'Ana', 'Sofia', 'Martinez', '09221234567', 'asdfgh', 'student'),
('user5@gmail.com', 'Carlos', 'Miguel', 'Lopez', '09231234567', 'asdfgh', 'student'),
('user6@gmail.com', 'Elena', 'Rose', 'Hernandez', '09241234567', 'asdfgh', 'student'),
('user7@gmail.com', 'David', 'James', 'Gonzalez', '09251234567', 'asdfgh', 'student'),
('user8@gmail.com', 'Sofia', 'Grace', 'Perez', '09261234567', 'asdfgh', 'student'),
('user9@gmail.com', 'Miguel', 'Luis', 'Sanchez', '09271234567', 'asdfgh', 'student'),
('user10@gmail.com', 'Isabella', 'Marie', 'Ramirez', '09281234567', 'asdfgh', 'student'),
('user11@gmail.com', 'Diego', 'Rafael', 'Torres', '09291234567', 'asdfgh', 'student'),
('user12@gmail.com', 'Camila', 'Victoria', 'Flores', '09301234567', 'asdfgh', 'student'),
('user13@gmail.com', 'Gabriel', 'Daniel', 'Rivera', '09311234567', 'asdfgh', 'student'),
('user14@gmail.com', 'Valentina', 'Luna', 'Gomez', '09321234567', 'asdfgh', 'student'),
('user15@gmail.com', 'Sebastian', 'Mateo', 'Diaz', '09331234567', 'asdfgh', 'student'),
('user16@gmail.com', 'Lucia', 'Carmen', 'Cruz', '09341234567', 'asdfgh', 'student'),
('user17@gmail.com', 'Mateo', 'Andres', 'Reyes', '09351234567', 'asdfgh', 'student'),
('user18@gmail.com', 'Emma', 'Sophia', 'Morales', '09361234567', 'asdfgh', 'student'),
('user19@gmail.com', 'Lucas', 'Gabriel', 'Jimenez', '09371234567', 'asdfgh', 'student'),
('user20@gmail.com', 'Mia', 'Isabella', 'Ruiz', '09381234567', 'asdfgh', 'student'),
('user21@gmail.com', 'Daniel', 'Alejandro', 'Mendoza', '09391234567', 'asdfgh', 'student'),
('user22@gmail.com', 'Olivia', 'Natalia', 'Castro', '09401234567', 'asdfgh', 'student'),
('user23@gmail.com', 'Adrian', 'Fernando', 'Ortiz', '09411234567', 'asdfgh', 'student'),
('user24@gmail.com', 'Ava', 'Gabriela', 'Romero', '09421234567', 'asdfgh', 'student'),
('user25@gmail.com', 'Santiago', 'Nicolas', 'Alvarez', '09431234567', 'asdfgh', 'student'),
('user26@gmail.com', 'Charlotte', 'Diana', 'Navarro', '09441234567', 'asdfgh', 'student'),
('user27@gmail.com', 'Nicolas', 'Eduardo', 'Gutierrez', '09451234567', 'asdfgh', 'student'),
('user28@gmail.com', 'Amelia', 'Patricia', 'Ramos', '09461234567', 'asdfgh', 'student'),
('user29@gmail.com', 'Leonardo', 'Ricardo', 'Vasquez', '09471234567', 'asdfgh', 'student'),
('user30@gmail.com', 'Harper', 'Eliza', 'Castillo', '09481234567', 'asdfgh', 'student'),
('user31@gmail.com', 'Alejandro', 'Xavier', 'Herrera', '09491234567', 'asdfgh', 'student'),
('user32@gmail.com', 'Evelyn', 'Jade', 'Medina', '09501234567', 'asdfgh', 'student'),
('user33@gmail.com', 'Samuel', 'Isaac', 'Aguilar', '09511234567', 'asdfgh', 'student'),
('user34@gmail.com', 'Abigail', 'Ruby', 'Vargas', '09521234567', 'asdfgh', 'student'),
('user35@gmail.com', 'Benjamin', 'Oliver', 'Cortez', '09531234567', 'asdfgh', 'student'),
('user36@gmail.com', 'Emily', 'Claire', 'Silva', '09541234567', 'asdfgh', 'student'),
('user37@gmail.com', 'Elijah', 'Noah', 'Fuentes', '09551234567', 'asdfgh', 'student'),
('user38@gmail.com', 'Elizabeth', 'Anne', 'Mendez', '09561234567', 'asdfgh', 'student'),
('user39@gmail.com', 'Matias', 'Julian', 'Santiago', '09571234567', 'asdfgh', 'student'),
('user40@gmail.com', 'Victoria', 'Grace', 'Delgado', '09581234567', 'asdfgh', 'student'),
('user41@gmail.com', 'Joshua', 'Caleb', 'Moreno', '09591234567', 'asdfgh', 'student'),
('user42@gmail.com', 'Madison', 'Faith', 'Guzman', '09601234567', 'asdfgh', 'student'),
('user43@gmail.com', 'Christopher', 'Ryan', 'Rojas', '09611234567', 'asdfgh', 'student'),
('user44@gmail.com', 'Chloe', 'Alexandra', 'Nunez', '09621234567', 'asdfgh', 'student'),
('user45@gmail.com', 'Andrew', 'Thomas', 'Rios', '09631234567', 'asdfgh', 'student'),
('user46@gmail.com', 'Grace', 'Lily', 'Salazar', '09641234567', 'asdfgh', 'student'),
('user47@gmail.com', 'Nathan', 'Aaron', 'Fernandez', '09651234567', 'asdfgh', 'student'),
('user48@gmail.com', 'Zoey', 'Hannah', 'Pena', '09661234567', 'asdfgh', 'student'),
('user49@gmail.com', 'Isaac', 'Jordan', 'Campos', '09671234567', 'asdfgh', 'student'),
('user50@gmail.com', 'Lily', 'Violet', 'Soto', '09681234567', 'asdfgh', 'student'),
('user51@gmail.com', 'Aaron', 'James', 'Williams', '09691234567', 'asdfgh', 'student'),
('user52@gmail.com', 'Bella', 'Rose', 'Johnson', '09701234567', 'asdfgh', 'student'),
('user53@gmail.com', 'Connor', 'Lee', 'Brown', '09711234567', 'asdfgh', 'student'),
('user54@gmail.com', 'Diana', 'Mae', 'Jones', '09721234567', 'asdfgh', 'student'),
('user55@gmail.com', 'Ethan', 'Cruz', 'Davis', '09731234567', 'asdfgh', 'student'),
('user56@gmail.com', 'Fiona', 'Claire', 'Miller', '09741234567', 'asdfgh', 'student'),
('user57@gmail.com', 'George', 'Paul', 'Wilson', '09751234567', 'asdfgh', 'student'),
('user58@gmail.com', 'Hannah', 'Joy', 'Moore', '09761234567', 'asdfgh', 'student'),
('user59@gmail.com', 'Ivan', 'Rey', 'Taylor', '09771234567', 'asdfgh', 'student'),
('user60@gmail.com', 'Julia', 'Ann', 'Anderson', '09781234567', 'asdfgh', 'student'),
('user61@gmail.com', 'Kevin', 'Mark', 'Thomas', '09791234567', 'asdfgh', 'student'),
('user62@gmail.com', 'Laura', 'Faith', 'Jackson', '09801234567', 'asdfgh', 'student'),
('user63@gmail.com', 'Marco', 'Luis', 'White', '09811234567', 'asdfgh', 'student'),
('user64@gmail.com', 'Nina', 'Grace', 'Harris', '09821234567', 'asdfgh', 'student'),
('user65@gmail.com', 'Oscar', 'Dante', 'Martin', '09831234567', 'asdfgh', 'student'),
('user66@gmail.com', 'Paula', 'Jean', 'Garcia', '09841234567', 'asdfgh', 'student'),
('user67@gmail.com', 'Quinn', 'Ray', 'Martinez', '09851234567', 'asdfgh', 'student'),
('user68@gmail.com', 'Rachel', 'Hope', 'Robinson', '09861234567', 'asdfgh', 'student'),
('user69@gmail.com', 'Stefan', 'Cole', 'Clark', '09871234567', 'asdfgh', 'student'),
('user70@gmail.com', 'Tanya', 'Mae', 'Rodriguez', '09881234567', 'asdfgh', 'student'),
('user71@gmail.com', 'Uriel', 'John', 'Lewis', '09891234567', 'asdfgh', 'student'),
('user72@gmail.com', 'Vera', 'Lynn', 'Lee', '09901234567', 'asdfgh', 'student'),
('user73@gmail.com', 'Walter', 'Ben', 'Walker', '09911234567', 'asdfgh', 'student'),
('user74@gmail.com', 'Xena', 'Rae', 'Hall', '09921234567', 'asdfgh', 'student'),
('user75@gmail.com', 'Yvan', 'Rex', 'Allen', '09931234567', 'asdfgh', 'student'),
('user76@gmail.com', 'Zara', 'Mae', 'Young', '09941234567', 'asdfgh', 'student'),
('user77@gmail.com', 'Alvin', 'Cruz', 'Hernandez', '09951234567', 'asdfgh', 'student'),
('user78@gmail.com', 'Bianca', 'Sofia', 'King', '09961234567', 'asdfgh', 'student'),
('user79@gmail.com', 'Cedric', 'Noel', 'Wright', '09971234567', 'asdfgh', 'student'),
('user80@gmail.com', 'Danica', 'Faye', 'Lopez', '09981234567', 'asdfgh', 'student'),
('user81@gmail.com', 'Emilio', 'Jose', 'Hill', '09991234567', 'asdfgh', 'student'),
('user82@gmail.com', 'Felicia', 'Dawn', 'Scott', '09101234568', 'asdfgh', 'student'),
('user83@gmail.com', 'Gerard', 'Marc', 'Green', '09111234568', 'asdfgh', 'student'),
('user84@gmail.com', 'Helena', 'Iris', 'Adams', '09121234568', 'asdfgh', 'student'),
('user85@gmail.com', 'Ignacio', 'Sam', 'Baker', '09131234568', 'asdfgh', 'student'),
('user86@gmail.com', 'Jasmine', 'Luz', 'Gonzalez', '09141234568', 'asdfgh', 'student'),
('user87@gmail.com', 'Kristian', 'Rey', 'Nelson', '09151234568', 'asdfgh', 'student'),
('user88@gmail.com', 'Lara', 'Beth', 'Carter', '09161234568', 'asdfgh', 'student'),
('user89@gmail.com', 'Manuel', 'Gio', 'Mitchell', '09171234568', 'asdfgh', 'student'),
('user90@gmail.com', 'Nadine', 'Elle', 'Perez', '09181234568', 'asdfgh', 'student'),
('user91@gmail.com', 'Orlando', 'Vince', 'Roberts', '09191234568', 'asdfgh', 'student'),
('user92@gmail.com', 'Pamela', 'Lyn', 'Turner', '09201234568', 'asdfgh', 'student'),
('user93@gmail.com', 'Quirino', 'Ace', 'Phillips', '09211234568', 'asdfgh', 'student'),
('user94@gmail.com', 'Rowena', 'Faith', 'Campbell', '09221234568', 'asdfgh', 'student'),
('user95@gmail.com', 'Sergio', 'Dan', 'Parker', '09231234568', 'asdfgh', 'student'),
('user96@gmail.com', 'Tricia', 'Anne', 'Evans', '09241234568', 'asdfgh', 'student'),
('user97@gmail.com', 'Ulysses', 'Ray', 'Edwards', '09251234568', 'asdfgh', 'student'),
('user98@gmail.com', 'Vivian', 'Rose', 'Collins', '09261234568', 'asdfgh', 'student'),
('user99@gmail.com', 'Winston', 'Carl', 'Stewart', '09271234568', 'asdfgh', 'student'),
('user100@gmail.com', 'Ximena', 'Luz', 'Sanchez', '09281234568', 'asdfgh', 'student'),
('user101@gmail.com', 'Mat', 'Lui', 'Ever', '09291234568', 'asdfgh', 'student'),
('user102@gmail.com', 'Xaia', 'Em', 'Vez', '09301234568', 'asdfgh', 'student');

-- ============================================
-- Insert sample applications
-- ============================================
INSERT INTO application (
    user_id, student_id, first_name, middle_name, last_name, contact_number,
    address, municipality, baranggay, school_name, course, year_level,
    gwa, year_applied, reason, scholarship_type, status
)
SELECT 
    u.user_id,
    CONCAT('STU-', LPAD(u.user_id, 5, '0')),
    u.first_name,
    u.middle_name,
    u.last_name,
    u.contact_number,
    CONCAT('Sample Address ', u.user_id),
    'Majayjay',
    CONCAT('Barangay ', (u.user_id % 20) + 1),
    'Sample University',
    'BS Information Technology',
    '2nd Year',
    ROUND(1.25 + (RAND() * 0.50), 2),
    2025,
    'I am applying for this scholarship to support my education and achieve my academic goals.',
    'new',
    'approved'
FROM users u
WHERE u.user_type = 'student'
LIMIT 100;

-- ============================================
-- Insert sample renewals
-- ============================================
INSERT INTO renew (
    application_id, user_id, student_id,
    first_name, middle_name, last_name,
    contact_number, address, municipality,
    baranggay, course, year_level,
    gwa, reason, status
)
SELECT
    a.application_id,
    a.user_id,
    a.student_id,
    a.first_name,
    a.middle_name,
    a.last_name,
    a.contact_number,
    a.address,
    a.municipality,
    a.baranggay,
    a.course,
    '3rd Year',
    ROUND(1.25 + (RAND() * 0.50), 2),
    'I would like to renew my scholarship to continue my studies and maintain my academic performance.',
    'Pending'
FROM application a
WHERE a.status = 'approved'
LIMIT 80;

-- ============================================
-- UPDATE: Change pending to approved
-- ============================================
UPDATE application
SET status = 'approved'
WHERE status = 'pending';

-- ============================================
-- ALTER: Remove year_applied column
-- ============================================
ALTER TABLE application
DROP COLUMN year_applied;

-- ============================================
-- Success message
-- ============================================
SELECT 'Database majayjay_scholars created successfully!' AS message;
SELECT COUNT(*) AS total_users FROM users;
SELECT COUNT(*) AS total_applications FROM application;
SELECT COUNT(*) AS total_renewals FROM renew;
SELECT * FROM users;
SELECT * from RENEW;

UPDATE users
SET first_name = 'Zaira'
WHERE user_id = 100;

DELETE FROM users
WHERE user_id = 104;


