#!/usr/bin/env python3
"""Check password for existing admin user"""
import mysql.connector
import bcrypt
from config import Config

conn = mysql.connector.connect(
    host=Config.MYSQL_HOST,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD if Config.MYSQL_PASSWORD else '',
    database=Config.MYSQL_DATABASE
)
cursor = conn.cursor(dictionary=True)

# Get the actual admin user
cursor.execute("SELECT * FROM users WHERE email = 'admin@smartg.co.ke'")
admin = cursor.fetchone()

if admin:
    print(f"Admin user found: {admin['email']}")
    print(f"Name: {admin['name']}")
    password_hash = admin['password_hash']
    
    # Test common passwords
    test_passwords = ['admin123', 'Admin@123', 'password', '123456', 'admin', 'smartg']
    
    print("\nTesting passwords:")
    for pwd in test_passwords:
        try:
            is_valid = bcrypt.checkpw(pwd.encode('utf-8'), password_hash.encode('utf-8'))
            if is_valid:
                print(f"✅ FOUND: Password is '{pwd}'")
            else:
                print(f"❌ '{pwd}' - NO")
        except Exception as e:
            print(f"⚠️  Error: {e}")
else:
    print("Admin user not found")

cursor.close()
conn.close()
