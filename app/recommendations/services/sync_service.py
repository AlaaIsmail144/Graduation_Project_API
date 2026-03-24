from typing import Dict
from datetime import datetime
from app.recommendations.services.data_service import data_service
from app.recommendations.services.vector_service import vector_service
from app.recommendations.utils.text_generator import TextGenerator
import logging

logger = logging.getLogger(__name__)


class SyncService:
    def __init__(self):
        self.text_gen = TextGenerator()
        print("Sync Service initialized")
    
    def process_add_candidate_bg(self, candidate_id: str):
        try:
            logger.info(f"[BG Task] Starting candidate sync: {candidate_id}")
            print('start refresh candidate')
            data_service.refresh_candidate(candidate_id)
            print('start process candidate')
            candidate = data_service.get_candidate(candidate_id)
            
            if not candidate:
                logger.error(f"[BG Task] Candidate {candidate_id} not found in database")
                return
            
            vector_text = self.text_gen.create_student_vector_text(candidate)
            print('vector text' , vector_text)
            metadata = {
                'major': str(candidate.get('Major', '')),      # ← Major
                'name': str(candidate.get('FullName', ''))     # ← FullName
            }
            print('start update candidate vector')
            vector_id = vector_service.update_candidate_vector(
                candidate_id, vector_text, metadata
            )
            
            logger.info(f"[BG Task] Candidate {candidate_id} synced successfully. Vector ID: {vector_id}")
            
        except Exception as e:
            logger.error(f"[BG Task] Error syncing candidate {candidate_id}: {str(e)}")
    
    def process_add_internship_bg(self, internship_id: str):
        try:
            logger.info(f"[BG Task] Starting internship sync: {internship_id}")

            print('start refresh internship')
            data_service.refresh_internship(internship_id)
            print('start internship process')
            internship = data_service.get_internship(internship_id)
            
            if not internship:
                logger.error(f"[BG Task] Internship {internship_id} not found in database")
                return
            
            vector_text = self.text_gen.create_internship_vector_text(internship)
            metadata = {
                'title': str(internship.get('Title', '')),        # ← Title
                'location': str(internship.get('Location', '')),  # ← Location
                'duration': str(internship.get('Duration', ''))   # ← Duration
            }
            print('start update internship process')
            vector_id = vector_service.update_internship_vector(
                internship_id, vector_text, metadata
            )
            
            logger.info(f"[BG Task] Internship {internship_id} synced successfully. Vector ID: {vector_id}")
            
        except Exception as e:
            logger.error(f"[BG Task] Error syncing internship {internship_id}: {str(e)}")
    
    def process_delete_candidate_bg(self, candidate_id: str):
        try:
            logger.info(f"[BG Task] Starting candidate deletion: {candidate_id}")
            vector_service.delete_candidate_vector(candidate_id)
            if candidate_id in data_service.candidate_cache:
                del data_service.candidate_cache[candidate_id]
            
            logger.info(f"[BG Task] Candidate {candidate_id} deleted successfully")
            
        except Exception as e:
            logger.error(f"[BG Task] Error deleting candidate {candidate_id}: {str(e)}")

    def process_delete_internship_bg(self, internship_id: str):
        try:
            logger.info(f"[BG Task] Starting internship deletion: {internship_id}")
            vector_service.delete_internship_vector(internship_id)
            if internship_id in data_service.internship_cache:
                del data_service.internship_cache[internship_id]
            
            logger.info(f"[BG Task] Internship {internship_id} deleted successfully")
            
        except Exception as e:
            logger.error(f"[BG Task] Error deleting internship {internship_id}: {str(e)}")


sync_service = SyncService()