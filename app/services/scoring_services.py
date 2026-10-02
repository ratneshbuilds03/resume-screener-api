import re
from typing import Dict ,List

def calculate_experience_score(resume_text:str,job_description:str) -> float:
    score = 0.0
    resume_lower=resume_text.lower()
    jd_lower=job_description.lower()
    
    
    required_years =0
    year_patterns = [
        r'(\d+)\+?\s*years?\s*of\s*experience',
        r'(\d+)\+?\s*years?\s*experience',
        r'minimum\s*(\d+)\s*years?',
    ]
    for pattern in year_patterns:
        match = re.search(pattern,jd_lower)
        if match:
            required_years =int(match.group(1))
            break
        
    resume_years = 0
    resume_year_patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
        r'(\d{4})\s*[--]\s*(\d{4}|present|current)',
    ]
    for pattern in resume_year_patterns:
        matches = re.findall(pattern,resume_lower)
        if matches and pattern == resume_year_patterns[1]:
            for match in matches:
                start = int(match[0])
                end = 2026 if match[1] in ['present','current'] else int(match[1])
                resume_years = max(resume_years,end - start)
        elif matches:
            resume_years = max(resume_years,int(matches[0]))
            
    if required_years == 0:
        score = 70.0
    elif resume_years >= required_years:
        score = 100.0
    elif resume_years >= required_years * 0.7:
        score = 75.0
    elif resume_years >= required_years * 0.5:
        score = 50.0
    else :
        score = 25.0
        
        
    senior_keywords = ["senior","lead","principal","architect","manager","head"]
    junior_keywords = ["junior","entry","fresher","trainee","intern"]
    
    jd_needs_senior = any(k in jd_lower for k in senior_keywords )
    resume_has_senior = any(k in resume_lower for k in senior_keywords)
    resume_is_junior = any(k in resume_lower for k in junior_keywords)
    
    if jd_needs_senior and resume_has_senior:
        score = min (100,score + 10)
    elif jd_needs_senior and resume_is_junior:
        score = max(0,score - 20)
        
    return round(score,2)

def calculate_education_score(resume_text:str , job_description:str) ->float:
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()
    
    score  = 60.0
    
    degree_scores ={
        "phd":100 , "doctorate":100,
        "master":90 ,"mtech":90, "msc":90,"mba":85,
        "bachelor":75,"btech":75,"bsc":75,"be":75,
        "diploma":50,"certification":60
    }
    
    for degree, degree_score in degree_scores.items():
        if degree in resume_lower:
            score =max(score,degree_score)
            break
        
    if "master" in  jd_lower or "mtech" in jd_lower:
        if not any(d in resume_lower for d in ["master","mtech","msc"]):
            score = max(0,score-20)
            
    return round(score,2)

def calculate_final_score(
    keyword_score:float,
    experience_score:float,
    skills_score:float,
    education_score:float
) -> float:
    
    final = (
        keyword_score * 0.25 +
        experience_score * 0.35 +
        skills_score * 0.25 +
        education_score * 0.15
    )
    
    return round(final , 2)

def get_score_grade(score:float) -> dict:
    if score >= 85:
        return {"grade": "A", "label": "Excellent Match", "color": "green"}
    elif score >= 70:
        return {"grade": "B", "label": "Good Match", "color": "blue"}
    elif score >= 55:
        return {"grade": "C", "label": "Average Match", "color": "yellow"}
    elif score >= 40:
        return {"grade": "D", "label": "Below Match", "color": "orange"}
    else :
        return {"grade": "F", "label": "Poor Match", "color": "red"}
    

def generate_feedback(
    keyword_score:float,
    experience_score:float,
    skills_score:float,
) -> dict :
    strengths =[]
    weaknesses = []
    suggestions = []
    
    if keyword_score >= 70:
        strengths.append("Good keyword alignment with job requirements")
    elif keyword_score >= 50:
        weaknesses.append("Some important keywords missing from resume")
        suggestions.append("Add missing technical keywords naturally in your experience section")
    else:
        weaknesses.append("Poor keyword match with job description")
        suggestions.append("Review job description carefully and incorporate relevant keywords")
        
        
    if experience_score >= 80:
        strengths.append("Experience level matches job requirements well")
    elif experience_score >= 60:
        weaknesses.append("Experience slightly below requirements")
        suggestions.append("Highlight relevant projects to compensate for experience gap")
    else:
        weaknesses.append("Significant experience gap for this position")
        suggestions.append("Consider applying for junior/mid level positions first")
        
    if skills_score >= 75:
        strengths.append("Strong technical skills match")
    else:
        weaknesses.append("Technical skills need improvement")
        suggestions.append("List all relevant technical skills explicitly in a dedicated section")


    suggestions.append("Quantify achievements with numbers and percentages")
    suggestions.append("Use action verbs at the start of each bullet point")
    
    return {
        "strengths":strengths,
        "weaknesses":weaknesses,
        "suggestions":suggestions
    }