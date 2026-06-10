#!/usr/bin/env python3
"""Database initialization script"""
import mysql.connector
import bcrypt
from config import Config

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_default_admin():
    """Create default admin user if it doesn't exist"""
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD if Config.MYSQL_PASSWORD else '',
            database=Config.MYSQL_DATABASE
        )
        cursor = conn.cursor(dictionary=True)
        
        # Check if admin already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", ('admin@smartg.com',))
        existing_admin = cursor.fetchone()
        
        if not existing_admin:
            # Create default admin
            default_password = 'admin123'
            password_hash = hash_password(default_password)
            
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                ('Administrator', 'admin@smartg.co.ke', password_hash, 'admin')
            )
            conn.commit()
            print("✅ Default admin user created!")
            print(f"   Email: admin@smartg.co.ke")
            print(f"   Password: {default_password}")
            print("   ⚠️  Please change the password after first login!")
        else:
            print("ℹ️  Admin user already exists")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")

def init_database():
    """Initialize the database from schema.sql"""
    try:
        # Connect to MySQL server (without database first)
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD if Config.MYSQL_PASSWORD else '',
        )
        cursor = conn.cursor()
        
        # Read and execute the schema file
        with open('database/schema.sql', 'r') as f:
            schema = f.read()
        
        # Execute each statement
        for statement in schema.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Database initialized successfully!")
        print(f"   Database: {Config.MYSQL_DATABASE}")
        print(f"   Host: {Config.MYSQL_HOST}")
        
        # Create default admin user
        create_default_admin()
        
    except mysql.connector.Error as err:
        if err.errno == 2003:
            print("❌ Error: Cannot connect to MySQL server.")
            print(f"   Make sure MySQL is running on {Config.MYSQL_HOST}")
            print("   Or set MYSQL_HOST in your .env file")
        else:
            print(f"❌ Database Error: {err}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    init_database()
