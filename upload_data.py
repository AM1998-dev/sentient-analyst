import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 1. Upload the file to Google's servers
print("🚀 Uploading document...")
sample_file = genai.upload_file(path="apple_10q.pdf", display_name="Apple Q1 2026 10-Q")

# 2. Verify the upload
print(f"✅ File Uploaded: {sample_file.display_name}")
print(f"🆔 File URI: {sample_file.name}")
print("---")
print("Copy the 'File URI' above (it looks like 'files/xxxx'). You will need it for the next step!")