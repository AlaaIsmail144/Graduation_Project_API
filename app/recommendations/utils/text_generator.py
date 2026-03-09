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
            title = project.get('title')
            tech = project.get('technologies')
            if title and tech:
                parts.append(f"Project {title} using {tech}")
        
        experiences = candidate_data.get('experiences', [])

        for exp in experiences[:2]:  
            position = exp.get('position')
            desc = exp.get('description')
            if position and desc:
                parts.append(f"Experience as {position}: {str(desc)[:100]}")
        
        education = candidate_data.get('education', {})
        field = education.get('field_of_study')
        if field:
            parts.append(f"Studying {field}")
        
        interests = candidate_data.get('interests', [])
        if interests:
            parts.append(f"Interested in {' '.join(interests)}")
        
        major = candidate_data.get('major')
        if major:
            parts.append(f"Major: {major}")
        
        return ' . '.join(parts)
    
    @staticmethod
    def create_internship_vector_text(internship_data: Dict) -> str:
        parts = []
        
        title = internship_data.get('title')
        if title:
            parts.append(f"Position: {title}")
            parts.append(f"Title: {title}")
        
        required_field = internship_data.get('required_field')
        if required_field:
            parts.append(f"Field: {required_field}")
        
        details = internship_data.get('details', {})
        responsibilities = details.get('responsibilities')
        if responsibilities:
            parts.append(f"Responsibilities: {responsibilities}")
        
        description = internship_data.get('description')
        if description:
            parts.append(f"Description: {str(description)[:300]}")
        
        location = internship_data.get('location')
        if location:
            parts.append(f"Location: {location}")

        duration = internship_data.get('duration')
        if duration:
            parts.append(f"Duration: {duration}")
        
        return ' . '.join(parts)