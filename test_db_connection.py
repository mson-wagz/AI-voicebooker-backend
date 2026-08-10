#!/usr/bin/env python3
"""
Test PostgreSQL database connection
"""
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test database connection"""
    try:
        # Connection parameters
        conn_params = {
            'host': 'gondola.proxy.rlwy.net',
            'port': '37599',
            'database': 'railway',
            'user': 'postgres',
            'password': 'yBvSGGYYcVIynQqwlVpLtUCIhjMkkrvS'
        }
        
        print("🔌 Connecting to PostgreSQL database...")
        print(f"Host: {conn_params['host']}")
        print(f"Port: {conn_params['port']}")
        print(f"Database: {conn_params['database']}")
        print(f"User: {conn_params['user']}")
        
        # Connect to database
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print("✅ Connection successful!")
        print(f"PostgreSQL version: {version[0]}")
        
        # Check tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print("\n📋 Available tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Close connection
        cursor.close()
        conn.close()
        print("\n🔌 Connection closed successfully")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_connection()
