-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS ecommerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ecommerce_db;

-- 2. 客户表 (Customers)
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY,
    country VARCHAR(100) NOT NULL
);

-- 3. 订单表 (Invoices)
CREATE TABLE IF NOT EXISTS invoices (
    invoice_no VARCHAR(20) PRIMARY KEY,
    invoice_date DATETIME NOT NULL,
    customer_id INT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 4. 订单明细表 (Invoice Items)
CREATE TABLE IF NOT EXISTS invoice_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_no VARCHAR(20) NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    description VARCHAR(255),
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (invoice_no) REFERENCES invoices(invoice_no)
);