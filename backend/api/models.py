# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AiMatchResults(models.Model):
    match_id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey('Candidates', models.DB_CASCADE)
    job = models.ForeignKey('Jobs', models.DB_CASCADE)
    matching_score = models.DecimalField(max_digits=5, decimal_places=2)
    matched_skills = models.JSONField(blank=True, null=True)
    missing_skills = models.JSONField(blank=True, null=True)
    skill_match_details = models.JSONField(blank=True, null=True)
    experience_match = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    education_match = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    salary_match = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    overall_recommendation = models.CharField(max_length=50, blank=True, null=True)
    calculated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ai_match_results'


class Applications(models.Model):
    application_id = models.AutoField(primary_key=True)
    job = models.ForeignKey('Jobs', models.DB_CASCADE)
    candidate = models.ForeignKey('Candidates', models.DB_CASCADE)
    cover_letter = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    applied_at = models.DateTimeField(blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'applications'
        unique_together = (('job', 'candidate'),)


class CandidateSkills(models.Model):
    candidate_skill_id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey('Candidates', models.DB_CASCADE)
    skill = models.ForeignKey('Skills', models.DB_CASCADE)
    proficiency_level = models.CharField(max_length=50, blank=True, null=True)
    years_of_experience = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'candidate_skills'
        unique_together = (('candidate', 'skill'),)


class Candidates(models.Model):
    candidate_id = models.AutoField(primary_key=True)
    user = models.OneToOneField('Users', models.DB_CASCADE)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    avatar_url = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    desired_position = models.CharField(max_length=255, blank=True, null=True)
    desired_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    years_of_experience = models.IntegerField(blank=True, null=True)
    cv_file_url = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'candidates'


class Companies(models.Model):
    company_id = models.AutoField(primary_key=True)
    user = models.OneToOneField('Users', models.DB_CASCADE)
    company_name = models.CharField(max_length=255)
    tax_code = models.CharField(unique=True, max_length=50, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    company_size = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    logo_url = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'companies'


class Education(models.Model):
    education_id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey(Candidates, models.DB_CASCADE)
    institution_name = models.CharField(max_length=255)
    degree = models.CharField(max_length=100, blank=True, null=True)
    major = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'education'


class Experience(models.Model):
    experience_id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey(Candidates, models.DB_CASCADE)
    company_name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(blank=True, null=True)
    responsibilities = models.TextField(blank=True, null=True)
    achievements = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'experience'


class JobSkills(models.Model):
    job_skill_id = models.AutoField(primary_key=True)
    job = models.ForeignKey('Jobs', models.DB_CASCADE)
    skill = models.ForeignKey('Skills', models.DB_CASCADE)
    required_level = models.CharField(max_length=50, blank=True, null=True)
    is_required = models.BooleanField(blank=True, null=True)
    weight = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'job_skills'
        unique_together = (('job', 'skill'),)


class JobViews(models.Model):
    view_id = models.AutoField(primary_key=True)
    job = models.ForeignKey('Jobs', models.DB_CASCADE)
    candidate = models.ForeignKey(Candidates, models.DB_SET_NULL, blank=True, null=True)
    ip_address = models.CharField(max_length=50, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    viewed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'job_views'


class Jobs(models.Model):
    job_id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Companies, models.DB_CASCADE)
    job_title = models.CharField(max_length=255)
    job_description = models.TextField()
    requirements = models.TextField(blank=True, null=True)
    benefits = models.TextField(blank=True, null=True)
    position_level = models.CharField(max_length=50, blank=True, null=True)
    employment_type = models.CharField(max_length=50, blank=True, null=True)
    num_of_positions = models.IntegerField(blank=True, null=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salary_currency = models.CharField(max_length=10, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    years_of_experience_required = models.IntegerField(blank=True, null=True)
    application_deadline = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    view_count = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'jobs'


class SavedJobs(models.Model):
    saved_job_id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey(Candidates, models.DB_CASCADE)
    job = models.ForeignKey(Jobs, models.DB_CASCADE)
    saved_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'saved_jobs'
        unique_together = (('candidate', 'job'),)


class Skills(models.Model):
    skill_id = models.AutoField(primary_key=True)
    skill_name = models.CharField(unique=True, max_length=255)
    category = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'skills'


class Users(models.Model):
    user_id = models.AutoField(primary_key=True)
    email = models.CharField(unique=True, max_length=255)
    password_hash = models.CharField(max_length=255)
    user_type = models.CharField(max_length=20)
    is_active = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'
