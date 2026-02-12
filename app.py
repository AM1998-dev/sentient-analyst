import streamlit as st
import requests
import uuid

# 1. 🌍 Configuration - Update this after deploying to Render!
RENDER_URL = "https://sentient-analyst-api.onrender.com" 

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
                resp = requests.post(f"{RENDER_URL}/upload", files=files, data=data)
                if resp.status_code == 200:
                    st.session_state.file_uri = resp.json()["file_uri"]
                    st.success("Analysis Engine Ready!")
        else:
            st.error("Missing Key or File")

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
            headers = {"X-Gemini-API-Key": user_key}
            
            with st.spinner("Calculating..."):
                resp = requests.post(f"{RENDER_URL}/analyze", json=payload, headers=headers)
                if resp.status_code == 200:
                    answer = resp.json()["analysis"]
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error("Analysis failed. Check your API Key.")