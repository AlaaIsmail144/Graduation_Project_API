import pandas as pd
import numpy as np
from collections import Counter
from datetime import datetime
from typing import Tuple, Dict, List, Optional
import uuid

from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import TfidfVectorizer

import google.generativeai as genai

from app.internship.core.config import get_settings
from app.internship.core.database import get_db_connection
from app.internship.utils.preprocessing import preprocess_text, combine_text_fields

settings = get_settings()
genai.configure(api_key=settings.GEMINI_API_KEY)

class ClusteringService:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.llm_model = genai.GenerativeModel('models/gemini-2.0-flash-exp')
        
    def find_optimal_clusters(self, embeddings: np.ndarray, max_clusters: int = None) -> int:
        if max_clusters is None:
            max_clusters = settings.MAX_CLUSTERS
        
        print("\n find number of optimal cluster")
        
        scores = []
        K_range = range(settings.MIN_CLUSTERS, min(max_clusters + 1, len(embeddings) // 10))
        
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels)
            scores.append((k, score))
        
        best_k = max(scores, key=lambda x: x[1])[0]
        best_score = max(scores, key=lambda x: x[1])[1]
        print(f"optimal topics: {best_k} (score: {best_score:.3f})")
        
        return best_k
   
    def perform_clustering(
        self, 
        df: pd.DataFrame, 
        n_topics: str = "auto"
    ) -> Tuple[pd.DataFrame, np.ndarray, float]:
     
        print(f"\n ------Starting clustering... ------")
        
        texts = df['cleaned_text'].tolist()

        print(" 1- Computing embeddings...")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)

        if n_topics == "auto":
            n_topics = self.find_optimal_clusters(embeddings)
        else:
            n_topics = int(n_topics)
        
        print(f" number of topics(clusters): {n_topics} topics")

        kmeans = KMeans(n_clusters=n_topics, random_state=42, n_init=20, max_iter=500)
        topics = kmeans.fit_predict(embeddings)

        final_score = silhouette_score(embeddings, topics)
        
        df['dominant_topic'] = topics
        
        print(f" Clustering complete")
        print(f"  **** {len(df)} documents assigned ****")
        print(f" **** Silhouette score: {final_score:.3f} ****")
        
        return df, embeddings, final_score
    
    def extract_keywords(self, df: pd.DataFrame, n_keywords: int = None) -> Dict[int, List[str]]:
       
        if n_keywords is None:
            n_keywords = settings.N_KEYWORDS
        
        print("\n ------ Extracting keywords with TF-IDF... ------")
        
        topic_keywords = {}
        
        for topic_id in sorted(df['dominant_topic'].unique()):
            topic_texts = df[df['dominant_topic'] == topic_id]['cleaned_text'].tolist()
            
            vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            tfidf_matrix = vectorizer.fit_transform(topic_texts)
            feature_names = np.array(vectorizer.get_feature_names_out())
            
            tfidf_scores = tfidf_matrix.sum(axis=0).A1
            top_indices = tfidf_scores.argsort()[::-1][:n_keywords]
            
            top_words = feature_names[top_indices]
            topic_keywords[topic_id] = list(top_words)
        
        print(" Keywords extracted")
        return topic_keywords
    
    def generate_labels_from_titles(self, df: pd.DataFrame) -> Dict[int, str]:
        print("\n generate labels")
        
        labels = {}
        
        for topic_id in sorted(df['dominant_topic'].unique()):
            titles = df[df['dominant_topic'] == topic_id]['title'].tolist()
            
            job_types = []
            for title in titles:
                title_clean = title.lower().replace("intern", "").strip()
                if title_clean:
                    job_types.append(title_clean.title())
   
            common_jobs = Counter(job_types).most_common(2)
            
            if len(common_jobs) >= 2:
                labels[topic_id] = f"{common_jobs[0][0]} & {common_jobs[1][0]}"
            elif len(common_jobs) == 1:
                labels[topic_id] = common_jobs[0][0]
            else:
                labels[topic_id] = f"Topic {topic_id}"
        
        print("Labels generated")
        return labels
    
    def refine_label_with_llm(self, label: str, keywords: List[str]) -> str:
       
        prompt = f"""
               Refine this into a short professional 2-4 word topic label for internships.
               Current: "{label}"
               Keywords: {', '.join(keywords[:5])}

               Return only the new label, nothing else.
               """
        
        try:
            response = self.llm_model.generate_content(prompt)
            refined = response.candidates[0].content.parts[0].text.strip()
     
            if self._validate_label(refined):
                return refined
            else:
                return label
        except Exception as e:
            print(f"opps LLM refinement failed: {e}")
            return label
        

    def _validate_label(self, label: str) -> bool:
        if not label or len(label) < 3 or len(label) > 60:
            return False
        
        invalid_words = ['refine', 'task:', 'rules:', 'current:', 'keywords:', 
                        'reply', 'example', 'label:', 'topic:']
        if any(word in label.lower() for word in invalid_words):
            return False
        
        return True
    

    def refine_all_labels(
        self, 
        labels: Dict[int, str], 
        keywords: Dict[int, List[str]]
    ) -> Dict[int, str]:
        print("\n enhance with gemini")
        
        refined = {}
        changed_count = 0
        
        for i, topic_id in enumerate(sorted(labels.keys()), 1):
            original = labels[topic_id]
            print(f"   [{i}/{len(labels)}] Topic {topic_id}...", end=' ')
            
            refined_label = self.refine_label_with_llm(original, keywords[topic_id])
            
            if refined_label != original:
                print(f" '{original}' → '{refined_label}'")
                changed_count += 1
            else:
                print(f" kept '{original}'")
            
            refined[topic_id] = refined_label
        
        print(f"\n LLM enhancement complete! Changed {changed_count}/{len(labels)} labels\n")
        return refined
    

    def save_topics_to_db(
        self,
        df: pd.DataFrame,
        labels: Dict[int, str],
        keywords: Dict[int, List[str]],
        silhouette_score: float,
        topic_version: str
    ) -> List[Dict]:
        
        print("\n save topics to database")
        
        created_topics = []

        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            try:
                for topic_num in sorted(labels.keys()):
                    topic_id = str(uuid.uuid4())
                    label = labels[topic_num]
                    keywords_list = keywords[topic_num]
                    doc_count = len(df[df['dominant_topic'] == topic_num])
                    
                    description = f"internships related to {', '.join(keywords_list[:5])}"
                    
                    topic_num_py = int(topic_num)
                    doc_count_py = int(doc_count)
                    silhouette_score_py = float(silhouette_score)
                    
                    cursor.execute("""
                        INSERT INTO Topics 
                        (topic_id, topic_version, topic_number, label, keywords, 
                         description, silhouette_score, document_count, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, GETDATE())
                    """, (
                        topic_id,
                        topic_version,
                        topic_num_py,
                        label,
                        str(keywords_list),
                        description,
                        silhouette_score_py,
                        doc_count_py
                    ))
                    
                    created_topics.append({
                        'topic_id': topic_id,
                        'topic_number': topic_num_py,
                        'label': label,
                        'keywords': keywords_list,
                        'document_count': doc_count_py
                    })
                    
                    print(f" topic {topic_num_py}: {label} ({doc_count_py} docs)")
                
                cursor.execute("""
                    UPDATE Topics 
                    SET is_active = 0 
                    WHERE topic_version != ? AND is_active = 1
                """, (topic_version,))
                
                deactivated = cursor.rowcount
        
                cursor.execute("""
                    WITH RecentVersions AS (
                        SELECT DISTINCT topic_version,
                               ROW_NUMBER() OVER (ORDER BY MAX(created_at) DESC) AS rn
                        FROM Topics
                        GROUP BY topic_version
                    )
                    DELETE FROM Topics
                    WHERE topic_version NOT IN (
                        SELECT topic_version 
                        FROM RecentVersions 
                        WHERE rn <= 2
                    )
                """)
                
                deleted = cursor.rowcount
                if deleted > 0:
                    print(f"   Deleted {deleted} topics from old versions")
                else:
                    print(f"   No old versions to delete")
            
                conn.commit()
                print(f"\nDone Transaction committed! Saved {len(created_topics)} topics.")
                
            except Exception as e:
                conn.rollback()
                print(f"\n transaction failed! Rolling back")
                raise Exception(f"Failed to save topics: {e}")
        
        return created_topics
    
    def update_internship_assignments(self, df: pd.DataFrame) -> int:

        with get_db_connection() as conn:
            topic_mapping = pd.read_sql("""
                SELECT topic_number, topic_id
                FROM Topics
                WHERE is_active = 1
            """, conn)
        
        topic_dict = dict(zip(topic_mapping['topic_number'], topic_mapping['topic_id']))
        
        updated_count = 0
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            for _, row in df.iterrows():
                internship_id = str(row['internship_id'])
                topic_num = int(row['dominant_topic'])  
                topic_id = topic_dict.get(topic_num)
                
                if topic_id:
                    topic_id_str = str(topic_id)
                    
                    cursor.execute("""
                        UPDATE Internship
                        SET last_topic_id = current_topic_id,
                            current_topic_id = ?,
                            assignment_updated_at = GETDATE()
                        WHERE internship_id = ?
                    """, (topic_id_str, internship_id))
                    updated_count += 1
            
            conn.commit()
        
        print(f" Updated {updated_count} internships")
        return updated_count

    def cluster_all_internships(self, topic_version: Optional[str] = None, n_topics: str = "auto") -> Dict:

     
        if not topic_version:
            topic_version = f"v1.0_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print("\n ------Fetching internships from database...------")
        with get_db_connection() as conn:
            df = pd.read_sql("""
                SELECT internship_id, title, description
                FROM Internship
                WHERE is_deleted = 0
            """, conn)
        
        if df.empty:
            raise ValueError("No internships found in database")
      
        df['combined_text'] = df.apply(
            lambda row: combine_text_fields(row['title'], row['description']),
            axis=1
        )
        df['cleaned_text'] = df['combined_text'].apply(preprocess_text)
        df = df[df['cleaned_text'].str.len() > 10].reset_index(drop=True)
        
        df, embeddings, sil_score = self.perform_clustering(df, n_topics)
        
        keywords = self.extract_keywords(df)
        labels = self.generate_labels_from_titles(df)
        labels = self.refine_all_labels(labels, keywords)
        created_topics = self.save_topics_to_db(df, labels, keywords, sil_score, topic_version)
        updated_count = self.update_internship_assignments(df)
        
        print(" CLUSTERING COMPLETED SUCCESSFULLY")

        
        return {
            'topic_version': topic_version,
            'n_topics': len(labels),
            'silhouette_score': sil_score,
            'total_internships': len(df),
            'updated_internships': updated_count,
            'topics_created': created_topics
        }