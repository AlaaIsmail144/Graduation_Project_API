import pandas as pd
from typing import Dict
from app.recommendations.utils.scoring import ScoringUtils


class RankingService:
    def __init__(self):
        self.weights = {
            'field_match': 15,
            'technical_skills': 10,
            'soft_skills': 5,
            'experience': 8,
            'projects': 5,
            'application_history': 7,
            'saved_similarity': 3,
            'gpa_bonus': 3,
            'verified_company': 5,
            'recency': 2,
            'similarity': 10
        }
    
    def rerank_internships(self, candidate: Dict, internships_df: pd.DataFrame,
                          similarity_map: Dict[str, float]) -> pd.DataFrame:
        
        scores = []
  
        tech_skills = [str(s).lower() for s in candidate.get('technical_skills', [])]
        soft_skills = [str(s).lower() for s in candidate.get('soft_skills', [])]
        experiences = candidate.get('experiences', [])
        projects = candidate.get('projects', [])
        field = str(candidate.get('education', {}).get('field_of_study', '')).lower()
        gpa = candidate.get('education', {}).get('gpa', 0)
        app_history = candidate.get('application_history', pd.DataFrame())
        saved = candidate.get('saved_internships', [])
        
        applied_fields = set()
        if not app_history.empty:
            for _, app in app_history.iterrows():
                intern_text = str(internships_df[
                    internships_df['internship_id'] == app['internship_id']
                ].get('required_field', '')).lower()
                if intern_text:
                    applied_fields.add(intern_text)
        
        for _, internship in internships_df.iterrows():
            score = 0.0
 
            required_field = str(internship.get('required_field', '')).lower()
            if field and (field in required_field or any(
                word in required_field for word in field.split()
            )):
                score += self.weights['field_match']

            intern_text = (
                str(internship.get('description', '')).lower() + " " +
                str(internship.get('details', {}).get('responsibilities', '')).lower()
            )
            
            tech_matches = ScoringUtils.calculate_skill_match(tech_skills, intern_text)
            score += min(tech_matches * 2, self.weights['technical_skills'])

            title_lower = str(internship.get('title', '')).lower()
            if any(kw in title_lower for kw in ['marketing', 'hr', 'management', 'business']):
                soft_matches = ScoringUtils.calculate_skill_match(soft_skills, intern_text)
                score += min(soft_matches * 1.5, self.weights['soft_skills'])

            for exp in experiences:
                exp_position = str(exp.get('position', '')).lower()
                exp_desc = str(exp.get('description', '')).lower()
                
                if exp_position and exp_position in title_lower:
                    score += 4
                
                overlap = ScoringUtils.calculate_text_overlap(exp_desc, intern_text)
                score += min(overlap / 10, 4)

            for project in projects[:3]:
                tech = str(project.get('technologies', '')).lower()
                if tech:
                    tech_list = [t.strip() for t in tech.split(',')]
                    matches = sum(1 for t in tech_list if t in intern_text)
                    score += min(matches, self.weights['projects'])
            
            if required_field in applied_fields:
                score += self.weights['application_history']

            if saved:
                if required_field in [
                    str(internships_df[internships_df['internship_id'] == sid]
                        .get('required_field', '')).lower()
                    for sid in saved
                ]:
                    score += self.weights['saved_similarity']
 
            if pd.notna(gpa):
                if gpa >= 3.5:
                    score += self.weights['gpa_bonus']
                elif gpa >= 3.0:
                    score += self.weights['gpa_bonus'] * 0.5
  
            company_data = internship.get('company', {})
            if company_data.get('verified') == 1:
                score += self.weights['verified_company']

            try:
                created_at = pd.to_datetime(internship.get('created_at'))
                days_old = (pd.Timestamp.now() - created_at).days
                recency_score = max(0, 60 - days_old) / 30 * self.weights['recency']
                score += recency_score
            except:
                pass

            distance = similarity_map.get(str(internship['internship_id']), 2.0)
            similarity_score = ScoringUtils.calculate_similarity_score(distance)
            score += self.weights['similarity'] * similarity_score
            
            scores.append(score)
        
        internships_df = internships_df.copy()
        internships_df['match_score'] = scores
        return internships_df.sort_values('match_score', ascending=False)
    
    def rerank_candidates(self, internship: Dict, candidates_df: pd.DataFrame,
                         similarity_map: Dict[str, float]) -> pd.DataFrame:
       
        scores = []
 
        required_field = str(internship.get('required_field', '')).lower()
        intern_text = (
            str(internship.get('description', '')).lower() + " " +
            str(internship.get('details', {}).get('responsibilities', '')).lower()
        )
        title_lower = str(internship.get('title', '')).lower()
    
        for _, candidate in candidates_df.iterrows():
            score = 0.0
  
            field = str(candidate.get('education', {}).get('field_of_study', '')).lower()
            if field and (field in required_field or any(
                word in required_field for word in field.split()
            )):
                score += self.weights['field_match']
      
            tech_skills = candidate.get('technical_skills', [])
            tech_matches = ScoringUtils.calculate_skill_match(tech_skills, intern_text)
            score += min(tech_matches * 2, self.weights['technical_skills'])
  
            experiences = candidate.get('experiences', [])
            for exp in experiences:
                exp_position = str(exp.get('position', '')).lower()
                if exp_position and exp_position in title_lower:
                    score += 4

            projects = candidate.get('projects', [])
            for project in projects[:3]:
                tech = str(project.get('technologies', '')).lower()
                if tech:
                    tech_list = [t.strip() for t in tech.split(',')]
                    matches = sum(1 for t in tech_list if t in intern_text)
                    score += min(matches, self.weights['projects'])

            gpa = candidate.get('gpa', 0)
            if pd.notna(gpa):
                if gpa >= 3.5:
                    score += self.weights['gpa_bonus']
                elif gpa >= 3.0:
                    score += self.weights['gpa_bonus'] * 0.5

            distance = similarity_map.get(str(candidate['candidate_id']), 2.0)
            similarity_score = ScoringUtils.calculate_similarity_score(distance)
            score += self.weights['similarity'] * similarity_score
            
            scores.append(score)
        
        candidates_df = candidates_df.copy()
        candidates_df['match_score'] = scores
        return candidates_df.sort_values('match_score', ascending=False)


ranking_service = RankingService()