import streamlit as st
import requests
import uuid

# Initialize a unique session ID if it doesn't exist
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# 1. Page Configuration
st.set_page_config(page_title="Sentient Analyst", page_icon="🤖")
st.title("🤖 Sentient Financial Analyst")
st.markdown("Query your financial documents with Gemini 3 Flash.")

# 2. Sidebar for Document Management
with st.sidebar:
    st.header("📂 Document Center")
    uploaded_file = st.file_uploader("Upload a financial PDF", type="pdf")
    st.header("Authentication key")
    user_key = st.text_input("Gemini API Key", type="password")
    st.markdown("[Get your free Gemini API Key here](https://aistudio.google.com/app/apikey)")
    
    if st.button("Initialize Document"):
        if uploaded_file:
            with st.spinner("Processing document..."):
                # We will build this endpoint next!
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}

                #Pack the ID as form data
                data = {"user_id": st.session_state.user_id}
                response = requests.post("http://127.0.0.1:8000/upload", files=files, data=data)
                
                if response.status_code == 200:
                    st.success(f"Successfully processed: {uploaded_file.name}")
                    # Store the File URI in the session so the chat can use it
                    st.session_state['file_uri'] = response.json().get("file_uri")
                else:
                    st.error("Failed to upload document.")
        else:
            st.warning("Please select a file first.")

# 3. Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask about the report..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 4. Talk to the FastAPI Backend
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            payload = {
                "ticker": "USER_DOC", 
                "query": prompt,
                "file_uri": st.session_state.get('file_uri'), # Send the specific file URI
                "user_id": st.session_state.user_id # Include the user ID for backend tracking
            }
            # We'll update the /analyze endpoint to handle this payload
            headers = {"X-Gemini-API-Key": user_key}
            response = requests.post("http://127.0.0.1:8000/analyze", json=payload, headers=headers)
            
            if response.status_code == 200:
                answer = response.json()["analysis"]
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error("The agent encountered an error during analysis.")