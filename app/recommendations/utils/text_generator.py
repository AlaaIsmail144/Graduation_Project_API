from typing import Dict, List


class TextGenerator:
    
    @staticmethod
    def create_student_vector_text(candidate_data: Dict) -> str:
        parts = []
        
        tech_skills = candidate_data.get('technical_skills', [])
        if tech_skills:
            skills_text = ' '.join(tech_skills)
            for _ in range(3):
                parts.append(f"Skills: {skills_text}")
        
        projects = candidate_data.get('projects', [])
        for project in projects[:3]:
            title = project.get('Title')           # ← Title
            tech = project.get('Technologies')     # ← Technologies
            if title and tech:
                parts.append(f"Project {title} using {tech}")
        
        experiences = candidate_data.get('experiences', [])
        for exp in experiences[:2]:
            position = exp.get('Position')         # ← Position
            desc = exp.get('Description')          # ← Description
            if position and desc:
                parts.append(f"Experience as {position}: {str(desc)[:100]}")
        
        education = candidate_data.get('education', {})
        field = education.get('FieldOfStudy')      # ← FieldOfStudy
        if field:
            parts.append(f"Studying {field}")
        
        interests = candidate_data.get('interests', [])
        if interests:
            parts.append(f"Interested in {' '.join(interests)}")
        
        major = candidate_data.get('Major')        # ← Major
        if major:
            parts.append(f"Major: {major}")
        print('parts' , parts)
        
        return ' . '.join(parts)
    
    @staticmethod
    def create_internship_vector_text(internship_data: Dict) -> str:
        parts = []
        
        title = internship_data.get('Title')                # ← Title
        if title:
            parts.append(f"Position: {title}")
            parts.append(f"Title: {title}")
        
        required_field = internship_data.get('RequiredField')  # ← RequiredField
        if required_field:
            parts.append(f"Field: {required_field}")
        
        details = internship_data.get('details', {})
        responsibilities = details.get('Responsibilities')   # ← Responsibilities
        if responsibilities:
            parts.append(f"Responsibilities: {responsibilities}")
        
        description = internship_data.get('Description')    # ← Description
        if description:
            parts.append(f"Description: {str(description)[:300]}")
        
        location = internship_data.get('Location')          # ← Location
        if location:
            parts.append(f"Location: {location}")

        duration = internship_data.get('Duration')          # ← Duration
        if duration:
            parts.append(f"Duration: {duration}")
        
        return ' . '.join(parts)
    