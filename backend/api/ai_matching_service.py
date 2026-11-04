"""
AI Matching Service for SmartJob
Integrates the advanced AI/ML Matching Package with Django Models & PostgreSQL.
"""

import re
from decimal import Decimal
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
from django.utils import timezone

# Ensure project root is in sys.path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from ai_matching.matching_engine import calculate_matching_score
from ai_matching.skill_extractor import extract_skills_from_text, parse_cv_text, parse_job_description
from ai_matching.ranking import rank_jobs_for_candidate, rank_candidates_for_job
from ai_matching.evaluator import run_recommendation_evaluation

from .models import (
    Candidates, Jobs, CandidateSkills, JobSkills,
    Education, Experience, AiMatchResults
)


def candidate_to_dict(candidate: Candidates) -> Dict[str, Any]:
    """Convert Django Candidate model into matching engine dictionary format."""
    skills_qs = CandidateSkills.objects.filter(candidate=candidate).select_related('skill')
    skills = [
        {
            'name': cs.skill.skill_name,
            'level': cs.proficiency_level or 'intermediate',
            'years': cs.years_of_experience or 1
        }
        for cs in skills_qs
    ]

    edu_obj = Education.objects.filter(candidate=candidate).order_by('-end_date').first()
    edu_degree = edu_obj.degree if edu_obj else 'Bachelor'

    return {
        'candidate_id': candidate.candidate_id,
        'full_name': candidate.full_name,
        'email': candidate.user.email if hasattr(candidate, 'user') and candidate.user else '',
        'phone': candidate.phone or '',
        'desired_position': candidate.desired_position or '',
        'desired_salary': float(candidate.desired_salary) if candidate.desired_salary else None,
        'years_of_experience': candidate.years_of_experience or 0,
        'location': candidate.address or '',
        'summary': candidate.summary or '',
        'education_level': edu_degree,
        'skills': skills
    }


def job_to_dict(job: Jobs) -> Dict[str, Any]:
    """Convert Django Job model into matching engine dictionary format."""
    job_skills_qs = JobSkills.objects.filter(job=job).select_related('skill')
    req_skills = [
        {
            'name': js.skill.skill_name,
            'level': js.required_level or 'intermediate',
            'is_required': js.is_required if js.is_required is not None else True,
            'weight': float(js.weight or 1.0)
        }
        for js in job_skills_qs
    ]

    return {
        'job_id': job.job_id,
        'job_title': job.job_title,
        'company_name': job.company.company_name if hasattr(job, 'company') and job.company else 'Doanh nghiệp',
        'company_logo': job.company.logo_url if hasattr(job, 'company') and job.company else '',
        'location': job.location or '',
        'position_level': job.position_level or 'Middle',
        'employment_type': job.employment_type or 'full-time',
        'salary_min': float(job.salary_min) if job.salary_min else None,
        'salary_max': float(job.salary_max) if job.salary_max else None,
        'salary_currency': job.salary_currency or 'VND',
        'years_of_experience_required': job.years_of_experience_required or 0,
        'education_level_required': 'Bachelor',
        'job_description': job.job_description or '',
        'requirements': job.requirements or '',
        'required_skills': req_skills
    }


def calculate_match(candidate: Candidates, job: Jobs, save_to_db: bool = True) -> Dict[str, Any]:
    """
    Calculate comprehensive matching score between a candidate and a job
    using the multi-dimensional AI Matching engine.
    """
    cand_dict = candidate_to_dict(candidate)
    job_dict = job_to_dict(job)

    result = calculate_matching_score(cand_dict, job_dict)
    total_score = Decimal(str(result['matching_score']))
    breakdown = result['score_breakdown']

    result_data = {
        'candidate_id': candidate.candidate_id,
        'job_id': job.job_id,
        'matching_score': float(total_score),
        'overall_recommendation': result['overall_recommendation'],
        'score_breakdown': breakdown,
        'matched_skills': result['matched_skills'],
        'missing_skills': result['missing_skills'],
        'bonus_skills': result['bonus_skills'],
        'skill_match_details': result['skill_match_details'],
        'experience_match': breakdown['experience_match'],
        'education_match': breakdown['education_match'],
        'salary_match': breakdown['salary_match'],
        'explanation': result['explanation'],
        'calculated_at': timezone.now()
    }

    if save_to_db:
        match_obj, created = AiMatchResults.objects.update_or_create(
            candidate=candidate,
            job=job,
            defaults={
                'matching_score': total_score,
                'matched_skills': result['matched_skills'],
                'missing_skills': result['missing_skills'],
                'skill_match_details': result['skill_match_details'],
                'experience_match': Decimal(str(breakdown['experience_match'])),
                'education_match': Decimal(str(breakdown['education_match'])),
                'salary_match': Decimal(str(breakdown['salary_match'])),
                'overall_recommendation': result['overall_recommendation'],
                'calculated_at': timezone.now()
            }
        )
        result_data['match_id'] = match_obj.match_id

    return result_data


def get_recommended_jobs_for_candidate(
    candidate: Candidates,
    limit: int = 10,
    min_score: float = 0.0,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Rank and return top matching active jobs for a candidate.
    """
    active_jobs = Jobs.objects.filter(status='active').select_related('company')
    cand_dict = candidate_to_dict(candidate)
    jobs_dicts = [job_to_dict(j) for j in active_jobs]

    ranked = rank_jobs_for_candidate(
        candidate_data=cand_dict,
        jobs_list=jobs_dicts,
        limit=limit,
        min_score=min_score,
        location=location
    )

    # Persist the top results to AiMatchResults
    for r in ranked:
        job_obj = active_jobs.filter(pk=r['job_id']).first()
        if job_obj:
            AiMatchResults.objects.update_or_create(
                candidate=candidate,
                job=job_obj,
                defaults={
                    'matching_score': Decimal(str(r['matching_score'])),
                    'matched_skills': r['matched_skills'],
                    'missing_skills': r['missing_skills'],
                    'skill_match_details': r.get('score_breakdown', {}),
                    'overall_recommendation': r['overall_recommendation'],
                    'calculated_at': timezone.now()
                }
            )

    return ranked


def get_recommended_candidates_for_job(
    job: Jobs,
    limit: int = 10,
    min_score: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Rank and return top matching candidates for a job opening.
    """
    candidates = Candidates.objects.all().select_related('user')
    job_dict = job_to_dict(job)
    cand_dicts = [candidate_to_dict(c) for c in candidates]

    return rank_candidates_for_job(
        job_data=job_dict,
        candidates_list=cand_dicts,
        limit=limit,
        min_score=min_score
    )


def extract_skills_service(text: str) -> List[Dict[str, Any]]:
    """Extract and normalize skills from free-form text."""
    return extract_skills_from_text(text)


def parse_cv_service(text: str) -> Dict[str, Any]:
    """Parse unstructured CV text into a structured profile."""
    return parse_cv_text(text)


def stateless_recommend_jobs_for_cv_text(
    cv_text: str,
    limit: int = 10,
    min_score: float = 0.0
) -> Dict[str, Any]:
    """
    Parse CV text dynamically and recommend top jobs from the active job database.
    """
    parsed = parse_cv_text(cv_text)
    active_jobs = Jobs.objects.filter(status='active').select_related('company')
    jobs_dicts = [job_to_dict(j) for j in active_jobs]

    ranked = rank_jobs_for_candidate(
        candidate_data=parsed,
        jobs_list=jobs_dicts,
        limit=limit,
        min_score=min_score
    )

    return {
        'parsed_candidate_profile': parsed,
        'recommended_jobs': ranked
    }


def get_ai_evaluation_metrics() -> Dict[str, Any]:
    """Run evaluation and return Precision@K, Recall@K, NDCG@K, MRR."""
    return run_recommendation_evaluation()


def extract_text_from_file(uploaded_file) -> str:
    """Extract plain text from uploaded PDF, DOCX, or text file."""
    name = (getattr(uploaded_file, 'name', '') or '').lower()
    if hasattr(uploaded_file, 'read'):
        content = uploaded_file.read()
    else:
        content = b''

    if name.endswith('.pdf'):
        try:
            import io
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            pages_text = [page.extract_text() or '' for page in reader.pages]
            return '\n'.join(pages_text).strip()
        except Exception as e:
            raise ValueError(f'Không thể đọc nội dung file PDF: {e}')

    elif name.endswith('.docx'):
        try:
            import io
            import docx
            doc = docx.Document(io.BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text]
            return '\n'.join(paragraphs).strip()
        except Exception as e:
            raise ValueError(f'Không thể đọc nội dung file DOCX: {e}')

    else:
        try:
            return content.decode('utf-8').strip()
        except UnicodeDecodeError:
            return content.decode('latin-1', errors='replace').strip()


def process_and_save_candidate_cv(
    candidate: Candidates,
    cv_text: str,
    file_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parses unstructured CV text, updates Candidate record, extracted skills,
    education, and pre-calculates and persists ranked AI matching scores.
    """
    from .models import Skills

    parsed = parse_cv_text(cv_text)

    # 1. Update Candidate profile fields from CV
    full_name = parsed.get('full_name')
    if full_name and len(full_name.strip()) >= 2 and full_name != 'Ứng viên Tiềm năng':
        candidate.full_name = full_name.strip()

    phone = parsed.get('phone')
    if phone:
        candidate.phone = phone

    location = parsed.get('location')
    if location:
        candidate.address = location

    desired_pos = parsed.get('desired_position')
    if desired_pos:
        candidate.desired_position = desired_pos

    years = parsed.get('years_of_experience')
    if years is not None and years >= 0:
        candidate.years_of_experience = years

    summary = parsed.get('summary')
    if summary:
        candidate.summary = summary

    if file_url:
        candidate.cv_file_url = file_url

    candidate.save()

    # 2. Synchronize Skills
    skills_cache = {s.skill_name.lower(): s for s in Skills.objects.all()}
    extracted_skills = parsed.get('skills', [])
    for s_info in extracted_skills:
        s_name = s_info.get('skill_name', '').strip()
        if not s_name:
            continue
        category = s_info.get('category', 'Technical')
        skill_obj = skills_cache.get(s_name.lower())
        if not skill_obj:
            skill_obj, _ = Skills.objects.get_or_create(
                skill_name=s_name,
                defaults={'category': category, 'description': f'Kỹ năng {s_name}'}
            )
            skills_cache[s_name.lower()] = skill_obj

        CandidateSkills.objects.update_or_create(
            candidate=candidate,
            skill=skill_obj,
            defaults={
                'proficiency_level': s_info.get('level', 'intermediate'),
                'years_of_experience': s_info.get('years', max(candidate.years_of_experience or 1, 1))
            }
        )

    # 3. Synchronize Education
    edu_level = parsed.get('education_level', 'Bachelor')
    edu_detail = parsed.get('education_detail', '')
    institution = 'Đại học'
    major = candidate.desired_position or 'Công nghệ thông tin'

    if edu_detail and '-' in edu_detail:
        parts = edu_detail.split('-', 1)
        major = parts[0].strip()
        institution = re.sub(r'\(.*?\)', '', parts[1]).strip()
    elif edu_detail:
        major = edu_detail.strip()

    edu_qs = Education.objects.filter(candidate=candidate)
    if edu_qs.exists():
        edu_obj = edu_qs.first()
        edu_obj.degree = edu_level
        edu_obj.institution_name = institution
        edu_obj.major = major
        edu_obj.save()
        edu_qs.exclude(pk=edu_obj.pk).delete()
    else:
        Education.objects.create(
            candidate=candidate,
            degree=edu_level,
            institution_name=institution,
            major=major
        )

    # 4. Automatically compute and persist AI Matching recommendations
    recommendations = get_recommended_jobs_for_candidate(candidate, limit=10)

    return {
        'parsed': parsed,
        'recommendations': recommendations
    }
