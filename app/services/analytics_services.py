from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta
from typing import Optional

async def get_user_analytics(mongo_db: AsyncIOMotorDatabase, user_id: int) -> dict:
    total = await mongo_db.analyses.count_documents({"user_id": user_id})

    if total == 0:
        return {
            "total_analyses": 0,
            "average_score": 0,
            "highest_score": 0,
            "lowest_score": 0,
            "score_distribution": {},
            "top_missing_keywords": [],
            "improvement_trend": []
        }


    pipeline_scores = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": None,
                "avg_score": {"$avg": "$scores.overall"},
                "max_score": {"$max": "$scores.overall"},
                "min_score": {"$min": "$scores.overall"}
            }
        }
    ]
    score_result = await mongo_db.analyses.aggregate(pipeline_scores).to_list(1)
    scores = score_result[0] if score_result else {}


    pipeline_grade = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$grade.grade",
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    grade_result = await mongo_db.analyses.aggregate(pipeline_grade).to_list(10)
    grade_dist = {item["_id"]: item["count"] for item in grade_result if item["_id"]}

    pipeline_keywords = [
        {"$match": {"user_id": user_id}},
        {"$unwind": "$keywords"},
        {"$match": {"keywords.found": False}},
        {"$group": {
            "_id": "$keywords.keyword",
            "missed_count": {"$sum": 1}
        }},
        {"$sort": {"missed_count": -1}},
        {"$limit": 10}
    ]
    missing_keywords = await mongo_db.analyses.aggregate(
        pipeline_keywords
    ).to_list(10)

    
    pipeline_trend = [
        {"$match": {"user_id": user_id}},
        {"$sort": {"created_at": 1}},
        {"$limit": 10},
        {"$project": {
            "_id": 0,
            "score": "$scores.overall",
            "date": "$created_at",
            "filename": 1
        }}
    ]
    trend = await mongo_db.analyses.aggregate(pipeline_trend).to_list(10)

    
    for item in trend:
        if "date" in item and isinstance(item["date"], datetime):
            item["date"] = item["date"].isoformat()

    return {
        "total_analyses": total,
        "average_score": round(scores.get("avg_score", 0) or 0, 2),
        "highest_score": round(scores.get("max_score", 0) or 0, 2),
        "lowest_score": round(scores.get("min_score", 0) or 0, 2),
        "grade_distribution": grade_dist,
        "top_missing_keywords": [
            {
                "keyword": k["_id"],
                "times_missed": k["missed_count"]
            }
            for k in missing_keywords
        ],
        "improvement_trend": trend
    }

async def get_skill_gap_analysis(
    mongo_db: AsyncIOMotorDatabase,
    user_id: int
) -> dict:

    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$unwind": "$keywords"},
        {
            "$group": {
                "_id": "$keywords.keyword",
                "total_occurrences": {"$sum": 1},
                "times_found": {
                    "$sum": {"$cond": ["$keywords.found", 1, 0]}
                }
            }
        },
        {
            "$project": {
                "keyword": "$_id",
                "total": "$total_occurrences",
                "found": "$times_found",
                "success_rate": {
                    "$multiply": [
                        {"$divide": ["$times_found", "$total_occurrences"]},
                        100
                    ]
                }
            }
        },
        {"$sort": {"success_rate": 1}},  # Lowest success rate pehle (gaps)
        {"$limit": 15}
    ]

    gaps = await mongo_db.analyses.aggregate(pipeline).to_list(15)

    skill_gaps = []
    skills_to_learn = []

    for gap in gaps:
        keyword = gap.get("keyword") or gap.get("_id")
        success_rate = round(gap.get("success_rate", 0), 2)
        skill_gaps.append({
            "skill": keyword,
            "success_rate": success_rate,
            "times_required": gap["total"],
            "times_present": gap["found"]
        })
        if success_rate < 50:
            skills_to_learn.append(keyword)

    return {
        "skill_gaps": skill_gaps,
        "priority_skills_to_learn": skills_to_learn,
        "total_unique_skills_analyzed": len(gaps)
    }

async def get_recent_analyses_summary(
    mongo_db: AsyncIOMotorDatabase,
    user_id: int,
    days: int = 30
) -> dict:
    date_from = datetime.utcnow() - timedelta(days=days)

    recent = await mongo_db.analyses.find(
        {
            "user_id": user_id,
            "created_at": {"$gte": date_from}
        },
        {
            "_id": 0,
            "analysis_id": 1,
            "scores.overall": 1,
            "grade": 1,
            "created_at": 1,
            "ai_result.hiring_recommendation": 1
        }
    ).sort("created_at", -1).to_list(50)


    for item in recent:
        if "created_at" in item:
            item["created_at"] = item["created_at"].isoformat()

    recommendations = {}
    for item in recent:
        rec = item.get("ai_result", {}).get("hiring_recommendation", "Unknown")
        recommendations[rec] = recommendations.get(rec, 0) + 1

    return {
        "period_days": days,
        "total_in_period": len(recent),
        "analyses": recent,
        "recommendation_breakdown": recommendations
    }