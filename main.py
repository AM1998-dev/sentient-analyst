import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import FastAPI, Form, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import Optional

# 1. Setup
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Define the "personality" and rules for your agent
SYSTEM_PROMPT = """
You are a Senior Financial Analyst. Your goal is to provide precise, data-driven insights.
1. Always look for Year-over-Year (YoY) or Quarter-over-Quarter (QoQ) changes when data is available.
2. If the user asks for a summary, provide a markdown table of Key Performance Indicators (KPIs) 
   including Revenue, Net Income, and Operating Margin.
3. If data is missing or unstructured, clearly state what you found and what is unavailable.
4. Perform basic calculations (like profit margins) automatically to add value to your answers.
"""

model = genai.GenerativeModel('gemini-3-flash-preview', system_instruction=SYSTEM_PROMPT)

app = FastAPI(title="Sentient Financial Analyst")

# Ensure an 'uploads' directory exists for temporary storage
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

class AnalysisRequest(BaseModel):
    ticker: str
    query: str
    user_id: str #Now required for every question to track which user is asking
    file_uri: Optional[str] = None # Now we can accept a dynamic file URI!

@app.get("/")
def home():
    return {"message": "Backend is online. 🤖"}

# 🚀 NEW: The Upload Endpoint
@app.post("/upload")
async def upload_document(file: UploadFile = File(...), user_id: str = Form(...)):
    try:
        # Save locally first (Google SDK often needs a path)
        local_path = UPLOAD_DIR / file.filename
        with local_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Upload to Google File API
        print(f"Uploading {file.filename} to Gemini...")
        genai_file = genai.upload_file(path=str(local_path), display_name=file.filename)
        
        # Clean up local file to save space
        os.remove(local_path)
        
        return {"file_uri": genai_file.name} # Return the ID for the dashboard to store
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_stock(request: AnalysisRequest):
    try:
        # Decide which document to use
        # If the user uploaded a new one, use that. Otherwise, use your hardcoded one.
        target_uri = request.file_uri if request.file_uri else "files/erlws8kwrgr0"
        
        report_file = genai.get_file(name=target_uri)
        
        prompt_parts = [
            report_file,
            f"\n\nQuestion: {request.query} regarding {request.ticker}."
        ]
        
        response = model.generate_content(prompt_parts)
        return {"analysis": response.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))