"""
Dedicated Test Suite for SmartJob AI/ML Module (Checklist 02)
Tests all AI endpoints:
- Skill Extraction & Normalization
- CV Parsing
- Direct Matching (IDs and Raw Text)
- Candidate Job Recommendations & Ranking
- Job Candidate Recommendations & Ranking
- Recommendation Evaluation Benchmark (Precision@K, Recall@K, NDCG@K)
"""

import os
import sys
from pathlib import Path

# Set UTF-8
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Setup Django
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartjob_backend.settings')
import django
django.setup()

from rest_framework.test import APIClient


def run_ai_tests():
    print("=" * 72)
    print("🧪 BẮT ĐẦU KIỂM THỬ TOÀN DIỆN MODULE AI/ML (CHECKLIST 02)")
    print("=" * 72)

    client = APIClient()
    total_tests = 0
    passed_tests = 0

    def assert_test(name, response, expected_status=200):
        nonlocal total_tests, passed_tests
        total_tests += 1
        if response.status_code == expected_status:
            print(f"  ✅ [PASS] {name} (Status: {response.status_code})")
            passed_tests += 1
            return True
        else:
            print(f"  ❌ [FAIL] {name} (Expected {expected_status}, got {response.status_code})")
            print(f"     Details: {getattr(response, 'data', response.content)}")
            return False

    # --------------------------------------------------------------------------
    # 1. Trích xuất & Chuẩn hóa kỹ năng (POST /api/ai/extract-skills/)
    # --------------------------------------------------------------------------
    print("\n1. Kiểm tra API Trích xuất & Chuẩn hóa Kỹ năng (/api/ai/extract-skills/):")
    sample_text = (
        "Ứng viên thành thạo Python 3, Django REST framework, PostgreSQL và Docker. "
        "Có kinh nghiệm làm việc với k8s, ReactJS, Machine Learning và xử lý ngôn ngữ tự nhiên (NLP). "
        "Tiếng Anh giao tiếp tốt (IELTS 7.0)."
    )
    res = client.post('/api/ai/extract-skills/', {'text': sample_text}, format='json')
    if assert_test("POST /api/ai/extract-skills/ (Bilingual & Synonyms)", res):
        skills = [s['skill_name'] for s in res.data.get('skills', [])]
        print(f"     -> Kỹ năng trích xuất được ({len(skills)}): {', '.join(skills)}")
        # Verify canonical normalization
        assert 'Kubernetes' in skills, "k8s should normalize to Kubernetes"
        assert 'React' in skills, "ReactJS should normalize to React"
        assert 'Python' in skills, "Python 3 should normalize to Python"
        assert 'NLP' in skills, "xử lý ngôn ngữ tự nhiên should normalize to NLP"
        print("     -> Chuẩn hóa alias -> canonical name hoàn toàn chính xác!")

    # --------------------------------------------------------------------------
    # 2. Phân tích cú pháp CV tự động (POST /api/ai/parse-cv/)
    # --------------------------------------------------------------------------
    print("\n2. Kiểm tra API Phân tích cú pháp CV thô (/api/ai/parse-cv/):")
    raw_cv = """
    Họ và tên: Lê Văn Hoàng
    Email: levanhoang@example.com
    SĐT: 0918889999
    Vị trí ứng tuyển: Senior AI Research Engineer
    Kinh nghiệm: 5 năm kinh nghiệm làm việc trong lĩnh vực Trí tuệ Nhân tạo, Deep Learning với PyTorch.
    Học vấn: Thạc sĩ Khoa học Máy tính Đại học Bách Khoa.
    Kỹ năng: Python, PyTorch, TensorFlow, NLP, Computer Vision, Docker.
    """
    res = client.post('/api/ai/parse-cv/', {'cv_text': raw_cv}, format='json')
    if assert_test("POST /api/ai/parse-cv/ (Trích xuất Name, Email, Exp, Skills)", res):
        data = res.data
        print(f"     -> Họ tên: {data['full_name']} | Email: {data['email']} | SĐT: {data['phone']}")
        print(f"     -> Số năm KN: {data['years_of_experience']} năm | Học vấn: {data['education_level']}")
        extracted_names = [s['skill_name'] for s in data['skills']]
        print(f"     -> Kỹ năng nhận diện: {', '.join(extracted_names)}")

    # --------------------------------------------------------------------------
    # 3. Thuật toán Matching Score (POST /api/ai/match/)
    # --------------------------------------------------------------------------
    print("\n3. Kiểm tra Thuật toán Tính điểm Tương thích Matching Score (/api/ai/match/):")
    # 3a. Bằng Database IDs
    res = client.post('/api/ai/match/', {'candidate_id': 1, 'job_id': 1}, format='json')
    if assert_test("POST /api/ai/match/ (Theo candidate_id và job_id)", res):
        score = res.data['matching_score']
        recom = res.data['overall_recommendation']
        print(f"     -> Điểm tương thích: {score}% | Đánh giá: {recom}")
        print(f"     -> Phân rã điểm: {res.data['score_breakdown']}")
        print(f"     -> Giải thích (Explainability): {res.data['explanation']}")

    # 3b. Bằng văn bản trực tiếp không cần database ID (Stateless)
    res = client.post('/api/ai/match/', {
        'cv_text': raw_cv,
        'job_title': 'Lead AI Engineer',
        'job_description': 'Tuyển Lead AI Engineer thành thạo Python, PyTorch, NLP, 4 năm kinh nghiệm.',
        'years_of_experience_required': 4
    }, format='json')
    if assert_test("POST /api/ai/match/ (Văn bản CV & JD trực tiếp)", res):
        print(f"     -> Điểm trực tiếp: {res.data['matching_score']}% | Đánh giá: {res.data['overall_recommendation']}")

    # --------------------------------------------------------------------------
    # 4. Gợi ý việc làm xếp hạng cho Ứng viên (GET /api/candidates/{id}/recommendations/)
    # --------------------------------------------------------------------------
    print("\n4. Kiểm tra Xếp hạng Gợi ý Việc làm cho Ứng viên:")
    res = client.get('/api/candidates/1/recommendations/?limit=5&min_score=50.0')
    if assert_test("GET /api/candidates/1/recommendations/?limit=5", res):
        jobs = res.data
        print(f"     -> Nhận được {len(jobs)} việc làm gợi ý xếp hạng:")
        for idx, j in enumerate(jobs[:3], 1):
            print(f"        #{idx}: {j['job_title']} ({j['company_name']}) - {j['matching_score']}% [{j['overall_recommendation']}]")

    # --------------------------------------------------------------------------
    # 5. Gợi ý ứng viên xếp hạng cho Nhà tuyển dụng (GET /api/jobs/{id}/recommended_candidates/)
    # --------------------------------------------------------------------------
    print("\n5. Kiểm tra Xếp hạng Gợi ý Ứng viên cho Tin tuyển dụng:")
    res = client.get('/api/jobs/1/recommended_candidates/?limit=5')
    if assert_test("GET /api/jobs/1/recommended_candidates/?limit=5", res):
        cands = res.data
        print(f"     -> Nhận được {len(cands)} ứng viên tiềm năng:")
        for idx, c in enumerate(cands[:3], 1):
            print(f"        #{idx}: {c['full_name']} ({c['desired_position']}) - {c['matching_score']}% [{c['overall_recommendation']}]")

    # --------------------------------------------------------------------------
    # 6. Gợi ý việc làm từ CV tự do (POST /api/ai/recommend-jobs/)
    # --------------------------------------------------------------------------
    print("\n6. Kiểm tra Gợi ý Việc làm từ CV tự do (/api/ai/recommend-jobs/):")
    res = client.post('/api/ai/recommend-jobs/', {
        'cv_text': "Frontend Developer chuyên React, TypeScript, Next.js, HTML/CSS, 3 năm kinh nghiệm.",
        'limit': 3
    }, format='json')
    if assert_test("POST /api/ai/recommend-jobs/ (Từ CV text)", res):
        recs = res.data.get('recommended_jobs', [])
        print(f"     -> Top gợi ý cho CV React: {recs[0]['job_title']} ({recs[0]['matching_score']}%)")

    # --------------------------------------------------------------------------
    # 7. Đánh giá chất lượng gợi ý (GET /api/ai/evaluation/)
    # --------------------------------------------------------------------------
    print("\n7. Kiểm tra API Đánh giá Chất lượng Gợi ý Benchmark (/api/ai/evaluation/):")
    res = client.get('/api/ai/evaluation/')
    if assert_test("GET /api/ai/evaluation/ (Precision@K, Recall@K, NDCG@K, MRR, MAP)", res):
        m = res.data['metrics']
        print(f"     -> Precision@1 : {m['precision@1']*100:.2f}% | Precision@3: {m['precision@3']*100:.2f}%")
        print(f"     -> Recall@1    : {m['recall@1']*100:.2f}% | Recall@3   : {m['recall@3']*100:.2f}%")
        print(f"     -> NDCG@1      : {m['ndcg@1']*100:.2f}% | NDCG@3     : {m['ndcg@3']*100:.2f}%")
        print(f"     -> MRR         : {res.data['mrr']:.4f} | MAP        : {res.data['map']:.4f}")

    # Summary
    print("\n" + "=" * 72)
    if passed_tests == total_tests:
        print(f"🎉 TẤT CẢ {passed_tests}/{total_tests} BÀI KIỂM THỬ AI/ML ĐỀU THÀNH CÔNG 100%!")
    else:
        print(f"⚠️ Có {total_tests - passed_tests} bài kiểm thử thất bại.")
    print("=" * 72)


if __name__ == '__main__':
    run_ai_tests()

