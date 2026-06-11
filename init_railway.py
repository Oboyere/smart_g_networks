#!/usr/bin/env python3
"""Initialize Railway database with schema and default data"""
import mysql.connector
import bcrypt
import os
from config import Config

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def read_schema():
    """Read schema.sql file"""
    with open('database/schema.sql', 'r') as f:
        return f.read()

def init_database():
    """Initialize the database"""
    try:
        print("🔄 Connecting to Railway MySQL...")
        # First connect without database to create it if needed
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD if Config.MYSQL_PASSWORD else '',
            port=Config.MYSQL_PORT
        )
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        print(f"📝 Creating database '{Config.MYSQL_DATABASE}' if needed...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE}")
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # Now connect to the database
        print("🔄 Connecting to database...")
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD if Config.MYSQL_PASSWORD else '',
            database=Config.MYSQL_DATABASE,
            port=Config.MYSQL_PORT
        )
        cursor = conn.cursor()
        
        # Read and execute schema
        print("📝 Creating database tables...")
        schema = read_schema()
        
        # Split by semicolon and execute each statement
        statements = schema.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement:
                try:
                    cursor.execute(statement)
                except mysql.connector.errors.ProgrammingError as e:
                    # Skip if table already exists
                    if "already exists" not in str(e):
                        print(f"⚠️  {e}")
        
        conn.commit()
        print("✅ Database tables created/updated!")
        
        # Verify and create default admin if needed
        cursor.execute("SELECT * FROM users WHERE email = %s", ('admin@smartg.co.ke',))
        existing_admin = cursor.fetchone()
        
        if not existing_admin:
            print("👤 Creating default admin user...")
            password_hash = hash_password('admin123')
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                ('Administrator', 'admin@smartg.co.ke', password_hash, 'admin')
            )
            conn.commit()
            print("✅ Admin user created!")
            print("   Email: admin@smartg.co.ke")
            print("   Password: admin123")
        else:
            print("ℹ️  Admin user already exists")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Database initialization complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    init_database()
