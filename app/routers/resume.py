"""Resume upload endpoints router."""
import os
from fastapi import APIRouter, HTTPException, File, UploadFile
from app.database import get_db
from app import schemas
from app.routers.dependencies import get_services

router = APIRouter(prefix="/api/users/{user_id}/resume", tags=["Resume"])


@router.post("/upload")
async def upload_resume(user_id: int, file: UploadFile = File(...)):
    """
    Upload resume file for a user.
    Supports: PDF, TXT, DOCX
    """
    services = get_services()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id, name FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate file type
        allowed_extensions = ['.pdf', '.txt', '.docx', '.doc']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save file
        safe_filename = f"user_{user_id}_resume{file_extension}"
        file_path = os.path.join(services.upload_dir, safe_filename)
        
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Update database
        cursor.execute(
            "UPDATE users SET resume_path = ? WHERE id = ?",
            (file_path, user_id)
        )
        
        return {
            "message": "Resume uploaded successfully",
            "user_id": user_id,
            "filename": safe_filename,
            "file_path": file_path,
            "file_size": len(content)
        }


@router.post("/upload-text")
def upload_resume_text(user_id: int, resume_data: schemas.ResumeUpload):
    """
    Upload resume as text (for copy-paste functionality).
    Useful when users don't have resume file or want to paste content directly.
    """
    services = get_services()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        
        # Save resume text to file
        safe_filename = f"user_{user_id}_resume.txt"
        file_path = os.path.join(services.upload_dir, safe_filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(resume_data.resume_text)
        
        # Update database with both path and text
        cursor.execute(
            "UPDATE users SET resume_path = ?, resume_text = ? WHERE id = ?",
            (file_path, resume_data.resume_text, user_id)
        )
        
        return {
            "message": "Resume text uploaded successfully",
            "user_id": user_id,
            "filename": safe_filename,
            "text_length": len(resume_data.resume_text)
        }


@router.get("/text")
def get_resume_text(user_id: int):
    """Get resume text for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT resume_text, resume_path FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        resume_text = row['resume_text']
        resume_path = row['resume_path']
        
        if not resume_text and not resume_path:
            raise HTTPException(status_code=404, detail="No resume found for this user")
        
        # If we have text, return it
        if resume_text:
            return {
                "user_id": user_id,
                "resume_text": resume_text,
                "source": "database"
            }
        
        # If we only have file path, try to read it
        if resume_path and os.path.exists(resume_path):
            try:
                with open(resume_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {
                    "user_id": user_id,
                    "resume_text": content,
                    "source": "file",
                    "file_path": resume_path
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading resume: {str(e)}")
        
        raise HTTPException(status_code=404, detail="Resume file not found")


@router.delete("")
def delete_resume(user_id: int):
    """Delete resume for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get user
        cursor.execute("SELECT resume_path FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        resume_path = row['resume_path']
        
        # Delete file if exists
        if resume_path and os.path.exists(resume_path):
            os.remove(resume_path)
        
        # Update database
        cursor.execute(
            "UPDATE users SET resume_path = NULL, resume_text = NULL WHERE id = ?",
            (user_id,)
        )
        
        return {"message": "Resume deleted successfully", "user_id": user_id}
