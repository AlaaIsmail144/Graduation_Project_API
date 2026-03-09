import pandas as pd
from typing import Dict, Optional
from app.recommendations.core.database import db_manager


class DataService:
    def __init__(self):
        self.candidate_cache: Dict[str, Dict] = {}
        self.internship_cache: Dict[str, Dict] = {}
        
        self.candidates_df: Optional[pd.DataFrame] = None
        self.internships_df: Optional[pd.DataFrame] = None
        self.applications_df: Optional[pd.DataFrame] = None
        
 
    def load_all_data(self):
        conn = db_manager.get_connection()
        
        try:
            users = pd.read_sql("SELECT * FROM [User]", conn)
   
            companies = pd.read_sql("SELECT * FROM Company", conn)
            
            self.internships_df = pd.read_sql(
                "SELECT * FROM Internship WHERE is_deleted = 0", conn
            )
            
            internship_details = pd.read_sql("SELECT * FROM Internship_Details", conn)
            
            self.candidates_df = pd.read_sql("SELECT * FROM Candidate", conn)

            candidate_skills = pd.read_sql("SELECT * FROM CandidateSkill", conn)
            
            candidate_interests = pd.read_sql("SELECT * FROM CandidateInterests", conn)
            
            candidate_projects = pd.read_sql("SELECT * FROM CandidateProject", conn)
            
            candidate_experiences = pd.read_sql("SELECT * FROM CandidateExperience", conn)
            
            education = pd.read_sql("SELECT * FROM Education", conn)

            candidate_university_data = pd.read_sql(
                "SELECT * FROM CandidateUniversityData", conn
            )
            
            self.applications_df = pd.read_sql("SELECT * FROM Application", conn)

            saved_internships = pd.read_sql("SELECT * FROM SavedInternship", conn)
            
            conn.close()

            self._build_candidate_cache(
                self.candidates_df,
                candidate_skills,
                candidate_interests,
                candidate_projects,
                candidate_experiences,
                education,
                candidate_university_data,
                self.applications_df,
                saved_internships
            )
            
            self._build_internship_cache(
                self.internships_df,
                internship_details,
                companies
            )
            

        except Exception as e:
            conn.close()
            raise Exception(f"Error loading data: {e}")
    
    def _build_candidate_cache(self, candidates, skills, interests, projects,
                               experiences, education, univ_data, applications,
                               saved_internships):
        for _, candidate in candidates.iterrows():
            cid = str(candidate['candidate_id'])
            
            skills_df = skills[skills['candidate_id'].astype(str) == cid]
            tech_skills = skills_df[skills_df['Soft_Skill'] == False]['skill_name'].tolist()
            soft_skills = skills_df[skills_df['Soft_Skill'] == True]['skill_name'].tolist()
            
            interests_df = interests[interests['candidate_id'].astype(str) == cid]
            interests_list = interests_df['interest'].tolist() if not interests_df.empty else []
            
            projects_list = projects[
                projects['candidate_id'].astype(str) == cid
            ].to_dict('records')
            
            experiences_list = experiences[
                experiences['candidate_id'].astype(str) == cid
            ].to_dict('records')
            
            edu = education[education['candidate_id'].astype(str) == cid]
            education_data = edu.to_dict('records')[0] if not edu.empty else {}
            
            univ = univ_data[univ_data['candidate_id'].astype(str) == cid]
            university_data = univ.to_dict('records')[0] if not univ.empty else {}
            
            app_history = applications[applications['candidate_id'].astype(str) == cid]
            
            saved = saved_internships[
                saved_internships['candidate_id'].astype(str) == cid
            ]['internship_id'].astype(str).tolist()
            
            self.candidate_cache[cid] = {
                **candidate.to_dict(),
                'technical_skills': tech_skills,
                'soft_skills': soft_skills,
                'interests': interests_list,
                'projects': projects_list,
                'experiences': experiences_list,
                'education': education_data,
                'university_data': university_data,
                'application_history': app_history,
                'saved_internships': saved
            }
    
    def _build_internship_cache(self, internships, details, companies):
        for _, internship in internships.iterrows():
            iid = str(internship['internship_id'])
            
            details_df = details[details['internship_id'].astype(str) == iid]
            details_data = details_df.to_dict('records')[0] if not details_df.empty else {}
            
            company = companies[
                companies['company_id'].astype(str) == str(internship['company_id'])
            ]
            company_data = company.to_dict('records')[0] if not company.empty else {}
            
            self.internship_cache[iid] = {
                **internship.to_dict(),
                'details': details_data,
                'company': company_data
            }
    
    def get_candidate(self, candidate_id: str) -> Optional[Dict]:
        return self.candidate_cache.get(str(candidate_id))
    
    def get_internship(self, internship_id: str) -> Optional[Dict]:
        return self.internship_cache.get(str(internship_id))

    def refresh_candidate(self, candidate_id: str):
        conn = db_manager.get_connection()
        try:
            cid = str(candidate_id)
            
            candidate = pd.read_sql(
                f"SELECT * FROM Candidate WHERE candidate_id = '{cid}'", conn
            )

            if candidate.empty:
                self.candidate_cache.pop(cid, None)
                return
    
            skills = pd.read_sql(
                f"SELECT * FROM CandidateSkill WHERE candidate_id = '{cid}'", conn
            )
            interests = pd.read_sql(
                f"SELECT * FROM CandidateInterests WHERE candidate_id = '{cid}'", conn
            )
            projects = pd.read_sql(
                f"SELECT * FROM CandidateProject WHERE candidate_id = '{cid}'", conn
            )
            experiences = pd.read_sql(
                f"SELECT * FROM CandidateExperience WHERE candidate_id = '{cid}'", conn
            )
            education = pd.read_sql(
                f"SELECT * FROM Education WHERE candidate_id = '{cid}'", conn
            )
            univ_data = pd.read_sql(
                f"SELECT * FROM CandidateUniversityData WHERE candidate_id = '{cid}'", conn
            )
            applications = pd.read_sql(
                f"SELECT * FROM Application WHERE candidate_id = '{cid}'", conn
            )
            saved = pd.read_sql(
                f"SELECT * FROM SavedInternship WHERE candidate_id = '{cid}'", conn
            )
            
            conn.close()
            
            self._build_candidate_cache(
                candidate, skills, interests, projects, experiences,
                education, univ_data, applications, saved
            )
            
        except Exception as e:
            conn.close()
            raise Exception(f"Error refreshing candidate: {e}")

    def refresh_internship(self, internship_id: str):
        conn = db_manager.get_connection()
        try:
            iid = str(internship_id)
            
            internship = pd.read_sql(
                f"SELECT * FROM Internship WHERE internship_id = '{iid}' AND is_deleted = 0",
                conn
            )
            
            if internship.empty:
                self.internship_cache.pop(iid, None)
                return
            
            details = pd.read_sql(
                f"SELECT * FROM Internship_Details WHERE internship_id = '{iid}'", conn
            )
            
            company_id = internship.iloc[0]['company_id']
            companies = pd.read_sql(
                f"SELECT * FROM Company WHERE company_id = '{company_id}'", conn
            )
            
            conn.close()
            
            self._build_internship_cache(internship, details, companies)
            
        except Exception as e:
            conn.close()
            raise Exception(f"Error refreshing internship: {e}")
    
    def get_applicant_ids(self, internship_id: str) -> list:
        if self.applications_df is None:
            return []
        
        apps = self.applications_df[
            self.applications_df['internship_id'].astype(str) == str(internship_id)
        ]
        return apps['candidate_id'].astype(str).tolist()

data_service = DataService()