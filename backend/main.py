from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import shutil
from typing import List, Dict, Any, Optional
from resume_parser import parse_resume
from suggest_careers import suggest_careers
from chatbot_service import CareerGuidanceChatbot
from ml_model.dl_pipeline import DLPipeline

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize DL pipeline (FAISS + Transformer + Ranker)
try:
    career_pipeline = DLPipeline()
except Exception as e:
    career_pipeline = None
    print(f"ERROR: Career DL pipeline not loaded -> {e}")

app = FastAPI(title="AI Career Suggester (DL)", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CareerMatchRequest(BaseModel):
    resume_text: str
    top_n: int = 5

class CareerAnalysisRequest(BaseModel):
    resume_text: str
    career_title: str

class ChatMessage(BaseModel):
    user_id: str
    message: str
    session_id: Optional[str] = None

@app.get("/")
async def root():
    return {"status": "running", "model": "DL + FAISS", "version": "2.1.0"}

@app.post("/upload_resume/")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
        raise HTTPException(status_code=400, detail="Only PDF/DOCX supported")
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "message": "Uploaded"}

@app.get("/parse_resume/")
def parse_resume_api(filename: str):
    try:
        return parse_resume(os.path.join(UPLOAD_DIR, filename))
    except Exception as e:
        return {"error": str(e)}

@app.post("/suggest_careers/")
async def suggest_careers_endpoint(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # Parse the resume
        parsed = parse_resume(file_path)
        resume_text = parsed.get("raw_text", "")
        if not resume_text.strip():
            return {
                "suggested_careers": [],
                "parsed_skills": [],
                "message": "Empty resume or could not extract text",
                "method_used": "Fallback (no text)"
            }

        # If career_pipeline is not available, use a simple fallback
        if not career_pipeline:
            print("Warning: Career pipeline not available. Using fallback suggestions.")
            from ml_model.dl_pipeline import DLPipeline
            fallback_pipeline = DLPipeline()
            matches = fallback_pipeline._get_fallback_suggestions(resume_text, top_n=5)
            method_used = "Fallback (pipeline not available)"
        else:
            # Use the main pipeline
            matches = career_pipeline.search_jobs(resume_text, top_n=5)
            method_used = "FAISS + Transformer (MiniLM) Semantic Search"


        return {
            "suggested_careers": matches,
            "parsed_skills": parsed.get("skills", []),
            "skills_count": len(parsed.get("skills", [])),
            "message": "Career suggestions generated successfully",
            "method_used": method_used

        }

    except Exception as e:
        print(f"Error in suggest_careers_endpoint: {e}")
        # Try to provide some fallback suggestions even if there's an error
        try:
            from ml_model.dl_pipeline import DLPipeline
            fallback_pipeline = DLPipeline()
            matches = fallback_pipeline._get_fallback_suggestions("", top_n=5)
            return {
                "suggested_careers": matches,
                "parsed_skills": [],
                "message": f"Error: {str(e)}. Showing fallback suggestions.",
                "method_used": "Fallback (error occurred)"
            }
        except Exception as fallback_error:
            return {
                "suggested_careers": [],
                "parsed_skills": [],
                "message": f"Error: {str(e)}. Could not generate fallback suggestions.",
                "method_used": "Error"
            }

@app.post("/api/career/matches")
async def get_career_matches(request: CareerMatchRequest):
    if not career_pipeline:
        raise HTTPException(status_code=503, detail="Career DL pipeline not initialized")
    return {"matches": career_pipeline.search_jobs(request.resume_text, top_n=request.top_n)}


@app.post("/api/career/analyze")
async def analyze_career_match(request: CareerAnalysisRequest):
    if not career_pipeline:
        raise HTTPException(status_code=503, detail="Career DL pipeline not initialized")
    return career_pipeline.analyze_match(request.resume_text, request.career_title)

# Chatbot endpoints remain the same
chatbot = CareerGuidanceChatbot()

@app.post("/chat/start")
async def start_chat_session(user_id: str):
    return {"success": True, "response": chatbot.start_conversation(user_id), "user_id": user_id}

@app.post("/chat/message")
async def send_chat_message(chat_data: ChatMessage):
    return {"success": True, "response": chatbot.process_message(chat_data.user_id, chat_data.message), "user_id": chat_data.user_id}

@app.get("/chat/history/{user_id}")
async def get_chat_history(user_id: str):
    return {"success": True, "summary": chatbot.get_conversation_summary(user_id)}

@app.post("/chat/reset/{user_id}")
async def reset_chat_session(user_id: str):
    chatbot.conversation_state.pop(user_id, None)
    return {"success": True, "message": "Chat reset"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
