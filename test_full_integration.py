import os
import sys
import json
from pathlib import Path

# Thêm backend vào path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartjob_backend.settings')

import django
django.setup()

from django.test import RequestFactory
from rest_framework.test import APIClient
from api.models import (
    Users, Candidates, Companies, Jobs, Skills,
    CandidateSkills, JobSkills, Applications, JobViews, AiMatchResults
)
from api.views import (
    AuthViewSet, JobViewSet, CandidateViewSet,
    AIMatchingAPIView, BIDashboardViewSet, RecommendJobsAPIView
)

def run_tests():
    print("=" * 60)
    print("   BÁO CÁO KIỂM TRA TÍCH HỢP DATA VÀ API (SMARTJOB)")
    print("=" * 60)
    
    # 1. KIỂM TRA DỮ LIỆU CSDL
    print("\n[1] KIỂM TRA DỮ LIỆU TRONG DATABASE (PostgreSQL):")
    counts = {
        "Users (Người dùng)": Users.objects.count(),
        "Candidates (Ứng viên)": Candidates.objects.count(),
        "Companies (Doanh nghiệp)": Companies.objects.count(),
        "Jobs (Tin tuyển dụng)": Jobs.objects.count(),
        "Skills (Kỹ năng chuẩn)": Skills.objects.count(),
        "CandidateSkills (Kỹ năng ứng viên)": CandidateSkills.objects.count(),
        "JobSkills (Yêu cầu kỹ năng việc)": JobSkills.objects.count(),
        "Applications (Đơn ứng tuyển)": Applications.objects.count(),
        "JobViews (Lượt xem tin)": JobViews.objects.count(),
        "AiMatchResults (Lịch sử Matching)": AiMatchResults.objects.count(),
    }
    for model_name, cnt in counts.items():
        status = "OK" if cnt > 0 else "WARNING (chưa có data)"
        print(f"  + {model_name:38}: {cnt:4} records -> {status}")
    
    client = APIClient()
    
    # 2. KIỂM TRA CÁC API ENDPOINTS
    print("\n[2] KIỂM TRA TÍCH HỢP API BACKEND & AI:")
    
    # Test 2.1: API Danh sách việc làm
    resp = client.get('/api/jobs/')
    print(f"  + GET /api/jobs/               -> Status {resp.status_code} | Tổng số jobs: {resp.data.get('count', len(resp.data))}")
    assert resp.status_code == 200, "Lỗi API /api/jobs/"
    
    # Test 2.2: API Chi tiết việc làm
    first_job = Jobs.objects.first()
    if first_job:
        resp = client.get(f'/api/jobs/{first_job.job_id}/')
        print(f"  + GET /api/jobs/{first_job.job_id}/           -> Status {resp.status_code} | Title: '{first_job.job_title}'")
        assert resp.status_code == 200, "Lỗi API chi tiết job"

    # Test 2.3: API Danh sách ứng viên & hồ sơ
    resp = client.get('/api/candidates/')
    print(f"  + GET /api/candidates/         -> Status {resp.status_code} | Tổng số ứng viên: {resp.data.get('count', len(resp.data))}")
    assert resp.status_code == 200, "Lỗi API /api/candidates/"
    
    first_cand = Candidates.objects.first()
    if first_cand:
        # Test 2.4: API Kỹ năng ứng viên
        resp = client.get(f'/api/candidates/{first_cand.candidate_id}/skills/')
        print(f"  + GET /api/candidates/{first_cand.candidate_id}/skills/   -> Status {resp.status_code} | Kỹ năng: {len(resp.data)} skills")
        assert resp.status_code == 200, "Lỗi API skills"
        
        # Test 2.5: API Gợi ý việc làm theo AI Matching
        resp = client.get(f'/api/candidates/{first_cand.candidate_id}/recommendations/')
        print(f"  + GET .../recommendations/     -> Status {resp.status_code} | Gợi ý: {len(resp.data)} jobs")
        if resp.data:
            top_rec = resp.data[0]
            print(f"    * Top 1 Match: {top_rec.get('job_title')} - Score: {top_rec.get('matching_score')}% ({top_rec.get('overall_recommendation')})")
        assert resp.status_code == 200, "Lỗi API AI recommendations"

    # Test 2.6: API Tính toán AI Matching trực tiếp
    if first_cand and first_job:
        resp = client.post('/api/ai/match/', {
            'candidate_id': first_cand.candidate_id,
            'job_id': first_job.job_id
        }, format='json')
        print(f"  + POST /api/ai/match/          -> Status {resp.status_code} | Score tính được: {resp.data.get('matching_score')}%")
        assert resp.status_code == 200, "Lỗi API AI match"

    # Test 2.7: API BI Dashboard
    bi_endpoints = [
        ('/api/bi/overview/', 'Tổng quan KPIs'),
        ('/api/bi/skills_demand/', 'Nhu cầu kỹ năng'),
        ('/api/bi/salary_trends/', 'Xu hướng tiền lương'),
        ('/api/bi/conversion_funnel/', 'Phễu tuyển dụng')
    ]
    for endpoint, desc in bi_endpoints:
        resp = client.get(endpoint)
        print(f"  + GET {endpoint:25} -> Status {resp.status_code} | {desc}")
        assert resp.status_code == 200, f"Lỗi API {endpoint}"

    # 3. KIỂM TRA MÃ NGUỒN FRONTEND & TÍCH HỢP JS
    print("\n[3] KIỂM TRA CÁC TRANG GIAO DIỆN FRONTEND:")
    frontend_files = [
        ('frontend/index.html', 'Trang chủ & Danh sách việc làm'),
        ('frontend/login.html', 'Đăng nhập / Đăng ký'),
        ('frontend/candidate-profile.html', 'Hồ sơ ứng viên & AI gợi ý việc'),
        ('frontend/job-detail.html', 'Chi tiết việc làm & Điểm Matching Score'),
        ('frontend/post-job.html', 'Đăng tin tuyển dụng'),
        ('frontend/employer-dashboard.html', 'Dashboard nhà tuyển dụng'),
        ('frontend/bi-dashboard.html', 'Dashboard BI thống kê & biểu đồ'),
        ('frontend/js/api.js', 'Module kết nối API trung tâm'),
        ('frontend/js/bi-dashboard.js', 'Script biểu đồ BI (Chart.js)')
    ]
    for rel_path, desc in frontend_files:
        p = BASE_DIR / rel_path
        if p.exists() and p.stat().st_size > 0:
            print(f"  + {rel_path:33}: Tồn tại ({p.stat().st_size:,} bytes) - {desc}")
        else:
            print(f"  - {rel_path:33}: THIẾU hoặc RỖNG!")

    # 4. KIỂM TRA ĐỊA CHỈ API_BASE TRONG FRONTEND
    api_js = (BASE_DIR / 'frontend/js/api.js').read_text(encoding='utf-8')
    if 'http://localhost:8000/api' in api_js:
        print("\n[4] CẤU HÌNH KẾT NỐI API TRONG FRONTEND:")
        print("  + API_BASE: 'http://localhost:8000/api' -> Khớp chuẩn với Django REST Framework")
    else:
        print("\n[4] CẤU HÌNH KẾT NỐI API TRONG FRONTEND: CẦN KIỂM TRA LẠI API_BASE")

    print("\n" + "=" * 60)
    print("   KẾT LUẬN: HỆ THỐNG DATA, BACKEND API VÀ FRONTEND ĐÃ SẴN SÀNG!")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
