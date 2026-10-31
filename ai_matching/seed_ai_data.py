"""
Seed AI Dataset into PostgreSQL Database
Populates 15 realistic Candidates, 15 Job Postings, Skills, Education,
Experience, and Pre-calculated Matching Scores into smartjob_db.
"""

import json
import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

# Set UTF-8 encoding
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root and backend to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartjob_backend.settings')
import django
django.setup()

from django.contrib.auth.hashers import make_password
from django.utils import timezone
from api.models import (
    Users, Candidates, Companies, Skills,
    CandidateSkills, JobSkills, Jobs, Education, Experience,
    AiMatchResults
)
from ai_matching.matching_engine import calculate_matching_score


DATA_DIR = Path(__file__).resolve().parent / "data"


def seed_database():
    print("=" * 70)
    print("🌱 SEEDING AI SAMPLE DATASET INTO POSTGRESQL DATABASE")
    print("=" * 70)

    # 1. Load taxonomy skills into Skills table
    taxonomy_file = DATA_DIR / "skills_taxonomy.json"
    with open(taxonomy_file, 'r', encoding='utf-8') as f:
        tax_data = json.load(f)

    skill_objs = {}
    skills_created = 0
    for s in tax_data.get('skills', []):
        obj, created = Skills.objects.get_or_create(
            skill_name=s['name'],
            defaults={'category': s.get('category', 'General')}
        )
        skill_objs[s['name']] = obj
        if created:
            skills_created += 1
    print(f"✅ Đã đồng bộ {len(skill_objs)} kỹ năng vào bảng Skills (+{skills_created} mới).")

    # 2. Seed Jobs & Companies
    jobs_file = DATA_DIR / "sample_jobs.json"
    with open(jobs_file, 'r', encoding='utf-8') as f:
        jobs_data = json.load(f)

    job_db_map = {}
    for j_data in jobs_data:
        comp_name = j_data.get('company_name', 'Tech Corp')
        comp_email = f"contact@{comp_name.lower().replace(' ', '')}.com"
        
        user, _ = Users.objects.get_or_create(
            email=comp_email,
            defaults={
                'password_hash': make_password('Password123!'),
                'user_type': 'company',
                'is_active': True,
                'created_at': timezone.now()
            }
        )
        company, _ = Companies.objects.get_or_create(
            user=user,
            defaults={
                'company_name': comp_name,
                'industry': 'Công nghệ thông tin',
                'address': j_data.get('location', 'Hà Nội'),
                'created_at': timezone.now()
            }
        )

        job, created = Jobs.objects.update_or_create(
            job_id=j_data['job_id'],
            defaults={
                'company': company,
                'job_title': j_data['job_title'],
                'job_description': j_data['job_description'],
                'requirements': j_data['requirements'],
                'position_level': j_data.get('position_level', 'Middle'),
                'employment_type': j_data.get('employment_type', 'full-time'),
                'salary_min': Decimal(str(j_data.get('salary_min', 20000000))),
                'salary_max': Decimal(str(j_data.get('salary_max', 40000000))),
                'salary_currency': 'VND',
                'location': j_data.get('location', 'Hà Nội'),
                'years_of_experience_required': j_data.get('years_of_experience_required', 2),
                'status': 'active',
                'view_count': 10,
                'created_at': timezone.now()
            }
        )
        job_db_map[j_data['job_id']] = job

        # Seed JobSkills
        for req_skill in j_data.get('required_skills', []):
            sk_name = req_skill['name']
            sk_obj = skill_objs.get(sk_name)
            if not sk_obj:
                sk_obj, _ = Skills.objects.get_or_create(skill_name=sk_name, defaults={'category': 'Technical'})
                skill_objs[sk_name] = sk_obj

            JobSkills.objects.update_or_create(
                job=job,
                skill=sk_obj,
                defaults={
                    'required_level': req_skill.get('level', 'intermediate'),
                    'is_required': req_skill.get('is_required', True),
                    'weight': Decimal(str(req_skill.get('weight', 1.0))),
                    'created_at': timezone.now()
                }
            )

    print(f"✅ Đã nạp {len(jobs_data)} tin tuyển dụng mẫu (Jobs) và yêu cầu kỹ năng (JobSkills).")

    # 3. Seed Candidates & CandidateSkills
    cvs_file = DATA_DIR / "sample_cvs.json"
    with open(cvs_file, 'r', encoding='utf-8') as f:
        cvs_data = json.load(f)

    cand_db_map = {}
    for c_data in cvs_data:
        cand_email = c_data['email']
        user, _ = Users.objects.get_or_create(
            email=cand_email,
            defaults={
                'password_hash': make_password('Candidate123!'),
                'user_type': 'candidate',
                'is_active': True,
                'created_at': timezone.now()
            }
        )

        cand, created = Candidates.objects.update_or_create(
            candidate_id=c_data['candidate_id'],
            defaults={
                'user': user,
                'full_name': c_data['full_name'],
                'phone': c_data.get('phone', '0901234567'),
                'address': c_data.get('location', 'Hà Nội'),
                'date_of_birth': date(1996, 5, 20),
                'gender': 'male',
                'summary': c_data.get('raw_cv_text', '')[:400],
                'desired_position': c_data['desired_position'],
                'desired_salary': Decimal(str(c_data.get('desired_salary', 30000000))),
                'years_of_experience': c_data.get('years_of_experience', 3),
                'cv_file_url': f"https://smartjob.vn/cvs/cand_{c_data['candidate_id']}.pdf",
                'created_at': timezone.now()
            }
        )
        cand_db_map[c_data['candidate_id']] = cand

        # Candidate Skills
        for sk in c_data.get('skills', []):
            sk_name = sk['name']
            sk_obj = skill_objs.get(sk_name)
            if not sk_obj:
                sk_obj, _ = Skills.objects.get_or_create(skill_name=sk_name, defaults={'category': 'Technical'})
                skill_objs[sk_name] = sk_obj

            CandidateSkills.objects.update_or_create(
                candidate=cand,
                skill=sk_obj,
                defaults={
                    'proficiency_level': sk.get('level', 'intermediate'),
                    'years_of_experience': sk.get('years', 2),
                    'created_at': timezone.now()
                }
            )

        # Education
        edu_info = c_data.get('education', {})
        if edu_info:
            Education.objects.update_or_create(
                candidate=cand,
                institution_name=edu_info.get('institution', 'Đại học'),
                defaults={
                    'degree': edu_info.get('degree', 'Cử nhân'),
                    'major': edu_info.get('major', 'CNTT'),
                    'start_date': date(2014, 9, 1),
                    'end_date': date(2018, 6, 30),
                    'gpa': Decimal('3.50'),
                    'created_at': timezone.now()
                }
            )

    print(f"✅ Đã nạp {len(cvs_data)} hồ sơ ứng viên mẫu (Candidates), kỹ năng và học vấn.")

    # 4. Precompute AI Matching Scores for top candidate-job pairs
    print("🧠 Đang tính toán và lưu kết quả AI Matching vào database...")
    match_count = 0
    for c_data in cvs_data:
        cand_obj = cand_db_map[c_data['candidate_id']]
        for j_data in jobs_data:
            job_obj = job_db_map[j_data['job_id']]
            score_data = calculate_matching_score(c_data, j_data)

            AiMatchResults.objects.update_or_create(
                candidate=cand_obj,
                job=job_obj,
                defaults={
                    'matching_score': Decimal(str(score_data['matching_score'])),
                    'matched_skills': score_data['matched_skills'],
                    'missing_skills': score_data['missing_skills'],
                    'skill_match_details': score_data['skill_match_details'],
                    'experience_match': Decimal(str(score_data['score_breakdown']['experience_match'])),
                    'education_match': Decimal(str(score_data['score_breakdown']['education_match'])),
                    'salary_match': Decimal(str(score_data['score_breakdown']['salary_match'])),
                    'overall_recommendation': score_data['overall_recommendation'],
                    'calculated_at': timezone.now()
                }
            )
            match_count += 1

    print(f"✅ Đã tính toán và lưu {match_count} cặp AI_Match_Results vào database!")

    # 5. Reset PostgreSQL Sequences
    from django.db import connection
    seq_tables = [
        ('candidates', 'candidate_id'),
        ('jobs', 'job_id'),
        ('users', 'user_id'),
        ('skills', 'skill_id'),
        ('companies', 'company_id'),
        ('applications', 'application_id'),
        ('candidate_skills', 'candidate_skill_id'),
        ('job_skills', 'job_skill_id'),
        ('education', 'education_id'),
        ('experience', 'experience_id'),
        ('ai_match_results', 'match_id'),
        ('job_views', 'view_id'),
        ('saved_jobs', 'saved_job_id')
    ]
    with connection.cursor() as cur:
        for tbl, col in seq_tables:
            cur.execute('SELECT pg_get_serial_sequence(%s, %s);', [tbl, col])
            row = cur.fetchone()
            if row and row[0]:
                seq = row[0]
                cur.execute(f'SELECT COALESCE(MAX({col}), 1) FROM {tbl};')
                max_v = cur.fetchone()[0]
                cur.execute('SELECT setval(%s, %s);', [seq, max_v])
    print("✅ Đã cập nhật lại toàn bộ PostgreSQL sequences chính xác.")

    print("=" * 70)
    print("🎉 HOÀN TẤT SEED DỮ LIỆU MẪU AI/ML THÀNH CÔNG!")
    print("=" * 70)


if __name__ == '__main__':
    seed_database()
