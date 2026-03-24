import chromadb
from sentence_transformers import SentenceTransformer
from typing import Optional, Dict, List
import pandas as pd
import time
import json

from app.internship.core.config import get_settings
from app.internship.core.database import get_db_connection

settings = get_settings()


class VectorDBService:


    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.base_name = "topics"
        self._collection = None

    def _get_all_versions(self) -> List[str]:
        collections = self.client.list_collections()
        names = [c.name for c in collections if c.name.startswith(self.base_name)]
        names.sort()
        return names

    def _get_latest_collection_name(self) -> Optional[str]:
        versions = self._get_all_versions()
        return versions[-1] if versions else None

    def _get_previous_collection_name(self) -> Optional[str]:
        versions = self._get_all_versions()
        return versions[-2] if len(versions) >= 2 else None

    @property
    def collection(self):
        if self._collection is None:
            latest = self._get_latest_collection_name()
            if not latest:
                return None
            self._collection = self.client.get_collection(latest)
        return self._collection

    def find_topic(self, text: str) -> Optional[Dict]:
        if not self.collection:
            print(" No topic collection found")
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
                SELECT TopicId, TopicNumber, Label, Keywords, Description
                FROM Topics
                WHERE IsActive = 1
            """, conn)

        if df.empty:
            print(" No active topics found")
            return False

        print(f" Found {len(df)} topics")
        version = int(time.time())
        collection_name = f"{self.base_name}_{version}"

        collection = self.client.create_collection(
            collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        ids, embeddings, metadatas = [], [], []

        for _, row in df.iterrows():
            topic_id = str(row['TopicId'])
            topic_num = row['TopicNumber']
            label = row['Label']
            keywords = row['Keywords'] or "[]"
            description = row['Description'] or ""

            try:
                keywords_list = json.loads(keywords) if isinstance(keywords, str) else keywords
                keywords_text = " ".join(keywords_list)
            except:
                keywords_list = []
                keywords_text = ""

            text = f"{label} {keywords_text} {description}".strip() or label

            emb = self.model.encode(text).tolist()

            ids.append(f"t{topic_num}")
            embeddings.append(emb)
            metadatas.append({
                "topic_id": topic_id,
                "topic_number": str(topic_num),
                "label": label,
                "keywords": ", ".join(keywords_list),
                "description": description
            })

        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

        print(f" Built new version: {collection_name}")

        # Cleanup old versions (keep only last 2)
        self._cleanup_old_versions()

        # Reset cache
        self._collection = collection

        return True

    def _cleanup_old_versions(self):
        versions = self._get_all_versions()

        if len(versions) <= 2:
            return

        for old in versions[:-2]:
            self.client.delete_collection(old)
            print(f" Deleted old version: {old}")

    def rollback(self) -> bool:
        prev = self._get_previous_collection_name()

        if not prev:
            print(" No previous version available")
            return False

        self._collection = self.client.get_collection(prev)
        print(f" Rolled back to: {prev}")
        return True

    def get_collection_info(self) -> Dict:
        versions = self._get_all_versions()

        return {
            "total_versions": len(versions),
            "latest": self._get_latest_collection_name(),
            "previous": self._get_previous_collection_name(),
            "all_versions": versions
        }
