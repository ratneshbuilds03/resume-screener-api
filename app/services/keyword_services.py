import re
from typing import List, Dict

def extract_keywords_form_jd(job_description: str ) -> List[str]:
    tech_keywords = [
        "python", "javascript", "java", "c++", "golang", "rust",
        "typescript", "php", "ruby", "swift", "kotlin",
        "fastapi", "flask", "django", "react", "vue", "angular",
        "spring", "express", "nodejs",
        "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "sqlite", "oracle", "cassandra",
        "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd",
        "jenkins", "github actions", "terraform",
        "git", "linux", "rest api", "graphql", "microservices"
    ]
    jd_lower= job_description.lower()
    found_keywords = []
    
    for keyword in tech_keywords:
        if keyword in jd_lower:
            found_keywords.append(keyword)
            
    custom_pattern=r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
    custom_keywords=re.findall(custom_pattern,job_description)
    found_keywords.extend([k.lower()for k in custom_keywords[:10]])
    
    return list(set(found_keywords))


def extract_keywords_from_jd(job_description: str) -> List[str]:
    return extract_keywords_form_jd(job_description)


def match_keywords(resume_text:str,keywords: List[str])->dict:
    resume_lower = resume_text.lower()
    matches = []
    found_count = 0
    
    for keyword in keywords:
        found = keyword in resume_lower
        context = ""
        
        if found:
            found_count += 1
            idx = resume_lower.find(keyword)
            start = max(0, idx-50)
            end = min(len(resume_lower),idx + len(keyword)+50)
            context=resume_text[start:end].strip()
            
        matches.append({
            "keyword":keyword,
            "found":found,
            "context": context if found else None
        })
        
    score = (found_count/len(keywords)*100) if keywords else 0
    
    return{
        "matches":matches,
        "score":round(score,2),
        "found_count":found_count,
        "total_keywords":len(keywords)
    }