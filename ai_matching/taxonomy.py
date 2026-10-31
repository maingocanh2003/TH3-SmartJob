"""
Taxonomy and Standardization Dictionary for AI Skill Matching
Provides canonical skill names, category mappings, and aliases/synonyms
for both English and Vietnamese technical terms.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set


DATA_DIR = Path(__file__).resolve().parent / "data"
TAXONOMY_FILE = DATA_DIR / "skills_taxonomy.json"


class SkillTaxonomy:
    """
    Manages standardized skills, categories, and alias resolutions.
    """
    _instance: Optional["SkillTaxonomy"] = None

    def __init__(self, json_path: Optional[Path] = None):
        path = json_path or TAXONOMY_FILE
        self.skills: Dict[str, dict] = {}
        self.alias_to_canonical: Dict[str, str] = {}
        self.canonical_names: Set[str] = set()
        self._load_taxonomy(path)

    @classmethod
    def get_instance(cls) -> "SkillTaxonomy":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_taxonomy(self, path: Path) -> None:
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data.get("skills", []):
            name = item["name"]
            category = item.get("category", "General")
            aliases = [a.lower().strip() for a in item.get("aliases", [])]
            
            self.skills[name] = {
                "name": name,
                "category": category,
                "aliases": aliases
            }
            self.canonical_names.add(name)

            # Map self lower
            self.alias_to_canonical[name.lower()] = name
            for alias in aliases:
                self.alias_to_canonical[alias] = name

    def normalize(self, term: str) -> Optional[str]:
        """
        Return the canonical skill name for a given raw term or alias.
        Returns None if not recognized.
        """
        clean = term.strip().lower()
        return self.alias_to_canonical.get(clean)

    def get_category(self, canonical_name: str) -> str:
        """Get the primary category for a canonical skill name."""
        info = self.skills.get(canonical_name)
        return info["category"] if info else "General"

    def get_all_canonical_names(self) -> List[str]:
        return sorted(list(self.canonical_names))

    def get_all_aliases(self) -> Dict[str, str]:
        """Returns map from lowercase alias to canonical skill name."""
        return dict(self.alias_to_canonical)


_taxonomy = SkillTaxonomy.get_instance()


def normalize_skill(term: str) -> Optional[str]:
    return _taxonomy.normalize(term)


def get_skill_category(skill_name: str) -> str:
    return _taxonomy.get_category(skill_name)

