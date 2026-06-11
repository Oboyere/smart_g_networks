#!/usr/bin/env python3
"""Initialize Railway database with schema and default data"""
import mysql.connector
import bcrypt
import os
import sys
from config import Config

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def read_schema():
    """Read schema.sql file"""
    try:
        with open('database/schema.sql', 'r') as f:
            return f.read()
    except FileNotFoundError:
        print("⚠️  schema.sql not found, skipping schema initialization")
        return None

def init_database():
    """Initialize the database"""
    try:
        print("🔄 Connecting to Railway MySQL...")
        # First connect without database to create it if needed
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD or '',
            port=Config.MYSQL_PORT,
            autocommit=True
        )
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        print(f"📝 Creating database '{Config.MYSQL_DATABASE}' if needed...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DATABASE}`")
        
        cursor.close()
        conn.close()
        
        # Now connect to the database
        print("🔄 Connecting to database...")
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD or '',
            database=Config.MYSQL_DATABASE,
            port=Config.MYSQL_PORT,
            autocommit=False
        )
        cursor = conn.cursor()
        
        # Read and execute schema
        schema = read_schema()
        if schema:
            print("📝 Creating database tables...")
            # Remove comments and split properly
            lines = [line.strip() for line in schema.split('\n') if line.strip() and not line.strip().startswith('--')]
            current_statement = ""
            
            for line in lines:
                current_statement += " " + line
                if line.endswith(';'):
                    statement = current_statement.strip()
                    if statement and not statement.startswith('CREATE DATABASE'):
                        try:
                            cursor.execute(statement)
                        except Exception as e:
                            if "already exists" not in str(e):
                                print(f"⚠️  {e}")
                    current_statement = ""
            
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
        print(f"⚠️  Database initialization warning: {e}")
        print("   App will attempt to initialize on first login")
        return False

if __name__ == '__main__':
    init_database()
