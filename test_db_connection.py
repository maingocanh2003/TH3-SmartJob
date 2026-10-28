"""
Test Database Connection for SmartJob
======================================
Script kiểm tra kết nối database và verify setup
Đọc thông tin kết nối từ file .env (an toàn cho GitHub)

Author: SmartJob Team
Date: 2026-10-28
"""

import sys
import psycopg2
from psycopg2 import OperationalError, DatabaseError
import os
from pathlib import Path

# Đảm bảo UTF-8 output trên Windows console
if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / '.env'
    env_vars = {}
    
    if not env_path.exists():
        print("⚠️  File .env không tồn tại!")
        print("\n💡 Hướng dẫn tạo file .env:")
        print("   1. Tạo file .env trong thư mục gốc dự án")
        print("   2. Thêm nội dung sau (thay đổi theo setup của bạn):")
        print("""
DB_NAME=smartjob_db
DB_USER=smartjob_user
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
        """)
        print("   3. Lưu file và chạy lại script này")
        print("\n⚠️  LƯU Ý: File .env không được commit vào git!")
        return None
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        print(f"❌ Lỗi đọc file .env: {e}")
        return None
    
    return env_vars

def test_connection():
    """Test basic database connection and schema status"""
    print("🔍 Đang kiểm tra kết nối database...")
    
    # Load environment variables
    env_vars = load_env()
    if not env_vars:
        return None
    
    # Check required variables
    required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
    missing_vars = [var for var in required_vars if var not in env_vars]
    
    if missing_vars:
        print(f"❌ Thiếu các biến trong file .env: {', '.join(missing_vars)}")
        return None
    
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=env_vars.get('DB_NAME'),
            user=env_vars.get('DB_USER'),
            password=env_vars.get('DB_PASSWORD'),
            host=env_vars.get('DB_HOST'),
            port=env_vars.get('DB_PORT')
        )
        print("✅ Kết nối database thành công!")
        print(f"\n📊 Thông tin kết nối:")
        print(f"   Database: {env_vars.get('DB_NAME')}")
        print(f"   User:     {env_vars.get('DB_USER')}")
        print(f"   Host:     {env_vars.get('DB_HOST')}:{env_vars.get('DB_PORT')}")
        
        with conn.cursor() as cur:
            # Lấy phiên bản PostgreSQL
            cur.execute("SELECT version();")
            db_version = cur.fetchone()[0]
            print(f"   Version:  {db_version.split(',')[0]}")
            
            # Kiểm tra các bảng đã tạo
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cur.fetchall()]
            
            print(f"\n📋 Kiểm tra Schema:")
            if tables:
                print(f"   ✅ Đã tìm thấy {len(tables)} bảng trong database:")
                for table in tables:
                    print(f"      - {table}")
                
                # Kiểm tra số lượng kỹ năng nếu bảng skills tồn tại
                lower_tables = [t.lower() for t in tables]
                if 'skills' in lower_tables:
                    cur.execute("SELECT COUNT(*) FROM Skills;")
                    skills_count = cur.fetchone()[0]
                    print(f"   ✅ Bảng Skills có {skills_count} kỹ năng mẫu.")
            else:
                print("   ⚠️  Chưa có bảng nào được tạo trong database 'smartjob_db'.")
                print("   💡 Hãy chạy script khởi tạo: docs/database-schema.sql")
                print("      Ví dụ: psql -U smartjob_user -d smartjob_db -f docs/database-schema.sql")
        
        return conn
    except OperationalError as e:
        print(f"❌ Lỗi kết nối: {e}")
        print("\n💡 Các bước khắc phục:")
        print("   1. Kiểm tra PostgreSQL service đã chạy chưa")
        print("   2. Kiểm tra thông tin trong file .env (username, password, port)")
        print("   3. Đảm bảo database đã được tạo (CREATE DATABASE smartjob_db;)")
        return None
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    test_connection()
