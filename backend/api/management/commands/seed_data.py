from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import date, timedelta
from api.models import (
    Users, Candidates, Companies, Skills, CandidateSkills,
    Education, Experience, Jobs, JobSkills, Applications,
    JobViews
)
from api.ai_matching_service import calculate_match


class Command(BaseCommand):
    help = 'Seeds initial sample data for SmartJob (Companies, Jobs, Candidates, Applications)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('🌱 Bắt đầu tạo dữ liệu mẫu cho SmartJob...'))

        # 1. TẠO CÁC CÔNG TY MẪU
        companies_data = [
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
        for cdata in companies_data:
            user, u_created = Users.objects.get_or_create(
                email=cdata['email'],
                defaults={
                    'password_hash': make_password('123456'),
                    'user_type': 'company',
                    'is_active': True
                }
            )
            company, comp_created = Companies.objects.get_or_create(
                user=user,
                defaults={
                    'company_name': cdata['name'],
                    'industry': cdata['industry'],
                    'company_size': cdata['size'],
                    'address': cdata['address'],
                    'phone': cdata['phone'],
                    'website': cdata['website'],
                    'logo_url': cdata['logo'],
                    'description': cdata['desc']
                }
            )
            created_companies.append(company)

        self.stdout.write(self.style.SUCCESS(f'✅ Đã tạo/cập nhật {len(created_companies)} công ty mẫu.'))

        # 2. TẠO CÁC TIN TUYỂN DỤNG MẪU
        skills_cache = {s.skill_name.lower(): s for s in Skills.objects.all()}

        jobs_data = [
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
            job, created = Jobs.objects.get_or_create(
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

            # Thêm job skills
            for sname, level, is_req, weight in jdata['skills']:
                skill_obj = skills_cache.get(sname.lower())
                if skill_obj:
                    JobSkills.objects.get_or_create(
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
        candidates_data = [
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
        for cdata in candidates_data:
            user, u_created = Users.objects.get_or_create(
                email=cdata['email'],
                defaults={
                    'password_hash': make_password('123456'),
                    'user_type': 'candidate',
                    'is_active': True
                }
            )
            candidate, cand_created = Candidates.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': cdata['name'],
                    'phone': cdata['phone'],
                    'desired_position': cdata['pos'],
                    'desired_salary': cdata['salary'],
                    'years_of_experience': cdata['exp'],
                    'address': cdata['address'],
                    'avatar_url': cdata['avatar'],
                    'summary': cdata['summary']
                }
            )
            created_candidates.append(candidate)

            # Thêm kỹ năng
            for sname, level, years in cdata['skills']:
                skill_obj = skills_cache.get(sname.lower())
                if skill_obj:
                    CandidateSkills.objects.get_or_create(
                        candidate=candidate,
                        skill=skill_obj,
                        defaults={'proficiency_level': level, 'years_of_experience': years}
                    )

            # Thêm học vấn
            inst, deg, maj, s_year, e_year, gpa = cdata['edu']
            Education.objects.get_or_create(
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

            # Thêm kinh nghiệm
            for comp, pos, s_date, e_date, is_curr, resp in cdata['experiences']:
                Experience.objects.get_or_create(
                    candidate=candidate,
                    company_name=comp,
                    defaults={
                        'position': pos,
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
            Applications.objects.get_or_create(
                job=job,
                candidate=cand,
                defaults={'status': st, 'cover_letter': letter}
            )
            # Tính toán và lưu AI Matching score
            calculate_match(cand, job, save_to_db=True)

            # Tạo lượt xem mẫu
            JobViews.objects.get_or_create(
                job=job,
                candidate=cand,
                defaults={'ip_address': '127.0.0.1', 'user_agent': 'Mozilla/5.0'}
            )

        self.stdout.write(self.style.SUCCESS('🎉 Hoàn thành nạp dữ liệu mẫu cho SmartJob thành công!'))
