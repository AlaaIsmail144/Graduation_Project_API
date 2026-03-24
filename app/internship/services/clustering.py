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
        self.llm_model = genai.GenerativeModel('gemini-2.0-flash')
        
    def find_optimal_clusters(self, embeddings: np.ndarray, max_clusters: int = None) -> int:
        if max_clusters is None:
            max_clusters = settings.MAX_CLUSTERS
        
        print("\n find number of optimal cluster")
        
        n_samples = len(embeddings)
        effective_max = min(max_clusters, n_samples // 2)
        effective_min = min(settings.MIN_CLUSTERS, effective_max - 1)
        effective_min = max(2, effective_min)
        
        if effective_min >= effective_max:
            print(f" Small dataset, using {effective_min} clusters")
            return effective_min
        
        scores = []
        K_range = range(effective_min, effective_max + 1)
        
        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels)
            scores.append((k, score))
        
        if not scores:
            return effective_min
        
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
    
    def save_topics_to_db(self, df, labels, keywords, silhouette_score, topic_version):
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
                    
                    cursor.execute("""
                        INSERT INTO Topics 
                        (TopicId, TopicVersion, TopicNumber, Label, Keywords, 
                        Description, SilhouetteScore, DocumentCount, IsActive, CreatedAt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, GETDATE())
                    """, (
                        topic_id, topic_version, int(topic_num), label,
                        str(keywords_list), description,
                        float(silhouette_score), int(doc_count)
                    ))
                    
                    created_topics.append({
                        'topic_id': topic_id,
                        'topic_number': int(topic_num),
                        'label': label,
                        'keywords': keywords_list,
                        'document_count': int(doc_count)
                    })
                    print(f" topic {topic_num}: {label} ({doc_count} docs)")
                
                cursor.execute("""
                    UPDATE Topics 
                    SET IsActive = 0 
                    WHERE TopicVersion != ? AND IsActive = 1
                """, (topic_version,))

                # ← هنا بالظبط
                cursor.execute("""
                   UPDATE Internships
                    SET CurrentTopicId = NULL,
                        LastTopicId = NULL
                    WHERE 
                        CurrentTopicId IN (
                            SELECT TopicId FROM Topics
                            WHERE TopicVersion NOT IN (
                                SELECT TopicVersion FROM (
                                    SELECT DISTINCT TopicVersion,
                                        ROW_NUMBER() OVER (ORDER BY MAX(CreatedAt) DESC) AS rn
                                    FROM Topics
                                    GROUP BY TopicVersion
                                ) AS rv WHERE rn <= 2
                            )
                        )
                        OR LastTopicId IN (
                            SELECT TopicId FROM Topics
                            WHERE TopicVersion NOT IN (
                                SELECT TopicVersion FROM (
                                    SELECT DISTINCT TopicVersion,
                                        ROW_NUMBER() OVER (ORDER BY MAX(CreatedAt) DESC) AS rn
                                    FROM Topics
                                    GROUP BY TopicVersion
                                ) AS rv WHERE rn <= 2
                            )
                        )
                """)

                cursor.execute("""
                    WITH RecentVersions AS (
                        SELECT DISTINCT TopicVersion,
                            ROW_NUMBER() OVER (ORDER BY MAX(CreatedAt) DESC) AS rn
                        FROM Topics
                        GROUP BY TopicVersion
                    )
                    DELETE FROM Topics
                    WHERE TopicVersion NOT IN (
                        SELECT TopicVersion FROM RecentVersions WHERE rn <= 2
                    )
                """)

                conn.commit()
                print(f"\nDone! Saved {len(created_topics)} topics.")
                
            except Exception as e:
                conn.rollback()
                raise Exception(f"Failed to save topics: {e}")
        
        return created_topics
        
    def update_internship_assignments(self, df):
        with get_db_connection() as conn:
            topic_mapping = pd.read_sql("""
                SELECT TopicNumber, TopicId
                FROM Topics
                WHERE IsActive = 1
            """, conn)
        
        topic_dict = dict(zip(topic_mapping['TopicNumber'], topic_mapping['TopicId']))
        updated_count = 0
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for _, row in df.iterrows():
                internship_id = str(row['internship_id'])
                topic_num = int(row['dominant_topic'])
                topic_id = topic_dict.get(topic_num)
                
                if topic_id:
                    cursor.execute("""
                        UPDATE Internships
                        SET LastTopicId = CurrentTopicId,
                            CurrentTopicId = ?,
                            AssignmentUpdatedAt = GETDATE()
                        WHERE InternshipId = ?
                    """, (str(topic_id), internship_id))
                    updated_count += 1
            
            conn.commit()
        
        print(f" Updated {updated_count} internships")
        return updated_count

    def cluster_all_internships(self, topic_version=None, n_topics="auto"):
        if not topic_version:
            topic_version = f"v1.0_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print("\n ------Fetching internships from database...------")
        with get_db_connection() as conn:
            df = pd.read_sql("""
                SELECT InternshipId, Title, Description
                FROM Internships
                WHERE IsDeleted = 0
            """, conn)
        
        print('df' , df)
        if df.empty:
            raise ValueError("No internships found in database")
        
        df = df.rename(columns={
            'InternshipId': 'internship_id',
            'Title': 'title',
            'Description': 'description'
        })
        
        df['combined_text'] = df.apply(
            lambda row: combine_text_fields(row['title'], row['description']), axis=1
        )
        df['cleaned_text'] = df['combined_text'].apply(preprocess_text)
        df = df[df['cleaned_text'].str.len() > 10].reset_index(drop=True)
        
        df, embeddings, sil_score = self.perform_clustering(df, n_topics)
        keywords = self.extract_keywords(df)
        labels = self.generate_labels_from_titles(df)
        labels = self.refine_all_labels(labels, keywords)
        created_topics = self.save_topics_to_db(df, labels, keywords, sil_score, topic_version)
        updated_count = self.update_internship_assignments(df)
        
        return {
            'topic_version': topic_version,
            'n_topics': len(labels),
            'silhouette_score': sil_score,
            'total_internships': len(df),
            'updated_internships': updated_count,
            'topics_created': created_topics
        }
