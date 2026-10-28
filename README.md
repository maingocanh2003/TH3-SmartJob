# TH3-SmartJob: Hệ thống Tìm việc Thông minh tích hợp AI và BI

## Giới thiệu

SmartJob là nền tảng tìm việc thông minh sử dụng AI để kết nối ứng viên với nhà tuyển dụng. Hệ thống tính toán điểm phù hợp (Matching Score) giữa kỹ năng ứng viên và yêu cầu công việc, đồng thời cung cấp dashboard BI để phân tích thị trường lao động.

## Cấu trúc dự án

```
TH3-SmartJob/
├── docs/
│   ├── requirements.md              # Yêu cầu nghiệp vụ chi tiết
│   ├── architecture.md              # Kiến trúc hệ thống
│   ├── database-design.md           # Thiết kế CSDL chi tiết (✅ Hoàn thành)
│   ├── database-schema.sql          # SQL script khởi tạo DB (✅ Hoàn thành)
│   ├── SETUP_DATABASE.md            # Hướng dẫn setup cho team (✅ Hoàn thành)
│   └── CHECKLIST_1_REPORT.md        # Báo cáo hoàn thành (✅ Hoàn thành)
├── .env                             # Config database (không commit)
├── .gitignore                       # Git ignore rules
├── test_db_connection.py            # Script test database
├── README.md                        # File này
├── backend/                         # Django REST API (Sắp triển khai)
├── frontend/                        # Giao diện người dùng (Sắp triển khai)
├── ai_matching/                     # Module AI Matching (Sắp triển khai)
└── bi_dashboard/                    # Dashboard BI (Sắp triển khai)
```

## ✅ Checklist 1: Thiết kế cơ sở dữ liệu (Hoàn thành)

### Những gì đã hoàn thành:

- [x] **Phân tích yêu cầu hệ thống** - `docs/requirements.md`
- [x] **Thiết kế kiến trúc** - `docs/architecture.md`
- [x] **Thiết kế CSDL chi tiết** - `docs/database-design.md`
  - 13 bảng với quan hệ đầy đủ
  - Sơ đồ ERD
  - 40+ indexes
  - 6 triggers/functions
  - 74 kỹ năng mẫu
- [x] **SQL Schema** - `docs/database-schema.sql`
- [x] **Hướng dẫn Setup** - `docs/SETUP_DATABASE.md`

## Thiết kế Database

### 13 bảng chính:

1. **Users** - Tài khoản (candidate/company/admin)
2. **Candidates** - Hồ sơ ứng viên
3. **Companies** - Thông tin công ty
4. **Skills** - 74 kỹ năng chuẩn hóa
5. **Candidate_Skills** - Kỹ năng của ứng viên
6. **Education** - Học vấn
7. **Experience** - Kinh nghiệm
8. **Jobs** - Tin tuyển dụng
9. **Job_Skills** - Kỹ năng yêu cầu
10. **Applications** - Đơn ứng tuyển
11. **AI_Match_Results** - Kết quả matching
12. **Job_Views** - Tracking (BI)
13. **Saved_Jobs** - Công việc đã lưu

## Cài đặt nhanh

### 1. Tạo database
```bash
psql -U postgres
```
```sql
CREATE DATABASE smartjob_db;
CREATE USER smartjob_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE smartjob_db TO smartjob_user;
```

### 2. Chạy schema
```bash
psql -U smartjob_user -d smartjob_db -f docs/database-schema.sql
```

### 3. Kiểm tra
```sql
SELECT COUNT(*) FROM Skills;  -- 74 skills
```

**Hoặc chạy script Python để test tự động:**
```bash
python test_db_connection.py
```

## Tài liệu

- 📄 [Yêu cầu nghiệp vụ](docs/requirements.md)
- 🏗️ [Kiến trúc hệ thống](docs/architecture.md)
- 🗄️ [Thiết kế Database (Chi tiết)](docs/database-design.md) ⭐
- 📜 [SQL Schema Script](docs/database-schema.sql) ⭐
- 🚀 [Hướng dẫn Setup Database](docs/SETUP_DATABASE.md) ⭐
- 📊 [Báo cáo Checklist 1](docs/CHECKLIST_1_REPORT.md)

## Công nghệ

- PostgreSQL 12+
- Python/Django (sắp triển khai)
- Apache Superset (sắp triển khai)

## License

Dự án học tập - Môn Hệ thống Kiến trúc Dữ liệu và Thông minh

