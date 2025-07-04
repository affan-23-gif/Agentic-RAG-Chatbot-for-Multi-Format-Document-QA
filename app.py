# app.py
import streamlit as st
import os
import tempfile
from agents.coordinator_agent import CoordinatorAgent

# Initialize Coordinator Agent (and other agents implicitly)
# Make sure to set your OpenAI API key as an environment variable or pass it directly
# st.secrets allows you to securely store API keys in Streamlit Cloud
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", st.secrets.get("OPENAI_API_KEY"))
if not OPENAI_API_KEY:
    st.error("OpenAI API Key not found. Please set OPENAI_API_KEY environment variable or in Streamlit secrets.")
    st.stop()

if 'coordinator' not in st.session_state:
    st.session_state.coordinator = CoordinatorAgent(openai_api_key=OPENAI_API_KEY)
    st.session_state.messages = []
    st.session_state.uploaded_files_info = []

st.set_page_config(page_title="Agentic RAG Chatbot")
st.title("Agentic RAG Chatbot with MCP")

# Sidebar for document uploads
with st.sidebar:
    st.header("Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose documents (PDF, PPTX, CSV, DOCX, TXT, MD)",
        type=["pdf", "pptx", "csv", "docx", "txt", "md"],
        accept_multiple_files=True
    )

    if uploaded_files:
        new_uploads = []
        for uploaded_file in uploaded_files:
            # Check if file already uploaded in current session
            if uploaded_file.name not in [f['name'] for f in st.session_state.uploaded_files_info]:
                new_uploads.append(uploaded_file)

        if new_uploads:
            for uploaded_file in new_uploads:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    temp_file_path = tmp_file.name
                st.write(f"Processing {uploaded_file.name}...")
                try:
                    chunks = st.session_state.coordinator.handle_user_upload(temp_file_path)
                    if chunks:
                        st.success(f"Successfully processed {uploaded_file.name}!")
                        st.session_state.uploaded_files_info.append({"name": uploaded_file.name, "path": temp_file_path, "status": "Processed"})
                    else:
                        st.error(f"Failed to process {uploaded_file.name}.")
                        st.session_state.uploaded_files_info.append({"name": uploaded_file.name, "path": temp_file_path, "status": "Failed"})
                except Exception as e:
                    st.error(f"An error occurred while processing {uploaded_file.name}: {e}")
                    st.session_state.uploaded_files_info.append({"name": uploaded_file.name, "path": temp_file_path, "status": "Failed"})
                finally:
                    # Clean up temp file (optional, for persistent storage, you'd save elsewhere)
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
            st.rerun() # Rerun to update the file list and chat history

    st.subheader("Uploaded Documents:")
    if st.session_state.uploaded_files_info:
        for f_info in st.session_state.uploaded_files_info:
            st.write(f"- {f_info['name']} ({f_info['status']})")
    else:
        st.write("No documents uploaded yet.")

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "source_context" in message and message["source_context"]:
            with st.expander("Source Context"):
                for source in message["source_context"]:
                    st.write(source)

# Accept user input
if prompt := st.chat_input("Ask a question about the documents..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Thinking..."):
        if not st.session_state.uploaded_files_info:
            response_content = "Please upload documents first before asking questions."
            source_info = []
        else:
            response = st.session_state.coordinator.handle_user_query(prompt)
            response_content = response.get("answer", "No answer found.")
            source_info = response.get("source_context", [])

    with st.chat_message("assistant"):
        st.markdown(response_content)
        if source_info:
            with st.expander("Source Context"):
                for source in source_info:
                    st.write(source)

    st.session_state.messages.append(
        {"role": "assistant", "content": response_content, "source_context": source_info}
    )