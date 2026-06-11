# Configuration file
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    
    # Railway uses MYSQLHOST, MYSQLUSER, MYSQLPASSWORD, MYSQLDATABASE
    # Local development uses MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or os.environ.get('MYSQLHOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or os.environ.get('MYSQLUSER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or os.environ.get('MYSQLPASSWORD') or ''
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or os.environ.get('MYSQLDATABASE') or 'smart_g_networks'
    try:
        MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or os.environ.get('MYSQLPORT') or 3306)
    except (ValueError, TypeError):
        MYSQL_PORT = 3306
    
    JWT_SECRET = os.environ.get('JWT_SECRET', 'jwt-secret-key-change-in-production')