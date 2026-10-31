# 🚀 HƯỚNG DẪN KHỞI TẠO DATABASE CHO TEAM

## 📌 Dành cho các thành viên trong nhóm

File này hướng dẫn chi tiết cách setup PostgreSQL database cho dự án SmartJob. Sau khi hoàn thành, bạn sẽ có database sẵn sàng để phát triển Backend, AI Matching, hoặc BI Dashboard.

## 🔐 LƯU Ý QUAN TRỌNG VỀ BẢO MẬT

**Mỗi thành viên có thể tự đặt thông tin kết nối riêng:**
- ✅ Tên database, username, password tùy ý
- ✅ File `.env` của bạn **KHÔNG** được commit vào git
- ✅ Mỗi người giữ file `.env` riêng trên máy local
- ✅ Không chia sẻ password trong tài liệu chung

**Ví dụ:**
- Thành viên A: `DB_PASSWORD=MatKhauCuaA123`
- Thành viên B: `DB_PASSWORD=MatKhauCuaB456`
- Thành viên C: `DB_USER=postgres`, `DB_NAME=my_smartjob`

---

## ✅ Bước 1: Cài đặt PostgreSQL

### Windows:

1. **Download PostgreSQL:**
   - Truy cập: https://www.postgresql.org/download/windows/
   - Download phiên bản 12 trở lên (khuyến nghị: PostgreSQL 14 hoặc 15)

2. **Cài đặt:**
   - Chạy file installer (.exe)
   - Chọn tất cả components (PostgreSQL Server, pgAdmin 4, Command Line Tools)
   - **GHI NHỚ PASSWORD** cho user `postgres` (sẽ dùng nhiều lần)
   - Port mặc định: `5432` (giữ nguyên)
   - Locale: `Default locale`
   - Hoàn thành cài đặt

3. **Kiểm tra:**
   ```bash
   # Mở Command Prompt/PowerShell
   psql --version
   # Kết quả mong đợi: psql (PostgreSQL) 14.x hoặc 15.x
   ```

### macOS:

```bash
# Sử dụng Homebrew
brew install postgresql@15

# Khởi động service
brew services start postgresql@15

# Kiểm tra
psql --version
```

### Linux (Ubuntu/Debian):

```bash
# Update và cài đặt
sudo apt update
sudo apt install postgresql postgresql-contrib

# Khởi động service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Kiểm tra
psql --version
```

---

## ✅ Bước 2: Khởi tạo Database

### 2.1. Kết nối vào PostgreSQL

**Windows:**
```bash
# Mở Command Prompt/PowerShell
psql -U postgres
# Nhập password đã tạo lúc cài đặt
```

**macOS/Linux:**
```bash
# Kết nối với user postgres
sudo -u postgres psql
```

### 2.2. Tạo Database và User

Copy và paste từng block SQL sau vào psql console:

```sql
-- Tạo database cho dự án
CREATE DATABASE smartjob_db;

-- Tạo user cho ứng dụng (thay password bằng password của bạn)
CREATE USER smartjob_user WITH PASSWORD 'your_password_here';

-- Cấp quyền cho user
GRANT ALL PRIVILEGES ON DATABASE smartjob_db TO smartjob_user;

-- Kết nối vào database vừa tạo
\c smartjob_db

-- Cấp quyền schema (quan trọng!)
GRANT ALL ON SCHEMA public TO smartjob_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO smartjob_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO smartjob_user;

-- Kiểm tra database đã tạo
\l smartjob_db
```

**✅ Kết quả:** Bạn sẽ thấy database `smartjob_db` trong danh sách.

### 2.3. Chạy SQL Schema

**Thoát khỏi psql:**
```sql
\q
```

**Chạy file schema từ terminal:**

```bash
# Di chuyển đến thư mục dự án
cd TH3-SmartJob  # (hoặc đường dẫn thư mục dự án trên máy bạn)

# Chạy schema (Windows)
psql -U smartjob_user -d smartjob_db -f docs/database-schema.sql
# Nhập password của bạn khi được yêu cầu

# Hoặc trên macOS/Linux
psql -U smartjob_user -d smartjob_db -h localhost -f docs/database-schema.sql
```

**⏱️ Thời gian:** ~5-10 giây

**✅ Kết quả mong đợi:**
```
CREATE TABLE
CREATE TABLE
...
CREATE INDEX
...
INSERT 0 74
```

---

## ✅ Bước 3: Kiểm tra Database

### 3.1. Kết nối lại vào database

```bash
psql -U smartjob_user -d smartjob_db
# Nhập password của bạn khi được yêu cầu
```

### 3.2. Kiểm tra các bảng

```sql
-- Liệt kê tất cả bảng
\dt

-- Kết quả mong đợi: 13 bảng
--  public | applications      | table | smartjob_user
--  public | ai_match_results  | table | smartjob_user
--  public | candidates        | table | smartjob_user
--  ...
```

### 3.3. Kiểm tra dữ liệu mẫu

```sql
-- Kiểm tra số lượng kỹ năng
SELECT COUNT(*) FROM Skills;
-- Kết quả: 74

-- Xem 10 kỹ năng đầu tiên
SELECT skill_id, skill_name, category FROM Skills LIMIT 10;

-- Xem cấu trúc bảng Candidates
\d Candidates
```

### 3.4. Test một vài queries

```sql
-- Query 1: Lấy kỹ năng theo category
SELECT category, COUNT(*) as count 
FROM Skills 
GROUP BY category 
ORDER BY count DESC;

-- Query 2: Kiểm tra indexes
SELECT tablename, indexname FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename;

-- Kết quả: Sẽ thấy 40+ indexes
```

**✅ Nếu tất cả đều OK, database của bạn đã sẵn sàng!**

---

## 🔧 Bước 4: Cấu hình cho Development

### 4.1. Lưu thông tin kết nối

Tạo file `.env` trong root folder (KHÔNG commit vào git):

```bash
# .env - Thay đổi thông tin theo setup của bạn
DB_NAME=smartjob_db
DB_USER=smartjob_user
DB_PASSWORD=your_password_here     # ⚠️ Thay bằng password của bạn
DB_HOST=localhost
DB_PORT=5432
```

**Lưu ý:**
- ✅ Mỗi thành viên có thể dùng username/password khác nhau
- ✅ File `.env` đã có trong `.gitignore` - không lo bị commit nhầm
- ✅ KHÔNG chia sẻ password trong chat/email

### 4.2. Test kết nối từ Python

Tạo file test: `test_db_connection.py`

```python
import psycopg2

# Test connection
conn = psycopg2.connect(
    dbname="smartjob_db",
    user="smartjob_user",
    password="your_password_here",  # Thay bằng password của bạn
    host="localhost",
    port="5432"
)

print("✅ Kết nối thành công!")

# Test query
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM Skills;")
count = cur.fetchone()[0]
print(f"✅ Database có {count} kỹ năng")

# Kiểm tra các bảng
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")
tables = [row[0] for row in cur.fetchall()]
print(f"✅ Database có {len(tables)} bảng:")
for table in tables:
    print(f"   - {table}")

cur.close()
conn.close()
print("\n🎉 Database sẵn sàng cho development!")
```

Chạy test:
```bash
python test_db_connection.py
```

---

## 📊 Thông tin Database cho Team

### Connection Info (Mẫu):
```
Host: localhost
Port: 5432
Database: smartjob_db
Username: smartjob_user
Password: (xem trong file .env của bạn)
```

**Lưu ý:** Mỗi thành viên tự cấu hình trong file `.env` riêng của mình.

### Database Structure:

**13 Bảng chính:**
1. `Users` - Tài khoản người dùng
2. `Candidates` - Hồ sơ ứng viên
3. `Companies` - Thông tin công ty
4. `Skills` - 74 kỹ năng chuẩn (đã có data)
5. `Candidate_Skills` - Kỹ năng của ứng viên
6. `Education` - Học vấn
7. `Experience` - Kinh nghiệm
8. `Jobs` - Tin tuyển dụng
9. `Job_Skills` - Kỹ năng yêu cầu
10. `Applications` - Đơn ứng tuyển
11. `AI_Match_Results` - Kết quả AI matching
12. `Job_Views` - Lượt xem (cho BI)
13. `Saved_Jobs` - Công việc đã lưu

### Dữ liệu có sẵn:
- ✅ 74 kỹ năng trong bảng `Skills` (Python, Java, React, Django, ML, etc.)
- ⚠️ Các bảng khác chưa có data (cần insert để test)

---

## 🔍 Insert Test Data

### 1. Tạo ứng viên test

```sql
-- Insert user
INSERT INTO Users (email, password_hash, user_type) 
VALUES ('candidate@test.com', 'hashed_password', 'candidate')
RETURNING user_id;

-- Insert candidate (thay 1 bằng user_id từ query trên)
INSERT INTO Candidates (user_id, full_name, phone, desired_position, years_of_experience)
VALUES (1, 'Nguyen Van A', '0901234567', 'Backend Developer', 3);

-- Thêm kỹ năng cho ứng viên
INSERT INTO Candidate_Skills (candidate_id, skill_id, proficiency_level, years_of_experience)
SELECT 1, skill_id, 'advanced', 3
FROM Skills WHERE skill_name IN ('Python', 'Django', 'PostgreSQL');
```

### 2. Tạo công ty và job test

```sql
-- Insert company user
INSERT INTO Users (email, password_hash, user_type) 
VALUES ('hr@company.com', 'hashed_password', 'company')
RETURNING user_id;

-- Insert company
INSERT INTO Companies (user_id, company_name, industry, company_size)
VALUES (2, 'Tech Company ABC', 'IT', '100-500');

-- Insert job
INSERT INTO Jobs (company_id, job_title, job_description, salary_min, salary_max, location, status)
VALUES (1, 'Backend Developer', 'Develop web applications', 15000000, 25000000, 'Ha Noi', 'active')
RETURNING job_id;

-- Thêm kỹ năng yêu cầu
INSERT INTO Job_Skills (job_id, skill_id, required_level, is_required)
SELECT 1, skill_id, 'intermediate', true
FROM Skills WHERE skill_name IN ('Python', 'Django', 'REST API');
```

---

## 🛠️ Troubleshooting

### ❌ Lỗi: "psql: command not found"

**Windows:** Thêm PostgreSQL vào PATH:
- Control Panel → System → Advanced → Environment Variables
- Thêm `C:\Program Files\PostgreSQL\15\bin` vào PATH

**macOS/Linux:**
```bash
export PATH="/usr/local/opt/postgresql@15/bin:$PATH"
```

### ❌ Lỗi: "password authentication failed"

Kiểm tra file `pg_hba.conf` và đảm bảo có dòng:
```
local   all   all   md5
```

### ❌ Lỗi: "permission denied for schema public"

```sql
\c smartjob_db postgres
GRANT ALL ON SCHEMA public TO smartjob_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO smartjob_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO smartjob_user;
```

### ❌ Lỗi: "could not connect to server"

Kiểm tra PostgreSQL đang chạy:
```bash
# Windows
pg_ctl status

# macOS
brew services list | grep postgresql

# Linux
sudo systemctl status postgresql
```

---

## 🔄 Reset Database (Nếu cần)

```sql
-- Kết nối với postgres
psql -U postgres

-- Ngắt connections
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE datname = 'smartjob_db' AND pid <> pg_backend_pid();

-- Xóa và tạo lại
DROP DATABASE IF EXISTS smartjob_db;
CREATE DATABASE smartjob_db;
GRANT ALL PRIVILEGES ON DATABASE smartjob_db TO smartjob_user;

-- Chạy lại schema
\q
psql -U smartjob_user -d smartjob_db -f docs/database-schema.sql
```

---

## 🎯 Checklist Setup

- [ ] PostgreSQL đã cài đặt và chạy
- [ ] Database `smartjob_db` đã tạo
- [ ] User `smartjob_user` đã tạo với đúng quyền
- [ ] File `database-schema.sql` đã chạy thành công
- [ ] 13 bảng đã được tạo (kiểm tra bằng `\dt`)
- [ ] 74 kỹ năng đã có trong bảng Skills
- [ ] Test connection từ Python thành công
- [ ] File `.env` đã tạo (không commit!)

**✅ Nếu tất cả đã check, bạn sẵn sàng develop!**

---

## 📚 Tài liệu liên quan

- `docs/database-design.md` - Thiết kế chi tiết
- `docs/database-schema.sql` - SQL script
- `docs/CHECKLIST_1_REPORT.md` - Báo cáo Checklist 1

**Good luck! 🚀**
