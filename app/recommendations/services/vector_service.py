from typing import List, Dict, Optional, Tuple
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from app.recommendations.core.config import settings

"""
1- Singleton pattern to ensure only one instance
2- Initialize without loading databases
3- Just mark as created, don't load anything yet
 """
class VectorService:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.embeddings = None
        self.db_students = None
        self.db_internships = None
        self._initialized = True
    

    def initialize(self):

        if self.db_students is not None and self.db_internships is not None:
            print(" Vector databases already loaded")
            return
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
 
        self.db_students = Chroma(
            persist_directory=settings.VECTOR_STUDENTS_PATH,
            embedding_function=self.embeddings,
            collection_name="students"
        )
        
        self.db_internships = Chroma(
            persist_directory=settings.VECTOR_INTERNSHIPS_PATH,
            embedding_function=self.embeddings,
            collection_name="internships"
        )
        
    
    def _ensure_initialized(self):
        if self.db_students is None or self.db_internships is None:
            raise RuntimeError(
                "VectorService not initialized! Call vector_service.initialize() first."
            )

    def add_candidate_vector(self, candidate_id: str, vector_text: str, 
                            metadata: Dict) -> str:
        self._ensure_initialized()
        
        doc = Document(
            page_content=vector_text,
            metadata={
                'candidate_id': str(candidate_id),
                **metadata
            }
        )
        ids = self.db_students.add_documents([doc])
        return ids[0] if ids else None
    
    def update_candidate_vector(self, candidate_id: str, vector_text: str,
                               metadata: Dict):
        self._ensure_initialized()
        self.delete_candidate_vector(candidate_id)
        return self.add_candidate_vector(candidate_id, vector_text, metadata)
    
    def delete_candidate_vector(self, candidate_id: str):
        self._ensure_initialized()
        try:
            self.db_students.delete(
                where={"candidate_id": str(candidate_id)}
            )
        except:
            pass  
    
    def search_candidates(self, query_text: str, filters: Optional[Dict] = None,
                         k: int = 10) -> Tuple[List[Document], Dict[str, float]]:
        self._ensure_initialized()
        
        search_kwargs = {"k": k}
        
        if filters:
            search_kwargs["filter"] = filters
        
        try:
            results_with_scores = self.db_students.similarity_search_with_score(
                query_text, **search_kwargs
            )
            
            docs = [doc for doc, _ in results_with_scores]
            similarity_map = {
                str(doc.metadata.get("candidate_id")): float(distance)
                for doc, distance in results_with_scores
            }
            
            return docs, similarity_map
            
        except:
            docs = self.db_students.similarity_search(query_text, **search_kwargs)
            similarity_map = {
                str(doc.metadata.get("candidate_id")): 1.0
                for doc in docs
            }
            return docs, similarity_map
    
    def search_candidates_by_ids(self, query_text: str, candidate_ids: List[str],
                                 k: int = 10) -> Tuple[List[Document], Dict[str, float]]:
        self._ensure_initialized()
        
        filters = {"candidate_id": {"$in": [str(cid) for cid in candidate_ids]}}
        
        return self.search_candidates(query_text, filters, k)
    
##################### Internship Operations ##########################
    
    def add_internship_vector(self, internship_id: str, vector_text: str,
                             metadata: Dict) -> str:
        self._ensure_initialized()
        
        doc = Document(
            page_content=vector_text,
            metadata={
                'internship_id': str(internship_id),
                **metadata
            }
        )
        
        ids = self.db_internships.add_documents([doc])
        return ids[0] if ids else None
    
    def update_internship_vector(self, internship_id: str, vector_text: str,
                                metadata: Dict):
        self._ensure_initialized()
        self.delete_internship_vector(internship_id)
        return self.add_internship_vector(internship_id, vector_text, metadata)
    
    def delete_internship_vector(self, internship_id: str):
        self._ensure_initialized()
        try:
            self.db_internships.delete(
                where={"internship_id": str(internship_id)}
            )
        except:
            pass  
    
    def get_candidate_embedding_vector(self, candidate_id: str) -> Optional[List[float]]:
        self._ensure_initialized()
        
        try:
            results = self.db_students._collection.get(
                where={"candidate_id": str(candidate_id)},
                include=['embeddings']
            )
            
            if results is None:
                return None
            
            embeddings_list = results.get('embeddings')
            if embeddings_list is None or len(embeddings_list) == 0:
                return None
            
            embedding = embeddings_list[0]

            if hasattr(embedding, 'tolist'):
                return embedding.tolist()
            return list(embedding) if isinstance(embedding, (list, tuple)) else embedding
        except Exception as e:
            print(f"Error getting candidate embedding: {e}")
            return None
    
    def get_internship_embedding_vector(self, internship_id: str) -> Optional[List[float]]:
        self._ensure_initialized()
        
        try:
            results = self.db_internships._collection.get(
                where={"internship_id": str(internship_id)},
                include=['embeddings']
            )
            
            if results is None:
                return None
            
            embeddings_list = results.get('embeddings')
            if embeddings_list is None or len(embeddings_list) == 0:
                return None
            
            embedding = embeddings_list[0]
            if hasattr(embedding, 'tolist'):
                return embedding.tolist()
            return list(embedding) if isinstance(embedding, (list, tuple)) else embedding
        except Exception as e:
            print(f"error getting internship embedding: {e}")
            return None
    
    def search_internships_by_vector(self, embedding: List[float], 
                                     filters: Optional[Dict] = None,
                                     k: int = 10) -> Tuple[List[Document], Dict[str, float]]:
        self._ensure_initialized()
        
        try:
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
            
            results_with_scores = self.db_internships.similarity_search_by_vector_with_relevance_scores(
                embedding=embedding,
                k=k,
                filter=filters
            )
            
            docs = [doc for doc, _ in results_with_scores]
            similarity_map = {
                str(doc.metadata.get("internship_id")): float(distance)
                for doc, distance in results_with_scores
            }
            
            return docs, similarity_map
            
        except Exception as e:
            print(f"Error in vector search: {e}")
            return [], {}
    
    def search_internships(self, query_text: str, filters: Optional[Dict] = None,
                          k: int = 10) -> Tuple[List[Document], Dict[str, float]]:
        self._ensure_initialized()
        
        search_kwargs = {"k": k}
        
        if filters:
            search_kwargs["filter"] = filters
        
        try:
            results_with_scores = self.db_internships.similarity_search_with_score(
                query_text, **search_kwargs
            )
            docs = [doc for doc, _ in results_with_scores]
            similarity_map = {
                str(doc.metadata.get("internship_id")): float(distance)
                for doc, distance in results_with_scores
            }
            
            return docs, similarity_map
            
        except:
            docs = self.db_internships.similarity_search(query_text, **search_kwargs)
            similarity_map = {
                str(doc.metadata.get("internship_id")): 1.0
                for doc in docs
            }
            return docs, similarity_map
    
    def search_candidates_by_vector(self, embedding: List[float],
                                    filters: Optional[Dict] = None,
                                    k: int = 10) -> Tuple[List[Document], Dict[str, float]]:
        self._ensure_initialized()
        
        try:
            results_with_scores = self.db_students.similarity_search_by_vector_with_relevance_scores(
                embedding=embedding,
                k=k,
                filter=filters
            )
            
            docs = [doc for doc, _ in results_with_scores]
            similarity_map = {
                str(doc.metadata.get("candidate_id")): float(distance)
                for doc, distance in results_with_scores
            }
            
            return docs, similarity_map
            
        except Exception as e:
            print(f"error in vector search: {e}")
            return [], {}


vector_service = VectorService()