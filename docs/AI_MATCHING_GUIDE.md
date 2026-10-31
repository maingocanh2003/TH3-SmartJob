# 📖 HƯỚNG DẪN CÀI ĐẶT, VẬN HÀNH VÀ SỬ DỤNG MODULE AI/ML
## Dự án TH3-SmartJob – Checklist 02: AI/ML Matching & Recommendation

---

## 📌 1. Giới thiệu tổng quan

Module AI/ML (`ai_matching`) cung cấp các năng lực thông minh cốt lõi cho nền tảng SmartJob:
1. **Trích xuất thực thể và chuẩn hóa kỹ năng:** Bóc tách các kỹ năng, cấp bậc kinh nghiệm, học vấn và thông tin liên hệ từ văn bản CV hoặc mô tả công việc (JD), giải quyết hơn 200 từ đồng nghĩa (aliases) song ngữ Việt - Anh.
2. **Thuật toán Matching Score đa tiêu chí:** Đánh giá độ tương thích giữa ứng viên và việc làm kết hợp 5 khía cạnh: Kỹ năng (50%), Ngữ nghĩa văn bản TF-IDF & Cosine Similarity (20%), Kinh nghiệm (15%), Mức lương (10%), Học vấn (5%).
3. **Động cơ xếp hạng gợi ý (Ranking Engine):** Xếp hạng danh sách việc làm phù hợp cho ứng viên và danh sách ứng viên phù hợp cho nhà tuyển dụng kèm giải thích chi tiết (explainability).
4. **Hệ thống đánh giá mô hình:** Tích hợp bộ đo lường chất lượng Information Retrieval & Recommender Systems (Precision@K, Recall@K, NDCG@K, MRR, MAP) trên tập nhãn chuẩn.

---

## 🛠️ 2. Yêu cầu môi trường & Cài đặt

Module AI/ML được thiết kế tối ưu, sử dụng các thư viện Python chuẩn và tận dụng `numpy`, `django`, `djangorestframework` có sẵn trong môi trường của dự án.

### Các thư viện sử dụng:
- Python 3.10+
- Django >= 5.0
- djangorestframework >= 3.14
- psycopg2-binary >= 2.9
- numpy >= 1.24

---

## 💾 3. Khởi tạo và Nạp dữ liệu mẫu AI/ML

Để nạp bộ dữ liệu gồm 15 hồ sơ ứng viên mẫu, 15 tin tuyển dụng mẫu và 225 kết quả matching vào CSDL PostgreSQL:

```bash
# Đứng tại thư mục gốc dự án TH3-SmartJob:
python ai_matching/seed_ai_data.py
```

**Kết quả màn hình dự kiến:**
```
======================================================================
🌱 SEEDING AI SAMPLE DATASET INTO POSTGRESQL DATABASE
======================================================================
✅ Đã đồng bộ 68 kỹ năng vào bảng Skills (+23 mới).
✅ Đã nạp 15 tin tuyển dụng mẫu (Jobs) và yêu cầu kỹ năng (JobSkills).
✅ Đã nạp 15 hồ sơ ứng viên mẫu (Candidates), kỹ năng và học vấn.
🧠 Đang tính toán và lưu kết quả AI Matching vào database...
✅ Đã tính toán và lưu 225 cặp AI_Match_Results vào database!
✅ Đã cập nhật lại toàn bộ PostgreSQL sequences chính xác.
======================================================================
🎉 HOÀN TẤT SEED DỮ LIỆU MẪU AI/ML THÀNH CÔNG!
======================================================================
```

---

## 📊 4. Chạy Đánh giá Chất lượng Gợi ý (Benchmark Evaluation)

Chạy script đánh giá độc lập để tính toán các chỉ số Precision@K, Recall@K, NDCG@K, MRR và MAP:

```bash
python run_ai_evaluation.py
```

**Bảng kết quả đo lường thực tế:**
```
==============================================================================
🏆 KẾT QUẢ ĐÁNH GIÁ CHẤT LƯỢNG GỢI Ý (MACRO METRICS)
==============================================================================
Chỉ số (Metric)        | K = 1        | K = 3        | K = 5        | K = 10      
------------------------------------------------------------------------------
Precision@K            |     100.00% |      44.44% |      26.67% |      13.33%
Recall@K               |      83.33% |     100.00% |     100.00% |     100.00%
NDCG@K                 |     100.00% |      95.86% |      95.69% |      96.68%
------------------------------------------------------------------------------
Mean Reciprocal Rank (MRR)             : 1.0000 (100.0%)
Mean Average Precision (MAP)           : 0.9889 (98.89%)
==============================================================================
```

---

## 🧪 5. Kiểm thử Tự động (Automated Tests)

### 5.1. Chạy bài test chuyên biệt cho Module AI/ML:
```bash
python backend/test_ai_api.py
```
Kiểm thử 8 ca kiểm thử gồm trích xuất kỹ năng, phân tích CV, tính điểm trực tiếp theo ID, tính điểm theo raw text, gợi ý việc làm, gợi ý ứng viên, gợi ý không trạng thái (stateless) và API đánh giá chất lượng.

### 5.2. Chạy kiểm thử toàn bộ hệ thống Backend:
```bash
python backend/test_api.py
```

---

## 🌐 6. Hướng dẫn sử dụng API (API Documentation)

### 6.1. Trích xuất và chuẩn hóa kỹ năng từ văn bản
- **Endpoint:** `POST /api/ai/extract-skills/`
- **Request Body:**
```json
{
  "text": "Lập trình viên thành thạo Python, Django, k8s, ReactJS, Machine Learning và Docker."
}
```
- **Response (200 OK):**
```json
{
  "total_skills_found": 6,
  "skills": [
    {
      "skill_name": "Kubernetes",
      "category": "DevOps & Cloud",
      "proficiency_level": "intermediate",
      "matched_alias": "k8s",
      "frequency": 1
    },
    {
      "skill_name": "React",
      "category": "Frontend Development",
      "proficiency_level": "intermediate",
      "matched_alias": "reactjs",
      "frequency": 1
    },
    {
      "skill_name": "Python",
      "category": "Programming Language",
      "proficiency_level": "advanced",
      "matched_alias": "python",
      "frequency": 1
    }
  ]
}
```

---

### 6.2. Phân tích cú pháp CV tự do (Parse CV)
- **Endpoint:** `POST /api/ai/parse-cv/`
- **Request Body:**
```json
{
  "cv_text": "Họ và tên: Nguyễn Văn An\nEmail: an.nguyen@email.com\nSĐT: 0912345678\nVị trí: Senior Backend Developer\n5 năm kinh nghiệm làm việc với Python, Django, PostgreSQL, Docker."
}
```
- **Response (200 OK):**
```json
{
  "full_name": "Nguyễn Văn An",
  "email": "an.nguyen@email.com",
  "phone": "0912345678",
  "desired_position": "Senior Backend Developer",
  "years_of_experience": 5,
  "education_level": "Bachelor",
  "skills": [
    {"skill_name": "Python", "proficiency_level": "expert"},
    {"skill_name": "Django", "proficiency_level": "advanced"},
    {"skill_name": "PostgreSQL", "proficiency_level": "advanced"},
    {"skill_name": "Docker", "proficiency_level": "intermediate"}
  ]
}
```

---

### 6.3. Tính điểm Matching Score giữa Ứng viên & Việc làm
- **Endpoint:** `POST /api/ai/match/`
- **Cách 1: Truyền ID trong Database**
```json
{
  "candidate_id": 1,
  "job_id": 1
}
```
- **Cách 2: Truyền trực tiếp văn bản CV và JD (không cần lưu DB)**
```json
{
  "cv_text": "Senior Python Developer 5 năm kinh nghiệm với Django, Docker, PostgreSQL",
  "job_title": "Senior Python Engineer",
  "job_description": "Yêu cầu 4 năm kinh nghiệm Python, Django, PostgreSQL, Docker.",
  "years_of_experience_required": 4
}
```
- **Response (200 OK):**
```json
{
  "candidate_id": 1,
  "job_id": 1,
  "matching_score": 87.85,
  "overall_recommendation": "highly_recommended",
  "score_breakdown": {
    "skill_match": 100.0,
    "semantic_match": 39.23,
    "experience_match": 100.0,
    "salary_match": 100.0,
    "education_match": 100.0
  },
  "matched_skills": [
    {"skill_name": "Python", "candidate_level": "expert", "required_level": "expert", "match_ratio": 100.0},
    {"skill_name": "Django", "candidate_level": "advanced", "required_level": "advanced", "match_ratio": 100.0},
    {"skill_name": "PostgreSQL", "candidate_level": "advanced", "required_level": "advanced", "match_ratio": 100.0}
  ],
  "missing_skills": [],
  "bonus_skills": ["FastAPI", "AWS", "Git"],
  "explanation": "Hồ sơ ứng viên cực kỳ phù hợp với vị trí này (Điểm tổng hợp: 87.85%). Khớp 6 kỹ năng chính: Python, Django, PostgreSQL, Redis, Docker. Kinh nghiệm làm việc đạt chuẩn (5/4 năm)."
}
```

---

### 6.4. Lấy danh sách việc làm AI gợi ý cho ứng viên
- **Endpoint:** `GET /api/candidates/{candidate_id}/recommendations/?limit=5&min_score=50`
- **Response (200 OK):**
```json
[
  {
    "job_id": 1,
    "job_title": "Senior Python / Django Backend Developer",
    "company_name": "TechVanguard Solutions",
    "location": "Hà Nội",
    "salary_min": 35000000.0,
    "salary_max": 50000000.0,
    "matching_score": 87.85,
    "overall_recommendation": "highly_recommended",
    "matched_skills": [...],
    "explanation": "Hồ sơ ứng viên cực kỳ phù hợp với vị trí này..."
  }
]
```

---

### 6.5. Lấy danh sách ứng viên AI gợi ý cho tin tuyển dụng
- **Endpoint:** `GET /api/jobs/{job_id}/recommended_candidates/?limit=5`
- **Response (200 OK):**
```json
[
  {
    "candidate_id": 1,
    "full_name": "Nguyễn Văn An",
    "desired_position": "Senior Python Backend Developer",
    "years_of_experience": 5,
    "matching_score": 87.85,
    "overall_recommendation": "highly_recommended",
    "matched_skills": [...]
  }
]
```

---

### 6.6. Lấy báo cáo đánh giá chất lượng gợi ý (Precision, Recall, NDCG)
- **Endpoint:** `GET /api/ai/evaluation/`
- **Response (200 OK):**
```json
{
  "num_queries_evaluated": 15,
  "total_jobs_in_pool": 15,
  "metrics": {
    "precision@1": 1.0,
    "precision@3": 0.4444,
    "precision@5": 0.2667,
    "precision@10": 0.1333,
    "recall@1": 0.8333,
    "recall@3": 1.0,
    "recall@5": 1.0,
    "recall@10": 1.0,
    "ndcg@1": 1.0,
    "ndcg@3": 0.9586,
    "ndcg@5": 0.9569,
    "ndcg@10": 0.9668
  },
  "mrr": 1.0,
  "map": 0.9889
}
```

---

## 📌 7. Ví dụ gọi API bằng cURL

### Trích xuất kỹ năng:
```bash
curl -X POST http://localhost:8000/api/ai/extract-skills/ \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"Thành thạo Python, Django, k8s, ReactJS\"}"
```

### Tính điểm Matching Score:
```bash
curl -X POST http://localhost:8000/api/ai/match/ \
  -H "Content-Type: application/json" \
  -d "{\"candidate_id\": 1, \"job_id\": 1}"
```

### Gợi ý việc làm:
```bash
curl -X GET "http://localhost:8000/api/candidates/1/recommendations/?limit=5"
```

