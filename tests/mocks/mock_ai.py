MOCK_AI_RESPONSE = {
    "overall_score": 78.5,
    "keyword_score": 75.0,
    "experience_score": 80.0,
    "skills_score": 82.0,
    "strengths": [
        "Strong Python background",
        "Good database experience",
        "DevOps knowledge present"
    ],
    "weaknesses": [
        "Limited cloud experience"
    ],
    "suggestions": [
        "Add specific AWS projects",
        "Mention Docker deployment examples",
        "Quantify achievements with metrics"
    ],
    "summary": "Strong backend developer with relevant Python skills",
    "hiring_recommendation": "Yes"
}

def mock_analyze_resume(resume_text, job_description, keyword_score):
    return MOCK_AI_RESPONSE, None

def mock_analyze_resume_fail(resume_text, job_description, keyword_score):
    return None, "AI service unavailable"