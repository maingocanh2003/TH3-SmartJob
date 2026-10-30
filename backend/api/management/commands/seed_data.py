"""
SmartJob Database Seeder Management Command
Seeds initial sample data directly into PostgreSQL:
- Standard Skills
- Sample Companies & User Accounts
- Sample Jobs & Job Required Skills
- Sample Candidates, Candidate Skills, Education & Experience
- Sample Job Applications & Pre-calculated AI Matching Scores
- Sample Job Views for BI Analytics
"""

import os
import sys
from datetime import date
from pathlib import Path
from typing import TypedDict, List, Tuple, Optional, Any, cast

# Đảm bảo UTF-8 output trên Windows console
for _stream in (sys.stdout, sys.stderr):
    if _stream and hasattr(_stream, 'reconfigure'):
        try:
            _stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

# Hỗ trợ thực thi trực tiếp script độc lập
_backend_dir = str(Path(__file__).resolve().parent.parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartjob_backend.settings')

import django  # noqa: E402
from django.conf import settings  # noqa: E402

if not settings.configured:
    django.setup()

from django.core.management.base import BaseCommand  # noqa: E402
from django.contrib.auth.hashers import make_password  # noqa: E402
from api.models import (  # noqa: E402
    Users, Candidates, Companies, Skills, CandidateSkills,
    Education, Experience, Jobs, JobSkills, Applications,
    JobViews
)
from api.ai_matching_service import calculate_match  # noqa: E402


# ĐỊNH NGHĨA KIỂU DỮ LIỆU ĐỂ LOẠI BỎ TOÀN BỘ CẢNH BÁO PYREFLY / PYRIGHT (bad-unpacking)
class CompanyData(TypedDict):
    email: str
    name: str
    industry: str
    size: str
    address: str
    phone: str
    website: str
    logo: str
    desc: str


class JobData(TypedDict):
    company: Any
    title: str
    desc: str
    req: str
    benefits: str
    level: str
    type: str
    salary_min: int
    salary_max: int
    location: str
    exp: int
    skills: List[Tuple[str, str, bool, float]]


class CandidateData(TypedDict):
    email: str
    name: str
    phone: str
    pos: str
    salary: int
    exp: int
    address: str
    avatar: str
    summary: str
    skills: List[Tuple[str, str, int]]
    edu: Tuple[str, str, str, int, int, float]
    experiences: List[Tuple[str, str, date, Optional[date], bool, str]]


class Command(BaseCommand):
    help = 'Seeds initial sample data for SmartJob into PostgreSQL database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('🌱 Bắt đầu tạo dữ liệu mẫu cho SmartJob...'))

        # 0. KHỞI TẠO CÁC KỸ NĂNG CHUẨN NẾU THIẾU
        essential_skills = [
            ('Python', 'Programming Language'),
            ('Django', 'Backend Framework'),
            ('PostgreSQL', 'Database'),
            ('Docker', 'DevOps'),
            ('REST API', 'API Development'),
            ('Machine Learning', 'AI/ML'),
            ('Natural Language Processing', 'AI/ML'),
            ('Deep Learning', 'AI/ML'),
            ('Data Analysis', 'Data Science'),
            ('JavaScript', 'Programming Language'),
            ('TypeScript', 'Programming Language'),
            ('React', 'Frontend Framework'),
            ('HTML/CSS', 'Web Development'),
            ('UI/UX Design', 'Design'),
            ('Kubernetes', 'DevOps'),
            ('AWS', 'Cloud Platform'),
            ('CI/CD', 'DevOps'),
            ('Linux', 'DevOps'),
            ('Git', 'Version Control')
        ]
        for sname, cat in essential_skills:
            Skills.objects.get_or_create(
                skill_name=sname,
                defaults={'category': cat, 'description': f'Kỹ năng {sname}'}
            )

        skills_cache = {s.skill_name.lower(): s for s in Skills.objects.all()}

        # 1. TẠO CÁC CÔNG TY MẪU
        companies_data: List[CompanyData] = [
            {
                'email': 'hr@fpt.com',
                'name': 'FPT Software',
                'industry': 'Information Technology',
                'size': '10000+ nhân viên',
                'address': 'Khu Công nghệ cao Hòa Lạc, Hà Nội',
                'phone': '02473007373',
                'website': 'https://fptsoftware.com',
                'logo': 'https://images.unsplash.com/photo-1549923746-c502d488b3ea?w=128&q=80',
                'desc': 'Tập đoàn công nghệ hàng đầu Việt Nam cung cấp dịch vụ chuyển đổi số toàn cầu.'
            },
            {
                'email': 'recruitment@vng.com.vn',
                'name': 'VNG Corporation',
                'industry': 'Internet & Software',
                'size': '1000-5000 nhân viên',
                'address': 'Khu chế xuất Tân Thuận, Quận 7, TP. HCM',
                'phone': '02839623888',
                'website': 'https://vng.com.vn',
                'logo': 'https://images.unsplash.com/photo-1551836022-d5d88e9218df?w=128&q=80',
                'desc': 'Kỳ lân công nghệ đầu tiên tại Việt Nam với hệ sinh thái Zalo, Zing, VNG Cloud.'
            },
            {
                'email': 'careers@viettel.vn',
                'name': 'Viettel Solutions',
                'industry': 'Telecommunications & IT',
                'size': '5000-10000 nhân viên',
                'address': 'Số 1 Trần Hữu Dực, Nam Từ Liêm, Hà Nội',
                'phone': '02462660198',
                'website': 'https://viettelsolutions.vn',
                'logo': 'https://images.unsplash.com/photo-1572021335469-31706a17aaef?w=128&q=80',
                'desc': 'Tổng công ty giải pháp doanh nghiệp Viettel tiên phong triển khai Cloud, AI và Big Data.'
            }
        ]

        created_companies = []
        for comp_data in companies_data:
            user, _ = Users.objects.update_or_create(
                email=comp_data['email'],
                defaults={
                    'password_hash': make_password('123456'),
                    'user_type': 'company',
                    'is_active': True
                }
            )
            company, _ = Companies.objects.update_or_create(
                user=user,
                defaults={
                    'company_name': comp_data['name'],
                    'industry': comp_data['industry'],
                    'company_size': comp_data['size'],
                    'address': comp_data['address'],
                    'phone': comp_data['phone'],
                    'website': comp_data['website'],
                    'logo_url': comp_data['logo'],
                    'description': comp_data['desc']
                }
            )
            created_companies.append(company)

        self.stdout.write(self.style.SUCCESS(f'✅ Đã tạo/cập nhật {len(created_companies)} công ty mẫu.'))

        # 2. TẠO CÁC TIN TUYỂN DỤNG MẪU
        jobs_data: List[JobData] = [
            {
                'company': created_companies[0],
                'title': 'Senior Python / Django Backend Developer',
                'desc': 'Phát triển hệ thống microservices và REST API phục vụ hàng triệu người dùng toàn cầu.',
                'req': 'Ít nhất 3 năm kinh nghiệm với Python, Django/FastAPI, cơ sở dữ liệu PostgreSQL.',
                'benefits': 'Lương tháng 13, thưởng dự án, bảo hiểm sức khỏe quốc tế, trợ cấp học chứng chỉ AWS.',
                'level': 'Senior',
                'type': 'full-time',
                'salary_min': 25000000,
                'salary_max': 45000000,
                'location': 'Hà Nội',
                'exp': 3,
                'skills': [
                    ('Python', 'advanced', True, 1.5),
                    ('Django', 'advanced', True, 1.2),
                    ('PostgreSQL', 'intermediate', True, 1.0),
                    ('Docker', 'intermediate', False, 0.8),
                    ('REST API', 'advanced', True, 1.0)
                ]
            },
            {
                'company': created_companies[1],
                'title': 'AI / Machine Learning Engineer',
                'desc': 'Nghiên cứu và triển khai mô hình gợi ý (Recommendation System) và xử lý ngôn ngữ tự nhiên NLP.',
                'req': 'Có kiến thức vững về Machine Learning, Deep Learning, kinh nghiệm với PyTorch/TensorFlow.',
                'benefits': 'Môi trường trẻ trung, văn phòng chuẩn Silicon Valley, thưởng hiệu suất hàng quý.',
                'level': 'Middle',
                'type': 'full-time',
                'salary_min': 22000000,
                'salary_max': 38000000,
                'location': 'TP. Hồ Chí Minh',
                'exp': 2,
                'skills': [
                    ('Python', 'advanced', True, 1.5),
                    ('Machine Learning', 'advanced', True, 1.5),
                    ('Natural Language Processing', 'intermediate', True, 1.2),
                    ('Deep Learning', 'intermediate', False, 1.0),
                    ('Data Analysis', 'intermediate', False, 0.8)
                ]
            },
            {
                'company': created_companies[2],
                'title': 'Frontend Developer (React & TypeScript)',
                'desc': 'Xây dựng giao diện Dashboard và hệ thống quản trị dữ liệu lớn cho các doanh nghiệp chuyển đổi số.',
                'req': 'Thành thạo React, TypeScript, HTML/CSS, REST API. Tối ưu trải nghiệm UI/UX tốt.',
                'benefits': 'Lương cạnh tranh, lộ trình thăng tiến rõ ràng, chế độ đãi ngộ hàng đầu ngành viễn thông.',
                'level': 'Junior / Middle',
                'type': 'full-time',
                'salary_min': 15000000,
                'salary_max': 28000000,
                'location': 'Hà Nội',
                'exp': 1,
                'skills': [
                    ('JavaScript', 'advanced', True, 1.2),
                    ('TypeScript', 'intermediate', True, 1.2),
                    ('React', 'advanced', True, 1.5),
                    ('HTML/CSS', 'advanced', True, 1.0),
                    ('UI/UX Design', 'beginner', False, 0.6)
                ]
            },
            {
                'company': created_companies[0],
                'title': 'DevOps Cloud Engineer (AWS / Kubernetes)',
                'desc': 'Thiết lập pipeline CI/CD, tự động hóa hạ tầng đám mây trên AWS và cụm Kubernetes.',
                'req': 'Có kinh nghiệm triển khai Docker, Kubernetes, CI/CD và hạ tầng đám mây.',
                'benefits': 'Thưởng theo dự án nước ngoài, cơ hội onsite Nhật Bản, Mỹ.',
                'level': 'Senior',
                'type': 'full-time',
                'salary_min': 30000000,
                'salary_max': 55000000,
                'location': 'Đà Nẵng',
                'exp': 4,
                'skills': [
                    ('Docker', 'advanced', True, 1.5),
                    ('Kubernetes', 'advanced', True, 1.5),
                    ('AWS', 'advanced', True, 1.3),
                    ('CI/CD', 'advanced', True, 1.2),
                    ('Linux', 'intermediate', False, 0.8)
                ]
            }
        ]

        created_jobs = []
        for jdata in jobs_data:
            job, _ = Jobs.objects.update_or_create(
                company=jdata['company'],
                job_title=jdata['title'],
                defaults={
                    'job_description': jdata['desc'],
                    'requirements': jdata['req'],
                    'benefits': jdata['benefits'],
                    'position_level': jdata['level'],
                    'employment_type': jdata['type'],
                    'salary_min': jdata['salary_min'],
                    'salary_max': jdata['salary_max'],
                    'location': jdata['location'],
                    'years_of_experience_required': jdata['exp'],
                    'status': 'active',
                    'view_count': 25
                }
            )
            created_jobs.append(job)

            # Thêm job skills (dùng cast để bảo đảm kiểu cho Pyrefly/Pyright)
            job_skills_list = cast(List[Tuple[str, str, bool, float]], jdata['skills'])
            for sname, level, is_req, weight in job_skills_list:
                skill_obj = skills_cache.get(sname.lower())
                if not skill_obj:
                    skill_obj, _ = Skills.objects.get_or_create(
                        skill_name=sname,
                        defaults={'category': 'General'}
                    )
                    skills_cache[sname.lower()] = skill_obj
                JobSkills.objects.update_or_create(
                    job=job,
                    skill=skill_obj,
                    defaults={
                        'required_level': level,
                        'is_required': is_req,
                        'weight': weight
                    }
                )

        self.stdout.write(self.style.SUCCESS(f'✅ Đã tạo/cập nhật {len(created_jobs)} tin tuyển dụng mẫu.'))

        # 3. TẠO CÁC ỨNG VIÊN MẪU
        candidates_data: List[CandidateData] = [
            {
                'email': 'nguyen.vana@gmail.com',
                'name': 'Nguyễn Văn An',
                'phone': '0912345678',
                'pos': 'Python Backend Developer',
                'salary': 30000000,
                'exp': 3,
                'address': 'Cầu Giấy, Hà Nội',
                'avatar': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=128&q=80',
                'summary': 'Lập trình viên Backend với 3 năm kinh nghiệm thiết kế kiến trúc RESTful API, PostgreSQL và hệ thống chịu tải cao.',
                'skills': [
                    ('Python', 'advanced', 3),
                    ('Django', 'advanced', 3),
                    ('PostgreSQL', 'advanced', 3),
                    ('Docker', 'intermediate', 2),
                    ('Git', 'advanced', 3),
                    ('REST API', 'advanced', 3)
                ],
                'edu': ('Đại học Bách Khoa Hà Nội', 'Kỹ sư', 'Công nghệ Thông tin', 2018, 2023, 3.4),
                'experiences': [
                    ('Công ty Công nghệ Alpha', 'Backend Developer', date(2023, 7, 1), None, True, 'Phát triển backend Django REST API')
                ]
            },
            {
                'email': 'tran.thib@gmail.com',
                'name': 'Trần Thị Bích',
                'phone': '0987654321',
                'pos': 'AI / Data Scientist',
                'salary': 28000000,
                'exp': 2,
                'address': 'Quận 1, TP. HCM',
                'avatar': 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=128&q=80',
                'summary': 'Đam mê nghiên cứu và áp dụng các mô hình Machine Learning, Xử lý ngôn ngữ tự nhiên NLP vào bài toán thực tiễn.',
                'skills': [
                    ('Python', 'advanced', 2),
                    ('Machine Learning', 'advanced', 2),
                    ('Natural Language Processing', 'intermediate', 2),
                    ('Data Analysis', 'advanced', 2),
                    ('Deep Learning', 'intermediate', 1)
                ],
                'edu': ('Đại học Quốc Gia TP. HCM', 'Cử nhân', 'Khoa học Máy tính', 2019, 2023, 3.6),
                'experiences': [
                    ('DataLab Studio', 'Junior AI Engineer', date(2023, 6, 1), None, True, 'Huấn luyện mô hình phân loại dữ liệu và NLP')
                ]
            },
            {
                'email': 'le.quocv@gmail.com',
                'name': 'Lê Quốc Việt',
                'phone': '0905123456',
                'pos': 'Frontend Developer',
                'salary': 20000000,
                'exp': 2,
                'address': 'Hải Châu, Đà Nẵng',
                'avatar': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=128&q=80',
                'summary': 'Frontend developer yêu thích xây dựng giao diện hiện đại, mượt mà và tối ưu hiệu năng.',
                'skills': [
                    ('JavaScript', 'advanced', 2),
                    ('TypeScript', 'intermediate', 1),
                    ('React', 'advanced', 2),
                    ('HTML/CSS', 'advanced', 2),
                    ('UI/UX Design', 'intermediate', 1)
                ],
                'edu': ('Đại học Bách Khoa Đà Nẵng', 'Kỹ sư', 'Kỹ thuật Phần mềm', 2019, 2023, 3.2),
                'experiences': [
                    ('TechWave Da Nang', 'Frontend Developer', date(2023, 8, 1), None, True, 'Lập trình ứng dụng Web ReactJS')
                ]
            }
        ]

        created_candidates = []
        for cand_data in candidates_data:
            user, _ = Users.objects.update_or_create(
                email=cand_data['email'],
                defaults={
                    'password_hash': make_password('123456'),
                    'user_type': 'candidate',
                    'is_active': True
                }
            )
            candidate, _ = Candidates.objects.update_or_create(
                user=user,
                defaults={
                    'full_name': cand_data['name'],
                    'phone': cand_data['phone'],
                    'desired_position': cand_data['pos'],
                    'desired_salary': cand_data['salary'],
                    'years_of_experience': cand_data['exp'],
                    'address': cand_data['address'],
                    'avatar_url': cand_data['avatar'],
                    'summary': cand_data['summary']
                }
            )
            created_candidates.append(candidate)

            # Thêm kỹ năng (dùng cast để bảo đảm kiểu cho Pyrefly/Pyright)
            cand_skills = cast(List[Tuple[str, str, int]], cand_data['skills'])
            for sname, level, years in cand_skills:
                skill_obj = skills_cache.get(sname.lower())
                if not skill_obj:
                    skill_obj, _ = Skills.objects.get_or_create(
                        skill_name=sname,
                        defaults={'category': 'General'}
                    )
                    skills_cache[sname.lower()] = skill_obj
                CandidateSkills.objects.update_or_create(
                    candidate=candidate,
                    skill=skill_obj,
                    defaults={'proficiency_level': level, 'years_of_experience': years}
                )

            # Thêm học vấn
            inst, deg, maj, s_year, e_year, gpa = cast(Tuple[str, str, str, int, int, float], cand_data['edu'])
            Education.objects.update_or_create(
                candidate=candidate,
                institution_name=inst,
                defaults={
                    'degree': deg,
                    'major': maj,
                    'start_date': date(s_year, 9, 1),
                    'end_date': date(e_year, 6, 30),
                    'gpa': gpa
                }
            )

            # Thêm kinh nghiệm (dùng cast để bảo đảm kiểu cho Pyrefly/Pyright)
            cand_experiences = cast(List[Tuple[str, str, date, Optional[date], bool, str]], cand_data['experiences'])
            for comp, pos, s_date, e_date, is_curr, resp in cand_experiences:
                Experience.objects.update_or_create(
                    candidate=candidate,
                    company_name=comp,
                    position=pos,
                    defaults={
                        'start_date': s_date,
                        'end_date': e_date,
                        'is_current': is_curr,
                        'responsibilities': resp
                    }
                )

        self.stdout.write(self.style.SUCCESS(f'✅ Đã tạo/cập nhật {len(created_candidates)} ứng viên mẫu.'))

        # 4. TẠO CÁC ĐƠN ỨNG TUYỂN VÀ CHẠY AI MATCHING
        app_samples = [
            (created_jobs[0], created_candidates[0], 'reviewing', 'Em rất hào hứng với cơ hội trở thành Backend Developer tại FPT Software.'),
            (created_jobs[1], created_candidates[1], 'shortlisted', 'Với kinh nghiệm NLP và Machine Learning, em tự tin sẽ đóng góp tốt cho dự án.'),
            (created_jobs[2], created_candidates[2], 'interviewed', 'Em mong muốn được phát triển giao diện người dùng chuyên nghiệp cho Viettel.')
        ]

        for job, cand, st, letter in app_samples:
            Applications.objects.update_or_create(
                job=job,
                candidate=cand,
                defaults={'status': st, 'cover_letter': letter}
            )
            # Tính toán và lưu AI Matching score
            calculate_match(cand, job, save_to_db=True)

            # Tạo lượt xem mẫu
            if not JobViews.objects.filter(job=job, candidate=cand).exists():
                JobViews.objects.create(
                    job=job,
                    candidate=cand,
                    ip_address='127.0.0.1',
                    user_agent='Mozilla/5.0'
                )

        self.stdout.write(self.style.SUCCESS('🎉 Hoàn thành nạp dữ liệu mẫu cho SmartJob thành công!'))


if __name__ == '__main__':
    Command().handle()
