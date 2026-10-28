"""
AI Matching Service for SmartJob
Calculates Matching Score between Candidate and Job
"""

from decimal import Decimal
from django.utils import timezone
from .models import (
    Candidates, Jobs, CandidateSkills, JobSkills,
    Education, Experience, AiMatchResults
)

LEVEL_WEIGHTS = {
    'beginner': 1,
    'intermediate': 2,
    'advanced': 3,
    'expert': 4
}


def calculate_match(candidate: Candidates, job: Jobs, save_to_db: bool = True) -> dict:
    """
    Calculate comprehensive matching score between a candidate and a job
    """
    # 1. SKILL MATCHING (~60% weight)
    candidate_skills = {
        cs.skill_id: {
            'name': cs.skill.skill_name,
            'level': (cs.proficiency_level or 'intermediate').lower(),
            'level_num': LEVEL_WEIGHTS.get((cs.proficiency_level or 'intermediate').lower(), 2),
            'years': cs.years_of_experience or 0
        }
        for cs in CandidateSkills.objects.filter(candidate=candidate).select_related('skill')
    }

    job_skills = JobSkills.objects.filter(job=job).select_related('skill')
    
    total_skill_weight = Decimal('0.0')
    earned_skill_weight = Decimal('0.0')
    matched_skills = []
    missing_skills = []
    skill_details = []

    if job_skills.exists():
        for js in job_skills:
            weight = Decimal(str(js.weight or 1.0))
            if js.is_required:
                weight *= Decimal('1.5')  # Tăng trọng số cho kỹ năng bắt buộc
            total_skill_weight += weight

            req_level = (js.required_level or 'intermediate').lower()
            req_level_num = LEVEL_WEIGHTS.get(req_level, 2)

            if js.skill_id in candidate_skills:
                cand_info = candidate_skills[js.skill_id]
                cand_level_num = cand_info['level_num']

                if cand_level_num >= req_level_num:
                    ratio = Decimal('1.0')
                else:
                    ratio = Decimal(str(cand_level_num)) / Decimal(str(req_level_num))
                
                earned = weight * ratio
                earned_skill_weight += earned

                matched_skills.append({
                    'skill_id': js.skill_id,
                    'skill_name': js.skill.skill_name,
                    'candidate_level': cand_info['level'],
                    'required_level': req_level,
                    'match_ratio': float(round(ratio * 100, 1))
                })
                skill_details.append({
                    'skill_name': js.skill.skill_name,
                    'status': 'matched',
                    'is_required': js.is_required
                })
            else:
                missing_skills.append({
                    'skill_id': js.skill_id,
                    'skill_name': js.skill.skill_name,
                    'required_level': req_level,
                    'is_required': js.is_required
                })
                skill_details.append({
                    'skill_name': js.skill.skill_name,
                    'status': 'missing',
                    'is_required': js.is_required
                })

        skill_score = (earned_skill_weight / total_skill_weight * Decimal('100.0')) if total_skill_weight > 0 else Decimal('100.0')
    else:
        # Nếu job không ghi rõ kỹ năng yêu cầu
        skill_score = Decimal('70.0')

    # 2. EXPERIENCE MATCHING (~25% weight)
    cand_exp = Decimal(str(candidate.years_of_experience or 0))
    job_exp_req = Decimal(str(job.years_of_experience_required or 0))

    if job_exp_req == 0:
        exp_score = Decimal('100.0')
    elif cand_exp >= job_exp_req:
        exp_score = Decimal('100.0')
    else:
        exp_score = min(Decimal('100.0'), (cand_exp / job_exp_req) * Decimal('100.0'))

    # 3. EDUCATION MATCHING (~5% weight)
    educations = Education.objects.filter(candidate=candidate)
    if educations.exists():
        edu_score = Decimal('100.0')
    else:
        edu_score = Decimal('70.0')

    # 4. SALARY MATCHING (~10% weight)
    cand_salary = candidate.desired_salary
    job_min = job.salary_min
    job_max = job.salary_max

    if cand_salary and job_max:
        if cand_salary <= job_max:
            salary_score = Decimal('100.0')
        else:
            diff = cand_salary - job_max
            penalty = (diff / job_max) * Decimal('50.0')
            salary_score = max(Decimal('20.0'), Decimal('100.0') - penalty)
    else:
        salary_score = Decimal('90.0')

    # TOTAL MATCHING SCORE (0 - 100)
    # Skill: 60%, Exp: 25%, Salary: 10%, Edu: 5%
    total_score = (
        skill_score * Decimal('0.60') +
        exp_score * Decimal('0.25') +
        salary_score * Decimal('0.10') +
        edu_score * Decimal('0.05')
    )
    total_score = min(Decimal('100.0'), max(Decimal('0.0'), total_score))
    total_score = round(total_score, 2)

    # RECOMMENDATION
    if total_score >= Decimal('80.0'):
        recommendation = 'highly_recommended'
    elif total_score >= Decimal('65.0'):
        recommendation = 'recommended'
    elif total_score >= Decimal('45.0'):
        recommendation = 'potential'
    else:
        recommendation = 'not_recommended'

    result_data = {
        'candidate_id': candidate.candidate_id,
        'job_id': job.job_id,
        'matching_score': float(total_score),
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'skill_match_details': skill_details,
        'experience_match': float(round(exp_score, 2)),
        'education_match': float(round(edu_score, 2)),
        'salary_match': float(round(salary_score, 2)),
        'overall_recommendation': recommendation,
        'calculated_at': timezone.now()
    }

    if save_to_db:
        # Cập nhật hoặc lưu vào AiMatchResults
        match_obj, created = AiMatchResults.objects.update_or_create(
            candidate=candidate,
            job=job,
            defaults={
                'matching_score': total_score,
                'matched_skills': matched_skills,
                'missing_skills': missing_skills,
                'skill_match_details': skill_details,
                'experience_match': exp_score,
                'education_match': edu_score,
                'salary_match': salary_score,
                'overall_recommendation': recommendation,
                'calculated_at': timezone.now()
            }
        )
        result_data['match_id'] = match_obj.match_id

    return result_data


def get_recommended_jobs_for_candidate(candidate: Candidates, limit: int = 10):
    """
    Find and rank top matching active jobs for a candidate
    """
    active_jobs = Jobs.objects.filter(status='active').select_related('company')
    results = []
    for job in active_jobs:
        match_info = calculate_match(candidate, job, save_to_db=True)
        results.append({
            'job_id': job.job_id,
            'job_title': job.job_title,
            'company_name': job.company.company_name,
            'company_logo': job.company.logo_url,
            'location': job.location,
            'salary_min': float(job.salary_min) if job.salary_min else None,
            'salary_max': float(job.salary_max) if job.salary_max else None,
            'salary_currency': job.salary_currency,
            'matching_score': match_info['matching_score'],
            'overall_recommendation': match_info['overall_recommendation'],
            'matched_skills': match_info['matched_skills'],
            'missing_skills': match_info['missing_skills']
        })

    results.sort(key=lambda x: x['matching_score'], reverse=True)
    return results[:limit]


def get_recommended_candidates_for_job(job: Jobs, limit: int = 10):
    """
    Find and rank top matching candidates for a job
    """
    candidates = Candidates.objects.all().select_related('user')
    results = []
    for cand in candidates:
        match_info = calculate_match(cand, job, save_to_db=True)
        results.append({
            'candidate_id': cand.candidate_id,
            'full_name': cand.full_name,
            'avatar_url': cand.avatar_url,
            'desired_position': cand.desired_position,
            'years_of_experience': cand.years_of_experience,
            'desired_salary': float(cand.desired_salary) if cand.desired_salary else None,
            'matching_score': match_info['matching_score'],
            'overall_recommendation': match_info['overall_recommendation'],
            'matched_skills': match_info['matched_skills'],
            'missing_skills': match_info['missing_skills']
        })

    results.sort(key=lambda x: x['matching_score'], reverse=True)
    return results[:limit]
