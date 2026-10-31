"""
AI Matching Engine for SmartJob
Calculates multi-dimensional Matching Score between Candidates and Jobs:
- Skill Compatibility & Required Coverage (50%)
- Semantic & Text Cosine Similarity (20%)
- Experience Level Fit (15%)
- Salary Compatibility (10%)
- Education Level Fit (5%)
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from .taxonomy import SkillTaxonomy, normalize_skill, get_skill_category
from .text_similarity import compute_semantic_similarity
from .skill_extractor import extract_skills_from_text


# Proficiency numerical scale
PROFICIENCY_LEVELS = {
    'beginner': 1,
    'intermediate': 2,
    'advanced': 3,
    'expert': 4
}

# Degree numerical scale
DEGREE_LEVELS = {
    'associate': 1,
    'bachelor': 2,
    'master': 3,
    'phd': 4
}

# Component Weights (Sum = 1.0)
WEIGHT_SKILLS = Decimal('0.50')
WEIGHT_SEMANTIC = Decimal('0.20')
WEIGHT_EXPERIENCE = Decimal('0.15')
WEIGHT_SALARY = Decimal('0.10')
WEIGHT_EDUCATION = Decimal('0.05')


class MatchingEngine:
    """
    Core AI matching engine providing score computation, explainability,
    and recommendation labeling.
    """

    def __init__(self):
        self.taxonomy = SkillTaxonomy.get_instance()

    def calculate_match(
        self,
        candidate_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive matching score between candidate profile and job posting.
        """
        # ======================================================================
        # 1. SKILL MATCHING (50% WEIGHT)
        # ======================================================================
        cand_skills_map = {}
        for s in candidate_data.get('skills', []):
            name = s.get('name') or s.get('skill_name')
            norm_name = normalize_skill(name) or name
            level_str = (s.get('level') or s.get('proficiency_level') or 'intermediate').lower()
            cand_skills_map[norm_name.lower()] = {
                'canonical_name': norm_name,
                'level': level_str,
                'level_num': PROFICIENCY_LEVELS.get(level_str, 2),
                'years': s.get('years', 1)
            }

        job_skills = job_data.get('required_skills', []) or job_data.get('skills', [])
        
        matched_skills = []
        missing_skills = []
        skill_details = []
        
        total_job_skill_weight = Decimal('0.0')
        earned_skill_weight = Decimal('0.0')
        missing_mandatory_count = 0

        if job_skills:
            for js in job_skills:
                raw_name = js.get('name') or js.get('skill_name')
                skill_name = normalize_skill(raw_name) or raw_name
                req_level = (js.get('level') or js.get('required_level') or 'intermediate').lower()
                req_level_num = PROFICIENCY_LEVELS.get(req_level, 2)
                is_required = js.get('is_required', True)
                base_weight = Decimal(str(js.get('weight', 1.0)))

                if is_required:
                    base_weight *= Decimal('1.5')  # Mandatory multiplier
                total_job_skill_weight += base_weight

                key = skill_name.lower()
                if key in cand_skills_map:
                    cand_info = cand_skills_map[key]
                    cand_level_num = cand_info['level_num']

                    if cand_level_num >= req_level_num:
                        ratio = Decimal('1.0')
                    else:
                        ratio = Decimal(str(cand_level_num)) / Decimal(str(req_level_num))

                    earned = base_weight * ratio
                    earned_skill_weight += earned

                    match_pct = float(round(ratio * 100, 1))
                    matched_skills.append({
                        'skill_name': skill_name,
                        'candidate_level': cand_info['level'],
                        'required_level': req_level,
                        'is_required': is_required,
                        'match_ratio': match_pct
                    })
                    skill_details.append({
                        'skill_name': skill_name,
                        'status': 'matched',
                        'is_required': is_required,
                        'score': match_pct
                    })
                else:
                    if is_required:
                        missing_mandatory_count += 1
                    missing_skills.append({
                        'skill_name': skill_name,
                        'required_level': req_level,
                        'is_required': is_required
                    })
                    skill_details.append({
                        'skill_name': skill_name,
                        'status': 'missing',
                        'is_required': is_required,
                        'score': 0.0
                    })

            raw_skill_score = (earned_skill_weight / total_job_skill_weight * Decimal('100.0')) if total_job_skill_weight > 0 else Decimal('100.0')
            
            # Penalty for missing mandatory skills: -10% per missing mandatory skill
            mandatory_penalty = Decimal(str(missing_mandatory_count * 8.0))
            skill_score = max(Decimal('0.0'), raw_skill_score - mandatory_penalty)

            # Bonus for candidate extra skills in relevant categories (up to +8%)
            candidate_keys = set(cand_skills_map.keys())
            job_keys = { (normalize_skill(js.get('name') or js.get('skill_name')) or '').lower() for js in job_skills }
            bonus_skills_list = []
            for k, info in cand_skills_map.items():
                if k not in job_keys:
                    bonus_skills_list.append(info['canonical_name'])
            bonus_score = min(Decimal('8.0'), Decimal(str(len(bonus_skills_list) * 1.5)))
            skill_score = min(Decimal('100.0'), skill_score + bonus_score)
        else:
            # If job didn't specify structured skills, extract from description
            jd_text = (job_data.get('job_description', '') + ' ' + job_data.get('requirements', '')).strip()
            extracted = extract_skills_from_text(jd_text)
            if extracted:
                return self.calculate_match(candidate_data, {**job_data, 'required_skills': extracted})
            skill_score = Decimal('70.0')
            bonus_skills_list = []

        # ======================================================================
        # 2. SEMANTIC CONTENT SIMILARITY (20% WEIGHT)
        # ======================================================================
        cand_text = " ".join([
            str(candidate_data.get('desired_position', '')),
            str(candidate_data.get('summary', '')),
            str(candidate_data.get('raw_cv_text', '')),
            " ".join([s['canonical_name'] for s in cand_skills_map.values()])
        ])
        job_text = " ".join([
            str(job_data.get('job_title', '')),
            str(job_data.get('job_description', '')),
            str(job_data.get('requirements', ''))
        ])

        cosine_sim = compute_semantic_similarity(cand_text, job_text)
        semantic_score = Decimal(str(round(cosine_sim * 100.0, 2)))

        # ======================================================================
        # 3. EXPERIENCE MATCHING (15% WEIGHT)
        # ======================================================================
        cand_exp = Decimal(str(candidate_data.get('years_of_experience', 0) or 0))
        req_exp = Decimal(str(job_data.get('years_of_experience_required', 0) or 0))

        if req_exp <= 0:
            exp_score = Decimal('100.0')
        elif cand_exp >= req_exp:
            # Full score, slight grace for extreme overqualification
            diff = cand_exp - req_exp
            if diff > 8:
                exp_score = Decimal('92.0')
            else:
                exp_score = Decimal('100.0')
        else:
            # Underqualified ratio
            ratio = cand_exp / req_exp
            exp_score = min(Decimal('100.0'), max(Decimal('20.0'), ratio * Decimal('100.0')))

        # ======================================================================
        # 4. SALARY COMPATIBILITY (10% WEIGHT)
        # ======================================================================
        cand_salary = candidate_data.get('desired_salary')
        job_min = job_data.get('salary_min')
        job_max = job_data.get('salary_max')

        if cand_salary and job_max:
            c_sal = Decimal(str(cand_salary))
            j_max = Decimal(str(job_max))
            j_min = Decimal(str(job_min)) if job_min else Decimal('0')

            if c_sal <= j_max:
                salary_score = Decimal('100.0')
            else:
                diff = c_sal - j_max
                penalty = (diff / j_max) * Decimal('50.0')
                salary_score = max(Decimal('20.0'), Decimal('100.0') - penalty)
        else:
            salary_score = Decimal('85.0')

        # ======================================================================
        # 5. EDUCATION LEVEL MATCHING (5% WEIGHT)
        # ======================================================================
        cand_edu = str(candidate_data.get('education_level', '') or '').lower()
        if not cand_edu and isinstance(candidate_data.get('education'), dict):
            cand_edu = str(candidate_data['education'].get('degree', '')).lower()
            
        req_edu = str(job_data.get('education_level_required', '') or '').lower()

        cand_edu_level = DEGREE_LEVELS.get(cand_edu, 2)  # default Bachelor
        req_edu_level = DEGREE_LEVELS.get(req_edu, 2)    # default Bachelor

        if cand_edu_level >= req_edu_level:
            edu_score = Decimal('100.0')
        elif cand_edu_level == req_edu_level - 1:
            edu_score = Decimal('80.0')
        else:
            edu_score = Decimal('60.0')

        # ======================================================================
        # TOTAL WEIGHTED SCORE & RECOMMENDATION
        # ======================================================================
        total_score = (
            skill_score * WEIGHT_SKILLS +
            semantic_score * WEIGHT_SEMANTIC +
            exp_score * WEIGHT_EXPERIENCE +
            salary_score * WEIGHT_SALARY +
            edu_score * WEIGHT_EDUCATION
        )
        total_score = round(min(Decimal('100.0'), max(Decimal('0.0'), total_score)), 2)

        # Recommendation Category
        if total_score >= Decimal('80.0'):
            recommendation = 'highly_recommended'
        elif total_score >= Decimal('65.0'):
            recommendation = 'recommended'
        elif total_score >= Decimal('45.0'):
            recommendation = 'potential'
        else:
            recommendation = 'not_recommended'

        # Natural language explainability rationale (Vietnamese)
        explanation = self._build_explanation(
            total_score=float(total_score),
            skill_score=float(skill_score),
            semantic_score=float(semantic_score),
            exp_score=float(exp_score),
            salary_score=float(salary_score),
            cand_exp=int(cand_exp),
            req_exp=int(req_exp),
            matched_skills=matched_skills,
            missing_skills=missing_skills
        )

        return {
            'matching_score': float(total_score),
            'overall_recommendation': recommendation,
            'score_breakdown': {
                'skill_match': float(round(skill_score, 2)),
                'semantic_match': float(round(semantic_score, 2)),
                'experience_match': float(round(exp_score, 2)),
                'salary_match': float(round(salary_score, 2)),
                'education_match': float(round(edu_score, 2))
            },
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'bonus_skills': bonus_skills_list,
            'skill_match_details': skill_details,
            'explanation': explanation
        }

    def _build_explanation(
        self,
        total_score: float,
        skill_score: float,
        semantic_score: float,
        exp_score: float,
        salary_score: float,
        cand_exp: int,
        req_exp: int,
        matched_skills: list,
        missing_skills: list
    ) -> str:
        """Construct detailed explainability rationale in Vietnamese."""
        parts = []

        if total_score >= 80.0:
            parts.append(f"Hồ sơ ứng viên cực kỳ phù hợp với vị trí này (Điểm tổng hợp: {total_score}%).")
        elif total_score >= 65.0:
            parts.append(f"Hồ sơ ứng viên phù hợp tốt với phần lớn yêu cầu công việc ({total_score}%).")
        elif total_score >= 45.0:
            parts.append(f"Hồ sơ có tiềm năng phát triển nhưng còn thiếu một số kỹ năng trọng yếu ({total_score}%).")
        else:
            parts.append(f"Độ tương thích thấp ({total_score}%), khác biệt nhiều về chuyên môn hoặc yêu cầu kinh nghiệm.")

        # Skills note
        if matched_skills:
            m_names = [s['skill_name'] for s in matched_skills[:5]]
            parts.append(f"Khớp {len(matched_skills)} kỹ năng chính: {', '.join(m_names)}.")
        
        mandatory_missing = [s['skill_name'] for s in missing_skills if s.get('is_required')]
        if mandatory_missing:
            parts.append(f"Cần bổ sung các kỹ năng bắt buộc: {', '.join(mandatory_missing)}.")
        elif missing_skills:
            opt_missing = [s['skill_name'] for s in missing_skills[:3]]
            parts.append(f"Chưa có một số kỹ năng ưu tiên: {', '.join(opt_missing)}.")

        # Experience note
        if cand_exp >= req_exp:
            parts.append(f"Kinh nghiệm làm việc đạt chuẩn ({cand_exp}/{req_exp} năm).")
        elif req_exp > 0:
            parts.append(f"Kinh nghiệm ({cand_exp} năm) thấp hơn yêu cầu ({req_exp} năm).")

        return " ".join(parts)


_engine = MatchingEngine()


def calculate_matching_score(candidate_data: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
    return _engine.calculate_match(candidate_data, job_data)

