import streamlit as st
import requests
import uuid

# 1. 🌍 Configuration
# Ensure your Streamlit Secret "BACKEND_URL" has NO trailing slash.
# Example: https://sentient-analyst-api.onrender.com
RENDER_URL = st.secrets["BACKEND_URL"] 

st.set_page_config(page_title="Sentient Analyst", page_icon="📈")

# 2. 🆔 Session & User Management
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("📈 Sentient Financial Analyst")

with st.sidebar:
    st.header("🔑 Auth & Data")
    user_key = st.text_input("Gemini API Key", type="password")
    st.caption("[Get a free key here](https://aistudio.google.com/app/apikey)")
    
    uploaded_file = st.file_uploader("Upload Financial PDF", type="pdf")
    
    if st.button("Process Document"):
        if uploaded_file and user_key:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            data = {"user_id": st.session_state.user_id}
            
            with st.spinner("Uploading to Analyst..."):
                try:
                    # Added a 30s timeout to handle Render "Cold Starts"
                    resp = requests.post(
                        f"{RENDER_URL}/upload", 
                        files=files, 
                        data=data, 
                        timeout=30 
                    )
                    
                    if resp.status_code == 200:
                        st.session_state.file_uri = resp.json()["file_uri"]
                        st.success("Analysis Engine Ready!")
                    else:
                        # Capture specific error codes like 403, 404, or 500
                        st.error(f"Backend Error {resp.status_code}: {resp.text}")
                
                except requests.exceptions.Timeout:
                    st.error("The request timed out. Render might be sleeping. Try again in 30 seconds.")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the backend. Check if RENDER_URL is correct.")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
        else:
            st.error("Please provide both an API Key and a PDF file.")

# 3. 💬 Chat Interface
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about the financials..."):
    if not st.session_state.get("file_uri"):
        st.warning("Please upload and process a document first.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            payload = {
                "ticker": "UPLOADED_DOC",
                "query": prompt,
                "user_id": st.session_state.user_id,
                "file_uri": st.session_state.file_uri
            }
            headers = {"X-Gemini-API-Key": user_key.strip()}
            
            with st.spinner("Calculating..."):
                try:
                    resp = requests.post(
                        f"{RENDER_URL}/analyze", 
                        json=payload, 
                        headers=headers, 
                        timeout=60 # Analysis can take longer than uploads
                    )
                    
                    if resp.status_code == 200:
                        answer = resp.json()["analysis"]
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        st.error(f"Analysis failed ({resp.status_code}). Please check your API Key.")
                except Exception as e:
                    st.error(f"Connection Error: {str(e)}")