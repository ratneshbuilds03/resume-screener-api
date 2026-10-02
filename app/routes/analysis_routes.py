from typing import Any, List

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.limiter import limiter
from app.models.analysis import Analysis, AnalysisStatus
from app.models.user import User
from app.mongodb import get_mongodb
from app.services.background_services import process_resume_background
from app.services.pdf_services import validate_pdf
from app.services.s3_service import delete_resume_from_s3, generate_presigned_url
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/analysis", tags=["Analysis"])


async def _create_analysis_record(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    job_description: str,
    db: Session,
    current_user: User,
):
    pdf_content = await validate_pdf(file)

    analysis = Analysis(
        user_id=current_user.id,
        resume_filename=file.filename,
        job_description=job_description,
        status=AnalysisStatus.PENDING,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    background_tasks.add_task(
        process_resume_background,
        analysis_id=analysis.id,
        pdf_content=pdf_content,
        filename=file.filename,
        job_description=job_description,
        user_id=current_user.id,
    )

    return analysis


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_and_analyze(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    job_description: str = Form(..., min_length=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis = await _create_analysis_record(background_tasks, file, job_description, db, current_user)
    return {
        "message": "Resume uploaded successfully. Analysis in progress...",
        "analysis_id": analysis.id,
        "status": "pending",
        "check_status_url": f"/analysis/{analysis.id}/status",
    }


@router.post("/upload-background", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/hour")
async def upload_resume(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    job_description: str = Form(..., min_length=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await upload_and_analyze(request, background_tasks, file, job_description, db, current_user)


@router.get("/history", response_model=List[dict])
async def analysis_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analyses = (
        db.query(Analysis)
        .filter(Analysis.user_id == current_user.id)
        .order_by(Analysis.created_at.desc())
        .all()
    )
    return [analysis.to_dict() for analysis in analyses]


@router.get("/{analysis_id}")
async def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    mongo_db: Any = Depends(get_mongodb),
    current_user: User = Depends(get_current_user),
):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    detail = None
    if mongo_db is not None:
        detail = await mongo_db.analyses.find_one({"analysis_id": analysis_id, "user_id": current_user.id})
        if detail and "_id" in detail:
            detail["_id"] = str(detail["_id"])

    download_url = None
    if analysis.resume_s3_url:
        download_url = generate_presigned_url(analysis.resume_s3_url)

    return {"analysis": analysis.to_dict(), "detail": detail, "download_url": download_url}


@router.get("/{analysis_id}/status")
async def check_status(
    analysis_id: int,
    db: Session = Depends(get_db),
    mongo_db: Any = Depends(get_mongodb),
    current_user: User = Depends(get_current_user),
):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    response = {
        "id": analysis.id,
        "status": analysis.status,
        "resume_filename": analysis.resume_filename,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
    }

    if analysis.status == AnalysisStatus.COMPLETED:
        if mongo_db is not None:
            detail = await mongo_db.analyses.find_one({"analysis_id": analysis_id, "user_id": current_user.id})
            if detail:
                detail["_id"] = str(detail["_id"])
                response["result"] = detail
        response["overall_score"] = analysis.overall_score
    elif analysis.status == AnalysisStatus.FAILED:
        response["error"] = analysis.error_message

    return response


@router.delete("/{analysis_id}", status_code=204)
async def delete_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if analysis.resume_s3_url:
        delete_resume_from_s3(analysis.resume_s3_url)

    mongo_db = get_mongodb()
    if mongo_db is not None:
        await mongo_db.analyses.delete_many({"analysis_id": analysis_id, "user_id": current_user.id})

    db.delete(analysis)
    db.commit()


