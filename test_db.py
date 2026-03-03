# test_db.py
import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )
    print("Successfully connected to MySQL server!")
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS upi_fraud_db")
    print("Database 'upi_fraud_db' is ready.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
