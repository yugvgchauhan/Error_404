from fastapi import FastAPI, UploadFile, File
from huggingface_hub import snapshot_download
import spacy
import os
import pymupdf  # PDF reader (pymupdf)
from docx import Document  # DOCX reader


app = FastAPI()


def get_text_from_resume(file_path: str) -> str:
    ext = file_path.lower().split(".")[-1]

    # PDF
    if ext == "pdf":
        text = ""
        pdf = pymupdf.open(file_path)
        for page in pdf:
            text += page.get_text()
        return text

    # DOCX
    elif ext == "docx":
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    # TXT
    elif ext == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    else:
        raise ValueError("❌ Only PDF, DOCX, TXT supported!")


# ✅ Download the model from the Hub
model_path = snapshot_download("amjad-awad/skill-extractor", repo_type="model")

# ✅ Load the model with spaCy
nlp = spacy.load(model_path)


# ✅ API Endpoint: Upload Resume and Extract Skills
@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):

    # ✅ Save uploaded file
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # ✅ Here text variable will store resume content
    text = get_text_from_resume(file_path)

    # ✅ Skill extraction
    doc = nlp(text)
    skills = [ent.text for ent in doc.ents if "SKILLS" in ent.label_]

    return {
        "filename": file.filename,
        "skills": skills
    }