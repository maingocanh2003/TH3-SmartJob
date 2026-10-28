from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Count, Avg, Q, F
from django.contrib.auth.hashers import make_password, check_password
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
    calculate_match, get_recommended_jobs_for_candidate, get_recommended_candidates_for_job
)


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

        if user_type not in ('candidate', 'company', 'admin'):
            return Response({'error': 'Loại tài khoản không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

        if Users.objects.filter(email=email).exists():
            return Response({'error': 'Email này đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)

        # Tạo user với password đã hash
        user = Users.objects.create(
            email=email,
            password_hash=make_password(password),
            user_type=user_type,
            is_active=True
        )

        # Tự động tạo hồ sơ tương ứng
        if user_type == 'candidate':
            candidate = Candidates.objects.create(
                user=user,
                full_name=full_name or email.split('@')[0]
            )
            profile_data = {'candidate_id': candidate.candidate_id, 'full_name': candidate.full_name}
        elif user_type == 'company':
            company = Companies.objects.create(
                user=user,
                company_name=company_name or email.split('@')[0]
            )
            profile_data = {'company_id': company.company_id, 'company_name': company.company_name}
        else:
            profile_data = {}

        return Response({
            'message': 'Đăng ký tài khoản thành công!',
            'user': UserSerializer(user).data,
            'profile': profile_data
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

        # Verify password hash
        if not check_password(password, user.password_hash) and user.password_hash != password:
            return Response({'error': 'Email hoặc mật khẩu không chính xác.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'error': 'Tài khoản đã bị khóa.'}, status=status.HTTP_403_FORBIDDEN)

        profile_data = {}
        if user.user_type == 'candidate':
            cand = Candidates.objects.filter(user=user).first()
            if cand:
                profile_data = {'candidate_id': cand.candidate_id, 'full_name': cand.full_name}
        elif user.user_type == 'company':
            comp = Companies.objects.filter(user=user).first()
            if comp:
                profile_data = {'company_id': comp.company_id, 'company_name': comp.company_name}

        return Response({
            'message': 'Đăng nhập thành công!',
            'user': UserSerializer(user).data,
            'profile': profile_data
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
        """Lấy danh sách các phân loại kỹ năng"""
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
        
        # POST - thêm kỹ năng
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
        recommendations = get_recommended_jobs_for_candidate(candidate, limit=limit)
        return Response(recommendations)


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
        jobs = Jobs.objects.filter(company=company).order_by('-created_at')
        return Response(JobSerializer(jobs, many=True).data)


# ==============================================================================
# JOBS VIEWS
# ==============================================================================

class JobViewSet(viewsets.ModelViewSet):
    queryset = Jobs.objects.all().select_related('company').order_by('-created_at')
    serializer_class = JobSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['job_title', 'company__company_name', 'location', 'requirements']

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        
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

    def retrieve(self, request, *args, **kwargs):
        job = self.get_object()
        # Tăng lượt xem và ghi nhận log
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
        recommendations = get_recommended_candidates_for_job(job, limit=limit)
        return Response(recommendations)

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
    queryset = Applications.objects.all().select_related('job', 'candidate', 'job__company').order_by('-applied_at')
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

        return qs

    def create(self, request, *args, **kwargs):
        job_id = request.data.get('job_id')
        candidate_id = request.data.get('candidate_id')
        cover_letter = request.data.get('cover_letter', '')

        if not job_id or not candidate_id:
            return Response({'error': 'Thiếu job_id hoặc candidate_id.'}, status=status.HTTP_400_BAD_REQUEST)

        if Applications.objects.filter(job_id=job_id, candidate_id=candidate_id).exists():
            return Response({'error': 'Bạn đã nộp đơn cho công việc này rồi.'}, status=status.HTTP_400_BAD_REQUEST)

        app = Applications.objects.create(
            job_id=job_id,
            candidate_id=candidate_id,
            cover_letter=cover_letter,
            status='pending'
        )
        return Response(ApplicationSerializer(app).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        app = self.get_object()
        new_status = request.data.get('status')
        valid_statuses = ['pending', 'reviewing', 'shortlisted', 'interviewed', 'offered', 'rejected', 'withdrawn']
        if new_status not in valid_statuses:
            return Response({'error': f'Trạng thái không hợp lệ. Chọn từ: {", ".join(valid_statuses)}'}, status=status.HTTP_400_BAD_REQUEST)

        app.status = new_status
        app.reviewed_at = timezone.now()
        app.notes = request.data.get('notes', app.notes)
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
# AI MATCHING VIEW
# ==============================================================================

class AIMatchingAPIView(APIView):
    """
    Direct calculation API for AI Matching
    """
    def post(self, request):
        candidate_id = request.data.get('candidate_id')
        job_id = request.data.get('job_id')

        if not candidate_id or not job_id:
            return Response({'error': 'Cần truyền candidate_id và job_id.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            candidate = Candidates.objects.get(pk=candidate_id)
            job = Jobs.objects.get(pk=job_id)
        except (Candidates.DoesNotExist, Jobs.DoesNotExist):
            return Response({'error': 'Ứng viên hoặc công việc không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

        match_data = calculate_match(candidate, job, save_to_db=True)
        return Response(match_data)


# ==============================================================================
# BI DASHBOARD ANALYTICS VIEWS
# ==============================================================================

class BIDashboardViewSet(viewsets.ViewSet):
    """
    Business Intelligence endpoints for recruitment and market trends
    """
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Tổng quan các chỉ số hệ thống"""
        total_jobs = Jobs.objects.count()
        active_jobs = Jobs.objects.filter(status='active').count()
        total_candidates = Candidates.objects.count()
        total_companies = Companies.objects.count()
        total_applications = Applications.objects.count()
        total_views = JobViews.objects.count()

        return Response({
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'total_candidates': total_candidates,
            'total_companies': total_companies,
            'total_applications': total_applications,
            'total_views': total_views
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
        shortlisted = Applications.objects.filter(status__in=['shortlisted', 'interviewed', 'offered']).count()
        interviewed = Applications.objects.filter(status__in=['interviewed', 'offered']).count()
        offered = Applications.objects.filter(status='offered').count()

        return Response({
            'funnel': [
                {'stage': 'Lượt xem (Views)', 'count': total_views},
                {'stage': 'Nộp đơn (Applications)', 'count': total_apps},
                {'stage': 'Sơ tuyển (Shortlisted)', 'count': shortlisted},
                {'stage': 'Phỏng vấn (Interviewed)', 'count': interviewed},
                {'stage': 'Trúng tuyển (Offered)', 'count': offered}
            ],
            'conversion_rates': {
                'view_to_application': round((total_apps / total_views * 100), 2) if total_views > 0 else 0,
                'application_to_offer': round((offered / total_apps * 100), 2) if total_apps > 0 else 0
            }
        })
