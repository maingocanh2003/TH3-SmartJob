from django.contrib import admin
from .models import (
    Users, Candidates, Companies, Skills, CandidateSkills,
    Education, Experience, Jobs, JobSkills, Applications,
    AiMatchResults, JobViews, SavedJobs
)


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'email', 'user_type', 'is_active', 'created_at')
    list_filter = ('user_type', 'is_active')
    search_fields = ('email',)


@admin.register(Candidates)
class CandidatesAdmin(admin.ModelAdmin):
    list_display = ('candidate_id', 'full_name', 'phone', 'desired_position', 'years_of_experience')
    search_fields = ('full_name', 'desired_position', 'phone')


@admin.register(Companies)
class CompaniesAdmin(admin.ModelAdmin):
    list_display = ('company_id', 'company_name', 'industry', 'company_size', 'phone')
    search_fields = ('company_name', 'industry')


@admin.register(Skills)
class SkillsAdmin(admin.ModelAdmin):
    list_display = ('skill_id', 'skill_name', 'category')
    list_filter = ('category',)
    search_fields = ('skill_name',)


@admin.register(Jobs)
class JobsAdmin(admin.ModelAdmin):
    list_display = ('job_id', 'job_title', 'company', 'location', 'status', 'view_count', 'created_at')
    list_filter = ('status', 'employment_type')
    search_fields = ('job_title', 'location')


@admin.register(Applications)
class ApplicationsAdmin(admin.ModelAdmin):
    list_display = ('application_id', 'job', 'candidate', 'status', 'applied_at')
    list_filter = ('status',)


@admin.register(AiMatchResults)
class AiMatchResultsAdmin(admin.ModelAdmin):
    list_display = ('match_id', 'candidate', 'job', 'matching_score', 'overall_recommendation', 'calculated_at')
    list_filter = ('overall_recommendation',)


admin.site.register(CandidateSkills)
admin.site.register(JobSkills)
admin.site.register(Education)
admin.site.register(Experience)
admin.site.register(JobViews)
admin.site.register(SavedJobs)
