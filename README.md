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
├── run_ai_evaluation.py             # Script đánh giá chất lượng AI Matching
├── README.md                        # File này
├── backend/                         # Django REST API (Đã tích hợp AI Endpoints)
├── ai_matching/                     # Module AI Matching & Recommendation (✅ Hoàn thành)
│   ├── taxonomy.py                  # Chuẩn hóa kỹ năng và từ điển từ đồng nghĩa
│   ├── skill_extractor.py           # Bóc tách kỹ năng từ CV và JD
│   ├── text_similarity.py           # Vector hóa TF-IDF & Cosine Similarity
│   ├── matching_engine.py           # Thuật toán tính Matching Score đa tiêu chí
│   ├── ranking.py                   # Động cơ xếp hạng Top-K việc làm & ứng viên
│   ├── evaluator.py                 # Bộ đánh giá Precision@K, Recall@K, NDCG@K
│   ├── seed_ai_data.py              # Script nạp dữ liệu mẫu vào PostgreSQL
│   └── data/                        # Dataset mẫu CV, Job, Benchmark nhãn chuẩn
├── frontend/                        # Giao diện người dùng (Sắp triển khai)
└── bi_dashboard/                    # Dashboard BI (Sắp triển khai)
```

## ✅ Checklist 1: Thiết kế cơ sở dữ liệu (Hoàn thành)
- [x] Thiết kế 13 bảng CSDL, quan hệ, indexes, triggers (`docs/database-schema.sql`)
- [x] Báo cáo Checklist 1: `docs/CHECKLIST_1_REPORT.md`

## ✅ Checklist 2: AI/ML Matching & Recommendation (Hoàn thành)
- [x] **Xây dựng bộ dữ liệu mẫu về CV và tin tuyển dụng:** 15 hồ sơ ứng viên, 15 tin tuyển dụng mẫu đa ngành nghề và ma trận benchmark 225 cặp (`ai_matching/data/`).
- [x] **Trích xuất & Chuẩn hóa kỹ năng:** Bóc tách thực thể kỹ năng, cấp độ thành thạo, kinh nghiệm từ văn bản CV/JD với từ điển hơn 200 từ đồng nghĩa song ngữ Việt - Anh.
- [x] **Thuật toán Matching Score đa tiêu chí:** Kết hợp 5 trọng số: Kỹ năng (50%), Ngữ nghĩa TF-IDF & Cosine (20%), Kinh nghiệm (15%), Lương (10%), Học vấn (5%) kèm cơ chế diễn giải tự nhiên (Explainability).
- [x] **Xếp hạng gợi ý việc làm:** Xếp hạng Top-K việc làm phù hợp nhất cho ứng viên và Top-K ứng viên phù hợp nhất cho nhà tuyển dụng.
- [x] **Tích hợp hệ thống REST API:** Cung cấp đầy đủ các API cho frontend (`/api/ai/match/`, `/api/ai/extract-skills/`, `/api/ai/parse-cv/`, `/api/ai/recommend-jobs/`, `/api/ai/evaluation/`).
- [x] **Đánh giá sơ bộ chất lượng gợi ý:** Precision@1 = 100%, Recall@3 = 100%, NDCG@1 = 100%, NDCG@3 = 95.86%, MRR = 1.0, MAP = 0.9889.
- [x] **Báo cáo & Hướng dẫn sử dụng:** `docs/CHECKLIST_2_AI_REPORT.md` và `docs/AI_MATCHING_GUIDE.md`.

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
- 💾 [SQL Seed Data Script](docs/seed-data.sql) ⭐
- 🚀 [Hướng dẫn Setup Database](docs/SETUP_DATABASE.md) ⭐
- 📊 [Báo cáo Checklist 1: CSDL](docs/CHECKLIST_1_REPORT.md)
- 🧠 [Báo cáo Checklist 2: AI/ML Matching](docs/CHECKLIST_2_AI_REPORT.md) ⭐
- 📖 [Hướng dẫn cài đặt & API AI/ML](docs/AI_MATCHING_GUIDE.md) ⭐

## Công nghệ

- PostgreSQL 12+
- Python/Django (sắp triển khai)
- Apache Superset (sắp triển khai)

## License

Dự án học tập - Môn Hệ thống Kiến trúc Dữ liệu và Thông minh

