from typing import List, Set


class ScoringUtils:

    @staticmethod
    def calculate_text_overlap(text1: str, text2: str) -> int:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        return len(words1 & words2)

    @staticmethod
    def calculate_skill_match(skills: List[str], text: str) -> int:
        text_lower = text.lower()
        return sum(1 for skill in skills if skill.lower() in text_lower)
  
    @staticmethod
    def normalize_score(score: float, max_score: float) -> float:
        if max_score == 0:
            return 0.0
        return min(score / max_score, 1.0)
  
    @staticmethod
    def calculate_similarity_score(distance: float) -> float:
        return 1 / (1 + distance)