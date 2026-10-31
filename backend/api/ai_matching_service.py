"""
AI Matching Service for SmartJob
Integrates the advanced AI/ML Matching Package with Django Models & PostgreSQL.
"""

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
