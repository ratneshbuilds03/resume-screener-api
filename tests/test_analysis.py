import pytest
import io
from unittest.mock import patch
from app.models.analysis import AnalysisStatus,Analysis

class TestAnalysisUpload:
    def test_upload_without_auth(self, client, sample_pdf):
        response = client.post(
            "/analysis/upload",
            files={"file": ("resume.pdf", sample_pdf, "application/pdf")},
            data={"job_description": "Python developer with FastAPI experience needed for backend role"}
        )
        assert response.status_code == 401

    def test_upload_success_with_mock_ai(self, client, auth_headers, sample_pdf):
        with patch("app.services.ai_service.analyze_resume_with_ai") as mock_ai:
            mock_ai.return_value = ({
                "overall_score": 78.5,
                "skills_score": 80.0,
                "strengths": ["Python skills"],
                "weaknesses": ["Limited cloud"],
                "suggestions": ["Add AWS"],
                "summary": "Good candidate",
                "hiring_recommendation": "Yes"
            }, None)

            with patch("app.services.s3_service.upload_resume_to_s3") as mock_s3:
                mock_s3.return_value = "https://s3.amazonaws.com/test/resume.pdf"

                response = client.post(
                    "/analysis/upload",
                    files={"file": ("resume.pdf", sample_pdf, "application/pdf")},
                    data={"job_description": "Python developer with FastAPI MySQL Docker experience needed"},
                    headers=auth_headers
                )

        assert response.status_code == 202
        data = response.json()
        assert "analysis_id" in data
        assert data["status"] == "pending"

    def test_upload_invalid_file_type(self, client, auth_headers):
        fake_txt = b"This is not a PDF file"
        response = client.post(
            "/analysis/upload",
            files={"file": ("resume.txt", fake_txt, "text/plain")},
            data={"job_description": "Python developer with FastAPI experience"},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_upload_short_job_description(self, client, auth_headers, sample_pdf):
        response = client.post(
            "/analysis/upload",
            files={"file": ("resume.pdf", sample_pdf, "application/pdf")},
            data={"job_description": "Too short"},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_check_status_not_found(self, client, auth_headers):
        response = client.get(
            "/analysis/999/status",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_analysis_history_empty(self, client, auth_headers):
        response = client.get(
            "/analysis/history",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_analysis_history_with_data(self, client, auth_headers, db, test_user):
        # Direct DB me analysis banao
        analysis = Analysis(
            user_id=test_user.id,
            resume_filename="test.pdf",
            job_description="Python developer with FastAPI experience for backend",
            overall_score=75.0,
            status=AnalysisStatus.COMPLETED
        )
        db.add(analysis)
        db.commit()

        response = client.get(
            "/analysis/history",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

class TestKeywordMatching:
    def test_keyword_extraction(self):
        from app.services.keyword_services import extract_keywords_from_jd
        jd = "Looking for Python developer with FastAPI MySQL Docker experience"
        keywords = extract_keywords_from_jd(jd)
        assert "python" in keywords
        assert "fastapi" in keywords
        assert "mysql" in keywords
        assert "docker" in keywords

    def test_keyword_matching(self):
        from app.services.keyword_services import match_keywords
        resume = "I have 3 years of Python experience with FastAPI and MySQL"
        keywords = ["python", "fastapi", "mysql", "docker"]
        result = match_keywords(resume, keywords)
        assert result["found_count"] == 3 
        assert result["score"] == 75.0

class TestScoringService:
    def test_score_grade_A(self):
        from app.services.scoring_services import get_score_grade
        grade = get_score_grade(90)
        assert grade["grade"] == "A"

    def test_score_grade_F(self):
        from app.services.scoring_services import get_score_grade
        grade = get_score_grade(30)
        assert grade["grade"] == "F"

    def test_final_score_calculation(self):
        from app.services.scoring_services import calculate_final_score
        score = calculate_final_score(
            keyword_score=80,
            experience_score=70,
            skills_score=75,
            education_score=65
        )
        expected = (80 * 0.25) + (70 * 0.35) + (75 * 0.25) + (65 * 0.15)
        assert abs(score - expected) < 0.1

class TestPDFService:
    def test_invalid_pdf(self):
        from app.services.pdf_services import extract_text_from_pdf
        from fastapi import HTTPException
        fake_pdf = b"Not a real PDF content"
        with pytest.raises(Exception):
            extract_text_from_pdf(fake_pdf)

    def test_clean_text(self):
        from app.services.pdf_services import clean_text
        dirty = "Hello   World\n\n  Python   Developer"
        clean = clean_text(dirty)
        assert "  " not in clean  