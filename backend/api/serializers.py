from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password
from .models import (
    Users, Candidates, Companies, Skills, CandidateSkills,
    Education, Experience, Jobs, JobSkills, Applications,
    AiMatchResults, JobViews, SavedJobs
)


STATUS_VI_MAP = {
    'pending': 'Đã tiếp nhận',
    'reviewing': 'Đang xem xét',
    'shortlisted': 'Đang xem xét',
    'interviewed': 'Mời phỏng vấn',
    'offered': 'Trúng tuyển',
    'rejected': 'Từ chối',
    'withdrawn': 'Đã rút hồ sơ',
}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['user_id', 'email', 'user_type', 'is_active', 'created_at']
        read_only_fields = ['user_id', 'is_active', 'created_at']


class SkillSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='skill_id', read_only=True)
    name = serializers.CharField(source='skill_name', read_only=True)

    class Meta:
        model = Skills
        fields = ['skill_id', 'id', 'skill_name', 'name', 'category', 'description', 'created_at']
        read_only_fields = ['skill_id', 'id', 'name', 'created_at']


class CandidateSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.skill_name', read_only=True)
    category = serializers.CharField(source='skill.category', read_only=True)

    class Meta:
        model = CandidateSkills
        fields = ['candidate_skill_id', 'candidate', 'skill', 'skill_name', 'category', 'proficiency_level', 'years_of_experience', 'created_at']
        read_only_fields = ['candidate_skill_id', 'created_at']


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['education_id', 'candidate', 'institution_name', 'degree', 'major', 'start_date', 'end_date', 'gpa', 'description', 'created_at']
        read_only_fields = ['education_id', 'created_at']


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ['experience_id', 'candidate', 'company_name', 'position', 'start_date', 'end_date', 'is_current', 'responsibilities', 'achievements', 'created_at']
        read_only_fields = ['experience_id', 'created_at']


class CandidateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    skills = serializers.SerializerMethodField()
    educations = serializers.SerializerMethodField()
    experiences = serializers.SerializerMethodField()

    class Meta:
        model = Candidates
        fields = [
            'candidate_id', 'user', 'email', 'full_name', 'phone', 'address',
            'date_of_birth', 'gender', 'avatar_url', 'summary',
            'desired_position', 'desired_salary', 'years_of_experience',
            'cv_file_url', 'skills', 'educations', 'experiences',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['candidate_id', 'created_at', 'updated_at']

    def get_skills(self, obj):
        skills_qs = CandidateSkills.objects.filter(candidate=obj).select_related('skill')
        return CandidateSkillSerializer(skills_qs, many=True).data

    def get_educations(self, obj):
        edu_qs = Education.objects.filter(candidate=obj).order_by('-start_date')
        return EducationSerializer(edu_qs, many=True).data

    def get_experiences(self, obj):
        exp_qs = Experience.objects.filter(candidate=obj).order_by('-start_date')
        return ExperienceSerializer(exp_qs, many=True).data


class CompanySerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    active_jobs_count = serializers.SerializerMethodField()

    class Meta:
        model = Companies
        fields = [
            'company_id', 'user', 'email', 'company_name', 'tax_code',
            'industry', 'company_size', 'address', 'phone', 'website',
            'logo_url', 'description', 'contact_person', 'contact_email',
            'active_jobs_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['company_id', 'created_at', 'updated_at']

    def get_active_jobs_count(self, obj):
        return Jobs.objects.filter(company=obj, status='active').count()


class JobSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.skill_name', read_only=True)
    category = serializers.CharField(source='skill.category', read_only=True)

    class Meta:
        model = JobSkills
        fields = ['job_skill_id', 'job', 'skill', 'skill_name', 'category', 'required_level', 'is_required', 'weight', 'created_at']
        read_only_fields = ['job_skill_id', 'created_at']


class JobSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    company_logo = serializers.CharField(source='company.logo_url', read_only=True)
    company_industry = serializers.CharField(source='company.industry', read_only=True)
    skills = serializers.SerializerMethodField()
    application_count = serializers.SerializerMethodField()
    id = serializers.IntegerField(source='job_id', read_only=True)
    title = serializers.CharField(source='job_title', read_only=True)
    description = serializers.CharField(source='job_description', read_only=True)
    job_type = serializers.CharField(source='employment_type', read_only=True)
    level = serializers.CharField(source='position_level', read_only=True)
    experience_required = serializers.IntegerField(source='years_of_experience_required', read_only=True)
    deadline = serializers.DateField(source='application_deadline', read_only=True)
    skills_required = serializers.SerializerMethodField()
    applications_count = serializers.SerializerMethodField()

    class Meta:
        model = Jobs
        fields = [
            'job_id', 'id', 'company', 'company_name', 'company_logo', 'company_industry',
            'job_title', 'title', 'job_description', 'description', 'requirements', 'benefits',
            'position_level', 'level', 'employment_type', 'job_type', 'num_of_positions',
            'salary_min', 'salary_max', 'salary_currency', 'location',
            'years_of_experience_required', 'experience_required', 'application_deadline', 'deadline',
            'status', 'view_count', 'skills', 'skills_required',
            'application_count', 'applications_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['job_id', 'view_count', 'created_at', 'updated_at']

    def get_skills(self, obj):
        job_skills = JobSkills.objects.filter(job=obj).select_related('skill')
        return JobSkillSerializer(job_skills, many=True).data

    def get_skills_required(self, obj):
        return self.get_skills(obj)

    def get_application_count(self, obj):
        return Applications.objects.filter(job=obj).count()

    def get_applications_count(self, obj):
        return self.get_application_count(obj)


class ApplicationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='application_id', read_only=True)
    job_title = serializers.CharField(source='job.job_title', read_only=True)
    job_location = serializers.CharField(source='job.location', read_only=True)
    job_salary_min = serializers.DecimalField(source='job.salary_min', max_digits=10, decimal_places=2, read_only=True)
    job_salary_max = serializers.DecimalField(source='job.salary_max', max_digits=10, decimal_places=2, read_only=True)
    job_employment_type = serializers.CharField(source='job.employment_type', read_only=True)
    company_id = serializers.IntegerField(source='job.company_id', read_only=True)
    company_name = serializers.CharField(source='job.company.company_name', read_only=True)

    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    candidate_email = serializers.EmailField(source='candidate.user.email', read_only=True)
    candidate_phone = serializers.CharField(source='candidate.phone', read_only=True)
    candidate_address = serializers.CharField(source='candidate.address', read_only=True)
    candidate_position = serializers.CharField(source='candidate.desired_position', read_only=True)
    candidate_experience = serializers.IntegerField(source='candidate.years_of_experience', read_only=True)
    candidate_summary = serializers.CharField(source='candidate.summary', read_only=True)
    candidate_cv = serializers.CharField(source='candidate.cv_file_url', read_only=True)
    candidate_skills = serializers.SerializerMethodField()
    candidate_education = serializers.SerializerMethodField()

    status_label = serializers.SerializerMethodField()
    ai_match = serializers.SerializerMethodField()

    class Meta:
        model = Applications
        fields = [
            'application_id', 'id', 'job', 'job_title', 'job_location',
            'job_salary_min', 'job_salary_max', 'job_employment_type',
            'company_id', 'company_name',
            'candidate', 'candidate_name', 'candidate_email', 'candidate_phone',
            'candidate_address', 'candidate_position', 'candidate_experience',
            'candidate_summary', 'candidate_cv', 'candidate_skills', 'candidate_education',
            'cover_letter', 'status', 'status_label', 'ai_match',
            'applied_at', 'reviewed_at', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['application_id', 'applied_at', 'created_at', 'updated_at']

    def get_status_label(self, obj):
        st = (obj.status or 'pending').lower()
        return STATUS_VI_MAP.get(st, obj.status)

    def get_candidate_skills(self, obj):
        if not obj.candidate_id:
            return []
        qs = CandidateSkills.objects.filter(candidate_id=obj.candidate_id).select_related('skill')
        return [
            {
                'skill_name': cs.skill.skill_name,
                'category': cs.skill.category,
                'proficiency_level': cs.proficiency_level
            }
            for cs in qs
        ]

    def get_candidate_education(self, obj):
        if not obj.candidate_id:
            return 'Đại học / Cử nhân'
        edu = Education.objects.filter(candidate_id=obj.candidate_id).order_by('-start_date').first()
        if not edu:
            return 'Đại học / Cử nhân'
        deg_map = {
            'Bachelor': 'Cử nhân',
            'Master': 'Thạc sĩ',
            'PhD': 'Tiến sĩ',
            'Doctorate': 'Tiến sĩ',
            'Associate': 'Cao đẳng',
        }
        deg = deg_map.get(edu.degree, edu.degree or 'Cử nhân')
        parts = [p for p in [edu.major or deg, edu.institution_name] if p and p not in ('Học vấn từ CV', 'None')]
        return ' · '.join(parts) if parts else deg

    def get_ai_match(self, obj):
        if not obj.candidate_id or not obj.job_id:
            return None
        match = AiMatchResults.objects.filter(candidate_id=obj.candidate_id, job_id=obj.job_id).first()
        if match:
            return {
                'matching_score': float(match.matching_score),
                'matched_skills': match.matched_skills or [],
                'missing_skills': match.missing_skills or [],
                'experience_match': float(match.experience_match or 0),
                'education_match': float(match.education_match or 0),
                'overall_recommendation': match.overall_recommendation or ''
            }
        return None


class SavedJobSerializer(serializers.ModelSerializer):
    job_details = JobSerializer(source='job', read_only=True)

    class Meta:
        model = SavedJobs
        fields = ['saved_job_id', 'candidate', 'job', 'job_details', 'saved_at', 'notes']
        read_only_fields = ['saved_job_id', 'saved_at']


class AiMatchResultSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.job_title', read_only=True)
    company_name = serializers.CharField(source='job.company.company_name', read_only=True)
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)

    class Meta:
        model = AiMatchResults
        fields = [
            'match_id', 'candidate', 'candidate_name', 'job', 'job_title', 'company_name',
            'matching_score', 'matched_skills', 'missing_skills', 'skill_match_details',
            'experience_match', 'education_match', 'salary_match',
            'overall_recommendation', 'calculated_at'
        ]
        read_only_fields = ['match_id', 'calculated_at']
