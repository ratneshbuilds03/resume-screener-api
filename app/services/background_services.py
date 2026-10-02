import asyncio
import hashlib
import logging
from datetime import datetime

from app.database import SessionLocal
from app.models.analysis import Analysis, AnalysisStatus
from app.redis_client import cache_get, cache_set
from app.services.ai_service import analyze_resume_with_ai
from app.services.keyword_services import extract_keywords_form_jd, match_keywords
from app.services.pdf_services import extract_resume_sections, extract_text_from_pdf
from app.services.s3_service import upload_resume_to_s3
from app.services.scoring_services import (
    calculate_education_score,
    calculate_experience_score,
    calculate_final_score,
    generate_feedback,
    get_score_grade,
)

logger = logging.getLogger(__name__)


def _make_cache_key(pdf_content: bytes, job_description: str, user_id: int) -> str:
    payload = f"{user_id}:{pdf_content[:200].hex()}:{job_description[:300]}"
    return f"resume:{hashlib.md5(payload.encode('utf-8')).hexdigest()}"


def process_resume_background(
    analysis_id: int,
    pdf_content: bytes,
    filename: str,
    job_description: str,
    user_id: int,
):
    db = SessionLocal()
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == user_id).first()
    if not analysis:
        db.close()
        return

    try:
        analysis.status = AnalysisStatus.PROCESSING
        db.commit()

        cache_key = _make_cache_key(pdf_content, job_description, user_id)
        cached = cache_get(cache_key)
        if cached:
            analysis.overall_score = float(cached.get("overall_score", 0))
            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.utcnow()
            db.commit()
            logger.info("Cache hit for analysis %s", analysis_id)
            return

        resume_text = extract_text_from_pdf(pdf_content)
        sections = extract_resume_sections(resume_text)
        keywords = extract_keywords_form_jd(job_description)
        keyword_result = match_keywords(resume_text, keywords)

        experience_score = calculate_experience_score(resume_text, job_description)
        education_score = calculate_education_score(resume_text, job_description)

        s3_url = upload_resume_to_s3(pdf_content, filename, user_id)
        analysis.resume_s3_url = s3_url
        db.commit()

        ai_result, ai_error = analyze_resume_with_ai(
            resume_text=resume_text,
            job_description=job_description,
            keyword_score=keyword_result["score"],
        )

        if ai_error or not ai_result:
            logger.warning("AI failed for analysis %s: %s", analysis_id, ai_error)
            feedback = generate_feedback(
                keyword_result["score"],
                experience_score,
                keyword_result["score"],
            )
            ai_result = {
                "skills_score": keyword_result["score"],
                "summary": "Analysis based on keyword matching and scoring fallback.",
                "hiring_recommendation": "Maybe",
                **feedback,
            }

        overall_score = calculate_final_score(
            keyword_score=keyword_result["score"],
            experience_score=experience_score,
            skills_score=ai_result.get("skills_score", keyword_result["score"]),
            education_score=education_score,
        )
        grade = get_score_grade(overall_score)

        from app.mongodb import get_mongodb

        async def save_to_mongo():
            mongo_db = get_mongodb()
            if mongo_db is None:
                return
            await mongo_db.analyses.insert_one(
                {
                    "analysis_id": analysis_id,
                    "user_id": user_id,
                    "resume_text_preview": resume_text[:500],
                    "sections": sections,
                    "keywords": keyword_result["matches"],
                    "scores": {
                        "overall": overall_score,
                        "keyword": keyword_result["score"],
                        "experience": experience_score,
                        "education": education_score,
                        "skills": ai_result.get("skills_score", 0),
                    },
                    "ai_result": ai_result,
                    "grade": grade,
                    "created_at": datetime.utcnow(),
                }
            )

        try:
            asyncio.run(save_to_mongo())
        except Exception as exc:
            raise RuntimeError(f"MongoDB save failed: {exc}") from exc

        analysis.overall_score = overall_score
        analysis.status = AnalysisStatus.COMPLETED
        analysis.completed_at = datetime.utcnow()

        response_data = {
            "overall_score": overall_score,
            "grade": grade,
            "scores": {
                "keyword": keyword_result["score"],
                "experience": experience_score,
                "education": education_score,
                "skills": ai_result.get("skills_score", 0),
            },
            "strengths": ai_result.get("strengths", []),
            "weaknesses": ai_result.get("weaknesses", []),
            "suggestions": ai_result.get("suggestions", []),
            "summary": ai_result.get("summary", ""),
            "hiring_recommendation": ai_result.get("hiring_recommendation", "Maybe"),
            "keyword_matches": keyword_result["matches"],
            "keywords_found": keyword_result["found_count"],
            "total_keywords": keyword_result["total_keywords"],
        }
        cache_set(cache_key, response_data, expire_seconds=3600)
        db.commit()
        logger.info("Analysis %s completed with final score %.2f", analysis_id, overall_score)
    except Exception as exc:
        logger.exception("Background processing failed for analysis %s", analysis_id)
        analysis.status = AnalysisStatus.FAILED
        analysis.error_message = str(exc)[:500]
        analysis.completed_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()