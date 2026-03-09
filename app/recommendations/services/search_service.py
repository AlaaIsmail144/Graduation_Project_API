from typing import Optional, List, Dict
from app.recommendations.services.data_service import data_service
from app.recommendations.services.vector_service import vector_service


class SearchService:
    def __init__(self):
        print("Search Service initialized")
    
    def search_internships(
        self,
        query: str,
        top_k: int = 20
    ) -> List[Dict]:
       
        docs, similarity_map = vector_service.search_internships(
            query,
            filters=None,
            k=top_k
        )
        
        if not docs:
            return []
        
        results = []
        
        for doc in docs:
            internship_id = doc.metadata.get('internship_id')
            internship = data_service.get_internship(str(internship_id))
            
            if internship:
                distance = similarity_map.get(str(internship_id), 2.0)
                similarity_score = 1 / (1 + distance)
                
                results.append({
                    'internship_id': internship['internship_id'],
                    'similarity_score': round(similarity_score, 4)
                })
        
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return results

search_service = SearchService()