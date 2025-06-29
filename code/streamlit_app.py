import streamlit as st
from agents.paper_agent import PaperAgent
import os
import shutil
import subprocess
import json

def get_available_ollama_models():
    """Get list of available Ollama models"""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')[1:]  # Skip header line
        models = []
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    model_name = parts[0]
                    models.append(model_name)
        return models
    except (subprocess.CalledProcessError, FileNotFoundError):
        st.error("Ollama not found or not running. Please make sure Ollama is installed and running.")
        return []

st.title("Paper Reader Agent")

# Step 1: Upload PDFs
st.header("Upload PDF files")
uploaded_files = st.file_uploader(
    "Choose PDF files", type="pdf", accept_multiple_files=True
)
pdf_dir = "./uploaded_pdfs"
os.makedirs(pdf_dir, exist_ok=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        with open(os.path.join(pdf_dir, uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
    st.success("PDFs uploaded!")

# Step 2: Model Selection
st.header("Select Foundation Model")
available_models = get_available_ollama_models()

if available_models:
    st.write("Available Ollama models:")
    for model in available_models:
        st.write(f"- {model}")
    
    # Filter for LLM models (exclude embedding models)
    llm_models = [model for model in available_models if 'embed' not in model.lower()]
    
    if llm_models:
        selected_model = st.selectbox(
            "Choose LLM model for paper analysis:",
            llm_models,
            index=0 if 'llama3.2:latest' in llm_models else 0
        )
        st.success(f"Selected model: {selected_model}")
    else:
        st.warning("No LLM models found. Please install at least one LLM model in Ollama.")
        selected_model = None
else:
    selected_model = None

# Step 3: Build Knowledge Base
if st.button("Build Knowledge Base", key="build_kb_btn") and selected_model:
    with st.spinner("Building knowledge base..."):
        agent = PaperAgent(
            embedding_model="nomic-embed-text",
            llm_model=selected_model,
            vector_store_dir="./vector_stores",
        )
        if agent.build_knowledge_base(pdf_dir, index_name="research_papers"):
            st.session_state["agent"] = agent
            st.success("Knowledge base built successfully!")
        else:
            st.error("Failed to build knowledge base")
elif st.button("Build Knowledge Base") and not selected_model:
    st.error("Please select a model first!")

# Step 4: Ask Questions
if "agent" in st.session_state:
    st.header("Ask a question")
    question = st.text_input("Your question:")
    if st.button("Get Answer", key="get_answer_btn") and question:
        with st.spinner("Generating answer..."):
            answer, sources = st.session_state["agent"].query(question)
            st.write(f"**Answer:** {answer}")
            if sources:
                st.markdown("**Sources:**")
                for i, source in enumerate(sources):
                    st.write(f"{i+1}. {source['filename']} - Page {source['page']}")

if st.button("Clean Up Uploaded PDFs", key="cleanup_btn"):
    if os.path.exists(pdf_dir):
        shutil.rmtree(pdf_dir)
        os.makedirs(pdf_dir, exist_ok=True)
        st.success("Uploaded PDF files have been cleaned up.")
    else:
        st.info("No uploaded files to clean up.")
