"""
AI Skill Extractor & Normalizer for CVs and Job Descriptions
Extracts canonical skills, proficiency levels, years of experience,
and education levels from unstructured text (Vietnamese & English).
"""

import re
import unicodedata
from typing import Dict, List, Optional, Set, Tuple, Any
from .taxonomy import SkillTaxonomy, normalize_skill, get_skill_category


# Level indicators in English and Vietnamese
LEVEL_PATTERNS = {
    'expert': [
        r'\bexpert\b', r'\blead\b', r'\barchitect\b', r'\bchuyên gia\b',
        r'\bchuyên sâu\b', r'\bbậc thầy\b', r'\bmastery\b', r'\bprincipal\b'
    ],
    'advanced': [
        r'\bsenior\b', r'\badvanced\b', r'\bthành thạo\b', r'\bthạo\b',
        r'\bchuyên nghiệp\b', r'\bproficient\b', r'\bfluent\b', r'\bchắc chắn\b',
        r'\bvững vàng\b', r'\bstrong experience\b', r'\bdeep knowledge\b'
    ],
    'intermediate': [
        r'\bmid-level\b', r'\bmiddle\b', r'\bintermediate\b', r'\bkhá\b',
        r'\btương đối\b', r'\bcó kinh nghiệm\b', r'\bexperienced\b', r'\bgood knowledge\b'
    ],
    'beginner': [
        r'\bjunior\b', r'\bfresher\b', r'\bintern\b', r'\bbeginner\b',
        r'\bcơ bản\b', r'\bnhập môn\b', r'\bbasic\b', r'\bfamiliar\b',
        r'\btìm hiểu\b', r'\bhiểu biết cơ bản\b', r'\bentry-level\b'
    ]
}

# Degree patterns
DEGREE_PATTERNS = [
    (r'\b(tiến sĩ|phd|doctorate)\b', 'PhD'),
    (r'\b(thạc sĩ|master|ms|m\.s\.)\b', 'Master'),
    (r'\b(kỹ sư|cử nhân|đại học|bachelor|b\.s\.|b\.a\.|university degree)\b', 'Bachelor'),
    (r'\b(cao đẳng|trung cấp|associate|diploma)\b', 'Associate')
]


def clean_text(text: str) -> str:
    """Normalize text encoding and basic whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize('NFC', text)
    # Replace multiple spaces, tabs, newlines with space while keeping basic punctuation
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


class SkillExtractor:
    """
    Extracts and normalizes technical skills from free-form text.
    """

    def __init__(self, taxonomy: Optional[SkillTaxonomy] = None):
        self.taxonomy = taxonomy or SkillTaxonomy.get_instance()
        self._build_regex_patterns()

    def _build_regex_patterns(self):
        """
        Pre-compile regex patterns for all aliases to ensure fast, safe boundary matching.
        Handles special characters like C++, C#, .NET, CI/CD, Vue.js, etc.
        """
        aliases_map = self.taxonomy.get_all_aliases()
        # Sort by alias length descending so longer phrases like "machine learning" match before "ml"
        sorted_aliases = sorted(aliases_map.keys(), key=lambda x: len(x), reverse=True)

        self.compiled_aliases = []
        for alias in sorted_aliases:
            canonical = aliases_map[alias]
            # Escape regex characters except space
            escaped = re.escape(alias)
            
            # Words with symbols need special boundary handling
            if re.match(r'^[a-zA-Z0-9\s]+$', alias):
                pattern = rf'(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])'
            else:
                pattern = rf'(?:\b|(?<=\s)){escaped}(?:\b|(?=\s|[.,;:!?\)]))'
                
            regex = re.compile(pattern, re.IGNORECASE)
            self.compiled_aliases.append((alias, canonical, regex))

    def extract_skills(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract unique standardized skills from text, along with category,
        detected proficiency level, and occurrence count.
        """
        if not text:
            return []

        cleaned = clean_text(text)
        found_skills: Dict[str, Dict[str, Any]] = {}

        # Search each alias
        for alias, canonical, regex in self.compiled_aliases:
            matches = list(regex.finditer(cleaned))
            if not matches:
                continue

            if canonical not in found_skills:
                category = self.taxonomy.get_category(canonical)
                # Detect level by analyzing text near the first occurrences
                level = self._detect_skill_level(cleaned, matches)
                found_skills[canonical] = {
                    'skill_name': canonical,
                    'category': category,
                    'proficiency_level': level,
                    'matched_alias': alias,
                    'frequency': len(matches)
                }
            else:
                found_skills[canonical]['frequency'] += len(matches)

        return list(found_skills.values())

    def _detect_skill_level(self, text: str, matches: list) -> str:
        """
        Inspect the window around the skill match (± 80 characters) to determine level.
        Default is 'intermediate' if no explicit modifier is found.
        """
        for match in matches:
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 80)
            window = text[start:end].lower()

            for level, patterns in LEVEL_PATTERNS.items():
                for pat in patterns:
                    if re.search(pat, window):
                        return level

        return 'intermediate'

    def extract_experience_years(self, text: str) -> int:
        """
        Detect years of experience specified in text (e.g., '3 năm kinh nghiệm', '5+ years experience').
        """
        if not text:
            return 0

        # Patterns for years of experience
        patterns = [
            r'(\d+)\+?\s*(?:năm|nam|years?|yrs?)\s*(?:kinh nghiệm|kinh nghiem|experience|exp)',
            r'(?:kinh nghiệm|kinh nghiem|experience|exp)\s*(?:từ|khoảng|hơn|over|at least)?\s*(\d+)\+?\s*(?:năm|nam|years?|yrs?)',
            r'(\d+)\+?\s*(?:năm|nam|years?|yrs?)\s*(?:làm việc|chuyên môn|in the field)',
        ]

        found_years = []
        for pat in patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                try:
                    val = int(m.group(1))
                    if 0 < val <= 40:
                        found_years.append(val)
                except (ValueError, IndexError):
                    pass

        return max(found_years) if found_years else 0

    def extract_education_level(self, text: str) -> str:
        """
        Detect highest education degree mentioned in text.
        """
        if not text:
            return "Bachelor"

        for pattern, degree in DEGREE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return degree
        return "Bachelor"

    def parse_cv(self, cv_text: str) -> Dict[str, Any]:
        """
        Comprehensive CV parsing: extracts name, email, phone, skills,
        experience years, education, and candidate summary.
        """
        cleaned = clean_text(cv_text)
        
        # 1. Email extraction
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', cv_text)
        email = email_match.group(0) if email_match else ""

        # 2. Phone extraction (supports VN format)
        phone_match = re.search(r'(?:\+?84|0)(?:3|5|7|8|9)\d{8}\b', cv_text.replace(" ", "").replace("-", ""))
        phone = phone_match.group(0) if phone_match else ""

        # 3. Full name heuristic (first line or after "Họ và tên", "Name:")
        name_match = re.search(r'(?:Họ và tên|Họ tên|Full name|Name)\s*[:\-]?\s*([^\r\n,;:]{2,35})', cv_text, re.IGNORECASE)
        if name_match:
            full_name = name_match.group(1).strip()
        else:
            first_line = cv_text.strip().split('\n')[0].strip()
            if 3 <= len(first_line) <= 35 and not any(kw in first_line.lower() for kw in ['cv', 'resume', 'curriculum', 'hồ sơ']):
                full_name = first_line
            else:
                full_name = "Ứng viên Tiềm năng"

        # 4. Desired Position heuristic
        pos_match = re.search(r'(?:Vị trí ứng tuyển|Vị trí|Chức danh|Target Position|Desired Role|Objective)\s*[:\-]?\s*([^\n\r.]+)', cv_text, re.IGNORECASE)
        desired_position = pos_match.group(1).strip() if pos_match else "Software Engineer"

        # 5. Extract Skills
        extracted_skills = self.extract_skills(cv_text)

        # 6. Extract Experience
        exp_years = self.extract_experience_years(cv_text)

        # 7. Extract Education
        edu_level = self.extract_education_level(cv_text)

        return {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'desired_position': desired_position,
            'skills': extracted_skills,
            'years_of_experience': exp_years,
            'education_level': edu_level,
            'raw_text_length': len(cv_text),
            'summary': cleaned[:300] + ("..." if len(cleaned) > 300 else "")
        }

    def parse_job_requirements(self, jd_text: str) -> Dict[str, Any]:
        """
        Extract required skills, experience, and mandatory criteria from a Job Description.
        """
        extracted_skills = self.extract_skills(jd_text)
        exp_required = self.extract_experience_years(jd_text)
        edu_required = self.extract_education_level(jd_text)

        # Detect mandatory requirements
        # (e.g. phrases like "Bắt buộc", "Yêu cầu", "Must have", "Required")
        mandatory_skills = []
        for s in extracted_skills:
            # Check if skill appears in required/must-have section
            name = s['skill_name']
            pat = rf'(?:bắt buộc|must have|yêu cầu|required).*?{re.escape(name)}'
            if re.search(pat, jd_text, re.IGNORECASE):
                mandatory_skills.append(name)

        return {
            'skills': extracted_skills,
            'mandatory_skills': mandatory_skills,
            'years_of_experience_required': exp_required,
            'education_level_required': edu_required
        }


# Global singleton instance
_extractor = SkillExtractor()


def extract_skills_from_text(text: str) -> List[Dict[str, Any]]:
    return _extractor.extract_skills(text)


def parse_cv_text(text: str) -> Dict[str, Any]:
    return _extractor.parse_cv(text)


def parse_job_description(text: str) -> Dict[str, Any]:
    return _extractor.parse_job_requirements(text)
