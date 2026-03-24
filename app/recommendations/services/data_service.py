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
            users = pd.read_sql("SELECT Id,UserName,Email FROM [AspNetUsers]", conn)
            companies = pd.read_sql("SELECT * FROM Companies", conn)
            self.internships_df = pd.read_sql(
                "SELECT * FROM Internships WHERE IsDeleted = 0", conn
            )
            internship_details = pd.read_sql("SELECT * FROM InternshipDetails", conn)
            self.candidates_df = pd.read_sql("SELECT * FROM Candidates", conn)
            candidate_skills = pd.read_sql("SELECT * FROM CandidateSkills", conn)
            candidate_interests = pd.read_sql("SELECT * FROM CandidateInterests", conn)
            candidate_projects = pd.read_sql("SELECT * FROM CandidateProjects", conn)
            candidate_experiences = pd.read_sql("SELECT * FROM CandidateExperiences", conn)
            education = pd.read_sql("SELECT * FROM Educations", conn)
            candidate_university_data = pd.read_sql("SELECT * FROM CandidateCollageDatas", conn)
            self.applications_df = pd.read_sql("SELECT * FROM Applications", conn)
            saved_internships = pd.read_sql("SELECT * FROM SavedInternships", conn)
            conn.close()
            self._build_candidate_cache(
                self.candidates_df, candidate_skills, candidate_interests,
                candidate_projects, candidate_experiences, education,
                candidate_university_data, self.applications_df, saved_internships
            )
            
            self._build_internship_cache(
                self.internships_df, internship_details, companies
            )

        except Exception as e:
            try:
                conn.close()
            except:
                pass
            raise Exception(f"Error loading data: {e}")
    
    def _build_candidate_cache(self, candidates, skills, interests, projects,
                           experiences, education, univ_data, applications,
                           saved_internships):
        for _, candidate in candidates.iterrows():
            cid = str(candidate['CandidateId'])
            
            skills_df = skills[skills['CandidateId'].astype(str) == cid]
            tech_skills = skills_df[skills_df['Soft_Skill'] == False]['SkillName'].tolist()
            soft_skills = skills_df[skills_df['Soft_Skill'] == True]['SkillName'].tolist()
            
            interests_df = interests[interests['CandidateId'].astype(str) == cid]
            interests_list = interests_df['Interest'].tolist() if not interests_df.empty else []
            
            projects_list = projects[projects['CandidateId'].astype(str) == cid].to_dict('records')
            
            experiences_list = experiences[experiences['CandidateId'].astype(str) == cid].to_dict('records')
            
            edu = education[education['CandidateId'].astype(str) == cid]
            education_data = edu.to_dict('records')[0] if not edu.empty else {}
            
            univ = univ_data[univ_data['CandidateId'].astype(str) == cid]
            university_data = univ.to_dict('records')[0] if not univ.empty else {}
            
            app_history = applications[applications['CandidateId'].astype(str) == cid]
            
            saved = saved_internships[
                saved_internships['CandidateId'].astype(str) == cid
            ]['InternshipId'].astype(str).tolist()
            
            self.candidate_cache[cid] = {
                **candidate.to_dict(),
                'candidate_id': cid,    # ← أضف ده
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
            iid = str(internship['InternshipId'])  # ← PascalCase
            
            details_df = details[details['InternshipId'].astype(str) == iid]
            details_data = details_df.to_dict('records')[0] if not details_df.empty else {}
            
            company = companies[companies['CompanyId'].astype(str) == str(internship['CompanyId'])]
            company_data = company.to_dict('records')[0] if not company.empty else {}
            
            self.internship_cache[iid] = {
                **internship.to_dict(),
                'internship_id': iid,   # ← أضف ده
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
                "SELECT * FROM Candidates WHERE CandidateId = ?", conn, params=[cid]
            )
            if candidate.empty:
                self.candidate_cache.pop(cid, None)
                return

            skills = pd.read_sql("SELECT * FROM CandidateSkills WHERE CandidateId = ?", conn, params=[cid])
            interests = pd.read_sql("SELECT * FROM CandidateInterests WHERE CandidateId = ?", conn, params=[cid])
            projects = pd.read_sql("SELECT * FROM CandidateProjects WHERE CandidateId = ?", conn, params=[cid])
            experiences = pd.read_sql("SELECT * FROM CandidateExperiences WHERE CandidateId = ?", conn, params=[cid])
            education = pd.read_sql("SELECT * FROM Educations WHERE CandidateId = ?", conn, params=[cid])
            univ_data = pd.read_sql("SELECT * FROM CandidateCollageDatas WHERE CandidateId = ?", conn, params=[cid])
            applications = pd.read_sql("SELECT * FROM Applications WHERE CandidateId = ?", conn, params=[cid])
            saved = pd.read_sql("SELECT * FROM SavedInternships WHERE CandidateId = ?", conn, params=[cid])
            
            conn.close()
            
            self._build_candidate_cache(
                candidate, skills, interests, projects, experiences,
                education, univ_data, applications, saved
            )
            
        except Exception as e:
            try:
                conn.close()
            except:
                pass
            raise Exception(f"Error refreshing candidate: {e}")

    def refresh_internship(self, internship_id: str):
        conn = db_manager.get_connection()
        try:
            iid = str(internship_id)
            
            internship = pd.read_sql(
                "SELECT * FROM Internships WHERE InternshipId = ? AND IsDeleted = 0", conn, params=[iid]
            )
            if internship.empty:
                self.internship_cache.pop(iid, None)
                return
            
            details = pd.read_sql("SELECT * FROM InternshipDetails WHERE InternshipId = ?", conn, params=[iid])
            
            company_id = str(internship.iloc[0]['CompanyId'])
            companies = pd.read_sql("SELECT * FROM Companies WHERE CompanyId = ?", conn, params=[company_id])
            
            conn.close()
            
            self._build_internship_cache(internship, details, companies)
            
        except Exception as e:
            try:
                conn.close()
            except:
                pass
            raise Exception(f"Error refreshing internship: {e}")
   
    def get_applicant_ids(self, internship_id: str) -> list:
        if self.applications_df is None:
            return []
        apps = self.applications_df[
            self.applications_df['InternshipId'].astype(str) == str(internship_id)
        ]
        return apps['CandidateId'].astype(str).tolist()

data_service = DataService()