import json

from openai import APIError, OpenAI

from app.config import settings


def _fallback_result(keyword_score: float, *, experience_score: float = 0.0, skills_score: float | None = None) -> dict:
    base_skills = skills_score if skills_score is not None else keyword_score
    return {
        "overall_score": round(max(0.0, min(100.0, keyword_score * 0.7 + experience_score * 0.3)), 2),
        "keyword_score": float(keyword_score),
        "experience_score": float(experience_score),
        "skills_score": float(base_skills),
        "strengths": ["Strong keyword alignment with the job description."],
        "weaknesses": ["AI scoring fallback used because the model was unavailable."],
        "suggestions": ["Review the resume for missing role-specific achievements and quantifiable metrics."],
        "summary": "The resume shows clear alignment with the role, but the AI evaluation used a fallback score because the model was unavailable.",
        "hiring_recommendation": "Maybe",
    }


def analyze_resume_with_ai(resume_text: str, job_description: str, keyword_score: float) -> tuple[dict | None, str | None]:
    if not settings.OPENAI_API_KEY:
        return _fallback_result(keyword_score), "OpenAI API key is not configured. Using fallback analysis."

    prompt = f"""
You are an expert HR recruiter and resume screener.

Analyze this resume against the job description and provide a detailed evaluation.

JOB DESCRIPTION:
{job_description[:2000]}

RESUME TEXT:
{resume_text[:3000]}
KEYWORD MATCH SCORE (already calculated): {keyword_score}%

Provide your analysis in this EXACT JSON format (no extra text):
{{
    "overall_score": <number 0-100>,
    "keyword_score": {keyword_score},
    "experience_score": <number 0-100>,
    "skills_score": <number 0-100>,
    "strengths": ["strength1", "strength2", "strength3"],
    "weaknesses": ["weakness1", "weakness2"],
    "suggestions": ["suggestion1", "suggestion2", "suggestion3"],
    "summary": "<2-3 line professional summary of fit>",
    "hiring_recommendation": "<Strong Yes / Yes / Maybe / No>"
}}

Scoring criteria:
- overall_score: Weighted average (keywords 30%, experience 40%, skills 30%)
- experience_score: Years and relevance of experience
- skills_score: Technical skills match
"""

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert HR recruiter. Always respond with valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.3,
            timeout=20,
        )

        ai_response = (response.choices[0].message.content or "").strip()
        if not ai_response:
            raise ValueError("Empty AI response")

        if ai_response.startswith("```"):
            ai_response = ai_response.strip("`")
            if ai_response.lower().startswith("json"):
                ai_response = ai_response[4:]
            ai_response = ai_response.strip()

        payload = json.loads(ai_response)
        if not isinstance(payload, dict):
            raise ValueError("AI response was not a JSON object")

        payload["keyword_score"] = float(keyword_score)
        payload["overall_score"] = float(payload.get("overall_score", keyword_score))
        payload["experience_score"] = float(payload.get("experience_score", keyword_score))
        payload["skills_score"] = float(payload.get("skills_score", keyword_score))
        return payload, None
    except (APIError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        fallback = _fallback_result(keyword_score)
        return fallback, f"AI analysis failed: {exc}"


__all__ = ["analyze_resume_with_ai"]
