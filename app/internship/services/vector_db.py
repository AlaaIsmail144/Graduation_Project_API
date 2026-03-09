import chromadb
from sentence_transformers import SentenceTransformer
from typing import Optional, Dict, List
import pandas as pd
from app.internship.core.config import get_settings
from app.internship.core.database import get_db_connection

settings = get_settings()

class VectorDBService:

    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.INTERNSHIP_CHROMA_DB_PATH)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = "topics"
        self._collection = None
    
    @property
    def collection(self):
        if self._collection is None:
            try:
                self._collection = self.client.get_collection(self.collection_name)
            except:
                self._collection = None
        return self._collection
    
    def find_topic(self, text: str) -> Optional[Dict]:
        if not self.collection:
            print(" No topic collection found in ChromaDB")
            return None
        
        embedding = self.model.encode(text).tolist()
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=1,
            include=['metadatas', 'distances']
        )
        
        if not results['ids'][0]:
            return None
        
        metadata = results['metadatas'][0][0]
        distance = results['distances'][0][0] if results['distances'] else None
        
        confidence = 1 / (1 + distance) if distance is not None else None
        
        return {
            'topic_id': metadata['topic_id'],
            'topic_number': int(metadata['topic_number']),
            'label': metadata['label'],
            'confidence': confidence
        }
    
    def rebuild_from_database(self) -> bool:

        with get_db_connection() as conn:
            df = pd.read_sql("""
                SELECT topic_id, topic_number, label, keywords, description
                FROM Topics
                WHERE is_active = 1
            """, conn)
        
        if df.empty:
            print(" No active topics found in database")
            return False
        
        print(f" Found {len(df)} active topics")
        
        try:
            self.client.delete_collection(self.collection_name)
            print(" Deleted old collection")
        except:
            print(" No previous collection to delete")

        self._collection = self.client.create_collection(
            self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        ids = []
        embeddings = []
        metadatas = []
        
        for _, row in df.iterrows():
            topic_id = str(row['topic_id'])
            topic_num = row['topic_number']
            label = row['label']
            keywords = row['keywords'] or "[]"
            description = row['description'] or ""

            try:
                keywords_list = eval(keywords) if isinstance(keywords, str) else keywords
                keywords_text = " ".join(keywords_list)
            except:
                keywords_text = ""
            
            text_for_embedding = f"{label} {keywords_text} {description}".strip()
            if not text_for_embedding:
                text_for_embedding = label

            emb = self.model.encode(text_for_embedding).tolist()
            
            ids.append(f"t{topic_num}")
            embeddings.append(emb)
            metadatas.append({
                "topic_id": topic_id,
                "topic_number": str(topic_num),
                "label": label,
                "keywords": ", ".join(keywords_list) if keywords_list else "",
                "description": description
            })
            
            print(f" Topic {topic_num}: {label}")

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        print(f"\n vector DB rebuilt successfully ({len(ids)} topics)\n")
        return True
    

    def get_collection_info(self) -> Dict:
        if not self.collection:
            return {"exists": False, "count": 0}
        
        count = self.collection.count()
        return {
            "exists": True,
            "count": count,
            "name": self.collection_name
        }