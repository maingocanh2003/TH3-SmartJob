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


_VN_ACCENTED_VOWELS = (
    'ăâêôơưáàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ'
    'ĂÂÊÔƠƯÁÀẢÃẠẮẰẲẴẶẤẦẨẪẬÉÈẺẼẸẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌỐỒỔỖỘỚỜỞỠỢÚÙỦŨỤỨỪỬỮỰÝỲỶỸỴ'
)
_ALL_VN_VOWELS = 'aăâeêioôơuưyAĂÂEÊIOÔƠUƯY' + _VN_ACCENTED_VOWELS


def normalize_vietnamese_pdf_text(text: str) -> str:
    """
    Repair spaced Vietnamese diacritics produced by PDF font subsetting
    (e.g. 'Nguy ễ n Lê Tú Anh' -> 'Nguyễn Lê Tú Anh', 'ki ể m th ử' -> 'kiểm thử').
    """
    if not text:
        return ""
    text = unicodedata.normalize('NFC', text)
    text = text.replace('\u00a0', ' ')
    # Join 'đ' / 'Đ' with a following vowel when separated by a single space
    text = re.sub(rf'(?<=[đĐ]) (?=[{_ALL_VN_VOWELS}])', '', text)
    # Join consonant/vowel cluster with a following accented Vietnamese vowel
    text = re.sub(rf'(?<=[b-df-hj-np-tv-zB-DF-HJ-NP-TV-ZđĐuUoOiIưƯ]) (?=[{_VN_ACCENTED_VOWELS}])', '', text)
    # Join accented Vietnamese vowel with a trailing final consonant (ng, nh, ch, c, m, n, p, t, i, u, o, y)
    text = re.sub(rf'(?<=[{_VN_ACCENTED_VOWELS}]) (?=(?:ng|nh|ch|[cmnptiuoy])\b)', '', text)
    # Collapse multiple spaces on the same line while preserving newlines
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text


def clean_text(text: str) -> str:
    """Normalize text encoding and basic whitespace."""
    if not text:
        return ""
    text = normalize_vietnamese_pdf_text(text)
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
            
            # Words with symbols or Vietnamese phrases needing lookaround boundary handling
            if alias.lower() == 'học máy':
                pattern = rf'(?<!khoa\s)(?:\b|(?<=\s)){escaped}(?:\b|(?=\s|[.,;:!?\)]))(?!\s+tính)'
            elif re.match(r'^[a-zA-Z0-9\s]+$', alias):
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
            r'(\d+)\+?\s*(?:năm|nam|years?|yrs?)\s*(?:làm việc|chuyên môn|trong nghề|lập trình|phát triển|in the field)',
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
        Comprehensive CV parsing: extracts contact info, position,
        skills, experience, education, and normalized summary.
        """
        cv_text = normalize_vietnamese_pdf_text(cv_text)
        # Strip TopCV / watermark lines & Private Use Area icons for clean summary & header parsing
        raw_lines = [
            re.sub(r'^[\ue000-\uf8ff\u2600-\u27bf•·\-*⭐]+\s*', '', ln).strip()
            for ln in cv_text.splitlines()
        ]
        non_empty_lines = [
            ln for ln in raw_lines
            if ln and not re.match(r'^(?:©\s*)?(?:topcv\.vn|vietnamworks\.com|itviec\.com|curriculum\s+vitae|cv|resume|hồ\s+sơ)$', ln, re.IGNORECASE)
        ]

        cleaned_lines_text = '\n'.join(non_empty_lines)
        cleaned = clean_text(cleaned_lines_text)

        # 1. Email heuristic
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', cv_text)
        email = email_match.group(0) if email_match else ""

        # 2. Phone heuristic
        phone_match = re.search(r'(?:\+?84|0)(?:\s*\d){9,10}', cv_text)
        phone = re.sub(r'\s+', '', phone_match.group(0)) if phone_match else ""

        # 3. Name & Desired Position heuristics
        full_name = "Ứng viên Tiềm năng"
        name_line_idx = -1
        name_match = re.search(r'(?:Họ và tên|Họ tên|Full name|Name)\s*[:\-]\s*([^\r\n,;:]{2,40})', cv_text, re.IGNORECASE)
        if name_match:
            full_name = name_match.group(1).strip()
        else:
            for idx, ln in enumerate(non_empty_lines[:6]):
                if (
                    2 <= len(ln) <= 42
                    and '@' not in ln
                    and not re.search(r'\d{3,}', ln)
                    and not any(kw in ln.lower() for kw in ['topcv', 'curriculum', 'thông tin cá nhân', 'mục tiêu', 'kinh nghiệm', 'kỹ năng', 'học vấn'])
                ):
                    full_name = ln
                    name_line_idx = idx
                    break

        # 4. Desired Position heuristic
        desired_position = ""
        pos_match = re.search(r'(?:Vị trí ứng tuyển|Vị trí|Chức danh|Target Position|Desired Role|Objective)\s*[:\-]\s*([^\n\r.]+)', cv_text, re.IGNORECASE)
        if pos_match:
            desired_position = pos_match.group(1).strip()
        elif name_line_idx >= 0 and (name_line_idx + 1) < len(non_empty_lines):
            next_ln = non_empty_lines[name_line_idx + 1]
            if (
                2 <= len(next_ln) <= 65
                and '@' not in next_ln
                and not re.search(r'\d{5,}', next_ln)
                and not any(kw in next_ln.lower() for kw in ['email:', 'phone:', 'sđt:', 'thông tin cá nhân', 'mục tiêu nghề nghiệp', 'học vấn:', 'education:'])
            ):
                desired_position = next_ln

        if not desired_position:
            desired_position = "Software Engineer"

        # 5. Extract Skills
        extracted_skills = self.extract_skills(cv_text)

        # 6. Extract Experience
        exp_years = self.extract_experience_years(cv_text)

        # 7. Extract Education & Education Detail
        edu_level = self.extract_education_level(cv_text)
        edu_detail = ""
        edu_match = re.search(r'(?:^|\n)\s*(?:Học vấn|Trình độ học vấn|Bằng cấp|Education)\s*[:\-]?\s*([^\r\n]*)', cleaned_lines_text, re.IGNORECASE)
        if edu_match:
            edu_line = edu_match.group(1).strip()
            after_lines = [l.strip() for l in cleaned_lines_text[edu_match.end():].splitlines() if l.strip()]
            if not edu_line or len(edu_line) < 3:
                collected_edu = []
                for l in after_lines[:3]:
                    if any(sec in l.lower() for sec in ['hoạt động', 'chứng chỉ', 'dự án', 'kinh nghiệm', 'kỹ năng', 'sở thích', 'người tham chiếu', 'tốt nghiệp', 'đạt học bổng', 'đạt giải']):
                        break
                    if not l.lower().startswith('xếp loại') and not re.match(r'^\d{4}\s*[-–]\s*\d{4}$', l):
                        clean_edu_ln = re.sub(r'[|·]?\s*(?:\d{1,2}/)?\d{4}\s*[-–]\s*(?:(?:\d{1,2}/)?\d{4}|nay|present|hiện tại)', '', l, flags=re.IGNORECASE).strip(' |·-')
                        if clean_edu_ln:
                            collected_edu.append(clean_edu_ln)
                    if len(collected_edu) >= 2:
                        break
                if collected_edu:
                    edu_detail = ' - '.join(collected_edu)
            else:
                edu_detail = re.sub(r'[|·]?\s*(?:\d{1,2}/)?\d{4}\s*[-–]\s*(?:(?:\d{1,2}/)?\d{4}|nay|present|hiện tại)', '', edu_line, flags=re.IGNORECASE).strip(' |·-')

        # 8. Extract Location / Address
        location = ""
        loc_match = re.search(r'(?:(?:Địa chỉ|Nơi ở|Khu vực|Location|Address)\s*[:\-]\s*|\uf3c5\s*)([^\r\n|]+)', cv_text, re.IGNORECASE)
        if loc_match:
            location = loc_match.group(1).strip()
        else:
            for pat, cname in [
                (r'(?:Mễ Trì|Cầu Giấy|Ba Đình|Đống Đa|Hai Bà Trưng|Thanh Xuân|Hà Đông|Tây Hồ|Nam Từ Liêm|Hà Nội|Ha Noi)', 'Hà Nội'),
                (r'(?:TP\.?\s*Hồ Chí Minh|TP\.?\s*HCM|Hồ Chí Minh|Ho Chi Minh|Sài Gòn|Saigon|Quận 1|Quận 3|Quận 7|Thủ Đức|Bình Thạnh|Tân Bình)', 'TP. Hồ Chí Minh'),
                (r'(?:Đà Nẵng|Da Nang|Hải Châu|Sơn Trà|Ngũ Hành Sơn)', 'Đà Nẵng'),
                (r'(?:Cần Thơ|Can Tho)', 'Cần Thơ'),
                (r'(?:Hải Phòng|Hai Phong)', 'Hải Phòng'),
            ]:
                if re.search(pat, cv_text, re.IGNORECASE):
                    location = cname
                    break

        # 9. Extract clean Objective / Summary
        summary_text = cleaned[:320] + ("..." if len(cleaned) > 320 else "")
        obj_match = re.search(
            r'(?:Mục tiêu nghề nghiệp|Tóm tắt bản thân|Giới thiệu bản thân|Career Objective|Professional Summary)\s*[:\-]?\s*([\s\S]{20,600}?)(?=\n\s*(?:Kỹ năng|Học vấn|Kinh nghiệm|Sở thích|Dự án|Chứng chỉ|Hoạt động|Skills|Education|Experience)\b|$)',
            cleaned_lines_text,
            re.IGNORECASE
        )
        if obj_match:
            obj_clean = clean_text(obj_match.group(1))
            if len(obj_clean) >= 20:
                summary_text = obj_clean[:360] + ("..." if len(obj_clean) > 360 else "")

        return {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'desired_position': desired_position,
            'location': location,
            'skills': extracted_skills,
            'years_of_experience': exp_years,
            'education_level': edu_level,
            'education_detail': edu_detail,
            'raw_text_length': len(cv_text),
            'summary': summary_text
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
