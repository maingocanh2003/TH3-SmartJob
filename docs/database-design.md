# THIẾT KẾ CƠ SỞ DỮ LIỆU - SMARTJOB

## 1. Tổng quan

Hệ thống SmartJob sử dụng PostgreSQL để lưu trữ dữ liệu. Thiết kế database tập trung vào:
- Quản lý người dùng (ứng viên và nhà tuyển dụng)
- Quản lý hồ sơ và kỹ năng
- Quản lý tin tuyển dụng và đơn ứng tuyển
- Lưu trữ kết quả AI Matching
- Hỗ trợ phân tích BI

## 2. Sơ đồ ERD (Entity Relationship Diagram)

```
┌─────────────┐         ┌──────────────┐
│   Users     │────────<│  Candidates  │
└─────────────┘         └──────────────┘
      │                        │
      │                        │
      │                        ├───────<┌─────────────────┐
      │                        │        │  Education      │
      │                        │        └─────────────────┘
      │                        │
      │                        ├───────<┌─────────────────┐
      │                        │        │  Experience     │
      │                        │        └─────────────────┘
      │                        │
      │                        ├───────<┌─────────────────┐
      │                        │        │ Candidate_Skills│
      │                        │        └─────────────────┘
      │                        │                 │
      │                        │                 │
      │                        │        ┌────────┴────────┐
      │                        │        │     Skills      │
      │                        │        └────────┬────────┘
      │                        │                 │
      │                        │        ┌────────┴────────┐
      │                        │        │  Job_Skills     │
      │                        │        └────────┬────────┘
      │                        │                 │
      │                        │        ┌────────┴────────┐
      │                        │        │    Jobs         │
      │                        │        └────────┬────────┘
      │                        │                 │
      │                        │                 │
      │                        └────────>┌───────┴─────────┐
      │                                  │  Applications   │
      │                                  └─────────────────┘
      │                                           │
      │                                           │
      │                                  ┌────────┴────────┐
      │                                  │ AI_Match_Results│
      │                                  └─────────────────┘
      │
      │                 ┌──────────────┐
      └────────────────<│  Companies   │
                        └──────────────┘
                               │
                               │
                      ┌────────┴────────┐
                      │    Jobs         │
                      └─────────────────┘
```

## 3. Chi tiết các bảng

### 3.1. Bảng Users (Người dùng)
Lưu thông tin đăng nhập và phân quyền cho tất cả người dùng.

| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---------|--------------|-----------|-------|
| user_id | SERIAL | PRIMARY KEY | ID người dùng |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email đăng nhập |
| password_hash | VARCHAR(255) | NOT NULL | Mật khẩu đã mã hóa |
| user_type | VARCHAR(20) | NOT NULL | Loại người dùng (candidate/company/admin) |
| is_active | BOOLEAN | DEFAULT TRUE | Trạng thái hoạt động |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian cập nhật |

**Ràng buộc:**
- CHECK (user_type IN ('candidate', 'company', 'admin'))

### 3.2. Bảng Candidates (Ứng viên)
Lưu hồ sơ chi tiết của ứng viên.

| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---------|--------------|-----------|-------|
| candidate_id | SERIAL | PRIMARY KEY | ID ứng viên |
| user_id | INTEGER | FOREIGN KEY → Users(user_id), UNIQUE | ID người dùng |
| full_name | VARCHAR(255) | NOT NULL | Họ tên đầy đủ |
| phone | VARCHAR(20) | | Số điện thoại |
| address | TEXT | | Địa chỉ |
| date_of_birth | DATE | | Ngày sinh |
| gender | VARCHAR(10) | | Giới tính |
| avatar_url | TEXT | | URL ảnh đại diện |
| summary | TEXT | | Giới thiệu bản thân |
| desired_position | VARCHAR(255) | | Vị trí mong muốn |
| desired_salary | DECIMAL(10,2) | | Mức lương mong muốn |
| years_of_experience | INTEGER | | Số năm kinh nghiệm |
| cv_file_url | TEXT | | URL file CV |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian cập nhật |

### 3.3. Bảng Companies (Công ty/Nhà tuyển dụng)
Lưu thông tin công ty và nhà tuyển dụng.

| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---------|--------------|-----------|-------|
| company_id | SERIAL | PRIMARY KEY | ID công ty |
| user_id | INTEGER | FOREIGN KEY → Users(user_id), UNIQUE | ID người dùng |
| company_name | VARCHAR(255) | NOT NULL | Tên công ty |
| tax_code | VARCHAR(50) | UNIQUE | Mã số thuế |
| industry | VARCHAR(100) | | Ngành nghề |
| company_size | VARCHAR(50) | | Quy mô công ty |
| address | TEXT | | Địa chỉ công ty |
| phone | VARCHAR(20) | | Số điện thoại |
| website | VARCHAR(255) | | Website công ty |
| logo_url | TEXT | | URL logo công ty |
| description | TEXT | | Giới thiệu công ty |
| contact_person | VARCHAR(255) | | Người liên hệ |
| contact_email | VARCHAR(255) | | Email liên hệ |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian cập nhật |

### 3.4. Bảng Skills (Kỹ năng)
Danh mục các kỹ năng chuẩn hóa.

| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---------|--------------|-----------|-------|
| skill_id | SERIAL | PRIMARY KEY | ID kỹ năng |
| skill_name | VARCHAR(255) | UNIQUE, NOT NULL | Tên kỹ năng |
| category | VARCHAR(100) | | Danh mục kỹ năng |
| description | TEXT | | Mô tả kỹ năng |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo |

**Ghi chú:** Bảng này chứa danh sách kỹ năng đã được chuẩn hóa để dễ dàng matching.

### 3.5. Bảng Candidate_Skills (Kỹ năng của ứng viên)
Liên kết ứng viên với kỹ năng của họ.

| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---------|--------------|-----------|-------|
| candidate_skill_id | SERIAL | PRIMARY KEY | ID |
| candidate_id | INTEGER | FOREIGN KEY → Candidates(candidate_id) | ID ứng viên |
| skill_id | INTEGER | FOREIGN KEY → Skills(skill_id) | ID kỹ năng |
| proficiency_level | VARCHAR(50) | | Mức độ thành thạo |
| years_of_experience | INTEGER | | Số năm kinh nghiệm với kỹ năng |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo |

**Ràng buộc:**
- UNIQUE (candidate_id, skill_id)
- CHECK (proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert'))

### 3.6. Bảng Education (Học vấn)
Lưu thông tin học vấn của ứng viên.

| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---------|--------------|-----------|-------|
| education_id | SERIAL | PRIMARY KEY | ID học vấn |
| candidate_id | INTEGER | FOREIGN KEY → Candidates(candidate_id) | ID ứng viên |
| institution_name | VARCHAR(255) | NOT NULL | Tên trường |
| degree | VARCHAR(100) | | Bằng cấp |
| major | VARCHAR(255) | | Chuyên ngành |
| start_date | DATE | | Ngày bắt đầu |
| end_date | DATE | | Ngày kết thúc |
| gpa | DECIMAL(3,2) | | Điểm trung bình |
| description | TEXT | | Mô tả thêm |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo |

### 3.7. Bảng Experience (Kinh nghiệm làm việc)
Lưu kinh nghiệm làm việc của ứng viên.

| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---------|--------------|-----------|-------|
| experience_id | SERIAL | PRIMARY KEY | ID kinh nghiệm |
| candidate_id | INTEGER | FOREIGN KEY → Candidates(candidate_id) | ID ứng viên |
| company_name | VARCHAR(255) | NOT NULL | Tên công ty |
| position | VARCHAR(255) | NOT NULL | Vị trí công việc |
| start_date | DATE | NOT NULL | Ngày bắt đầu |
| end_date | DATE | | Ngày kết thúc (NULL nếu đang làm) |
| is_current | BOOLEAN | DEFAULT FALSE | Đang làm việc |
| responsibilities | TEXT | | Mô tả công việc |
| achievements | TEXT | | Thành tích |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo |

### 3.8. Bảng Jobs (Tin tuyển dụng)
Lưu thông tin các tin tuyển dụng.

| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---------|--------------|-----------|-------|
| job_id | SERIAL | PRIMARY KEY | ID tin tuyển dụng |
| company_id | INTEGER | FOREIGN KEY → Companies(company_id) | ID công ty |
| job_title | VARCHAR(255) | NOT NULL | Tiêu đề công việc |
| job_description | TEXT | NOT NULL | Mô tả công việc |
| requirements | TEXT | | Yêu cầu công việc |
| benefits | TEXT | | Quyền lợi |
| position_level | VARCHAR(50) | | Cấp bậc |
| employment_type | VARCHAR(50) | | Loại hợp đồng |
| num_of_positions | INTEGER | DEFAULT 1 | Số lượng tuyển |
| salary_min | DECIMAL(10,2) | | Mức lương tối thiểu |
| salary_max | DECIMAL(10,2) | | Mức lương tối đa |
| salary_currency | VARCHAR(10) | DEFAULT 'VND' | Đơn vị tiền tệ |
| location | VARCHAR(255) | | Địa điểm làm việc |
| years_of_experience_required | INTEGER | | Số năm kinh nghiệm yêu cầu |
| application_deadline | DATE | | Hạn nộp hồ sơ |
| status | VARCHAR(20) | DEFAULT 'active' | Trạng thái tin |
| view_count | INTEGER | DEFAULT 0 | Số lượt xem |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian cập nhật |

**Ràng buộc:**
- CHECK (status IN ('active', 'closed', 'draft'))
- CHECK (employment_type IN ('full-time', 'part-time', 'contract', 'internship'))

### 3.9. Bảng Job_Skills (Kỹ năng yêu cầu cho công việc)
Liên kết tin tuyển dụng với các kỹ năng yêu cầu.

| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---------|--------------|-----------|-------|
| job_skill_id | SERIAL | PRIMARY KEY | ID |
| job_id | INTEGER | FOREIGN KEY → Jobs(job_id) | ID tin tuyển dụng |
| skill_id | INTEGER | FOREIGN KEY → Skills(skill_id) | ID kỹ năng |
| required_level | VARCHAR(50) | | Mức độ yêu cầu |
| is_required | BOOLEAN | DEFAULT TRUE | Kỹ năng bắt buộc |
| weight | DECIMAL(3,2) | DEFAULT 1.0 | Trọng số kỹ năng (để tính matching) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo |

**Ràng buộc:**
- UNIQUE (job_id, skill_id)
- CHECK (required_level IN ('beginner', 'intermediate', 'advanced', 'expert'))

### 3.10. Bảng Applications (Đơn ứng tuyển)
Lưu thông tin đơn ứng tuyển của ứng viên.

| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---------|--------------|-----------|-------|
| application_id | SERIAL | PRIMARY KEY | ID đơn ứng tuyển |
| job_id | INTEGER | FOREIGN KEY → Jobs(job_id) | ID tin tuyển dụng |
| candidate_id | INTEGER | FOREIGN KEY → Candidates(candidate_id) | ID ứng viên |
| cover_letter | TEXT | | Thư xin việc |
| status | VARCHAR(20) | DEFAULT 'pending' | Trạng thái đơn |
| applied_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian nộp |
| reviewed_at | TIMESTAMP | | Thời gian xem xét |
| notes | TEXT | | Ghi chú của nhà tuyển dụng |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian cập nhật |

**Ràng buộc:**
- UNIQUE (job_id, candidate_id) - Mỗi ứng viên chỉ ứng tuyển 1 lần/công việc
- CHECK (status IN ('pending', 'reviewing', 'shortlisted', 'interviewed', 'offered', 'rejected', 'withdrawn'))

### 3.11. Bảng AI_Match_Results (Kết quả AI Matching)
Lưu kết quả phân tích matching giữa ứng viên và công việc.

| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---------|--------------|-----------|-------|
| match_id | SERIAL | PRIMARY KEY | ID matching |
| candidate_id | INTEGER | FOREIGN KEY → Candidates(candidate_id) | ID ứng viên |
| job_id | INTEGER | FOREIGN KEY → Jobs(job_id) | ID công việc |
| matching_score | DECIMAL(5,2) | NOT NULL | Điểm matching (0-100) |
| matched_skills | JSONB | | Danh sách kỹ năng phù hợp |
| missing_skills | JSONB | | Danh sách kỹ năng còn thiếu |
| skill_match_details | JSONB | | Chi tiết so sánh từng kỹ năng |
| experience_match | DECIMAL(5,2) | | Điểm phù hợp về kinh nghiệm |
| education_match | DECIMAL(5,2) | | Điểm phù hợp về học vấn |
| salary_match | DECIMAL(5,2) | | Điểm phù hợp về lương |
| overall_recommendation | VARCHAR(50) | | Đề xuất tổng thể |
| calculated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tính toán |

**Ràng buộc:**
- CHECK (matching_score >= 0 AND matching_score <= 100)
- CHECK (overall_recommendation IN ('highly_recommended', 'recommended', 'potential', 'not_recommended'))

**Ghi chú:** Sử dụng JSONB để lưu trữ dữ liệu phức tạp và linh hoạt cho kết quả AI.

### 3.12. Bảng Job_Views (Lượt xem tin tuyển dụng)
Theo dõi lượt xem tin tuyển dụng để phân tích BI.

| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---------|--------------|-----------|-------|
| view_id | SERIAL | PRIMARY KEY | ID lượt xem |
| job_id | INTEGER | FOREIGN KEY → Jobs(job_id) | ID tin tuyển dụng |
| candidate_id | INTEGER | FOREIGN KEY → Candidates(candidate_id), NULL | ID ứng viên (nếu đã login) |
| ip_address | VARCHAR(50) | | Địa chỉ IP |
| user_agent | TEXT | | Thông tin trình duyệt |
| viewed_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian xem |

### 3.13. Bảng Saved_Jobs (Công việc đã lưu)
Lưu danh sách công việc mà ứng viên quan tâm.

| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---------|--------------|-----------|-------|
| saved_job_id | SERIAL | PRIMARY KEY | ID |
| candidate_id | INTEGER | FOREIGN KEY → Candidates(candidate_id) | ID ứng viên |
| job_id | INTEGER | FOREIGN KEY → Jobs(job_id) | ID công việc |
| saved_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian lưu |
| notes | TEXT | | Ghi chú cá nhân |

**Ràng buộc:**
- UNIQUE (candidate_id, job_id)

## 4. Indexes (Chỉ mục)

Để tối ưu hiệu suất truy vấn, các index sau nên được tạo:

```sql
-- Users
CREATE INDEX idx_users_email ON Users(email);
CREATE INDEX idx_users_type ON Users(user_type);

-- Candidates
CREATE INDEX idx_candidates_user_id ON Candidates(user_id);
CREATE INDEX idx_candidates_desired_position ON Candidates(desired_position);

-- Companies
CREATE INDEX idx_companies_user_id ON Companies(user_id);
CREATE INDEX idx_companies_industry ON Companies(industry);

-- Jobs
CREATE INDEX idx_jobs_company_id ON Jobs(company_id);
CREATE INDEX idx_jobs_status ON Jobs(status);
CREATE INDEX idx_jobs_location ON Jobs(location);
CREATE INDEX idx_jobs_deadline ON Jobs(application_deadline);
CREATE INDEX idx_jobs_created_at ON Jobs(created_at DESC);

-- Applications
CREATE INDEX idx_applications_job_id ON Applications(job_id);
CREATE INDEX idx_applications_candidate_id ON Applications(candidate_id);
CREATE INDEX idx_applications_status ON Applications(status);
CREATE INDEX idx_applications_applied_at ON Applications(applied_at DESC);

-- Skills
CREATE INDEX idx_skills_name ON Skills(skill_name);
CREATE INDEX idx_skills_category ON Skills(category);

-- AI Match Results
CREATE INDEX idx_match_candidate_id ON AI_Match_Results(candidate_id);
CREATE INDEX idx_match_job_id ON AI_Match_Results(job_id);
CREATE INDEX idx_match_score ON AI_Match_Results(matching_score DESC);
CREATE INDEX idx_match_calculated_at ON AI_Match_Results(calculated_at DESC);

-- Job Views (for BI)
CREATE INDEX idx_job_views_job_id ON Job_Views(job_id);
CREATE INDEX idx_job_views_date ON Job_Views(viewed_at);
```

## 5. Quan hệ giữa các bảng

### Quan hệ chính:
1. **Users** → **Candidates** (1:1) - Một user là một ứng viên
2. **Users** → **Companies** (1:1) - Một user là một công ty
3. **Candidates** → **Candidate_Skills** (1:N) - Một ứng viên có nhiều kỹ năng
4. **Candidates** → **Education** (1:N) - Một ứng viên có nhiều bằng cấp
5. **Candidates** → **Experience** (1:N) - Một ứng viên có nhiều kinh nghiệm
6. **Companies** → **Jobs** (1:N) - Một công ty có nhiều tin tuyển dụng
7. **Jobs** → **Job_Skills** (1:N) - Một công việc yêu cầu nhiều kỹ năng
8. **Jobs** → **Applications** (1:N) - Một công việc có nhiều đơn ứng tuyển
9. **Candidates** → **Applications** (1:N) - Một ứng viên có nhiều đơn ứng tuyển
10. **Skills** → **Candidate_Skills** (1:N) - Một kỹ năng được nhiều ứng viên sở hữu
11. **Skills** → **Job_Skills** (1:N) - Một kỹ năng được nhiều công việc yêu cầu
12. **Candidates** × **Jobs** → **AI_Match_Results** (N:M) - Matching giữa ứng viên và công việc

## 6. Chiến lược dữ liệu cho AI và BI

### 6.1. Dữ liệu cho AI Matching
- Bảng **Skills** chứa danh sách kỹ năng chuẩn hóa
- Bảng **Candidate_Skills** và **Job_Skills** lưu mức độ kỹ năng để so sánh
- Bảng **AI_Match_Results** lưu kết quả để tránh tính toán lại và hỗ trợ phân tích
- Sử dụng JSONB để lưu chi tiết phức tạp, dễ mở rộng

### 6.2. Dữ liệu cho BI Dashboard
- Bảng **Job_Views** theo dõi hành vi người dùng
- Bảng **Applications** với trường `status` để phân tích conversion funnel
- Bảng **Jobs** với các trường về lương, vị trí, ngành nghề để phân tích xu hướng
- Timestamp fields trên tất cả bảng để phân tích theo thời gian

## 7. Trigger và Stored Procedure (Khuyến nghị)

### 7.1. Auto-update timestamp
```sql
-- Tự động cập nhật updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Áp dụng cho các bảng cần thiết
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON Users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_candidates_updated_at BEFORE UPDATE ON Candidates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON Companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON Jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_applications_updated_at BEFORE UPDATE ON Applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 7.2. Auto-increment view count
```sql
-- Tự động tăng view_count khi có lượt xem mới
CREATE OR REPLACE FUNCTION increment_job_view_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Jobs SET view_count = view_count + 1 WHERE job_id = NEW.job_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_job_view_count AFTER INSERT ON Job_Views
    FOR EACH ROW EXECUTE FUNCTION increment_job_view_count();
```

## 8. Dữ liệu mẫu (Sample Data)

### 8.1. Kỹ năng mẫu (Skills)
```sql
INSERT INTO Skills (skill_name, category) VALUES
('Python', 'Programming Language'),
('Java', 'Programming Language'),
('JavaScript', 'Programming Language'),
('React', 'Frontend Framework'),
('Django', 'Backend Framework'),
('PostgreSQL', 'Database'),
('MySQL', 'Database'),
('MongoDB', 'Database'),
('Machine Learning', 'AI/ML'),
('Data Analysis', 'Data Science'),
('Communication', 'Soft Skills'),
('Teamwork', 'Soft Skills'),
('Problem Solving', 'Soft Skills'),
('Project Management', 'Management'),
('Agile/Scrum', 'Methodology');
```

## 9. Backup và Migration Strategy

### 9.1. Backup
- Daily automated backup của toàn bộ database
- Export định kỳ các bảng quan trọng (Users, Candidates, Companies, Jobs)
- Lưu trữ backup ít nhất 30 ngày

### 9.2. Migration
- Sử dụng migration tool (Django migrations, Alembic, etc.)
- Version control cho database schema
- Testing migration trên môi trường development trước khi deploy production

## 10. Security Considerations

1. **Password**: Luôn hash password, không lưu plain text
2. **Personal Data**: Mã hóa các thông tin nhạy cảm (số điện thoại, địa chỉ)
3. **SQL Injection**: Sử dụng parameterized queries, ORM
4. **Access Control**: Implement row-level security nếu cần
5. **Audit Log**: Cân nhắc thêm bảng audit log để theo dõi các thay đổi quan trọng

## 11. Performance Optimization

1. **Partitioning**: Cân nhắc partition bảng lớn như Job_Views theo thời gian
2. **Archiving**: Archive dữ liệu cũ (jobs closed > 6 months) vào bảng riêng
3. **Caching**: Cache các truy vấn phổ biến (danh sách skills, job listings)
4. **Connection Pooling**: Sử dụng connection pool để tối ưu database connections

## 12. Mở rộng trong tương lai

1. **Notifications**: Thêm bảng Notifications để gửi thông báo cho user
2. **Messages**: Thêm hệ thống nhắn tin giữa ứng viên và nhà tuyển dụng
3. **Reviews**: Cho phép ứng viên đánh giá công ty và ngược lại
4. **Certifications**: Bảng riêng cho chứng chỉ của ứng viên
5. **Job Categories**: Bảng danh mục công việc để phân loại tốt hơn
6. **Locations**: Bảng địa điểm chuẩn hóa (city, district, country)
