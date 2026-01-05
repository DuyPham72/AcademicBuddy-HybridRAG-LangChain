import streamlit as st
from src.api_client import APIClient

def render_sidebar(api: APIClient):
    """Renders the file upload and management sidebar."""
    with st.sidebar:
        st.header("📚 Knowledge Base")
        
        # --- Upload Section ---
        # 1. Initialize state for resetting the uploader
        if "uploader_key" not in st.session_state:
            st.session_state.uploader_key = 0

        # 2. Initialize a set to track processed filenames
        if "processed_files" not in st.session_state:
            st.session_state.processed_files = set()

        uploaded_files = st.file_uploader(
            label="Upload PDF", 
            accept_multiple_files=True,
            type=["pdf"],
            label_visibility="collapsed",
            key=f"uploader_{st.session_state.uploader_key}"
        )
        
        if uploaded_files:
            # Filter: Find files that haven't been processed yet
            new_files = [
                f for f in uploaded_files 
                if f.name not in st.session_state.processed_files
            ]

            # Auto-Process
            if new_files:
                with st.spinner(f"Auto-processing {len(new_files)} new file(s)..."):
                    success = api.upload_files(new_files)
                    if success:
                        # Mark these files as processed
                        for f in new_files:
                            st.session_state.processed_files.add(f.name)
                        
                        st.success("Files processed!")
                        
                        # Invalidate cache to force list refresh
                        if "file_list" in st.session_state:
                            del st.session_state["file_list"]
                        
                        # Increment key to reset the uploader widget
                        st.session_state.uploader_key += 1
                        st.rerun()
                    else:
                        st.error("Upload failed.")

        st.divider()

        # --- File List Section ---
        st.subheader("Stored Files")
        
        # Check cache or fetch
        if "file_list" in st.session_state:
            files = st.session_state.file_list
        else:
            files = api.get_files()
            if files is not None:
                st.session_state.file_list = files
        
        # Render List
        if files is None:
            st.warning("Connecting to Backend...")
            if st.button("↻ Retry Connection"):
                st.rerun()
                
        elif not files:
            st.caption("No files found.")
            if st.button("↻ Refresh List"):
                if "file_list" in st.session_state:
                    del st.session_state["file_list"]
                st.rerun()
        else:
            selected_files = []
            for filename in files:
                # Checkbox logic
                if st.checkbox(filename, key=f"select_{filename}"):
                    selected_files.append(filename)
            
            # Save to Session State
            st.session_state.selected_files_list = selected_files
            
            st.write("")

            if st.button("🗑️ Delete Selected", type="primary", use_container_width=True, disabled=len(selected_files) == 0):
                with st.spinner(f"Deleting {len(selected_files)} file(s)..."):
                    for filename in selected_files:
                        api.delete_file(filename)
                        
                        # Clean up 'processed' memory so it can be re-uploaded immediately if desired
                        if filename in st.session_state.processed_files:
                            st.session_state.processed_files.remove(filename)

                    # Refresh the list
                    if "file_list" in st.session_state:
                        del st.session_state["file_list"]
                    
                    st.success("Files deleted.")
                    st.rerun()

        st.divider()
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()