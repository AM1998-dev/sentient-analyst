import os
import shutil
import uuid
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai


app = FastAPI(title="Sentient Financial Analyst API")

origins = [
    "https://sentient-analyst-7xhexjqgafwq9shff4gdng.streamlit.app", # Replace with your real Streamlit URL
    "http://localhost:8501",               # For local testing
]

# 1. 🛡️ CORS Configuration: Allows Streamlit Cloud to talk to Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # For tighter security, replace "*" with your Streamlit URL later
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 📁 Multi-User Storage Setup
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

class AnalysisRequest(BaseModel):
    ticker: str
    query: str
    user_id: str
    file_uri: Optional[str] = None

# 3. 🧠 System Instructions (The "Brain")
SYSTEM_PROMPT = """
You are a Senior Financial Analyst. Your goal is to provide precise, data-driven insights.
1. Always look for Year-over-Year (YoY) or Quarter-over-Quarter (QoQ) changes.
2. If asked for a summary, provide a markdown table of KPIs (Revenue, Net Income, Operating Margin).
3. Perform basic calculations (like profit margins) automatically.
4. If data is missing, clearly state what is unavailable.
"""

@app.get("/")
def home():
    return {"status": "online", "agent": "Senior Financial Analyst"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...), user_id: str = Form(...)):
    try:
        user_path = UPLOAD_DIR / user_id
        user_path.mkdir(exist_ok=True)
        local_file = user_path / file.filename
        
        with local_file.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # We don't configure global genai here to keep it stateless per user request
        # The file upload will use the SERVER's key for storage management
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        genai_file = genai.upload_file(path=str(local_file), display_name=file.filename)
        
        os.remove(local_file)
        return {"file_uri": genai_file.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_stock(request: AnalysisRequest, x_gemini_api_key: str = Header(None)):
    if not x_gemini_api_key:
        raise HTTPException(status_code=401, detail="Please provide your Gemini API Key")

    try:
        # 🔑 Configure on-the-fly with the user's key (BYOK)
        genai.configure(api_key=x_gemini_api_key)
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=SYSTEM_PROMPT
        )
        
        report_file = genai.get_file(name=request.file_uri)
        response = model.generate_content([report_file, f"\n\nQuestion: {request.query}"])
        
        return {"analysis": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))