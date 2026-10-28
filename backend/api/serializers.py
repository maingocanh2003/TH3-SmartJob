from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password
from .models import (
    Users, Candidates, Companies, Skills, CandidateSkills,
    Education, Experience, Jobs, JobSkills, Applications,
    AiMatchResults, JobViews, SavedJobs
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['user_id', 'email', 'user_type', 'is_active', 'created_at']
        read_only_fields = ['user_id', 'is_active', 'created_at']


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skills
        fields = ['skill_id', 'skill_name', 'category', 'description', 'created_at']
        read_only_fields = ['skill_id', 'created_at']


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

    class Meta:
        model = Jobs
        fields = [
            'job_id', 'company', 'company_name', 'company_logo', 'company_industry',
            'job_title', 'job_description', 'requirements', 'benefits',
            'position_level', 'employment_type', 'num_of_positions',
            'salary_min', 'salary_max', 'salary_currency', 'location',
            'years_of_experience_required', 'application_deadline', 'status',
            'view_count', 'skills', 'application_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['job_id', 'view_count', 'created_at', 'updated_at']

    def get_skills(self, obj):
        job_skills = JobSkills.objects.filter(job=obj).select_related('skill')
        return JobSkillSerializer(job_skills, many=True).data

    def get_application_count(self, obj):
        return Applications.objects.filter(job=obj).count()


class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.job_title', read_only=True)
    company_name = serializers.CharField(source='job.company.company_name', read_only=True)
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    candidate_phone = serializers.CharField(source='candidate.phone', read_only=True)
    candidate_cv = serializers.CharField(source='candidate.cv_file_url', read_only=True)

    class Meta:
        model = Applications
        fields = [
            'application_id', 'job', 'job_title', 'company_name',
            'candidate', 'candidate_name', 'candidate_phone', 'candidate_cv',
            'cover_letter', 'status', 'applied_at', 'reviewed_at', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['application_id', 'applied_at', 'created_at', 'updated_at']


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
