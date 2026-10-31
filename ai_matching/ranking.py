"""
Job & Candidate Ranking Engine
Ranks job postings for a given candidate, or ranks candidates for a job opening.
Supports filtering by minimum matching score, location, and salary.
"""

from typing import Any, Dict, List, Optional
from .matching_engine import MatchingEngine, calculate_matching_score


class RankingEngine:
    """
    Ranks items based on multi-dimensional AI Matching Scores.
    """

    def __init__(self, engine: Optional[MatchingEngine] = None):
        self.engine = engine or MatchingEngine()

    def rank_jobs_for_candidate(
        self,
        candidate_data: Dict[str, Any],
        jobs_list: List[Dict[str, Any]],
        limit: int = 10,
        min_score: float = 0.0,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Rank a collection of jobs for a single candidate.
        Returns top-K jobs sorted descending by matching score.
        """
        scored_jobs = []

        for job in jobs_list:
            # Optional location filter
            if location and job.get('location'):
                if location.lower() not in job['location'].lower():
                    continue

            match_result = self.engine.calculate_match(candidate_data, job)
            score = match_result['matching_score']

            if score < min_score:
                continue

            scored_jobs.append({
                'job_id': job.get('job_id'),
                'job_title': job.get('job_title'),
                'company_name': job.get('company_name') or (job.get('company', {}).get('company_name') if isinstance(job.get('company'), dict) else 'Company'),
                'location': job.get('location'),
                'position_level': job.get('position_level'),
                'employment_type': job.get('employment_type'),
                'salary_min': job.get('salary_min'),
                'salary_max': job.get('salary_max'),
                'salary_currency': job.get('salary_currency', 'VND'),
                'matching_score': score,
                'overall_recommendation': match_result['overall_recommendation'],
                'score_breakdown': match_result['score_breakdown'],
                'matched_skills': match_result['matched_skills'],
                'missing_skills': match_result['missing_skills'],
                'bonus_skills': match_result['bonus_skills'],
                'explanation': match_result['explanation']
            })

        # Sort descending by matching score
        scored_jobs.sort(key=lambda x: x['matching_score'], reverse=True)
        return scored_jobs[:limit]

    def rank_candidates_for_job(
        self,
        job_data: Dict[str, Any],
        candidates_list: List[Dict[str, Any]],
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Rank a collection of candidates for a single job opening.
        Returns top-K candidates sorted descending by matching score.
        """
        scored_candidates = []

        for cand in candidates_list:
            match_result = self.engine.calculate_match(cand, job_data)
            score = match_result['matching_score']

            if score < min_score:
                continue

            scored_candidates.append({
                'candidate_id': cand.get('candidate_id'),
                'full_name': cand.get('full_name'),
                'email': cand.get('email'),
                'phone': cand.get('phone'),
                'desired_position': cand.get('desired_position'),
                'years_of_experience': cand.get('years_of_experience'),
                'desired_salary': cand.get('desired_salary'),
                'matching_score': score,
                'overall_recommendation': match_result['overall_recommendation'],
                'score_breakdown': match_result['score_breakdown'],
                'matched_skills': match_result['matched_skills'],
                'missing_skills': match_result['missing_skills'],
                'bonus_skills': match_result['bonus_skills'],
                'explanation': match_result['explanation']
            })

        scored_candidates.sort(key=lambda x: x['matching_score'], reverse=True)
        return scored_candidates[:limit]


_ranking = RankingEngine()


def rank_jobs_for_candidate(
    candidate_data: Dict[str, Any],
    jobs_list: List[Dict[str, Any]],
    limit: int = 10,
    min_score: float = 0.0,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    return _ranking.rank_jobs_for_candidate(candidate_data, jobs_list, limit, min_score, location)


def rank_candidates_for_job(
    job_data: Dict[str, Any],
    candidates_list: List[Dict[str, Any]],
    limit: int = 10,
    min_score: float = 0.0
) -> List[Dict[str, Any]]:
    return _ranking.rank_candidates_for_job(job_data, candidates_list, limit, min_score)

