#!/usr/bin/env python3
"""Helper script to configure MySQL credentials"""
import mysql.connector
from mysql.connector import Error

def test_mysql_connection(host='localhost', user='root', password='', database=''):
    """Test MySQL connection with given credentials"""
    try:
        if database:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
        else:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password
            )
        conn.close()
        return True
    except Error as err:
        return False

def main():
    print("MySQL Credential Test")
    print("=" * 50)
    
    # Try common password combinations
    common_passwords = ['', 'root', 'password', '123456', 'mysql']
    host = 'localhost'
    user = 'root'
    
    print(f"\nTesting connections for user '{user}' on '{host}'...")
    
    for pwd in common_passwords:
        if test_mysql_connection(host, user, pwd):
            print(f"✅ SUCCESS: Password is '{pwd if pwd else '(empty)'}'")
            print(f"\nUpdate your .env file with:")
            print(f"  MYSQL_PASSWORD={pwd}")
            return
    
    print("❌ Could not find working credentials.")
    print("\nPlease either:")
    print("1. Reset MySQL root password")
    print("2. Create a new MySQL user")
    print("3. Update .env with correct credentials")
    print("\nTo set MySQL root password, run:")
    print("  mysql -u root -e \"ALTER USER 'root'@'localhost' IDENTIFIED BY 'your_password';\"")

if __name__ == "__main__":
    main()
