-- Create Database
CREATE DATABASE IF NOT EXISTS ssuet_ai_db;
USE ssuet_ai_db;

-- 1. Users Table (Registration)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- 2. Chat Sessions Table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_name VARCHAR(100) DEFAULT 'New Chat',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Messages Table (Chat History)
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    sender ENUM('user', 'ai') NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

-- 4. Leads Table (Admission Interest)
CREATE TABLE IF NOT EXISTS leads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    interest_program VARCHAR(100),
    status ENUM('new', 'contacted', 'converted', 'closed') DEFAULT 'new',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 5. Feedback/Reviews Table
CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    category ENUM('ai_assistant', 'website', 'admissions', 'general') DEFAULT 'general',
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 6. Support Tickets Table
CREATE TABLE IF NOT EXISTS tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    subject VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    status ENUM('open', 'in_progress', 'resolved', 'closed') DEFAULT 'open',
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
    assigned_to VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 7. Admin Users Table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert Default Admin (username: admin, password: admin123)
-- Password hash for 'admin123' using bcrypt
INSERT INTO admins (username, password_hash, email) VALUES 
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS8Meb9uO', 'admin@ssuet.edu.pk');

-- Sample Faculty Data (Scraped from SSUET Website)
CREATE TABLE IF NOT EXISTS faculty (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    designation VARCHAR(100),
    department VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    office VARCHAR(50),
    specialization TEXT
);

-- Insert Sample Faculty Data
INSERT INTO faculty (name, designation, department, email, phone, office, specialization) VALUES
('Dr. Niaz Ahmed Akhtar', 'Chairman', 'HEC', 'chairman@hec.gov.pk', '+92-51-9100682', 'Islamabad', 'Higher Education Policy'),
('Dr. Muhammad Ali Ismail', 'Vice Chancellor', 'Administration', 'vc@ssuet.edu.pk', '+92-21-34988000', 'VC Office', 'Engineering Management'),
('Dr. Farooq Ahmad', 'Dean', 'FoECE', 'dean.ece@ssuet.edu.pk', '+92-21-34988001', 'Block A', 'Electrical Engineering'),
('Dr. Salman Ahmed', 'Dean', 'FoCAS', 'dean.cas@ssuet.edu.pk', '+92-21-34988002', 'Block B', 'Computer Science'),
('Dr. Asma Khan', 'Dean', 'FoCVA', 'dean.cva@ssuet.edu.pk', '+92-21-34988003', 'Block C', 'Civil Engineering'),
('Dr. Hassan Raza', 'Dean', 'FoBMS', 'dean.bms@ssuet.edu.pk', '+92-21-34988004', 'Block D', 'Business Management'),
('Prof. Dr. Tahir Hussain', 'Professor', 'Computer Science', 'tahir.hussain@ssuet.edu.pk', '+92-21-34988010', 'Room 201', 'Artificial Intelligence'),
('Dr. Sana Malik', 'Associate Professor', 'Software Engineering', 'sana.malik@ssuet.edu.pk', '+92-21-34988011', 'Room 202', 'Machine Learning'),
('Dr. Ahmed Qureshi', 'Assistant Professor', 'Electrical Engineering', 'ahmed.qureshi@ssuet.edu.pk', '+92-21-34988012', 'Room 203', 'Power Systems'),
('Dr. Fatima Zahra', 'Assistant Professor', 'Biomedical Engineering', 'fatima.zahra@ssuet.edu.pk', '+92-21-34988013', 'Room 204', 'Medical Imaging'),
('mrs. Mehwish', 'Assistant Professor', 'ACES', 'mehwish@ssuet.edu.pk', '+92-21-34988013', 'Room DFT2', 'AI'),
('mrs. kaneez', 'Assistant Professor', 'ACES', 'kaneez@ssuet.edu.pk', '+92-21-34988013', 'Room GFT4', 'AI');

-- Create Indexes for Better Performance
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_session_user ON chat_sessions(user_id);
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_tickets_status ON tickets(status);
