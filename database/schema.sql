CREATE DATABASE IF NOT EXISTS upi_fraud_db;
USE upi_fraud_db;

CREATE TABLE IF NOT EXISTS registration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fullname VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    userpwd VARCHAR(255) NOT NULL,
    emailid VARCHAR(100) NOT NULL,
    contact_no VARCHAR(15) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    step INT,
    type VARCHAR(20),
    amount DECIMAL(15, 2),
    nameOrig VARCHAR(50),
    oldbalanceOrg DECIMAL(15, 2),
    newbalanceOrig DECIMAL(15, 2),
    nameDest VARCHAR(50),
    oldbalanceDest DECIMAL(15, 2),
    newbalanceDest DECIMAL(15, 2),
    isFraud TINYINT(1),
    isFlaggedFraud TINYINT(1),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS models_performance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(50),
    accuracy DECIMAL(5, 4),
    precision_score DECIMAL(5, 4),
    recall_score DECIMAL(5, 4),
    f1_score DECIMAL(5, 4),
    trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
