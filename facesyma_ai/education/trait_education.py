"""
Educational Module
Provides trait explanations, recommendations, and learning resources
"""
import json
import os
from typing import Dict, List, Any, Optional
import logging

log = logging.getLogger(__name__)

class TraitExplanation:
    """Detailed explanation of a single trait"""
    def __init__(self, trait_name: str, lang: str = "tr"):
        self.trait_name = trait_name
        self.lang = lang
        self.definition = ""
        self.characteristics = []
        self.strengths = []
        self.growth_areas = []
        self.career_matches = []
        self.relationship_insights = []
        self.development_tips = []
        self.famous_examples = []

class TraitEducator:
    """Educational content about traits"""
    def __init__(self, education_db_path: str = "./education_db.json"):
        self.education_db_path = education_db_path
        self.trait_database: Dict[str, Dict[str, TraitExplanation]] = {}
        self.recommendations: Dict[str, List[str]] = {}
        self.load_education_content()

    def load_education_content(self):
        """Load educational content"""
        if os.path.exists(self.education_db_path):
            try:
                with open(self.education_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.trait_database = data.get("traits", {})
                    self.recommendations = data.get("recommendations", {})
                log.info(f"Loaded education content for {len(self.trait_database)} traits")
            except Exception as e:
                log.error(f"Error loading education content: {e}")

    def get_trait_explanation(self, trait_name: str, lang: str = "tr") -> Optional[Dict[str, Any]]:
        """Get detailed explanation of a trait"""
        if trait_name not in self.trait_database:
            return None

        trait_data = self.trait_database[trait_name]
        if lang not in trait_data:
            lang = "en"  # Fallback to English

        return trait_data.get(lang)

    def get_trait_strengths(self, trait_name: str, lang: str = "tr") -> List[str]:
        """Get strengths associated with a trait"""
        trait = self.get_trait_explanation(trait_name, lang)
        return trait.get("strengths", []) if trait else []

    def get_growth_areas(self, trait_name: str, lang: str = "tr") -> List[str]:
        """Get growth areas for a trait"""
        trait = self.get_trait_explanation(trait_name, lang)
        return trait.get("growth_areas", []) if trait else []

    def get_career_recommendations(self, sifatlar: List[str], lang: str = "tr") -> Dict[str, Any]:
        """Get career recommendations based on traits"""
        recommendations = {
            "ideal_careers": [],
            "career_strengths": [],
            "skill_development": [],
            "work_environment": []
        }

        for sifat in sifatlar:
            trait = self.get_trait_explanation(sifat, lang)
            if trait:
                recommendations["ideal_careers"].extend(trait.get("career_matches", [])[:2])
                recommendations["career_strengths"].extend(trait.get("strengths", [])[:2])
                recommendations["skill_development"].extend(trait.get("development_tips", [])[:1])

        # Remove duplicates
        recommendations["ideal_careers"] = list(set(recommendations["ideal_careers"]))[:5]
        recommendations["career_strengths"] = list(set(recommendations["career_strengths"]))[:5]
        recommendations["skill_development"] = list(set(recommendations["skill_development"]))[:5]

        return recommendations

    def get_relationship_insights(self, trait_name: str, lang: str = "tr") -> List[str]:
        """Get relationship insights for a trait"""
        trait = self.get_trait_explanation(trait_name, lang)
        return trait.get("relationship_insights", []) if trait else []

    def get_development_tips(self, trait_name: str, lang: str = "tr") -> List[str]:
        """Get development tips for a trait"""
        trait = self.get_trait_explanation(trait_name, lang)
        return trait.get("development_tips", []) if trait else []

    def get_compatible_traits(self, trait_name: str) -> List[str]:
        """Get traits that work well with this trait"""
        return self.recommendations.get(f"{trait_name}_compatible", [])

    def create_learning_path(self, sifatlar: List[str], lang: str = "tr") -> Dict[str, Any]:
        """Create a personalized learning path"""
        learning_path = {
            "focus_areas": [],
            "learning_resources": [],
            "milestones": [],
            "estimated_duration": "8-12 weeks"
        }

        for sifat in sifatlar[:3]:  # Top 3 traits
            growth_areas = self.get_growth_areas(sifat, lang)
            dev_tips = self.get_development_tips(sifat, lang)

            learning_path["focus_areas"].extend(growth_areas[:2])
            learning_path["learning_resources"].extend(dev_tips[:2])

        learning_path["milestones"] = [
            f"Week 1-2: Understand {sifatlar[0]} strengths",
            f"Week 3-4: Address growth areas in {sifatlar[0]}",
            f"Week 5-8: Integrate {', '.join(sifatlar[1:])} development",
            "Week 9-12: Create action plan and track progress"
        ]

        return learning_path

    def get_daily_insight(self, sifatlar: List[str], lang: str = "tr") -> str:
        """Generate a daily insight based on traits"""
        if not sifatlar:
            return "Focus on understanding yourself better each day."

        trait = sifatlar[0]  # Primary trait
        trait_data = self.get_trait_explanation(trait, lang)

        if trait_data:
            strengths = trait_data.get("strengths", [])
            if strengths:
                return f"Today, leverage your {trait} nature by {strengths[0].lower()}."

        return f"Today, reflect on how your {trait} trait shows up in your decisions."

    def compare_traits(self, trait1: str, trait2: str, lang: str = "tr") -> Dict[str, Any]:
        """Compare two traits"""
        t1 = self.get_trait_explanation(trait1, lang)
        t2 = self.get_trait_explanation(trait2, lang)

        if not t1 or not t2:
            return {"error": "Trait not found"}

        return {
            "trait1": {
                "name": trait1,
                "strengths": t1.get("strengths", [])[:3],
                "growth_areas": t1.get("growth_areas", [])[:2]
            },
            "trait2": {
                "name": trait2,
                "strengths": t2.get("strengths", [])[:3],
                "growth_areas": t2.get("growth_areas", [])[:2]
            },
            "complementary": trait2 in self.get_compatible_traits(trait1)
        }
