"""
TH3-SmartJob AI/ML Matching Package (Checklist 02)
==================================================
Provides:
- Skill Extraction & Normalization from CVs and Job Descriptions
- Multi-dimensional Matching Score Engine
- Candidate & Job Recommendation Ranking
- Precision@K, Recall@K, NDCG@K Evaluation Benchmark
"""

from .taxonomy import SkillTaxonomy, normalize_skill, get_skill_category
from .skill_extractor import (
    SkillExtractor,
    extract_skills_from_text,
    parse_cv_text,
    parse_job_description
)
from .matching_engine import (
    MatchingEngine,
    calculate_matching_score
)
from .ranking import (
    RankingEngine,
    rank_jobs_for_candidate,
    rank_candidates_for_job
)
from .evaluator import (
    RecommendationEvaluator,
    run_recommendation_evaluation
)

__all__ = [
    'SkillTaxonomy',
    'normalize_skill',
    'get_skill_category',
    'SkillExtractor',
    'extract_skills_from_text',
    'parse_cv_text',
    'parse_job_description',
    'MatchingEngine',
    'calculate_matching_score',
    'RankingEngine',
    'rank_jobs_for_candidate',
    'rank_candidates_for_job',
    'RecommendationEvaluator',
    'run_recommendation_evaluation',
]

