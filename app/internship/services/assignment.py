from typing import Optional, Dict, List
from uuid import UUID
from app.internship.core.database import get_db_connection
from app.internship.services.vector_db import VectorDBService
from app.internship.utils.preprocessing import preprocess_text, combine_text_fields


class AssignmentService:

    def __init__(self):
        self.vector_db = VectorDBService()

    def assign_single_internship(self, internship_id: UUID) -> Optional[Dict]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Title, Description, CurrentTopicId
                FROM Internships
                WHERE InternshipId = ? AND IsDeleted = 0
            """, (str(internship_id),))
            
            row = cursor.fetchone()
            if not row:
                print(f"opps... Internship {internship_id} not found")
                return None
            
            title, description, previous_topic_id = row

        combined_text = combine_text_fields(title, description)
        cleaned_text = preprocess_text(combined_text)
        
        if len(cleaned_text) < 0:
            print(f"opps... Internship {internship_id} has insufficient text")
            return None
        
        result = self.vector_db.find_topic(cleaned_text)
        if not result:
            return None
        
        topic_id = result['topic_id']
        topic_number = result['topic_number']
        label = result['label']
        confidence = result.get('confidence')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TopicId FROM Topics
                WHERE TopicId = ? AND IsActive = 1
            """, (topic_id,))
            
            if not cursor.fetchone():
                print(f" Topic {topic_id} not found or inactive")
                return None

            cursor.execute("""
                UPDATE Internships
                SET LastTopicId = CurrentTopicId,
                    CurrentTopicId = ?,
                    AssignmentUpdatedAt = GETDATE()
                WHERE InternshipId = ?
            """, (topic_id, str(internship_id)))
            
            conn.commit()
        
        return {
            'internship_id': str(internship_id),
            'topic_id': topic_id,
            'topic_number': topic_number,
            'label': label,
            'confidence': confidence,
            'previous_topic_id': previous_topic_id
        }
        
    def assign_batch_internships(self, internship_ids: List[UUID]) -> Dict:
    
        print(f"\n process batch assignment for {len(internship_ids)} internships")
        
        results = []
        failed = []
        
        for internship_id in internship_ids:
            try:
                result = self.assign_single_internship(internship_id)
                if result:
                    results.append(result)
                else:
                    failed.append(str(internship_id))
            except Exception as e:
                print(f"opps... Error assigning {internship_id}: {e}")
                failed.append(str(internship_id))
        
        print(f"Batch complete: {len(results)} assigned, {len(failed)} failed")
        
        return {
            'total': len(internship_ids),
            'assigned': len(results),
            'failed': len(failed),
            'results': results,
            'failed_ids': failed
        }
  
      
       