import streamlit as st
from agents.paper_agent import PaperAgent
import os
import shutil

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

# Step 2: Build Knowledge Base
if st.button("Build Knowledge Base"):
    agent = PaperAgent(
        embedding_model="nomic-embed-text",
        llm_model="llama3.2:latest",
        vector_store_dir="./vector_stores",
    )
    if agent.build_knowledge_base(pdf_dir, index_name="research_papers"):
        st.session_state["agent"] = agent
        st.success("Knowledge base built successfully!")
    else:
        st.error("Failed to build knowledge base")

# Step 3: Ask Questions
if "agent" in st.session_state:
    st.header("Ask a question")
    question = st.text_input("Your question:")
    if st.button("Get Answer") and question:
        answer, sources = st.session_state["agent"].query(question)
        st.write(f"**Answer:** {answer}")
        if sources:
            st.markdown("**Sources:**")
            for i, source in enumerate(sources):
                st.write(f"{i+1}. {source['filename']} - Page {source['page']}")

if st.button("Clean Up Uploaded PDFs"):
    if os.path.exists(pdf_dir):
        shutil.rmtree(pdf_dir)
        os.makedirs(pdf_dir, exist_ok=True)
        st.success("Uploaded PDF files have been cleaned up.")
    else:
        st.info("No uploaded files to clean up.")
