
from typing import Tuple
from app.internship.core.database import get_db_connection
from app.internship.services.clustering import ClusteringService
from app.internship.services.vector_db import VectorDBService


def check_topics_exist():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Topics WHERE IsActive = 1")
            count = cursor.fetchone()[0]
        
        if count > 0:
            return True, f"Found {count} active topics", count
        else:
            return False, "No active topics found", 0
            
    except Exception as e:
        return False, f"Error checking topics: {e}", 0


def run_initial_clustering():
   
    print("built initial cluster")
    
    try:
        clustering_service = ClusteringService()

        result = clustering_service.cluster_all_internships(
            topic_version="v1.0",
            n_topics="auto"
        )
        
        vector_db = VectorDBService()
        vector_db.rebuild_from_database()
        print(f" Initial clustering complete! with Topics created: {result['n_topics']} + number of Internships clustered: {result['total_internships']}")

        return True
        
    except Exception as e:
        print(f" error when built initial clustering: {e}")
        raise RuntimeError(
            f"Cannot start Internship System without topics. Error: {e}"
        )


def initialize_internship_system():

    exists, message, count = check_topics_exist()
    
    if exists:
        print(f" {message}")
        return
    print(f" {message}")
    run_initial_clustering()