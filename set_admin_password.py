#!/usr/bin/env python3
"""Script to set/reset admin password"""
import mysql.connector
import bcrypt
from config import Config

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def set_admin_password(email, new_password):
    """Set admin password"""
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD if Config.MYSQL_PASSWORD else '',
            database=Config.MYSQL_DATABASE
        )
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User {email} not found")
            cursor.close()
            conn.close()
            return
        
        # Update password
        password_hash = hash_password(new_password)
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE email = %s",
            (password_hash, email)
        )
        conn.commit()
        
        print(f"✅ Password updated for {email}")
        print(f"   New password: {new_password}")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Set default admin password
    set_admin_password('admin@smartg.com', 'Admin@123')
