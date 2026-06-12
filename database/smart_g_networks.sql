-- Database schema
-- Create Database
CREATE DATABASE IF NOT EXISTS smart_g_networks;
USE smart_g_networks;

-- Users table (Admin and Branch Managers)
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'manager') DEFAULT 'manager',
    branch_id INT NULL,
    branch_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_branch_id (branch_id)
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    cost DECIMAL(10,2) NOT NULL,
    sales_commission DECIMAL(10,2) DEFAULT 0,
    manager_commission DECIMAL(10,2) DEFAULT 0,
    central_stock INT DEFAULT 0,
    low_stock_threshold INT DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Branch Stock table
CREATE TABLE IF NOT EXISTS branch_stock (
    id INT PRIMARY KEY AUTO_INCREMENT,
    branch_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY unique_branch_product (branch_id, product_id)
);

-- Sales table
CREATE TABLE IF NOT EXISTS sales (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sale_date DATE NOT NULL,
    branch_id INT NOT NULL,
    branch_name VARCHAR(100),
    total_amount DECIMAL(10,2) DEFAULT 0,
    total_sales_commission DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sale Items table
CREATE TABLE IF NOT EXISTS sale_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sale_id INT NOT NULL,
    product_id INT NOT NULL,
    product_name VARCHAR(200),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    commission DECIMAL(10,2),
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Stock Transfers/Approvals table
CREATE TABLE IF NOT EXISTS stock_approvals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    product_name VARCHAR(200),
    branch_id INT NOT NULL,
    quantity INT NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Expenses/Deductions table
CREATE TABLE IF NOT EXISTS expenses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    branch_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    reason TEXT,
    type ENUM('expense', 'shortage') DEFAULT 'expense',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Branch Reports table
CREATE TABLE IF NOT EXISTS branch_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    branch_id INT NOT NULL,
    branch_name VARCHAR(100),
    title VARCHAR(200) NOT NULL,
    summary TEXT,
    daily_production DECIMAL(10,2) DEFAULT 0,
    sales_commission DECIMAL(10,2) DEFAULT 0,
    total_deductions DECIMAL(10,2) DEFAULT 0,
    deduction_reason TEXT,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    admin_comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default admin user (password: admin123)
INSERT INTO users (name, email, password_hash, role) 
VALUES ('Administrator', 'admin@smartg.co.ke', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTt2j5dZqVkz.K', 'admin')
ON DUPLICATE KEY UPDATE id=id;

-- Insert sample products
INSERT INTO products (product_code, name, price, cost, sales_commission, manager_commission, central_stock) VALUES
('P001', 'Router X1', 2500, 1800, 100, 50, 50),
('P002', 'Network Switch', 4500, 3200, 150, 75, 30),
('P003', 'Ethernet Cable (10m)', 350, 200, 20, 10, 100),
('P004', 'WiFi Extender', 1800, 1200, 80, 40, 25),
('P005', 'Fiber Optic Kit', 8900, 6500, 300, 150, 15)
ON DUPLICATE KEY UPDATE id=id;

-- Insert sample branch (optional - for testing)
INSERT IGNORE INTO users (name, email, password_hash, role, branch_id, branch_name) 
VALUES ('John Mwangi', 'nairobi@smartg.co.ke', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTt2j5dZqVkz.K', 'manager', 2, 'Nairobi Branch');