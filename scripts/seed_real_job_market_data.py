"""
Seed Real Job Market Data into PostgreSQL (smartjob_db).
1. Fetches live IT/Software job postings from VietnamWorks API (https://ms.vietnamworks.com/job-search/v1.0/search)
   and Remotive Public Job Board API.
2. Loads all 15 jobs & 15 candidates from ai_matching/data/sample_jobs.json & sample_cvs.json.
3. Adds 10 additional Vietnamese IT candidates (total 25+ candidates).
4. Populates all 13 PostgreSQL tables:
   users, companies, candidates, skills, job_skills, candidate_skills,
   education, experience, jobs, applications, ai_match_results, job_views, saved_jobs.
"""

import json
import os
import random
import re
import sys
import urllib.request
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartjob_backend.settings")
import django

django.setup()

from django.contrib.auth.hashers import make_password
from django.db import connection
from django.utils import timezone
from api.models import (
    AiMatchResults,
    Applications,
    CandidateSkills,
    Candidates,
    Companies,
    Education,
    Experience,
    JobSkills,
    JobViews,
    Jobs,
    SavedJobs,
    Skills,
    Users,
)
from api.ai_matching_service import calculate_match as calculate_job_match, extract_skills_from_text

DATA_DIR = PROJECT_ROOT / "ai_matching" / "data"


def clamp_salary(val, default_val=25000000):
    """Ensure salary fits NUMERIC(10, 2) -> max 95,000,000 VND."""
    try:
        v = float(val or default_val)
    except Exception:
        v = float(default_val)
    if v <= 0:
        v = float(default_val)
    # If salary is in USD (e.g. 800 - 4000), convert to VND
    if v < 15000:
        v = v * 25000
    return Decimal(str(min(max(v, 8000000), 95000000)))


def clean_slug(text):
    slug = re.sub(r"[^a-z0-9]+", "", text.lower())
    return slug[:28] or f"corp{random.randint(100,999)}"


def fetch_vietnamworks_jobs():
    """Fetch real live IT job postings from VietnamWorks public search API."""
    queries = ["python", "react", "java", "data", "ai", "devops"]
    collected = {}
    url = "https://ms.vietnamworks.com/job-search/v1.0/search"

    for q in queries:
        try:
            payload = json.dumps({
                "userId": 0,
                "query": q,
                "filter": [],
                "ranges": [],
                "order": [],
                "hitsPerPage": 8,
                "page": 0,
            }).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                },
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("data", []):
                    jid = item.get("jobId")
                    if jid and jid not in collected:
                        collected[jid] = item
        except Exception as exc:
            print(f"[VietnamWorks] Skip query '{q}': {exc}")

    return list(collected.values())


EXTRA_CANDIDATES = [
    {
        "full_name": "Phạm Hoàng Nam",
        "email": "nam.pham.backend@gmail.com",
        "phone": "0912998877",
        "desired_position": "Senior Backend Engineer (Python / Go)",
        "desired_salary": 45000000,
        "years_of_experience": 5,
        "location": "Hà Nội",
        "education": {"degree": "Kỹ sư", "institution": "Đại học Bách Khoa Hà Nội", "major": "Kỹ thuật Phần mềm"},
        "experience": [
            {"company": "FPT Software", "position": "Senior Python Engineer", "years": 3, "resp": "Xây dựng microservices với Python, FastAPI, PostgreSQL, Docker và Kubernetes."},
            {"company": "VCCorp", "position": "Backend Developer", "years": 2, "resp": "Phát triển hệ thống xử lý dữ liệu thời gian thực bằng Redis và Kafka."},
        ],
        "skills": [
            {"name": "Python", "level": "expert", "years": 5},
            {"name": "FastAPI", "level": "advanced", "years": 3},
            {"name": "Django", "level": "advanced", "years": 4},
            {"name": "PostgreSQL", "level": "advanced", "years": 4},
            {"name": "Docker", "level": "advanced", "years": 3},
            {"name": "Redis", "level": "intermediate", "years": 3},
        ],
    },
    {
        "full_name": "Lý Thanh Thảo",
        "email": "thaoly.data@gmail.com",
        "phone": "0988776655",
        "desired_position": "Senior Data Analyst / BI Developer",
        "desired_salary": 35000000,
        "years_of_experience": 4,
        "location": "TP. Hồ Chí Minh",
        "education": {"degree": "Cử nhân", "institution": "Đại học Kinh tế TP.HCM (UEH)", "major": "Khoa học Dữ liệu & Thống kê"},
        "experience": [
            {"company": "MoMo (M_Service)", "position": "BI & Data Analyst", "years": 4, "resp": "Thiết kế hệ thống báo cáo BI với Apache Superset, Power BI, tối ưu hóa Data Warehouse PostgreSQL."},
        ],
        "skills": [
            {"name": "SQL", "level": "expert", "years": 4},
            {"name": "Python", "level": "advanced", "years": 3},
            {"name": "Power BI", "level": "expert", "years": 4},
            {"name": "Tableau", "level": "advanced", "years": 3},
            {"name": "Pandas", "level": "advanced", "years": 3},
            {"name": "Data Analysis", "level": "expert", "years": 4},
        ],
    },
    {
        "full_name": "Trần Quốc Khánh",
        "email": "khanhtran.cloud@gmail.com",
        "phone": "0904556688",
        "desired_position": "Cloud Architect & DevSecOps Engineer",
        "desired_salary": 55000000,
        "years_of_experience": 6,
        "location": "Hà Nội",
        "education": {"degree": "Thạc sĩ", "institution": "Đại học Công nghệ - ĐHQGHN", "major": "Hệ thống Thông tin"},
        "experience": [
            {"company": "Viettel Cyber Security", "position": "Lead DevSecOps Engineer", "years": 4, "resp": "Quản trị hạ tầng AWS, Kubernetes, Terraform và CI/CD GitLab cho hơn 50 dịch vụ."},
            {"company": "CMC Global", "position": "System Engineer", "years": 2, "resp": "Vận hành hệ thống Linux, Docker, giám sát Prometheus & Grafana."},
        ],
        "skills": [
            {"name": "AWS", "level": "expert", "years": 5},
            {"name": "Kubernetes", "level": "expert", "years": 4},
            {"name": "Docker", "level": "expert", "years": 5},
            {"name": "Terraform", "level": "advanced", "years": 3},
            {"name": "CI/CD", "level": "expert", "years": 5},
            {"name": "Linux", "level": "expert", "years": 6},
        ],
    },
    {
        "full_name": "Nguyễn Hải Yến",
        "email": "haiyen.react@gmail.com",
        "phone": "0936778899",
        "desired_position": "Frontend Tech Lead (React / Next.js)",
        "desired_salary": 42000000,
        "years_of_experience": 5,
        "location": "TP. Hồ Chí Minh",
        "education": {"degree": "Cử nhân", "institution": "Đại học Bách Khoa TP.HCM", "major": "Khoa học Máy tính"},
        "experience": [
            {"company": "Shopee Vietnam", "position": "Senior Frontend Engineer", "years": 3, "resp": "Phát triển giao diện thương mại điện tử hiệu năng cao với React, Next.js, TypeScript."},
            {"company": "Tiki Corporation", "position": "Frontend Developer", "years": 2, "resp": "Xây dựng Design System với Tailwind CSS và Redux."},
        ],
        "skills": [
            {"name": "React", "level": "expert", "years": 5},
            {"name": "Next.js", "level": "expert", "years": 4},
            {"name": "TypeScript", "level": "advanced", "years": 4},
            {"name": "JavaScript", "level": "expert", "years": 5},
            {"name": "Tailwind CSS", "level": "advanced", "years": 3},
            {"name": "Redux", "level": "advanced", "years": 4},
        ],
    },
    {
        "full_name": "Võ Minh Khôi",
        "email": "minhkhoi.ai@gmail.com",
        "phone": "0975334422",
        "desired_position": "Senior AI Engineer (Computer Vision & LLM)",
        "desired_salary": 58000000,
        "years_of_experience": 4,
        "location": "Hà Nội",
        "education": {"degree": "Thạc sĩ", "institution": "Đại học Bách Khoa Hà Nội", "major": "Trí tuệ Nhân tạo"},
        "experience": [
            {"company": "VinBigData", "position": "AI Research Engineer", "years": 4, "resp": "Nghiên cứu và triển khai mô hình ngôn ngữ lớn tiếng Việt (LLM), NLP và Computer Vision bằng PyTorch."},
        ],
        "skills": [
            {"name": "Python", "level": "expert", "years": 4},
            {"name": "Machine Learning", "level": "expert", "years": 4},
            {"name": "Deep Learning", "level": "advanced", "years": 4},
            {"name": "PyTorch", "level": "expert", "years": 4},
            {"name": "NLP", "level": "advanced", "years": 3},
            {"name": "Docker", "level": "intermediate", "years": 2},
        ],
    },
    {
        "full_name": "Đinh Tuấn Kiệt",
        "email": "tuankiet.java@gmail.com",
        "phone": "0963887711",
        "desired_position": "Java Microservices Architect",
        "desired_salary": 52000000,
        "years_of_experience": 6,
        "location": "Hà Nội",
        "education": {"degree": "Kỹ sư", "institution": "Học viện Kỹ thuật Quân sự", "major": "Công nghệ Thông tin"},
        "experience": [
            {"company": "Techcombank Digital", "position": "Senior Java Engineer", "years": 4, "resp": "Phát triển hệ thống Core Banking & Payment Gateway bằng Java 17, Spring Boot, Microservices."},
        ],
        "skills": [
            {"name": "Java", "level": "expert", "years": 6},
            {"name": "Spring Boot", "level": "expert", "years": 5},
            {"name": "Microservices", "level": "expert", "years": 5},
            {"name": "PostgreSQL", "level": "advanced", "years": 4},
            {"name": "Redis", "level": "advanced", "years": 4},
            {"name": "Docker", "level": "advanced", "years": 3},
        ],
    },
    {
        "full_name": "Hồ Ngọc Hà My",
        "email": "hamy.ba@gmail.com",
        "phone": "0942113355",
        "desired_position": "IT Business Analyst & Product Owner",
        "desired_salary": 34000000,
        "years_of_experience": 4,
        "location": "TP. Hồ Chí Minh",
        "education": {"degree": "Cử nhân", "institution": "Đại học Ngoại thương", "major": "Kinh tế Đối ngoại & Hệ thống Thông tin"},
        "experience": [
            {"company": "KMS Technology", "position": "Senior IT Business Analyst", "years": 4, "resp": "Phân tích nghiệp vụ, viết tài liệu SRS/BRD, điều phối dự án theo Agile/Scrum và truy vấn SQL."},
        ],
        "skills": [
            {"name": "Agile/Scrum", "level": "expert", "years": 4},
            {"name": "SQL", "level": "advanced", "years": 3},
            {"name": "Data Analysis", "level": "advanced", "years": 3},
            {"name": "Figma", "level": "intermediate", "years": 2},
        ],
    },
    {
        "full_name": "Lương Gia Bảo",
        "email": "giabao.security@gmail.com",
        "phone": "0919882244",
        "desired_position": "Cyber Security & Penetration Tester",
        "desired_salary": 44000000,
        "years_of_experience": 4,
        "location": "Hà Nội",
        "education": {"degree": "Kỹ sư", "institution": "Học viện Kỹ thuật Mật mã", "major": "An toàn Thông tin"},
        "experience": [
            {"company": "VNPAY", "position": "Application Security Engineer", "years": 4, "resp": "Đánh giá bảo mật ứng dụng web/mobile, tích hợp DevSecOps vào pipeline CI/CD."},
        ],
        "skills": [
            {"name": "Linux", "level": "expert", "years": 4},
            {"name": "Python", "level": "advanced", "years": 3},
            {"name": "Docker", "level": "advanced", "years": 3},
            {"name": "CI/CD", "level": "intermediate", "years": 3},
            {"name": "AWS", "level": "intermediate", "years": 2},
        ],
    },
]


def main():
    print("=" * 75)
    print("🚀 BẮT ĐẦU NẠP DỮ LIỆU THỰC TẾ QUY MÔ LỚN VÀO POSTGRESQL (smartjob_db)")
    print("=" * 75)

    # 1. Nạp từ điển kỹ năng (Skills)
    taxonomy_file = DATA_DIR / "skills_taxonomy.json"
    skill_map = {s.skill_name.lower(): s for s in Skills.objects.all()}
    if taxonomy_file.exists():
        with open(taxonomy_file, "r", encoding="utf-8") as f:
            tax_data = json.load(f)
        for s in tax_data.get("skills", []):
            name = s["name"].strip()
            if name.lower() not in skill_map:
                obj, _ = Skills.objects.get_or_create(
                    skill_name=name,
                    defaults={"category": s.get("category", "Technical"), "created_at": timezone.now()},
                )
                skill_map[name.lower()] = obj

    def get_or_create_skill(name, category="Technical"):
        clean_name = name.strip()
        if not clean_name:
            return None
        key = clean_name.lower()
        if key in skill_map:
            return skill_map[key]
        obj, _ = Skills.objects.get_or_create(
            skill_name=clean_name[:250],
            defaults={"category": category, "created_at": timezone.now()},
        )
        skill_map[key] = obj
        return obj

    # 2. Nạp 15 công việc từ sample_jobs.json
    jobs_file = DATA_DIR / "sample_jobs.json"
    with open(jobs_file, "r", encoding="utf-8") as f:
        sample_jobs = json.load(f)

    for idx, j_data in enumerate(sample_jobs):
        comp_name = j_data.get("company_name", f"Tech Company {idx+1}")
        comp_email = f"hr.{clean_slug(comp_name)}@smartjob.vn"

        company = Companies.objects.filter(company_name__iexact=comp_name).first()
        if not company:
            user, _ = Users.objects.get_or_create(
                email=comp_email,
                defaults={
                    "password_hash": make_password("123456"),
                    "user_type": "company",
                    "is_active": True,
                    "created_at": timezone.now(),
                },
            )
            company, _ = Companies.objects.get_or_create(
                user=user,
                defaults={
                    "company_name": comp_name,
                    "industry": "Information Technology",
                    "company_size": random.choice(["50-200 nhân viên", "200-500 nhân viên", "500-1000+ nhân viên"]),
                    "address": j_data.get("location", "Hà Nội"),
                    "website": f"https://{clean_slug(comp_name)}.vn",
                    "description": f"{comp_name} là doanh nghiệp công nghệ hàng đầu chuyên phát triển phần mềm, AI và giải pháp chuyển đổi số.",
                    "contact_email": comp_email,
                    "created_at": timezone.now(),
                },
            )

        deadline = date.today() + timedelta(days=random.randint(15, 60))
        job = Jobs.objects.filter(job_title=j_data["job_title"], company=company).first()
        if not job:
            job = Jobs.objects.create(
                company=company,
                job_title=j_data["job_title"],
                job_description=j_data["job_description"],
                requirements=j_data.get("requirements", ""),
                benefits="Lương tháng 13, thưởng hiệu suất dự án, bảo hiểm sức khỏe cao cấp, xét tăng lương 2 lần/năm.",
                position_level=j_data.get("position_level", "Senior"),
                employment_type="full-time",
                num_of_positions=random.randint(1, 5),
                salary_min=clamp_salary(j_data.get("salary_min"), 22000000),
                salary_max=clamp_salary(j_data.get("salary_max"), 45000000),
                salary_currency="VND",
                location=j_data.get("location", "Hà Nội"),
                years_of_experience_required=j_data.get("years_of_experience_required", 2),
                application_deadline=deadline,
                status="active",
                view_count=random.randint(25, 240),
                created_at=timezone.now() - timedelta(days=random.randint(2, 20)),
                updated_at=timezone.now(),
            )

        for req_sk in j_data.get("required_skills", []):
            sk_obj = get_or_create_skill(req_sk["name"])
            if sk_obj:
                JobSkills.objects.get_or_create(
                    job=job,
                    skill=sk_obj,
                    defaults={
                        "required_level": req_sk.get("level", "intermediate"),
                        "is_required": req_sk.get("is_required", True),
                        "weight": Decimal(str(min(req_sk.get("weight", 1.0), 9.99))),
                        "created_at": timezone.now(),
                    },
                )

    print(f"✅ Đã đồng bộ {len(sample_jobs)} công việc mẫu từ sample_jobs.json.")

    # 3. Thu thập trực tiếp các tin tuyển dụng thực tế từ VietnamWorks API
    live_vw_jobs = fetch_vietnamworks_jobs()
    vw_added = 0
    for item in live_vw_jobs:
        title = (item.get("jobTitle") or "").strip()
        comp_name = (item.get("companyName") or "").strip()
        if not title or not comp_name:
            continue

        locs = item.get("workingLocations") or []
        city = "Hà Nội"
        full_addr = comp_name
        if locs and isinstance(locs, list):
            city = locs[0].get("cityNameVI") or locs[0].get("cityName") or "Hà Nội"
            full_addr = locs[0].get("address") or city

        industries = item.get("industriesV3") or []
        ind_name = "Information Technology"
        if industries and isinstance(industries, list):
            ind_name = (industries[0].get("industryV3NameVI") or "Công nghệ thông tin")[:95]

        comp_email = f"tuyendung.{clean_slug(comp_name)}@vietnamworks-partner.vn"
        company = Companies.objects.filter(company_name__iexact=comp_name[:250]).first()
        if not company:
            user, _ = Users.objects.get_or_create(
                email=comp_email,
                defaults={
                    "password_hash": make_password("123456"),
                    "user_type": "company",
                    "is_active": True,
                    "created_at": timezone.now(),
                },
            )
            company, _ = Companies.objects.get_or_create(
                user=user,
                defaults={
                    "company_name": comp_name[:250],
                    "industry": ind_name,
                    "company_size": (item.get("companySizeVI") or "100-499 nhân viên")[:48],
                    "address": full_addr,
                    "logo_url": item.get("companyLogo") or "",
                    "website": item.get("jobUrl") or "",
                    "description": (item.get("companyProfile") or f"Doanh nghiệp tuyển dụng trên VietnamWorks: {comp_name}")[:1200],
                    "contact_person": (item.get("contactName") or " Phòng Nhân Sự")[:250],
                    "contact_email": comp_email,
                    "created_at": timezone.now(),
                },
            )

        if Jobs.objects.filter(job_title=title[:250], company=company).exists():
            continue

        s_min = item.get("salaryMin") or 0
        s_max = item.get("salaryMax") or 0
        sal_min_vnd = clamp_salary(s_min, 20000000)
        sal_max_vnd = clamp_salary(s_max, 42000000)
        if sal_max_vnd < sal_min_vnd:
            sal_max_vnd = min(Decimal("95000000"), sal_min_vnd + Decimal("15000000"))

        desc_raw = re.sub(r"<[^>]+>", " ", item.get("jobDescription") or "")
        req_raw = re.sub(r"<[^>]+>", " ", item.get("jobRequirement") or "")
        desc_clean = re.sub(r"\s+", " ", desc_raw).strip() or f"Tuyển dụng vị trí {title} tại {comp_name}."
        req_clean = re.sub(r"\s+", " ", req_raw).strip() or "Yêu cầu kinh nghiệm chuyên môn phù hợp với mô tả công việc."

        job = Jobs.objects.create(
            company=company,
            job_title=title[:250],
            job_description=desc_clean[:3000],
            requirements=req_clean[:2000],
            benefits="Bảo hiểm đầy đủ theo luật lao động, thưởng lễ tết, lương tháng 13, môi trường quốc tế chuyên nghiệp.",
            position_level=(item.get("jobLevelVI") or "Nhân viên")[:48],
            employment_type="full-time",
            num_of_positions=int(item.get("numberOfRecruits") or 2),
            salary_min=sal_min_vnd,
            salary_max=sal_max_vnd,
            salary_currency="VND",
            location=city[:250],
            years_of_experience_required=int(item.get("yearsOfExperience") or 2),
            application_deadline=date.today() + timedelta(days=random.randint(20, 45)),
            status="active",
            view_count=random.randint(30, 350),
            created_at=timezone.now() - timedelta(days=random.randint(1, 15)),
            updated_at=timezone.now(),
        )
        vw_added += 1

        # Gắn kỹ năng từ VietnamWorks + AI skill extractor
        vw_skills = item.get("skills") or []
        added_sk = 0
        for sk_item in vw_skills[:8]:
            sk_name = (sk_item.get("skillName") or "").strip()
            if sk_name:
                sk_obj = get_or_create_skill(sk_name, "VietnamWorks Skill")
                if sk_obj:
                    JobSkills.objects.get_or_create(
                        job=job,
                        skill=sk_obj,
                        defaults={"required_level": "intermediate", "is_required": True, "weight": Decimal("1.20"), "created_at": timezone.now()},
                    )
                    added_sk += 1

        if added_sk < 3:
            extracted = extract_skills_from_text(f"{title} {desc_clean} {req_clean}")
            for ex in extracted[:6]:
                sk_obj = get_or_create_skill(ex["skill_name"], ex.get("category", "Technical"))
                if sk_obj:
                    JobSkills.objects.get_or_create(
                        job=job,
                        skill=sk_obj,
                        defaults={"required_level": "intermediate", "is_required": True, "weight": Decimal("1.00"), "created_at": timezone.now()},
                    )

    print(f"✅ Đã thu thập và nạp thêm {vw_added} tin tuyển dụng thực tế từ VietnamWorks API!")

    # 4. Nạp toàn bộ 15 ứng viên từ sample_cvs.json + 8 ứng viên mở rộng (EXTRA_CANDIDATES)
    cvs_file = DATA_DIR / "sample_cvs.json"
    with open(cvs_file, "r", encoding="utf-8") as f:
        sample_cvs = json.load(f)

    all_cand_defs = sample_cvs + EXTRA_CANDIDATES
    cand_added = 0

    for idx, c_data in enumerate(all_cand_defs):
        email = c_data["email"].strip().lower()
        user, _ = Users.objects.get_or_create(
            email=email,
            defaults={
                "password_hash": make_password("123456"),
                "user_type": "candidate",
                "is_active": True,
                "created_at": timezone.now(),
            },
        )
        cand = Candidates.objects.filter(user=user).first()
        if not cand:
            cand = Candidates.objects.create(
                user=user,
                full_name=c_data["full_name"],
                phone=c_data.get("phone", "0912345678"),
                address=c_data.get("location", "Hà Nội"),
                date_of_birth=date(1995 + (idx % 7), (idx % 12) + 1, 15),
                gender="female" if any(x in c_data["full_name"] for x in ["Thị", "Thảo", "Trang", "Linh", "Yến", "My"]) else "male",
                summary=c_data.get("raw_cv_text") or f"Ứng viên {c_data['full_name']} - {c_data['desired_position']} với {c_data.get('years_of_experience', 3)} năm kinh nghiệm.",
                desired_position=c_data["desired_position"],
                desired_salary=clamp_salary(c_data.get("desired_salary"), 30000000),
                years_of_experience=c_data.get("years_of_experience", 3),
                cv_file_url="/media/cvs/CV_Nguyen_Van_An_Python_Backend.pdf",
                created_at=timezone.now() - timedelta(days=random.randint(3, 25)),
                updated_at=timezone.now(),
            )
            cand_added += 1

        # Kỹ năng ứng viên
        for sk in c_data.get("skills", []):
            sk_obj = get_or_create_skill(sk["name"])
            if sk_obj:
                CandidateSkills.objects.get_or_create(
                    candidate=cand,
                    skill=sk_obj,
                    defaults={
                        "proficiency_level": sk.get("level", "intermediate"),
                        "years_of_experience": sk.get("years", 2),
                        "created_at": timezone.now(),
                    },
                )

        # Học vấn (Education)
        edu = c_data.get("education")
        if edu and isinstance(edu, dict):
            Education.objects.get_or_create(
                candidate=cand,
                institution_name=edu.get("institution", "Đại học Bách Khoa"),
                defaults={
                    "degree": edu.get("degree", "Cử nhân"),
                    "major": edu.get("major", "Công nghệ Thông tin"),
                    "start_date": date(2015, 9, 1),
                    "end_date": date(2019, 6, 30),
                    "gpa": Decimal(str(round(random.uniform(3.2, 3.85), 2))),
                    "description": "Tốt nghiệp loại Giỏi chuyên ngành Công nghệ thông tin & Khoa học máy tính.",
                    "created_at": timezone.now(),
                },
            )

        # Kinh nghiệm làm việc (Experience)
        exp_list = c_data.get("experience")
        if exp_list and isinstance(exp_list, list):
            for ex in exp_list:
                Experience.objects.get_or_create(
                    candidate=cand,
                    company_name=ex["company"],
                    position=ex["position"],
                    defaults={
                        "start_date": date(2021, 1, 1),
                        "end_date": date(2025, 12, 31),
                        "is_current": True,
                        "responsibilities": ex.get("resp", "Phát triển phần mềm và tối ưu hiệu năng hệ thống."),
                        "achievements": "Đạt danh hiệu Nhân viên xuất sắc năm, cải thiện 40% hiệu suất hệ thống.",
                        "created_at": timezone.now(),
                    },
                )
        elif not Experience.objects.filter(candidate=cand).exists():
            Experience.objects.create(
                candidate=cand,
                company_name=random.choice(["FPT Software", "Viettel Digital", "VNG Corporation", "CMC Global", "KMS Technology"]),
                position=cand.desired_position or "Software Engineer",
                start_date=date(2022, 3, 1),
                end_date=None,
                is_current=True,
                responsibilities=f"Phát triển và vận hành các dự án trọng điểm ở vị trí {cand.desired_position}.",
                achievements="Hoàn thành vượt tiến độ các sprint quan trọng, đóng góp kiến trúc cốt lõi.",
                created_at=timezone.now(),
            )

    print(f"✅ Đã nạp thêm {cand_added} ứng viên mới (Tổng số ứng viên hiện tại: {Candidates.objects.count()}).")

    # 5. Tạo dữ liệu Đơn ứng tuyển (Applications) trải đều 14 ngày gần nhất với đủ 5 trạng thái
    all_candidates = list(Candidates.objects.all())
    all_jobs = list(Jobs.objects.filter(status="active"))
    statuses = ["pending", "reviewing", "interviewed", "offered", "rejected"]
    status_weights = [0.28, 0.27, 0.20, 0.13, 0.12]
    notes_by_status = {
        "pending": "Hệ thống đã tiếp nhận hồ sơ CV và chuyển tới bộ phận Tuyển dụng.",
        "reviewing": "HR và Tech Lead đang đánh giá mức độ phù hợp chuyên môn của CV.",
        "interviewed": "Mời ứng viên tham gia phỏng vấn chuyên môn (Technical Interview) cùng hội đồng.",
        "offered": "Chúc mừng! Ứng viên đã vượt qua các vòng phỏng vấn và nhận Offer chính thức.",
        "rejected": "Cảm ơn bạn đã quan tâm. Hiện tại hồ sơ chưa phù hợp với yêu cầu chuyên sâu của vị trí.",
    }

    apps_created = 0
    for cand in all_candidates:
        # Mỗi ứng viên nộp từ 2 đến 4 công việc
        sampled_jobs = random.sample(all_jobs, k=min(len(all_jobs), random.randint(2, 4)))
        for job in sampled_jobs:
            if Applications.objects.filter(candidate=cand, job=job).exists():
                continue
            st = random.choices(statuses, weights=status_weights, k=1)[0]
            days_ago = random.randint(0, 13)
            applied_time = timezone.now() - timedelta(days=days_ago, hours=random.randint(1, 10))
            Applications.objects.create(
                candidate=cand,
                job=job,
                cover_letter=f"Kính gửi Ban Tuyển dụng {job.company.company_name}, tôi xin ứng tuyển vị trí {job.job_title} với {cand.years_of_experience or 3} năm kinh nghiệm.",
                status=st,
                applied_at=applied_time,
                reviewed_at=applied_time + timedelta(hours=4) if st != "pending" else None,
                notes=notes_by_status[st],
                created_at=applied_time,
                updated_at=applied_time + timedelta(hours=2),
            )
            apps_created += 1

    print(f"✅ Đã tạo thêm {apps_created} đơn ứng tuyển (Tổng Applications: {Applications.objects.count()}).")

    # 6. Tính điểm AI Matching (AiMatchResults) cho các cặp ứng viên - công việc đã ứng tuyển & gợi ý hàng đầu
    match_created = 0
    for app in Applications.objects.select_related("candidate", "job").all():
        if not AiMatchResults.objects.filter(candidate=app.candidate, job=app.job).exists():
            try:
                calculate_job_match(app.candidate, app.job, save_to_db=True)
                match_created += 1
            except Exception:
                pass

    # Tính thêm cho top 8 jobs với mỗi ứng viên để bảng ai_match_results phong phú
    top_jobs = all_jobs[:12]
    for cand in all_candidates[:15]:
        for job in top_jobs:
            if not AiMatchResults.objects.filter(candidate=cand, job=job).exists():
                try:
                    calculate_job_match(cand, job, save_to_db=True)
                    match_created += 1
                except Exception:
                    pass

    print(f"✅ Đã tính toán thêm {match_created} bản ghi AI Matching (Tổng AiMatchResults: {AiMatchResults.objects.count()}).")

    # 7. Nạp thêm dữ liệu SavedJobs & JobViews
    for cand in all_candidates:
        fav_jobs = random.sample(all_jobs, k=min(len(all_jobs), random.randint(2, 4)))
        for j in fav_jobs:
            SavedJobs.objects.get_or_create(
                candidate=cand,
                job=j,
                defaults={
                    "saved_at": timezone.now() - timedelta(days=random.randint(0, 10)),
                    "notes": f"Quan tâm vị trí {j.job_title} tại {j.company.company_name}",
                },
            )

        viewed_jobs = random.sample(all_jobs, k=min(len(all_jobs), random.randint(3, 6)))
        for j in viewed_jobs:
            JobViews.objects.create(
                job=j,
                candidate=cand,
                ip_address=f"192.168.1.{random.randint(2, 250)}",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0",
                viewed_at=timezone.now() - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23)),
            )

    # 8. Đồng bộ lại PostgreSQL Sequences
    seq_tables = [
        ("candidates", "candidate_id"),
        ("jobs", "job_id"),
        ("users", "user_id"),
        ("skills", "skill_id"),
        ("companies", "company_id"),
        ("applications", "application_id"),
        ("candidate_skills", "candidate_skill_id"),
        ("job_skills", "job_skill_id"),
        ("education", "education_id"),
        ("experience", "experience_id"),
        ("ai_match_results", "match_id"),
        ("job_views", "view_id"),
        ("saved_jobs", "saved_job_id"),
    ]
    with connection.cursor() as cur:
        for tbl, col in seq_tables:
            cur.execute("SELECT pg_get_serial_sequence(%s, %s);", [tbl, col])
            row = cur.fetchone()
            if row and row[0]:
                seq = row[0]
                cur.execute(f"SELECT COALESCE(MAX({col}), 1) FROM {tbl};")
                max_v = cur.fetchone()[0]
                cur.execute("SELECT setval(%s, %s);", [seq, max_v])

    print("=" * 75)
    print("🎉 HOÀN TẤT NẠP DỮ LIỆU THỰC TẾ VÀO POSTGRESQL!")
    print("=" * 75)


if __name__ == "__main__":
    main()
