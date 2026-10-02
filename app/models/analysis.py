from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class AnalysisStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_filename = Column(String(250), nullable=False)
    resume_s3_url = Column(String(500), nullable=True)
    job_description = Column(Text, nullable=False)
    overall_score = Column(Float, nullable=True)
    status = Column(String(20), default=AnalysisStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    error_message = Column(String(500), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "resume_filename": self.resume_filename,
            "resume_s3_url": self.resume_s3_url,
            "job_description": (self.job_description[:100] + "...") if self.job_description else "",
            "overall_score": self.overall_score,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "error_message": self.error_message,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

