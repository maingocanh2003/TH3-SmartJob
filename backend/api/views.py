from datetime import date, timedelta
from rest_framework import viewsets, status, filters
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Count, Avg, Q, F
from django.db.models.functions import TruncDate
from django.contrib.auth.hashers import make_password, check_password
from django.core import signing
from django.utils import timezone

from .models import (
    Users, Candidates, Companies, Skills, CandidateSkills,
    Education, Experience, Jobs, JobSkills, Applications,
    AiMatchResults, JobViews, SavedJobs
)
from .serializers import (
    UserSerializer, CandidateSerializer, CompanySerializer,
    SkillSerializer, CandidateSkillSerializer, EducationSerializer,
    ExperienceSerializer, JobSerializer, JobSkillSerializer,
    ApplicationSerializer, SavedJobSerializer, AiMatchResultSerializer
)
from .ai_matching_service import (
    calculate_match, get_recommended_jobs_for_candidate, get_recommended_candidates_for_job,
    extract_skills_service, parse_cv_service, stateless_recommend_jobs_for_cv_text,
    get_ai_evaluation_metrics, extract_text_from_file, process_and_save_candidate_cv
)


STATUS_NORMALIZE_MAP = {
    'pending': 'pending',
    'received': 'pending',
    'reviewing': 'reviewing',
    'reviewed': 'reviewing',
    'shortlisted': 'reviewing',
    'interview': 'interviewed',
    'interviewed': 'interviewed',
    'offered': 'offered',
    'accepted': 'offered',
    'hired': 'offered',
    'rejected': 'rejected',
    'withdrawn': 'withdrawn',
}


# ==============================================================================
# AUTHENTICATION VIEWS
# ==============================================================================

class AuthViewSet(viewsets.ViewSet):
    """
    User registration, login, and profile lookup
    """
    @action(detail=False, methods=['post'])
    def register(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        user_type = request.data.get('user_type', 'candidate')
        full_name = request.data.get('full_name', '')
        company_name = request.data.get('company_name', '')

        if not email or not password:
            return Response({'error': 'Email và mật khẩu là bắt buộc.'}, status=status.HTTP_400_BAD_REQUEST)

        if user_type not in ('candidate', 'company'):
            return Response({'error': 'Loại tài khoản không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

        if Users.objects.filter(email=email).exists():
            return Response({'error': 'Email này đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)

        user = Users.objects.create(
            email=email,
            password_hash=make_password(password),
            user_type=user_type,
            is_active=True
        )

        if user_type == 'candidate':
            candidate = Candidates.objects.create(
                user=user,
                full_name=full_name or email.split('@')[0]
            )
            profile_data = {'candidate_id': candidate.candidate_id, 'full_name': candidate.full_name}
        elif user_type == 'company':
            company = Companies.objects.create(
                user=user,
                company_name=company_name or full_name or email.split('@')[0]
            )
            profile_data = {'company_id': company.company_id, 'company_name': company.company_name, 'full_name': company.company_name}
        else:
            profile_data = {}

        token = signing.dumps(user.user_id, salt='smartjob.api.auth')
        user_data = UserSerializer(user).data

        return Response({
            'message': 'Đăng ký tài khoản thành công!',
            'token': token,
            'user': user_data,
            'profile': profile_data,
            **user_data,
            **profile_data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def login(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')

        if not email or not password:
            return Response({'error': 'Email và mật khẩu là bắt buộc.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            return Response({'error': 'Email hoặc mật khẩu không chính xác.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, user.password_hash):
            return Response({'error': 'Email hoặc mật khẩu không chính xác.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'error': 'Tài khoản đã bị khóa.'}, status=status.HTTP_403_FORBIDDEN)

        profile_data = {}
        if user.user_type == 'candidate':
            cand = Candidates.objects.filter(user=user).first()
            if not cand:
                cand = Candidates.objects.create(user=user, full_name=email.split('@')[0])
            profile_data = {'candidate_id': cand.candidate_id, 'full_name': cand.full_name}
        elif user.user_type == 'company':
            comp = Companies.objects.filter(user=user).first()
            if not comp:
                comp = Companies.objects.create(user=user, company_name=email.split('@')[0])
            profile_data = {'company_id': comp.company_id, 'company_name': comp.company_name, 'full_name': comp.company_name}

        return Response({
            'message': 'Đăng nhập thành công!',
            'token': signing.dumps(user.user_id, salt='smartjob.api.auth'),
            **UserSerializer(user).data,
            **profile_data,
        })


# ==============================================================================
# SKILLS VIEWS
# ==============================================================================

class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skills.objects.all().order_by('category', 'skill_name')
    serializer_class = SkillSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['skill_name', 'category']

    @action(detail=False, methods=['get'])
    def categories(self, request):
        cats = Skills.objects.values_list('category', flat=True).distinct().order_by('category')
        return Response([c for c in cats if c])


# ==============================================================================
# CANDIDATES VIEWS
# ==============================================================================

class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidates.objects.all().select_related('user').order_by('candidate_id')
    serializer_class = CandidateSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'desired_position', 'address']

    @action(detail=True, methods=['get', 'post'])
    def skills(self, request, pk=None):
        candidate = self.get_object()
        if request.method == 'GET':
            skills = CandidateSkills.objects.filter(candidate=candidate).select_related('skill')
            return Response(CandidateSkillSerializer(skills, many=True).data)

        skill_id = request.data.get('skill_id')
        level = request.data.get('proficiency_level', 'intermediate')
        years = request.data.get('years_of_experience', 1)

        try:
            skill = Skills.objects.get(pk=skill_id)
        except Skills.DoesNotExist:
            return Response({'error': 'Kỹ năng không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

        cand_skill, created = CandidateSkills.objects.update_or_create(
            candidate=candidate,
            skill=skill,
            defaults={'proficiency_level': level, 'years_of_experience': years}
        )
        return Response(CandidateSkillSerializer(cand_skill).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='skills/(?P<skill_id>[^/.]+)')
    def remove_skill(self, request, pk=None, skill_id=None):
        candidate = self.get_object()
        CandidateSkills.objects.filter(candidate=candidate, skill_id=skill_id).delete()
        return Response({'message': 'Đã xóa kỹ năng khỏi hồ sơ.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        """Lấy danh sách công việc gợi ý bởi AI cho ứng viên này"""
        candidate = self.get_object()
        limit = int(request.query_params.get('limit', 10))
        min_score = float(request.query_params.get('min_score', 0.0))
        location = request.query_params.get('location', None)
        recommendations = get_recommended_jobs_for_candidate(
            candidate, limit=limit, min_score=min_score, location=location
        )
        return Response(recommendations)

    @action(detail=True, methods=['get'], url_path='ai-analysis')
    def ai_analysis(self, request, pk=None):
        """
        Phân tích toàn diện CV & Hồ sơ ứng viên bằng AI:
        - Đánh giá mức độ hoàn thiện hồ sơ (Completeness score & checklist)
        - Đánh giá kỹ năng (theo nhóm, mức độ thành thạo, đối sánh nhu cầu thị trường)
        - Đánh giá kinh nghiệm & học vấn
        - Đề xuất cải thiện hồ sơ & kỹ năng còn thiếu
        """
        candidate = self.get_object()
        skills_qs = CandidateSkills.objects.filter(candidate=candidate).select_related('skill')
        edu_qs = Education.objects.filter(candidate=candidate).order_by('-start_date')
        recs = get_recommended_jobs_for_candidate(candidate, limit=10)

        # 1. Checklist & Mức độ hoàn thiện hồ sơ
        skill_count = skills_qs.count()
        has_edu = edu_qs.exists()
        has_exp = (candidate.years_of_experience is not None and candidate.years_of_experience >= 0)
        has_summary = bool(candidate.summary and len(candidate.summary.strip()) >= 20)
        has_cv = bool(candidate.cv_file_url)
        has_position = bool(candidate.desired_position and candidate.desired_position.strip())
        has_contact = bool(candidate.phone and candidate.address)
        has_name = bool(candidate.full_name and candidate.full_name not in ('Ứng viên', 'Ứng viên Tiềm năng'))

        checklist = [
            {
                'key': 'cv_file',
                'label': 'Tệp CV gốc đã đăng tải',
                'completed': has_cv,
                'weight': 20,
                'detail': candidate.cv_file_url.split('/')[-1] if has_cv else 'Chưa tải lên tệp CV',
                'tip': 'Tải lên bản CV định dạng PDF/DOCX để hệ thống AI bóc tách dữ liệu chuẩn xác nhất.'
            },
            {
                'key': 'full_name_pos',
                'label': 'Họ tên & Vị trí ứng tuyển mục tiêu',
                'completed': has_name and has_position,
                'weight': 15,
                'detail': f"{candidate.full_name} — {candidate.desired_position or 'Chưa rõ vị trí'}",
                'tip': 'Ghi rõ chức danh/vị trí ứng tuyển ở đầu CV (VD: Senior Python Backend Developer).'
            },
            {
                'key': 'contact',
                'label': 'Thông tin liên hệ (Email, SĐT, Địa chỉ)',
                'completed': has_contact,
                'weight': 10,
                'detail': f"{candidate.phone or 'Thiếu SĐT'} · {candidate.address or 'Thiếu địa chỉ'}",
                'tip': 'Đảm bảo CV có đầy đủ Số điện thoại, Email và Khu vực làm việc.'
            },
            {
                'key': 'skills',
                'label': 'Kỹ năng chuyên môn (Tối thiểu 5 kỹ năng)',
                'completed': skill_count >= 5,
                'weight': 25,
                'detail': f"Đã nhận diện {skill_count} kỹ năng công nghệ từ CV",
                'tip': 'Liệt kê đầy đủ ngôn ngữ lập trình, framework, cơ sở dữ liệu và công cụ DevOps trong CV.'
            },
            {
                'key': 'experience',
                'label': 'Kinh nghiệm làm việc thực tế',
                'completed': has_exp and (candidate.years_of_experience or 0) > 0,
                'weight': 15,
                'detail': f"{candidate.years_of_experience or 0} năm kinh nghiệm",
                'tip': 'Nêu rõ số năm kinh nghiệm cùng các dự án, trách nhiệm và thành tựu định lượng.'
            },
            {
                'key': 'education',
                'label': 'Trình độ học vấn & Chuyên ngành',
                'completed': has_edu,
                'weight': 10,
                'detail': f"{edu_qs.first().major or edu_qs.first().degree} - {edu_qs.first().institution_name}" if has_edu else 'Chưa có thông tin học vấn',
                'tip': 'Bổ sung bằng cấp (Cử nhân/Kỹ sư/Thạc sĩ), chuyên ngành và tên trường đại học.'
            },
            {
                'key': 'summary',
                'label': 'Tóm tắt mục tiêu & Năng lực cốt lõi',
                'completed': has_summary,
                'weight': 5,
                'detail': 'Đã có đoạn tóm tắt chuyên môn' if has_summary else 'Chưa có tóm tắt bản thân',
                'tip': 'Viết 2-3 câu tóm tắt điểm mạnh nổi bật và định hướng nghề nghiệp ở phần mở đầu CV.'
            }
        ]

        completeness_score = sum(item['weight'] for item in checklist if item['completed'])
        if 0 < skill_count < 5:
            completeness_score += int(25 * (skill_count / 5.0))
        completeness_score = min(100, completeness_score)

        if completeness_score >= 85:
            completeness_level = 'Hồ sơ Rất Hoàn Thiện'
        elif completeness_score >= 65:
            completeness_level = 'Hồ sơ Khá Tốt'
        else:
            completeness_level = 'Cần Bổ Sung Thông Tin'

        # 2. Phân tích kỹ năng theo danh mục & mức độ
        by_category = {}
        by_level = {'expert': 0, 'advanced': 0, 'intermediate': 0, 'beginner': 0}
        candidate_skill_names = set()

        for cs in skills_qs:
            cat = cs.skill.category or 'Khác'
            s_name = cs.skill.skill_name
            lvl = (cs.proficiency_level or 'intermediate').lower()
            candidate_skill_names.add(s_name.lower())
            by_category.setdefault(cat, []).append({
                'skill_name': s_name,
                'proficiency_level': lvl,
                'years_of_experience': cs.years_of_experience or candidate.years_of_experience or 1
            })
            if lvl in by_level:
                by_level[lvl] += 1
            else:
                by_level['intermediate'] += 1

        # Đối sánh với nhu cầu thị trường & các việc làm gợi ý
        missing_freq = {}
        matched_freq = {}
        scores = []
        for r in recs:
            sc = float(r.get('matching_score') or r.get('match_score') or 0)
            scores.append(sc)
            for ms in (r.get('matched_skills') or r.get('details', {}).get('matched_skills') or []):
                name = ms if isinstance(ms, str) else ms.get('skill_name', '')
                if name:
                    matched_freq[name] = matched_freq.get(name, 0) + 1
            for mis in (r.get('missing_skills') or r.get('details', {}).get('missing_skills') or []):
                name = mis if isinstance(mis, str) else mis.get('skill_name', '')
                if name:
                    missing_freq[name] = missing_freq.get(name, 0) + 1

        # Bổ sung thêm từ top kỹ năng thị trường nếu cần
        market_top = (
            JobSkills.objects
            .values('skill__skill_name', 'skill__category')
            .annotate(cnt=Count('job_id'))
            .order_by('-cnt')[:12]
        )
        for mt in market_top:
            s_name = mt['skill__skill_name']
            if s_name.lower() not in candidate_skill_names and s_name not in missing_freq:
                missing_freq[s_name] = mt['cnt']

        recommended_missing_skills = [
            {'skill_name': k, 'job_count': v}
            for k, v in sorted(missing_freq.items(), key=lambda x: x[1], reverse=True)[:8]
        ]
        strong_matched_skills = [
            {'skill_name': k, 'job_count': v}
            for k, v in sorted(matched_freq.items(), key=lambda x: x[1], reverse=True)[:8]
        ]

        # 3. Đánh giá kinh nghiệm
        years = candidate.years_of_experience or 0
        if years >= 5:
            seniority = 'Senior / Chuyên gia cao cấp'
        elif years >= 3:
            seniority = 'Mid-Senior / Có kinh nghiệm vững'
        elif years >= 1:
            seniority = 'Junior / Đã có kinh nghiệm thực tế'
        else:
            seniority = 'Fresher / Mới tốt nghiệp'

        avg_market_exp = Jobs.objects.filter(status='active').aggregate(avg=Avg('years_of_experience_required'))['avg'] or 2.5

        # 4. Đề xuất cải thiện thông minh
        suggestions = []
        if recommended_missing_skills:
            top_mis_names = ', '.join(x['skill_name'] for x in recommended_missing_skills[:4])
            suggestions.append({
                'priority': 'high',
                'category': 'Bổ sung Kỹ năng',
                'title': f'Bổ sung các kỹ năng đang thiếu so với JD thị trường: {top_mis_names}',
                'description': f'Phân tích AI trên các tin tuyển dụng phù hợp cho thấy nếu bạn bổ sung hoặc nêu rõ kinh nghiệm làm việc với {top_mis_names} trong CV, điểm Matching trung bình có thể tăng thêm 15% - 25%.'
            })

        if skill_count < 6:
            suggestions.append({
                'priority': 'high',
                'category': 'Tối ưu từ khóa CV (ATS)',
                'title': 'Mở rộng danh sách kỹ năng công nghệ & công cụ trong CV',
                'description': 'CV hiện tại mới chỉ trích xuất được ít kỹ năng. Hãy liệt kê chi tiết thêm các thư viện, cơ sở dữ liệu (PostgreSQL, Redis), công cụ quản lý mã nguồn (Git, CI/CD, Docker) mà bạn đã từng sử dụng.'
            })

        if years < avg_market_exp:
            suggestions.append({
                'priority': 'medium',
                'category': 'Kinh nghiệm dự án',
                'title': 'Làm nổi bật các dự án thực tế & số liệu định lượng',
                'description': f'Số năm kinh nghiệm hiện tại ({years} năm) thấp hơn mức trung bình của một số vị trí Senior ({avg_market_exp:.1f} năm). Hãy mô tả chi tiết quy mô dự án, hiệu năng tối ưu hóa để tăng điểm tương thích ngữ nghĩa.'
            })
        else:
            suggestions.append({
                'priority': 'medium',
                'category': 'Kinh nghiệm & Vai trò',
                'title': 'Nhấn mạnh kinh nghiệm thiết kế kiến trúc hệ thống & dẫn dắt nhóm',
                'description': f'Với {years} năm kinh nghiệm ({seniority}), bạn hoàn toàn đủ điều kiện ứng tuyển các vị trí Senior/Lead. Hãy bổ sung các từ khóa như System Design, Microservices, Mentoring vào mô tả công việc trong CV.'
            })

        for item in checklist:
            if not item['completed']:
                suggestions.append({
                    'priority': 'medium',
                    'category': 'Hoàn thiện hồ sơ',
                    'title': f"Cập nhật mục: {item['label']}",
                    'description': item['tip']
                })

        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        best_score = round(max(scores), 1) if scores else 0.0
        high_match_count = sum(1 for s in scores if s >= 65)

        return Response({
            'candidate_id': candidate.candidate_id,
            'full_name': candidate.full_name,
            'desired_position': candidate.desired_position,
            'completeness': {
                'score': completeness_score,
                'level': completeness_level,
                'checklist': checklist,
            },
            'skill_analysis': {
                'total_skills': skill_count,
                'by_category': by_category,
                'by_level': by_level,
                'strong_matched_skills': strong_matched_skills,
                'recommended_missing_skills': recommended_missing_skills,
            },
            'experience_analysis': {
                'years_of_experience': years,
                'seniority_level': seniority,
                'market_avg_required_years': round(float(avg_market_exp), 1),
            },
            'matching_overview': {
                'total_jobs_analyzed': len(scores),
                'avg_match_score': avg_score,
                'best_match_score': best_score,
                'high_match_jobs_count': high_match_count,
            },
            'improvement_suggestions': suggestions,
        })

    @action(detail=True, methods=['post'], url_path='upload-cv', parser_classes=[MultiPartParser, FormParser, JSONParser])
    def upload_cv(self, request, pk=None):
        candidate = self.get_object()
        cv_file = request.FILES.get('cv_file')
        cv_text = request.data.get('cv_text', '')
        file_url = None

        if cv_file:
            cvs_dir = settings.MEDIA_ROOT / 'cvs'
            cvs_dir.mkdir(parents=True, exist_ok=True)
            safe_name = f"cv_{candidate.candidate_id}_{cv_file.name.replace(' ', '_')}"
            dest_path = cvs_dir / safe_name
            with open(dest_path, 'wb+') as dest:
                for chunk in cv_file.chunks():
                    dest.write(chunk)
            file_url = f"/media/cvs/{safe_name}"

            cv_file.seek(0)
            try:
                cv_text = extract_text_from_file(cv_file)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if not cv_text or len(cv_text.strip()) < 10:
            return Response(
                {'error': 'Không tìm thấy nội dung CV hợp lệ từ file hoặc văn bản tải lên.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = process_and_save_candidate_cv(candidate, cv_text, file_url=file_url)
            candidate.refresh_from_db()
            skills_qs = CandidateSkills.objects.filter(candidate=candidate).select_related('skill')
            return Response({
                'message': 'Đã tải lên và tự động trích xuất hồ sơ ứng viên thành công!',
                'candidate': CandidateSerializer(candidate).data,
                'extracted_profile': result['parsed'],
                'skills': CandidateSkillSerializer(skills_qs, many=True).data,
                'recommendations': result['recommendations']
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Lỗi khi xử lý hồ sơ: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==============================================================================
# COMPANIES VIEWS
# ==============================================================================

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Companies.objects.all().select_related('user').order_by('company_id')
    serializer_class = CompanySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['company_name', 'industry', 'address']

    @action(detail=True, methods=['get'])
    def jobs(self, request, pk=None):
        company = self.get_object()
        jobs = Jobs.objects.filter(company=company).order_by('-created_at', '-job_id')
        return Response(JobSerializer(jobs, many=True).data)


# ==============================================================================
# JOBS VIEWS
# ==============================================================================

class JobViewSet(viewsets.ModelViewSet):
    queryset = Jobs.objects.all().select_related('company').order_by('-created_at', '-job_id')
    serializer_class = JobSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['job_title', 'company__company_name', 'location', 'requirements']

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)

        company_id = self.request.query_params.get('company_id')
        if company_id:
            qs = qs.filter(company_id=company_id)

        industry = self.request.query_params.get('industry')
        if industry:
            qs = qs.filter(company__industry__icontains=industry)

        location = self.request.query_params.get('location')
        if location:
            qs = qs.filter(location__icontains=location)

        min_sal = self.request.query_params.get('min_salary')
        if min_sal:
            qs = qs.filter(salary_max__gte=min_sal)

        exp = self.request.query_params.get('experience')
        if exp:
            qs = qs.filter(years_of_experience_required__lte=exp)

        return qs

    def _normalize_job_payload(self, data, partial=False):
        payload = {}
        # Map title -> job_title
        if 'job_title' in data or 'title' in data:
            payload['job_title'] = (data.get('job_title') or data.get('title') or '').strip()
        # Map description -> job_description
        if 'job_description' in data or 'description' in data:
            payload['job_description'] = (data.get('job_description') or data.get('description') or '').strip()
        # Map employment_type / job_type
        if 'employment_type' in data or 'job_type' in data:
            emp = (data.get('employment_type') or data.get('job_type') or 'full-time').strip().lower().replace('_', '-')
            if emp not in ('full-time', 'part-time', 'contract', 'internship'):
                emp = 'full-time'
            payload['employment_type'] = emp
        elif not partial:
            payload['employment_type'] = 'full-time'

        # Map position_level / level
        if 'position_level' in data or 'level' in data:
            payload['position_level'] = data.get('position_level') or data.get('level') or 'Middle'

        # Map num_of_positions / slots
        if 'num_of_positions' in data or 'slots' in data:
            try:
                payload['num_of_positions'] = max(1, int(data.get('num_of_positions') or data.get('slots') or 1))
            except (ValueError, TypeError):
                payload['num_of_positions'] = 1

        # Map years_of_experience_required / experience_required
        if 'years_of_experience_required' in data or 'experience_required' in data:
            raw_exp = data.get('years_of_experience_required')
            if raw_exp is None:
                raw_exp = data.get('experience_required')
            exp_map = {'entry': 0, 'junior': 1, 'mid': 2, 'senior': 5, 'manager': 5}
            if isinstance(raw_exp, str) and raw_exp.lower() in exp_map:
                payload['years_of_experience_required'] = exp_map[raw_exp.lower()]
            else:
                try:
                    payload['years_of_experience_required'] = int(raw_exp)
                except (ValueError, TypeError):
                    payload['years_of_experience_required'] = 1

        # Map application_deadline / deadline
        if 'application_deadline' in data or 'deadline' in data:
            dl = data.get('application_deadline') or data.get('deadline')
            if dl:
                payload['application_deadline'] = str(dl)[:10]
            else:
                payload['application_deadline'] = None

        for field in ['requirements', 'benefits', 'location', 'salary_currency', 'status']:
            if field in data:
                payload[field] = data.get(field)

        for sal_field in ['salary_min', 'salary_max']:
            if sal_field in data:
                val = data.get(sal_field)
                payload[sal_field] = val if val not in ('', None) else None

        if 'company' in data and data.get('company'):
            payload['company'] = data.get('company')
        elif not partial:
            first_comp = Companies.objects.first()
            if first_comp:
                payload['company'] = first_comp.company_id

        return payload

    def _sync_job_skills(self, job, data):
        skill_ids = data.get('skill_ids')
        skill_names = data.get('skill_names')

        if isinstance(skill_ids, list):
            JobSkills.objects.filter(job=job).delete()
            for sid in skill_ids:
                skill_obj = Skills.objects.filter(pk=sid).first()
                if skill_obj:
                    JobSkills.objects.update_or_create(
                        job=job, skill=skill_obj,
                        defaults={'required_level': 'intermediate', 'is_required': True, 'weight': 1.0}
                    )
        elif isinstance(skill_names, list):
            JobSkills.objects.filter(job=job).delete()
            for sname in skill_names:
                sname_clean = str(sname).strip()
                if not sname_clean:
                    continue
                skill_obj = Skills.objects.filter(skill_name__iexact=sname_clean).first()
                if not skill_obj:
                    skill_obj = Skills.objects.create(skill_name=sname_clean, category='Technical')
                JobSkills.objects.update_or_create(
                    job=job, skill=skill_obj,
                    defaults={'required_level': 'intermediate', 'is_required': True, 'weight': 1.0}
                )
        elif not JobSkills.objects.filter(job=job).exists():
            # Tự động trích xuất kỹ năng từ JD nếu chưa có kỹ năng nào được chọn
            jd_text = f"{job.job_title} {job.job_description or ''} {job.requirements or ''}"
            extracted = extract_skills_service(jd_text)
            for s_info in extracted[:10]:
                s_name = s_info.get('skill_name', '').strip()
                if not s_name:
                    continue
                skill_obj = Skills.objects.filter(skill_name__iexact=s_name).first()
                if not skill_obj:
                    skill_obj = Skills.objects.create(
                        skill_name=s_name,
                        category=s_info.get('category', 'Technical')
                    )
                JobSkills.objects.update_or_create(
                    job=job, skill=skill_obj,
                    defaults={'required_level': s_info.get('proficiency_level', 'intermediate'), 'is_required': True, 'weight': 1.0}
                )

    def create(self, request, *args, **kwargs):
        payload = self._normalize_job_payload(request.data, partial=False)
        if not payload.get('application_deadline'):
            payload['application_deadline'] = (date.today() + timedelta(days=30)).isoformat()
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        job = serializer.save(created_at=timezone.now(), updated_at=timezone.now())
        self._sync_job_skills(job, request.data)
        return Response(self.get_serializer(job).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        payload = self._normalize_job_payload(request.data, partial=partial)
        serializer = self.get_serializer(instance, data=payload, partial=True)
        serializer.is_valid(raise_exception=True)
        job = serializer.save(updated_at=timezone.now())
        if 'skill_ids' in request.data or 'skill_names' in request.data:
            self._sync_job_skills(job, request.data)
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=['post', 'patch'])
    def extend(self, request, pk=None):
        """Gia hạn thời gian nộp hồ sơ cho tin tuyển dụng và kích hoạt lại tin"""
        job = self.get_object()
        new_deadline = request.data.get('application_deadline') or request.data.get('deadline')
        days = int(request.data.get('days', 30))

        if new_deadline:
            job.application_deadline = str(new_deadline)[:10]
        else:
            base_date = job.application_deadline if (job.application_deadline and job.application_deadline >= date.today()) else date.today()
            job.application_deadline = base_date + timedelta(days=days)

        job.status = 'active'
        job.updated_at = timezone.now()
        job.save()
        return Response({
            'message': f'Đã gia hạn tin tuyển dụng đến ngày {job.application_deadline}!',
            'job': JobSerializer(job).data
        })

    def retrieve(self, request, *args, **kwargs):
        job = self.get_object()
        cand_id = request.query_params.get('candidate_id')
        candidate = None
        if cand_id:
            candidate = Candidates.objects.filter(pk=cand_id).first()

        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        JobViews.objects.create(
            job=job,
            candidate=candidate,
            ip_address=ip,
            user_agent=user_agent
        )

        serializer = self.get_serializer(job)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def recommended_candidates(self, request, pk=None):
        """Lấy danh sách ứng viên AI gợi ý cho tin tuyển dụng này"""
        job = self.get_object()
        limit = int(request.query_params.get('limit', 10))
        min_score = float(request.query_params.get('min_score', 0.0))
        recommendations = get_recommended_candidates_for_job(job, limit=limit, min_score=min_score)
        return Response(recommendations)

    @action(detail=True, methods=['get', 'post'])
    def skills(self, request, pk=None):
        job = self.get_object()
        if request.method == 'GET':
            js = JobSkills.objects.filter(job=job).select_related('skill')
            return Response(JobSkillSerializer(js, many=True).data)
        return self.add_skill_requirement(request, pk=pk)

    @action(detail=True, methods=['post'])
    def add_skill_requirement(self, request, pk=None):
        job = self.get_object()
        skill_id = request.data.get('skill_id')
        required_level = request.data.get('required_level', 'intermediate')
        is_required = request.data.get('is_required', True)
        weight = request.data.get('weight', 1.0)

        try:
            skill = Skills.objects.get(pk=skill_id)
        except Skills.DoesNotExist:
            return Response({'error': 'Kỹ năng không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

        job_skill, created = JobSkills.objects.update_or_create(
            job=job,
            skill=skill,
            defaults={'required_level': required_level, 'is_required': is_required, 'weight': weight}
        )
        return Response(JobSkillSerializer(job_skill).data, status=status.HTTP_201_CREATED)


# ==============================================================================
# APPLICATIONS VIEWS
# ==============================================================================

class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Applications.objects.all().select_related('job', 'candidate', 'candidate__user', 'job__company').order_by('-applied_at', '-application_id')
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        candidate_id = self.request.query_params.get('candidate_id')
        if candidate_id:
            qs = qs.filter(candidate_id=candidate_id)

        job_id = self.request.query_params.get('job_id')
        if job_id:
            qs = qs.filter(job_id=job_id)

        company_id = self.request.query_params.get('company_id')
        if company_id:
            qs = qs.filter(job__company_id=company_id)

        status_param = self.request.query_params.get('status')
        if status_param:
            norm_st = STATUS_NORMALIZE_MAP.get(status_param.lower(), status_param.lower())
            qs = qs.filter(status=norm_st)

        return qs

    def create(self, request, *args, **kwargs):
        job_id = request.data.get('job_id') or request.data.get('job')
        candidate_id = request.data.get('candidate_id') or request.data.get('candidate')
        cover_letter = request.data.get('cover_letter', '')

        if not job_id or not candidate_id:
            return Response({'error': 'Thiếu job_id hoặc candidate_id.'}, status=status.HTTP_400_BAD_REQUEST)

        if Applications.objects.filter(job_id=job_id, candidate_id=candidate_id).exists():
            existing = Applications.objects.filter(job_id=job_id, candidate_id=candidate_id).first()
            return Response({
                'error': 'Bạn đã nộp đơn ứng tuyển cho công việc này rồi.',
                'application': ApplicationSerializer(existing).data
            }, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        app = Applications.objects.create(
            job_id=job_id,
            candidate_id=candidate_id,
            cover_letter=cover_letter or 'Ứng tuyển tự động kèm phân tích AI Matching từ hệ thống SmartJob.',
            status='pending',
            applied_at=now,
            created_at=now,
            updated_at=now
        )

        # Tự động chạy AI/ML Matching giữa CV ứng viên và JD công việc khi ứng tuyển
        try:
            cand = Candidates.objects.get(pk=candidate_id)
            job = Jobs.objects.get(pk=job_id)
            calculate_match(cand, job, save_to_db=True)
        except Exception:
            pass

        return Response(ApplicationSerializer(app).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch', 'post'])
    def update_status(self, request, pk=None):
        app = self.get_object()
        raw_status = (request.data.get('status') or '').strip().lower()
        new_status = STATUS_NORMALIZE_MAP.get(raw_status)

        valid_statuses = ['pending', 'reviewing', 'shortlisted', 'interviewed', 'offered', 'rejected', 'withdrawn']
        if not new_status or new_status not in valid_statuses:
            return Response(
                {'error': f'Trạng thái không hợp lệ. Chọn từ: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        app.status = new_status
        app.reviewed_at = timezone.now()
        app.updated_at = timezone.now()
        if 'notes' in request.data:
            app.notes = request.data.get('notes')
        app.save()
        return Response(ApplicationSerializer(app).data)


# ==============================================================================
# SAVED JOBS VIEWS
# ==============================================================================

class SavedJobViewSet(viewsets.ModelViewSet):
    queryset = SavedJobs.objects.all().select_related('job', 'candidate', 'job__company').order_by('-saved_at')
    serializer_class = SavedJobSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        candidate_id = self.request.query_params.get('candidate_id')
        if candidate_id:
            qs = qs.filter(candidate_id=candidate_id)
        return qs

    def create(self, request, *args, **kwargs):
        candidate_id = request.data.get('candidate_id')
        job_id = request.data.get('job_id')
        notes = request.data.get('notes', '')

        if not candidate_id or not job_id:
            return Response({'error': 'Thiếu candidate_id hoặc job_id.'}, status=status.HTTP_400_BAD_REQUEST)

        saved, created = SavedJobs.objects.get_or_create(
            candidate_id=candidate_id,
            job_id=job_id,
            defaults={'notes': notes}
        )
        return Response(SavedJobSerializer(saved).data, status=status.HTTP_201_CREATED)


# ==============================================================================
# AI MATCHING VIEWS (CHECKLIST 02)
# ==============================================================================

class AIMatchingAPIView(APIView):
    """
    Direct calculation API for AI Matching.
    Supports either database IDs (candidate_id & job_id) or direct payload (cv_text & job_description).
    """
    def post(self, request):
        candidate_id = request.data.get('candidate_id')
        job_id = request.data.get('job_id')
        cv_text = request.data.get('cv_text')
        job_description = request.data.get('job_description')

        if candidate_id and job_id:
            try:
                candidate = Candidates.objects.get(pk=candidate_id)
                job = Jobs.objects.get(pk=job_id)
            except (Candidates.DoesNotExist, Jobs.DoesNotExist):
                return Response({'error': 'Ứng viên hoặc công việc không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

            match_data = calculate_match(candidate, job, save_to_db=True)
            return Response(match_data)

        elif cv_text and job_description:
            parsed_cand = parse_cv_service(cv_text)
            parsed_skills = extract_skills_service(job_description)
            job_payload = {
                'job_title': request.data.get('job_title', 'Vị trí tuyển dụng'),
                'job_description': job_description,
                'requirements': request.data.get('requirements', ''),
                'years_of_experience_required': request.data.get('years_of_experience_required', 0),
                'salary_min': request.data.get('salary_min'),
                'salary_max': request.data.get('salary_max'),
                'required_skills': parsed_skills
            }
            from ai_matching.matching_engine import calculate_matching_score
            match_data = calculate_matching_score(parsed_cand, job_payload)
            return Response(match_data)

        return Response(
            {'error': 'Cần truyền (candidate_id và job_id) HOẶC (cv_text và job_description).'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ExtractSkillsAPIView(APIView):
    """
    Extracts and normalizes skills from free-form text (CV or Job Description).
    """
    def post(self, request):
        text = request.data.get('text', '')
        if not text:
            return Response({'error': 'Tham số "text" không được để trống.'}, status=status.HTTP_400_BAD_REQUEST)

        skills = extract_skills_service(text)
        return Response({
            'total_skills_found': len(skills),
            'skills': skills
        })


class ParseCVAPIView(APIView):
    """
    Parses unstructured CV text or uploaded CV file into a structured candidate profile.
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        cv_file = request.FILES.get('cv_file')
        cv_text = request.data.get('cv_text', '')
        if cv_file:
            try:
                cv_text = extract_text_from_file(cv_file)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if not cv_text:
            return Response({'error': 'Tham số "cv_text" hoặc file "cv_file" không được để trống.'}, status=status.HTTP_400_BAD_REQUEST)

        profile = parse_cv_service(cv_text)
        return Response(profile)


class RecommendJobsAPIView(APIView):
    """
    Recommends ranked jobs for a candidate either by candidate_id, raw CV text, or uploaded CV file.
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        candidate_id = request.data.get('candidate_id')
        cv_file = request.FILES.get('cv_file')
        cv_text = request.data.get('cv_text')
        if cv_file:
            try:
                cv_text = extract_text_from_file(cv_file)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        limit = int(request.data.get('limit', 10))
        min_score = float(request.data.get('min_score', 0.0))
        location = request.data.get('location')

        if candidate_id:
            try:
                candidate = Candidates.objects.get(pk=candidate_id)
            except Candidates.DoesNotExist:
                return Response({'error': 'Ứng viên không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

            recs = get_recommended_jobs_for_candidate(
                candidate, limit=limit, min_score=min_score, location=location
            )
            return Response({
                'candidate_id': candidate_id,
                'candidate_name': candidate.full_name,
                'recommendations_count': len(recs),
                'recommendations': recs
            })

        elif cv_text:
            result = stateless_recommend_jobs_for_cv_text(
                cv_text=cv_text, limit=limit, min_score=min_score
            )
            return Response(result)

        return Response(
            {'error': 'Cần truyền "candidate_id" hoặc "cv_text".'},
            status=status.HTTP_400_BAD_REQUEST
        )


class AIEvaluationAPIView(APIView):
    """
    Executes benchmark evaluation on the test dataset and returns Precision@K, Recall@K, NDCG@K, MRR, MAP.
    """
    def get(self, request):
        metrics_data = get_ai_evaluation_metrics()
        return Response(metrics_data)


# ==============================================================================
# BI DASHBOARD ANALYTICS VIEWS
# ==============================================================================

class BIDashboardViewSet(viewsets.ViewSet):
    """
    Business Intelligence endpoints for recruitment and market trends
    """
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Tổng quan các chỉ số hệ thống & BI cho Nhà tuyển dụng"""
        company_id = request.query_params.get('company_id')
        jobs_qs = Jobs.objects.all()
        apps_qs = Applications.objects.all()

        if company_id:
            jobs_qs = jobs_qs.filter(company_id=company_id)
            apps_qs = apps_qs.filter(job__company_id=company_id)

        total_jobs = jobs_qs.count()
        active_jobs = jobs_qs.filter(status='active').count()
        total_candidates = Candidates.objects.count()
        total_companies = Companies.objects.count()
        total_applications = apps_qs.count()
        total_views = JobViews.objects.count()

        pending_apps = apps_qs.filter(status__in=['pending', 'reviewing', 'shortlisted']).count()
        only_pending = apps_qs.filter(status='pending').count()
        reviewing_apps = apps_qs.filter(status__in=['reviewing', 'shortlisted']).count()
        interviewed_apps = apps_qs.filter(status='interviewed').count()
        accepted_apps = apps_qs.filter(status='offered').count()
        rejected_apps = apps_qs.filter(status='rejected').count()

        hiring_success_rate = round((accepted_apps / total_applications * 100.0), 1) if total_applications > 0 else 0.0

        # Thống kê hồ sơ ứng tuyển theo thời gian
        timeline_map = {}
        for app in apps_qs.order_by('applied_at'):
            dt = (app.applied_at or app.created_at or timezone.now()).date().isoformat()
            if dt not in timeline_map:
                timeline_map[dt] = {'date': dt, 'count': 0, 'accepted': 0, 'pending': 0}
            timeline_map[dt]['count'] += 1
            if app.status == 'offered':
                timeline_map[dt]['accepted'] += 1
            elif app.status in ('pending', 'reviewing', 'shortlisted'):
                timeline_map[dt]['pending'] += 1

        applications_over_time = sorted(timeline_map.values(), key=lambda x: x['date'])

        status_breakdown = [
            {'code': 'pending', 'label': 'Đã tiếp nhận', 'count': only_pending},
            {'code': 'reviewing', 'label': 'Đang xem xét', 'count': reviewing_apps},
            {'code': 'interviewed', 'label': 'Mời phỏng vấn', 'count': interviewed_apps},
            {'code': 'offered', 'label': 'Trúng tuyển', 'count': accepted_apps},
            {'code': 'rejected', 'label': 'Từ chối', 'count': rejected_apps},
        ]

        return Response({
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'total_candidates': total_candidates,
            'total_companies': total_companies,
            'total_applications': total_applications,
            'pending_applications': pending_apps,
            'interviewed_applications': interviewed_apps,
            'accepted_applications': accepted_apps,
            'rejected_applications': rejected_apps,
            'hiring_success_rate': hiring_success_rate,
            'total_views': total_views,
            'applications_over_time': applications_over_time,
            'status_breakdown': status_breakdown,
            'superset_embed_url': 'http://localhost:8088/superset/dashboard/smartjob-bi/?standalone=true'
        })

    @action(detail=False, methods=['get'])
    def skills_demand(self, request):
        """Top các kỹ năng được thị trường tuyển dụng yêu cầu nhiều nhất"""
        limit = int(request.query_params.get('limit', 10))
        top_skills = (
            JobSkills.objects
            .values('skill__skill_name', 'skill__category')
            .annotate(demand_count=Count('job_id'))
            .order_by('-demand_count')[:limit]
        )
        return Response([
            {
                'skill_name': item['skill__skill_name'],
                'category': item['skill__category'],
                'demand_count': item['demand_count']
            }
            for item in top_skills
        ])

    @action(detail=False, methods=['get'])
    def salary_trends(self, request):
        """Xu hướng mức lương theo ngành nghề và cấp bậc"""
        by_industry = (
            Jobs.objects
            .filter(salary_max__isnull=False)
            .values('company__industry')
            .annotate(
                avg_min=Avg('salary_min'),
                avg_max=Avg('salary_max'),
                job_count=Count('job_id')
            )
            .order_by('-avg_max')
        )
        by_level = (
            Jobs.objects
            .filter(salary_max__isnull=False, position_level__isnull=False)
            .values('position_level')
            .annotate(
                avg_min=Avg('salary_min'),
                avg_max=Avg('salary_max'),
                job_count=Count('job_id')
            )
            .order_by('-avg_max')
        )
        return Response({
            'by_industry': [
                {
                    'industry': item['company__industry'] or 'Khác',
                    'avg_min': float(round(item['avg_min'] or 0, 2)),
                    'avg_max': float(round(item['avg_max'] or 0, 2)),
                    'job_count': item['job_count']
                }
                for item in by_industry if item['company__industry']
            ],
            'by_position_level': [
                {
                    'level': item['position_level'],
                    'avg_min': float(round(item['avg_min'] or 0, 2)),
                    'avg_max': float(round(item['avg_max'] or 0, 2)),
                    'job_count': item['job_count']
                }
                for item in by_level
            ]
        })

    @action(detail=False, methods=['get'])
    def conversion_funnel(self, request):
        """Phễu chuyển đổi tuyển dụng (Lượt xem -> Đơn nộp -> Duyệt -> Phỏng vấn -> Trúng tuyển)"""
        total_views = JobViews.objects.count()
        total_apps = Applications.objects.count()
        shortlisted = Applications.objects.filter(status__in=['reviewing', 'shortlisted', 'interviewed', 'offered']).count()
        interviewed = Applications.objects.filter(status__in=['interviewed', 'offered']).count()
        offered = Applications.objects.filter(status='offered').count()

        return Response({
            'funnel': [
                {'stage': 'Lượt xem (Views)', 'count': total_views},
                {'stage': 'Đã tiếp nhận (Applications)', 'count': total_apps},
                {'stage': 'Đang xem xét (Reviewing)', 'count': shortlisted},
                {'stage': 'Mời phỏng vấn (Interviewed)', 'count': interviewed},
                {'stage': 'Trúng tuyển (Offered)', 'count': offered}
            ],
            'conversion_rates': {
                'view_to_application': round((total_apps / total_views * 100), 2) if total_views > 0 else 0,
                'application_to_offer': round((offered / total_apps * 100), 2) if total_apps > 0 else 0
            }
        })
