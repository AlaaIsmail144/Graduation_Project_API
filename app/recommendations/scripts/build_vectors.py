import pandas as pd
import pyodbc
import time
import gc
from langchain_core.documents import Document 
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from app.recommendations.core.config import settings
from app.recommendations.core.database import db_manager
from app.recommendations.utils.text_generator import TextGenerator
import shutil
from pathlib import Path
from tqdm import tqdm  


def safe_remove_directory(path: Path, max_retries: int = 3) -> bool:
    if not path.exists():
        return True
    
    for attempt in range(max_retries):
        try:
            gc.collect()
            time.sleep(0.5) 
            shutil.rmtree(path)
            print(f" removed old DB at {path}")
            return True
        except PermissionError:
            if attempt < max_retries - 1:
                print(f" directory locked, retrying... ({attempt + 1}/{max_retries})")
                time.sleep(1)
            else:
                print(f" Could not remove {path} - file is in use")
                return False
        except Exception as e:
            print(f" error removing {path}: {e}")
            return False
    
    return False


def build_vector_databases():
    print(" Building Vector Databases from SQL Server")

    for path in [settings.VECTOR_STUDENTS_PATH, settings.VECTOR_INTERNSHIPS_PATH]:
        if Path(path).exists():
            success = safe_remove_directory(Path(path))
            if not success:
                raise RuntimeError("Cannot rebuild Vector DB because existing database is locked.")
    
    text_gen = TextGenerator()
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    except Exception as e:
        print(f"Failed to load embeddings model: {e}")
        raise

    if db_manager is None:
        raise Exception(" error in connection settings")
    
    conn = db_manager.get_connection()

    try:
        candidates = pd.read_sql("SELECT * FROM Candidates", conn)
        candidate_skills = pd.read_sql("SELECT * FROM CandidateSkills", conn)
        candidate_interests = pd.read_sql("SELECT * FROM CandidateInterests", conn)
        candidate_projects = pd.read_sql("SELECT * FROM CandidateProjects", conn)
        candidate_experiences = pd.read_sql("SELECT * FROM CandidateExperiences", conn)
        education = pd.read_sql("SELECT * FROM Educations", conn)
        
        internships = pd.read_sql("SELECT * FROM Internships WHERE IsDeleted = 0", conn)
        internship_details = pd.read_sql("SELECT * FROM InternshipDetails", conn)
        
        print(f" loaded {len(candidates)} candidates, {len(internships)} internships\n")
        
    except Exception as e:
        print(f" error loading data from SQL Server: {e}")
        raise
    finally:
        try:
            conn.close()
        except:
            pass

    print("Building candidate vectors...")
    candidate_docs = []
    
    for _, candidate in tqdm(candidates.iterrows(), total=len(candidates), desc="Processing candidates"):
        try:
            cid = str(candidate['CandidateId'])

            skills_df = candidate_skills[candidate_skills['CandidateId'].astype(str) == cid]
            tech_skills = skills_df[skills_df['Soft_Skill'] == False]['SkillName'].tolist()
            
            interests_df = candidate_interests[candidate_interests['CandidateId'].astype(str) == cid]
            interests = interests_df['Interest'].tolist() if not interests_df.empty else []
            
            projects = candidate_projects[
                candidate_projects['CandidateId'].astype(str) == cid
            ].to_dict('records')
            
            experiences = candidate_experiences[
                candidate_experiences['CandidateId'].astype(str) == cid
            ].to_dict('records')

            edu = education[education['CandidateId'].astype(str) == cid]
            edu_data = edu.to_dict('records')[0] if not edu.empty else {}

            candidate_data = {
                **candidate.to_dict(),
                'technical_skills': tech_skills,
                'interests': interests,
                'projects': projects,
                'experiences': experiences,
                'education': edu_data
            }
            
            vector_text = text_gen.create_student_vector_text(candidate_data)
            
            if not vector_text or not vector_text.strip():
                print(f" no vector text for candidate {cid}")
                continue
            
            doc = Document(
                page_content=vector_text,
                metadata={
                    'candidate_id': cid,
                    'major': str(candidate['Major']) if pd.notna(candidate.get('Major')) else '',
                    'name': str(candidate.get('FullName', ''))
                }
            )
            candidate_docs.append(doc)
            
        except Exception as e:
            print(f" error processing candidate {candidate.get('CandidateId')}: {e}")
            continue
    
    if len(candidate_docs) == 0:
        raise Exception("No candidate documents created")

    print("Building internship vectors...")
    internship_docs = []
    
    for _, internship in tqdm(internships.iterrows(), total=len(internships), desc="Processing internships"):
        try:
            iid = str(internship['InternshipId'])
            
            details = internship_details[internship_details['InternshipId'].astype(str) == iid]
            details_data = details.to_dict('records')[0] if not details.empty else {}
            
            internship_data = {
                **internship.to_dict(),
                'details': details_data
            }
            
            vector_text = text_gen.create_internship_vector_text(internship_data)
            
            if not vector_text or not vector_text.strip():
                print(f" no vector text for internship {iid}")
                continue
            
            doc = Document(
                page_content=vector_text,
                metadata={
                    'internship_id': iid,
                    'title': str(internship.get('Title', '')),
                    'location': str(internship.get('Location', '')),
                    'duration': str(internship.get('Duration', ''))
                }
            )
            internship_docs.append(doc)
            
        except Exception as e:
            print(f" error processing internship {internship.get('InternshipId')}: {e}")
            continue
    
    if len(internship_docs) == 0:
        raise Exception("No internship documents created")

    print("Creating vector stores...")
    
    try:
        print(" Building student vector DB...")
        db_students = Chroma.from_documents(
            documents=candidate_docs,
            embedding=embeddings,
            persist_directory=settings.VECTOR_STUDENTS_PATH,
            collection_name="students"
        )
        print(f" Student DB saved to {settings.VECTOR_STUDENTS_PATH}")
    except Exception as e:
        print(f" Failed to create student vector DB: {e}")
        raise
    
    try:
        print(" Building internship vector DB...")
        db_internships = Chroma.from_documents(
            documents=internship_docs,
            embedding=embeddings,
            persist_directory=settings.VECTOR_INTERNSHIPS_PATH,
            collection_name="internships"
        )
        print(f" Internship DB saved to {settings.VECTOR_INTERNSHIPS_PATH}")
    except Exception as e:
        print(f" Failed to create internship vector DB: {e}")
        raise
    
    print(" Vector Databases Built Successfully!")


if __name__ == "__main__":
    build_vector_databases()