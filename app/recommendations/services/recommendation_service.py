import pandas as pd
from typing import Optional, Dict, Tuple
from app.recommendations.services.data_service import data_service
from app.recommendations.services.vector_service import vector_service
from app.recommendations.services.ranking_service import ranking_service
from app.recommendations.utils.text_generator import TextGenerator


class RecommendationService:
    def __init__(self):
        self.text_gen = TextGenerator()
        print("start Recommendation Service ")
    
    def get_internship_recommendations(
        self,
        candidate_id: str,

    ) -> Tuple[pd.DataFrame, Dict]:
        
        candidate = data_service.get_candidate(str(candidate_id)) 
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")
        
        candidate_embedding = vector_service.get_candidate_embedding_vector(candidate_id)
        if candidate_embedding is None: 
            print(f" Embedding not found for candidate {candidate_id}, using text search")
            query_text = self.text_gen.create_student_vector_text(candidate)
    
            search_k = 10000  
            docs, similarity_map = vector_service.search_internships(
                query_text,
                None, 
                search_k
            )
        else:
            search_k = 10000 
            docs, similarity_map = vector_service.search_internships_by_vector(
                candidate_embedding,
                None, 
                search_k
            )
        
        if not docs:
            return pd.DataFrame(), candidate
    
        internship_ids = [doc.metadata.get('internship_id') for doc in docs]
        internships_list = []
        
        for iid in internship_ids:
            internship = data_service.get_internship(str(iid))
            if internship:
                internships_list.append(internship)
        
        if not internships_list:
            return pd.DataFrame(), candidate
        
        internships_df = pd.DataFrame(internships_list)
        ranked_df = ranking_service.rerank_internships(
            candidate, internships_df, similarity_map
        )
        
        return ranked_df, candidate
    
    def get_candidate_recommendations(
        self,
        internship_id: str,
    
        
    ) -> Tuple[pd.DataFrame, Dict]:
       
        internship = data_service.get_internship(str(internship_id))
        
        if not internship:
            raise ValueError(f"Internship {internship_id} not found")
        
        applicant_ids = data_service.get_applicant_ids(internship_id)
        
        if not applicant_ids:
            return pd.DataFrame(), internship
        
        search_k = len(applicant_ids)  
        query_text = self.text_gen.create_internship_vector_text(internship)
        docs, similarity_map = vector_service.search_candidates_by_ids(
            query_text, applicant_ids, search_k
        )
        
        if not docs:
            return pd.DataFrame(), internship
    
        candidate_ids = [doc.metadata.get('candidate_id') for doc in docs]
        candidates_list = []
        
        for cid in candidate_ids:
            candidate = data_service.get_candidate(str(cid))
            if candidate:
                candidates_list.append({
                    'candidate_id': candidate['CandidateId'],        # ← هنا
                    'gpa': candidate.get('education', {}).get('Gpa', 0),
                    'education': candidate.get('education', {}),
                    'technical_skills': candidate.get('technical_skills', []),
                    'experiences': candidate.get('experiences', []),
                    'projects': candidate.get('projects', []),
                })
                
        if not candidates_list:
            return pd.DataFrame(), internship
        
        candidates_df = pd.DataFrame(candidates_list)
        
        if candidates_df.empty:
            return pd.DataFrame(), internship
        
        ranked_df = ranking_service.rerank_candidates(
            internship, candidates_df, similarity_map
        )
        return ranked_df, internship


recommendation_service = RecommendationService()