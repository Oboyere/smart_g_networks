#!/usr/bin/env python3
"""Diagnostic script to troubleshoot admin login issues"""
import mysql.connector
import bcrypt
from config import Config

def check_admin_user():
    """Check if admin user exists and diagnose issues"""
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD if Config.MYSQL_PASSWORD else '',
            database=Config.MYSQL_DATABASE
        )
        cursor = conn.cursor(dictionary=True)
        
        print("=" * 60)
        print("ADMIN LOGIN DIAGNOSTIC REPORT")
        print("=" * 60)
        
        # Check if users table exists
        try:
            cursor.execute("SHOW TABLES LIKE 'users'")
            if not cursor.fetchone():
                print("❌ ERROR: 'users' table does not exist!")
                print("   → Run: python init_db.py")
                cursor.close()
                conn.close()
                return
        except Exception as e:
            print(f"❌ ERROR checking table: {e}")
            cursor.close()
            conn.close()
            return
        
        print("✅ Database tables exist\n")
        
        # Check if admin user exists
        cursor.execute("SELECT * FROM users WHERE email = 'admin@smartg.com'")
        admin = cursor.fetchone()
        
        if not admin:
            print("❌ Admin user with email 'admin@smartg.com' does NOT exist!")
            print("   Recommended fixes:")
            print("   1. Run: python init_db.py  (to create default admin)")
            print("   2. Or run: python set_admin_password.py  (if user exists)\n")
            
            # List all users
            cursor.execute("SELECT id, name, email, role, branch_name FROM users")
            all_users = cursor.fetchall()
            if all_users:
                print(f"   Existing users in database ({len(all_users)}):")
                for user in all_users:
                    print(f"     - {user['email']} | Role: {user['role']} | Name: {user['name']}")
            else:
                print("   No users exist in the database at all!")
        else:
            print(f"✅ Admin user found!")
            print(f"   Email: {admin['email']}")
            print(f"   Name: {admin['name']}")
            print(f"   Role: {admin['role']}")
            print(f"   Branch ID: {admin['branch_id']}")
            print()
            
            # Test password with known values
            test_passwords = ['Admin@123', 'admin123', 'Admin@123', 'password']
            password_hash = admin['password_hash']
            
            print("Testing passwords:")
            for pwd in test_passwords:
                try:
                    is_valid = bcrypt.checkpw(pwd.encode('utf-8'), password_hash.encode('utf-8'))
                    status = "✅ MATCH" if is_valid else "❌ NO MATCH"
                    print(f"   {status}: '{pwd}'")
                except Exception as e:
                    print(f"   ⚠️  Error testing '{pwd}': {e}")
            
            print("\nIf none of the passwords above match, follow these steps:")
            print("   1. Run: python set_admin_password.py")
            print("   2. Use email: admin@smartg.com")
            print("   3. New password will be: Admin@123")
        
        # Check login screen credentials
        print("\n" + "=" * 60)
        print("LOGIN SCREEN INFORMATION")
        print("=" * 60)
        print("The login screen hints show:")
        print("   Admin Email: admin@smartg.co.ke  ← INCORRECT!")
        print("   Password: admin123  ← INCORRECT!")
        print()
        print("CORRECT LOGIN CREDENTIALS ARE:")
        print("   Email: admin@smartg.com")
        print("   Password: Admin@123")
        print("   Role: System Administrator (select from dropdown)")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        if err.errno == 2003:
            print("❌ ERROR: Cannot connect to MySQL!")
            print(f"   Host: {Config.MYSQL_HOST}")
            print(f"   Make sure MySQL server is running")
        else:
            print(f"❌ Database Error: {err}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_admin_user()
