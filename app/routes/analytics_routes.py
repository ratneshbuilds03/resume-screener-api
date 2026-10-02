from fastapi import APIRouter, Depends
from app.mongodb import get_mongodb
from app.utils.dependencies import get_current_user
from app.models.user import User
from app.services.analytics_services import (
    get_user_analytics,
    get_skill_gap_analysis,
    get_recent_analyses_summary
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/overview")
async def analytics_overview(
    mongo_db = Depends(get_mongodb),
    current_user: User = Depends(get_current_user)
):
    analytics = await get_user_analytics(mongo_db, current_user.id)
    return analytics

@router.get("/skill-gaps")
async def skill_gaps(
    mongo_db = Depends(get_mongodb),
    current_user: User = Depends(get_current_user)
):
    gaps = await get_skill_gap_analysis(mongo_db, current_user.id)
    return gaps

@router.get("/recent")
async def recent_analyses(
    days: int = 30,
    mongo_db = Depends(get_mongodb),
    current_user: User = Depends(get_current_user)
):
    if days > 365:
        days = 365
    summary = await get_recent_analyses_summary(mongo_db, current_user.id, days)
    return summary

@router.get("/compare/{analysis_id_1}/{analysis_id_2}")
async def compare_analyses(
    analysis_id_1: int,
    analysis_id_2: int,
    mongo_db = Depends(get_mongodb),
    current_user: User = Depends(get_current_user)
):
    analysis1 = await mongo_db.analyses.find_one(
        {"analysis_id": analysis_id_1, "user_id": current_user.id}
    )
    analysis2 = await mongo_db.analyses.find_one(
        {"analysis_id": analysis_id_2, "user_id": current_user.id}
    )

    if not analysis1 or not analysis2:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="One or both analyses not found")

    # Score comparison
    scores1 = analysis1.get("scores", {})
    scores2 = analysis2.get("scores", {})

    comparison = {}
    for key in ["overall", "keyword", "experience", "education", "skills"]:
        s1 = scores1.get(key, 0) or 0
        s2 = scores2.get(key, 0) or 0
        comparison[key] = {
            "analysis_1": s1,
            "analysis_2": s2,
            "difference": round(s2 - s1, 2),
            "improved": s2 > s1
        }

    return {
        "analysis_1_id": analysis_id_1,
        "analysis_2_id": analysis_id_2,
        "score_comparison": comparison,
        "overall_improvement": comparison["overall"]["improved"],
        "improvement_amount": comparison["overall"]["difference"]
    }