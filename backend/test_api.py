"""
Automated Backend API Test Suite for SmartJob
Verifies all DRF endpoints, AI Matching, and BI Analytics
"""

import os
import sys
import django

# Ensure UTF-8 output
if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartjob_backend.settings')
django.setup()

from rest_framework.test import APIClient
from api.models import Users, Skills, Jobs, Candidates, Companies, Applications, AiMatchResults


def run_tests():
    print("=" * 60)
    print("🧪 BẮT ĐẦU KIỂM THỬ BACKEND API SMARTJOB")
    print("=" * 60)

    client = APIClient()
    all_passed = True

    def check(name, response, expected_status=200):
        nonlocal all_passed
        if response.status_code == expected_status:
            print(f"  ✅ [PASS] {name} (Status: {response.status_code})")
            return True
        else:
            print(f"  ❌ [FAIL] {name} (Expected: {expected_status}, Got: {response.status_code})")
            print(f"     Response: {response.data}")
            all_passed = False
            return False

    # 1. Test Skills API
    print("\n1. Kiểm tra Skills API:")
    res = client.get('/api/skills/')
    if check("GET /api/skills/", res):
        count = res.data.get('count', len(res.data.get('results', [])))
        print(f"     -> Tổng số kỹ năng trả về: {count}")
    
    res = client.get('/api/skills/categories/')
    check("GET /api/skills/categories/", res)

    # 2. Test Companies API
    print("\n2. Kiểm tra Companies API:")
    res = client.get('/api/companies/')
    check("GET /api/companies/", res)

    # 3. Test Jobs API
    print("\n3. Kiểm tra Jobs API & Filter:")
    res = client.get('/api/jobs/')
    if check("GET /api/jobs/", res):
        jobs_count = res.data.get('count', len(res.data.get('results', [])))
        print(f"     -> Tổng số tin tuyển dụng: {jobs_count}")

    res = client.get('/api/jobs/?search=Python')
    check("GET /api/jobs/?search=Python", res)

    res = client.get('/api/jobs/1/')
    check("GET /api/jobs/1/ (Chi tiết + tăng lượt xem)", res)

    # 4. Test Candidates API
    print("\n4. Kiểm tra Candidates API:")
    res = client.get('/api/candidates/')
    check("GET /api/candidates/", res)

    res = client.get('/api/candidates/1/')
    check("GET /api/candidates/1/", res)

    # 5. Test AI Matching API
    print("\n5. Kiểm tra AI Matching Engine:")
    res = client.get('/api/candidates/1/recommendations/')
    if check("GET /api/candidates/1/recommendations/ (AI Gợi ý việc)", res):
        recs = res.data
        if recs:
            top = recs[0]
            print(f"     -> Top 1 công việc: {top['job_title']} (Điểm: {top['matching_score']}%)")

    res = client.get('/api/jobs/1/recommended_candidates/')
    check("GET /api/jobs/1/recommended_candidates/ (AI Gợi ý ứng viên)", res)

    res = client.post('/api/ai/match/', {'candidate_id': 1, 'job_id': 1}, format='json')
    check("POST /api/ai/match/ (Tính toán trực tiếp Matching Score)", res)

    # 6. Test BI Dashboard Analytics API
    print("\n6. Kiểm tra BI Dashboard Analytics API:")
    res = client.get('/api/bi/overview/')
    if check("GET /api/bi/overview/", res):
        print(f"     -> Thống kê tổng quan: {res.data}")

    res = client.get('/api/bi/skills_demand/')
    if check("GET /api/bi/skills_demand/ (Nhu cầu kỹ năng thị trường)", res):
        print(f"     -> Top skills: {[s['skill_name'] for s in res.data[:5]]}")

    res = client.get('/api/bi/salary_trends/')
    check("GET /api/bi/salary_trends/ (Xu hướng lương)", res)

    res = client.get('/api/bi/conversion_funnel/')
    check("GET /api/bi/conversion_funnel/ (Phễu chuyển đổi tuyển dụng)", res)

    # 7. Test Auth API
    print("\n7. Kiểm tra Auth API:")
    Users.objects.filter(email='testuser_drf@smartjob.vn').delete()
    
    res_reg = client.post('/api/auth/register/', {
        'email': 'testuser_drf@smartjob.vn',
        'password': 'Password@123',
        'user_type': 'candidate',
        'full_name': 'Tester Candidate'
    }, format='json')
    check("POST /api/auth/register/ (Đăng ký tài khoản)", res_reg, expected_status=201)

    res_login = client.post('/api/auth/login/', {
        'email': 'testuser_drf@smartjob.vn',
        'password': 'Password@123'
    }, format='json')
    check("POST /api/auth/login/ (Đăng nhập)", res_login, expected_status=200)

    # Clean up test user
    Users.objects.filter(email='testuser_drf@smartjob.vn').delete()

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 TẤT CẢ CÁC API BACKEND ĐỀU HOẠT ĐỘNG CHÍNH XÁC 100%!")
    else:
        print("⚠️ Có một số bài test chưa đạt yêu cầu, vui lòng kiểm tra lại log.")
    print("=" * 60)


if __name__ == '__main__':
    run_tests()
