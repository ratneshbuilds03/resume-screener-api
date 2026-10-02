import PyPDF2
import io
import re
from fastapi import UploadFile , HTTPException

ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024


async def validate_pdf(file: UploadFile) -> bytes:
    filename = file.filename.lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files allowed"
        )
        
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum 5MB allowed"
        )
    try:
        PyPDF2.PdfReader(io.BytesIO(content))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid or corrupted PDF file"
        )
        
    return content
def extract_text_from_pdf(pdf_content:bytes) -> str:
    try:
        reader=PyPDF2.PdfReader(io.BytesIO(pdf_content))
        text = ""
        
        for page in reader.pages:
            page_text =page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF. Make sure its not scanned image."
            )
            
        return clean_text(text)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF processing failed: {str(e)}"
        )

def clean_text(text:str) -> str:
    text = re.sub(r'\s+',' ',text)
    text = re.sub(r'[^\w\s\.,;:()\-@+]',' ',text)
    return text.strip()

def extract_resume_sections(text:str) -> dict:
    sections={
        "full_text":text,
        "skills":"",
        "experience":"",
        "education":"",
        "contact":""
    }
    
    text_lower = text.lower()
    
    
    skills_patterns = ["skills","technical skills", "core competencies"]
    for pattern in skills_patterns:
        idx = text_lower.find(pattern)
        if idx != -1:
            sections["skills"] =text[idx:idx+500]
            break
    
    
    exp_patterns = ["experience", "work history", "employment"]
    for pattern in exp_patterns:
        idx = text_lower.find(pattern)
        if idx != -1:
            sections["experience"] = text[idx:idx+1000]
            break
        
    edu_patterns = ["education","academic","qualification"]
    for pattern in edu_patterns:
        idx = text_lower.find(pattern)
        if idx != -1:
            sections["education"] = text[idx:idx+500]
            break
    return sections