#!/usr/bin/env python3
"""Reset admin password for admin@smartg.co.ke"""
import mysql.connector
import bcrypt
from config import Config

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

conn = mysql.connector.connect(
    host=Config.MYSQL_HOST,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD if Config.MYSQL_PASSWORD else '',
    database=Config.MYSQL_DATABASE
)
cursor = conn.cursor(dictionary=True)

# Reset password for the actual admin user
new_password = "admin123"
password_hash = hash_password(new_password)

cursor.execute(
    "UPDATE users SET password_hash = %s WHERE email = %s",
    (password_hash, 'admin@smartg.co.ke')
)
conn.commit()

print("✅ Admin password has been reset!")
print(f"   Email: admin@smartg.co.ke")
print(f"   New Password: {new_password}")
print(f"\n   Login with:")
print(f"   - Email: admin@smartg.co.ke")
print(f"   - Password: {new_password}")
print(f"   - Role: System Administrator")

cursor.close()
conn.close()
