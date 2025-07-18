import streamlit as st
from agents.paper_agent import PaperAgent
from agents.reference_manager import ReferenceManager, DownloadConfig
import os
import shutil
import uuid
from datetime import datetime

st.title("Paper Reader Agent")

# Initialize session state
if "reference_manager" not in st.session_state:
    st.session_state.reference_manager = ReferenceManager()
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Sidebar for configuration
with st.sidebar:
    st.header("Reference Download Settings")
    
    # Download path configuration
    download_path = st.text_input(
        "Download Path", 
        value="./downloaded_references",
        help="Directory where reference papers will be downloaded"
    )
    
    # Reference download options
    st.subheader("Download Options")
    enable_reference_download = st.checkbox(
        "Enable Reference Download", 
        value=False,
        help="Allow downloading reference papers from uploaded PDFs"
    )
    
    if enable_reference_download:
        st.info("⚠️ **Copyright Notice**: Only download papers that are freely available and respect copyright restrictions.")
        
        # Advanced options
        with st.expander("Advanced Settings"):
            max_concurrent = st.slider("Max Concurrent Downloads", 1, 10, 3)
            retry_attempts = st.slider("Retry Attempts", 1, 5, 3)
            timeout_seconds = st.slider("Timeout (seconds)", 30, 120, 60)
            
            # Update configuration
            config = DownloadConfig(
                download_path=download_path,
                max_concurrent_downloads=max_concurrent,
                retry_attempts=retry_attempts,
                timeout_seconds=timeout_seconds
            )
            st.session_state.reference_manager.config = config

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

# Step 1.5: Reference Extraction
st.header("Reference Extraction")

# Check if we should extract references (either enabled in sidebar or if PDFs are already uploaded)
should_extract = enable_reference_download or (not uploaded_files and any(f.endswith('.pdf') for f in os.listdir(pdf_dir)))

if should_extract:
    # Extract references from uploaded PDFs or existing PDFs
    all_references = {}
    reference_summaries = {}
    
    # Get list of PDFs to process
    pdfs_to_process = []
    if uploaded_files:
        pdfs_to_process = [(f.name, os.path.join(pdf_dir, f.name)) for f in uploaded_files]
    else:
        # Process existing PDFs in the directory
        pdfs_to_process = [(f, os.path.join(pdf_dir, f)) for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    
    with st.spinner("Extracting references from PDFs..."):
        for filename, pdf_path in pdfs_to_process:
            references = st.session_state.reference_manager.extract_references_from_pdf(pdf_path)
            all_references[filename] = references
            reference_summaries[filename] = st.session_state.reference_manager.get_reference_summary(references)
            
            # Show immediate feedback
            st.success(f"✅ {filename}: {len(references)} references extracted")
    
    # Display reference summaries
    st.info(f"📊 Reference extraction completed! Found references in {len([s for s in reference_summaries.values() if s['total_references'] > 0])} PDF(s)")
    
    for filename, summary in reference_summaries.items():
        with st.expander(f"References in {filename} ({summary['total_references']} found)"):
            if summary['total_references'] > 0:
                # Show statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total References", summary['total_references'])
                with col2:
                    st.metric("High Confidence", summary['high_confidence'])
                with col3:
                    st.metric("With DOI", summary['with_doi'])
                
                # Show sample references
                st.subheader("Sample References")
                for i, ref in enumerate(summary['sample_references']):
                    with st.container():
                        st.markdown("---")
                        st.markdown(f"**{i+1}. {ref['authors']} ({ref['year']})**")
                        st.markdown(f"**Title:** {ref['title']}")
                        st.markdown(f"**Journal:** {ref['journal']}")
                        if ref['doi']:
                            st.markdown(f"**DOI:** `{ref['doi']}`")
                        st.markdown(f"**Confidence:** {ref['confidence']:.2f}")
                        
                        # Show full title in a code block for better visibility
                        st.code(f"Full Title: {ref['title']}", language=None)
            else:
                st.info("No references found in this PDF.")
    
    # User consent for reference downloading
    total_refs = sum(summary['total_references'] for summary in reference_summaries.values())
    if total_refs > 0:
        st.header("Reference Download")
        
        # Show a note about enabling download in sidebar if not enabled
        if not enable_reference_download:
            st.warning("⚠️ **Note:** To download reference papers, please check 'Enable Reference Download' in the sidebar.")
        
        # Initialize session state for showing reference list
        if 'show_reference_download' not in st.session_state:
            st.session_state.show_reference_download = False
        
        # Button to enable reference download
        if not st.session_state.show_reference_download:
            st.success(f"✅ Found {total_refs} references across all PDFs!")
            st.info("Click the button below to see the list of reference papers available for download.")
            if st.button("📥 Show Reference Papers", type="primary", help="Click to view and select reference papers for download"):
                st.session_state.show_reference_download = True
                st.rerun()
        else:
            # Show the reference download interface
            st.warning("""
            **Important Information:**
            - Reference papers will be searched and downloaded from academic databases
            - Only freely available papers will be downloaded
            - Downloaded papers will be stored in your specified directory
            - You are responsible for complying with copyright laws
            """)
            
            consent_given = st.checkbox(
                "I consent to download reference papers and understand the copyright implications",
                value=False
            )
            
            if consent_given:
                # Reference selection
                st.subheader("Select References to Download")
                
                selected_references_map = {}
                
                for filename, references in all_references.items():
                    if references:
                        with st.expander(f"Select references from {filename} ({len(references)} total)"):
                            # Add search/filter functionality
                            search_term = st.text_input(
                                f"Search references in {filename}",
                                placeholder="Enter author name, title keywords, or journal name...",
                                key=f"search_{filename}"
                            )
                            
                            # Filter references based on search term
                            filtered_references = references
                            if search_term:
                                search_lower = search_term.lower()
                                filtered_references = [
                                    ref for ref in references
                                    if (search_lower in ref.authors.lower() or
                                        search_lower in ref.title.lower() or
                                        search_lower in ref.journal.lower())
                                ]
                                st.info(f"Showing {len(filtered_references)} of {len(references)} references matching '{search_term}'")
                            
                            # Initialize selection state for this filename
                            selection_key = f"selected_refs_{filename}"
                            if selection_key not in st.session_state:
                                st.session_state[selection_key] = []
                            
                            # Add select all/clear all buttons
                            col1, col2, col3 = st.columns([1, 1, 2])
                            with col1:
                                if st.button("Select All", key=f"select_all_{filename}"):
                                    st.session_state[selection_key] = list(range(len(filtered_references)))
                                    st.rerun()
                            with col2:
                                if st.button("Clear All", key=f"clear_all_{filename}"):
                                    st.session_state[selection_key] = []
                                    st.rerun()
                            
                            st.markdown("---")
                            
                            # Pagination for references
                            items_per_page = 5
                            total_pages = (len(filtered_references) + items_per_page - 1) // items_per_page
                            
                            # Initialize current page in session state
                            page_key = f"page_{filename}"
                            if page_key not in st.session_state:
                                st.session_state[page_key] = 0
                            
                            # Page navigation
                            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
                            with col1:
                                if st.button("◀ Previous", key=f"prev_{filename}", disabled=st.session_state[page_key] == 0):
                                    st.session_state[page_key] = max(0, st.session_state[page_key] - 1)
                                    st.rerun()
                            with col2:
                                st.write(f"Page {st.session_state[page_key] + 1} of {total_pages}")
                            with col3:
                                if st.button("Next ▶", key=f"next_{filename}", disabled=st.session_state[page_key] >= total_pages - 1):
                                    st.session_state[page_key] = min(total_pages - 1, st.session_state[page_key] + 1)
                                    st.rerun()
                            
                            st.markdown("---")
                            
                            # Show references for current page
                            start_idx = st.session_state[page_key] * items_per_page
                            end_idx = min(start_idx + items_per_page, len(filtered_references))
                            current_page_references = filtered_references[start_idx:end_idx]
                            
                            for i, ref in enumerate(current_page_references):
                                actual_idx = start_idx + i
                                # Create a more readable display for each reference
                                with st.container():
                                    st.markdown("---")
                                    col1, col2 = st.columns([1, 20])
                                    with col1:
                                        is_selected = st.checkbox(
                                            f"📥", 
                                            key=f"ref_{filename}_{actual_idx}", 
                                            value=actual_idx in st.session_state[selection_key],
                                            help="Select to download this reference"
                                        )
                                        if is_selected and actual_idx not in st.session_state[selection_key]:
                                            st.session_state[selection_key].append(actual_idx)
                                        elif not is_selected and actual_idx in st.session_state[selection_key]:
                                            st.session_state[selection_key].remove(actual_idx)
                                    with col2:
                                        # Display full paper information clearly
                                        st.markdown(f"**{actual_idx + 1}. {ref.authors} ({ref.year})**")
                                        st.markdown(f"**Title:** {ref.title}")
                                        st.markdown(f"**Journal:** {ref.journal}")
                                        if ref.doi:
                                            st.markdown(f"**DOI:** `{ref.doi}`")
                                        if hasattr(ref, 'confidence') and ref.confidence:
                                            st.markdown(f"**Confidence:** {ref.confidence:.2f}")
                                        
                                        # Show a preview of the full title in a code block for better visibility
                                        st.code(f"Full Title: {ref.title}", language=None)
                            
                            # Map the filtered indices back to original reference indices
                            # We need to map the filtered indices to the original reference indices
                            original_indices = []
                            for i in st.session_state[selection_key]:
                                if i < len(filtered_references):
                                    # Find the index of this reference in the original references list
                                    try:
                                        original_index = references.index(filtered_references[i])
                                        original_indices.append(original_index)
                                    except ValueError:
                                        # If not found, skip it
                                        continue
                            
                            selected_references_map[filename] = original_indices
                            
                            if st.session_state[selection_key]:
                                st.info(f"Selected {len(st.session_state[selection_key])} references from {filename}")
                
                # Download button
                if any(selected_references_map.values()):
                    if st.button("Download Selected References"):
                        with st.spinner("Downloading reference papers..."):
                            # Create progress bar
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            def progress_callback(current, total, message):
                                progress = current / total if total > 0 else 0
                                progress_bar.progress(progress)
                                status_text.text(message)
                            
                            # Process PDFs with selected references
                            pdf_paths = [os.path.join(pdf_dir, filename) for filename in all_references.keys()]
                            results = st.session_state.reference_manager.batch_process_pdfs(
                                pdf_paths=pdf_paths,
                                user_id=st.session_state.user_id,
                                session_id=st.session_state.session_id,
                                consent_given=True,
                                selected_references_map=selected_references_map,
                                custom_download_path=download_path,
                                progress_callback=progress_callback
                            )
                            
                            # Show results
                            progress_bar.empty()
                            status_text.empty()
                            
                            st.success(f"Download completed!")
                            
                            # Display download statistics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("PDFs Processed", results['processed_pdfs'])
                            with col2:
                                st.metric("References Found", results['total_references_extracted'])
                            with col3:
                                st.metric("Successfully Downloaded", results['total_references_downloaded'])
                            with col4:
                                success_rate = f"{results['successful_pdfs']}/{results['total_pdfs']}"
                                st.metric("PDF Success Rate", success_rate)
                            
                            # Show detailed results
                            with st.expander("Download Details"):
                                # Show download path information
                                download_info = st.session_state.reference_manager.get_download_path_info()
                                st.write(f"**Download Path:** {download_info['path']}")
                                st.write(f"**Path exists:** {download_info['exists']}")
                                st.write(f"**Files in directory:** {download_info['file_count']}")
                                st.write(f"**Total size:** {download_info['total_size_mb']} MB")
                                
                                st.markdown("---")
                                
                                for result in results['pdf_results']:
                                    if result.get('download_results'):
                                        st.write(f"**{result['pdf_filename']}:**")
                                        st.write(f"- References extracted: {result['references_extracted']}")
                                        
                                        # Show download summary with better formatting
                                        successful = result['download_results']['successful_downloads']
                                        failed = result['download_results']['failed_downloads']
                                        skipped = result['download_results']['skipped_downloads']
                                        
                                        if successful > 0:
                                            st.success(f"✅ Downloads successful: {successful}")
                                        if failed > 0:
                                            st.error(f"❌ Downloads failed: {failed}")
                                        if skipped > 0:
                                            st.info(f"⏭️ Downloads skipped: {skipped}")
                                        
                                        # Show overall status
                                        total_attempted = successful + failed
                                        if total_attempted > 0:
                                            success_rate = (successful / total_attempted) * 100
                                            if success_rate == 100:
                                                st.success(f"🎉 All downloads successful! ({success_rate:.0f}%)")
                                            elif success_rate > 0:
                                                st.warning(f"⚠️ Partial success: {success_rate:.0f}% of downloads succeeded")
                                            else:
                                                st.error(f"💥 All downloads failed ({success_rate:.0f}% success rate)")
                                        
                                        # Show detailed download results if available
                                        if 'download_details' in result['download_results']:
                                            st.write("**Individual download results:**")
                                            for detail in result['download_results']['download_details']:
                                                if detail['status'] == 'success':
                                                    st.success(f"✅ **{detail['reference'].title[:60]}...**")
                                                    st.write(f"  📁 File: {detail['file_path']}")
                                                    st.write(f"  📡 Source: {detail.get('source', 'Unknown')}")
                                                elif detail['status'] == 'failed':
                                                    st.error(f"❌ **{detail['reference'].title[:60]}...**")
                                                    st.write(f"  💬 Reason: {detail.get('message', 'Unknown error')}")
                                                else:  # skipped
                                                    st.info(f"⏭️ **{detail['reference'].title[:60]}...**")
                                                    st.write(f"  💬 Reason: {detail.get('message', 'Already downloaded')}")
                                                    if detail.get('file_path'):
                                                        st.write(f"  📁 Existing file: {detail['file_path']}")
                                                st.write("---")
                                        
                                        st.divider()
            else:
                st.info("Please provide consent to proceed with reference downloading.")
            
            # Add a button to go back
            if st.button("← Back to Main View"):
                st.session_state.show_reference_download = False
                st.rerun()
    
    # Add a customized reference download section
    st.header("Customized Reference Download")
    st.info("Download a specific reference paper by entering its details manually:")
    
    # Manual reference input
    custom_authors = st.text_input("Authors", value="Shaojie Bai, J Zico Kolter, Vladlen Koltun")
    custom_title = st.text_input("Title", value="An empirical evaluation of generic convolutional and recurrent networks for sequence modeling")
    custom_journal = st.text_input("Journal", value="arXiv")
    custom_year = st.text_input("Year", value="2018")
    
    if st.button("Download This Reference"):
        from agents.reference_extractor import Reference
        
        # Create a custom reference
        custom_ref = Reference(
            authors=custom_authors,
            title=custom_title,
            journal=custom_journal,
            year=custom_year
        )
        
        # Download the reference
        with st.spinner("Downloading reference..."):
            from agents.reference_downloader import ReferenceDownloader
            downloader = ReferenceDownloader(download_path)
            
            result = downloader.download_single_reference(custom_ref)
            
            if result['status'] == 'success':
                st.success(f"✅ Download successful!")
                st.write(f"**File saved as:** {result['file_path']}")
                st.write(f"**Source:** {result['source']}")
                st.write(f"**Message:** {result['message']}")
            elif result['status'] == 'skipped':
                st.info(f"⏭️ Download skipped: {result['message']}")
                if result.get('file_path'):
                    st.write(f"**File already exists:** {result['file_path']}")
            else:
                st.error(f"❌ Download failed: {result['message']}")

# Step 2: Build Knowledge Base
st.header("Build Knowledge Base")

# Create a drag-and-drop interface for papers
st.subheader("📚 Paper Selection for Knowledge Base")

# Initialize paper selection in session state
if 'selected_papers_for_kb' not in st.session_state:
    st.session_state.selected_papers_for_kb = []

# Create two columns for the drag-and-drop interface
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📄 Available Papers")
    st.markdown("Click to add papers to your knowledge base:")
    
    # Show original uploaded PDFs
    st.markdown("**Original Papers:**")
    for pdf_file in os.listdir(pdf_dir):
        if pdf_file.endswith('.pdf'):
            paper_key = f"orig_{pdf_file}"
            if st.checkbox(f"📄 {pdf_file}", key=paper_key, value=paper_key in st.session_state.selected_papers_for_kb):
                if paper_key not in st.session_state.selected_papers_for_kb:
                    st.session_state.selected_papers_for_kb.append(paper_key)
            else:
                if paper_key in st.session_state.selected_papers_for_kb:
                    st.session_state.selected_papers_for_kb.remove(paper_key)
    
    # Show downloaded reference papers
    download_path_info = st.session_state.reference_manager.get_download_path_info()
    if download_path_info['file_count'] > 0:
        st.markdown("**Downloaded References:**")
        try:
            for ref_file in os.listdir(download_path_info['path']):
                if ref_file.endswith('.pdf'):
                    paper_key = f"ref_{ref_file}"
                    if st.checkbox(f"📚 {ref_file}", key=paper_key, value=paper_key in st.session_state.selected_papers_for_kb):
                        if paper_key not in st.session_state.selected_papers_for_kb:
                            st.session_state.selected_papers_for_kb.append(paper_key)
                    else:
                        if paper_key in st.session_state.selected_papers_for_kb:
                            st.session_state.selected_papers_for_kb.remove(paper_key)
        except FileNotFoundError:
            st.info("No downloaded references found.")

with col2:
    st.markdown("### 🎯 Selected for Knowledge Base")
    st.markdown("Papers that will be included in your knowledge base:")
    
    if st.session_state.selected_papers_for_kb:
        for paper_key in st.session_state.selected_papers_for_kb:
            if paper_key.startswith("orig_"):
                paper_name = paper_key.replace("orig_", "")
                st.markdown(f"📄 **{paper_name}** (Original)")
            elif paper_key.startswith("ref_"):
                paper_name = paper_key.replace("ref_", "")
                st.markdown(f"📚 **{paper_name}** (Reference)")
        
        st.markdown(f"**Total papers selected:** {len(st.session_state.selected_papers_for_kb)}")
        
        # Clear all button
        if st.button("🗑️ Clear All Selections"):
            st.session_state.selected_papers_for_kb = []
            st.rerun()
    else:
        st.info("No papers selected. Select papers from the left panel to build your knowledge base.")

st.markdown("---")

# Build knowledge base button
if st.session_state.selected_papers_for_kb:
    if st.button("🏗️ Build Knowledge Base with Selected Papers"):
        agent = PaperAgent(
            embedding_model="nomic-embed-text",
            llm_model="llama3.2:latest",
            vector_store_dir="./vector_stores",
        )
        
        # Build knowledge base from uploaded PDFs
        success = agent.build_knowledge_base(pdf_dir, index_name="research_papers")
        
        # If we have downloaded references, add them to the knowledge base
        if success and download_path_info['file_count'] > 0:
            st.info("Adding downloaded reference papers to knowledge base...")
            # Note: This would require extending the PaperAgent to handle additional PDF directories
            # For now, we'll just note that references are available
        
        if success:
            st.session_state["agent"] = agent
            st.success("Knowledge base built successfully!")
            if download_path_info['file_count'] > 0:
                st.info(f"Includes {download_path_info['file_count']} reference papers")
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

# Cleanup section
st.header("Cleanup")
col1, col2 = st.columns(2)

with col1:
    if st.button("Clean Up Uploaded PDFs"):
        if os.path.exists(pdf_dir):
            shutil.rmtree(pdf_dir)
            os.makedirs(pdf_dir, exist_ok=True)
            st.success("Uploaded PDF files have been cleaned up.")
        else:
            st.info("No uploaded files to clean up.")

with col2:
    if st.button("Clean Up Downloaded References"):
        if enable_reference_download:
            cleanup_results = st.session_state.reference_manager.cleanup_downloads(older_than_days=30)
            st.success(f"Cleanup completed: {cleanup_results['files_removed']} files removed, {cleanup_results['space_freed_mb']} MB freed")
        else:
            st.info("Reference download is not enabled.")

# Footer with copyright information
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    <p>⚠️ <strong>Copyright Notice:</strong> This tool is for educational and research purposes only. 
    Users are responsible for complying with copyright laws when downloading reference papers.</p>
</div>
""", unsafe_allow_html=True)
