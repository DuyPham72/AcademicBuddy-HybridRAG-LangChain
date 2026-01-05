import streamlit as st
import html
from src.api_client import APIClient

# Define CSS globally to ensure it never breaks due to indentation
CHAT_CSS = """
<style>
    .source-pill {
        display: inline-block;
        background-color: #f0f2f6;
        color: #31333f;
        padding: 4px 12px;
        border-radius: 16px;
        margin-right: 8px;
        margin-bottom: 8px;
        border: 1px solid #e0e0e0;
        font-size: 0.85em;
        cursor: help;
        position: relative;
        text-decoration: none;
        vertical-align: middle;
    }
    .source-pill:hover {
        background-color: #e8eaf0;
        border-color: #d0d0d0;
    }
    .source-label {
        color: #666; 
        font-size: 0.9em; 
        font-weight: 600; 
        margin-right: 8px;
        vertical-align: middle;
    }
</style>
"""

def render_chat(api: APIClient):
    """Renders the main chat interface with Source Citations."""
    
    # Inject CSS immediately
    st.markdown(CHAT_CSS, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                display_sources(message["sources"])

    # Handle User Input
    if prompt := st.chat_input("Ask about your documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            retrieved_sources = []
            
            chat_history = [
                {"role": m["role"], "content": m["content"]} 
                for m in st.session_state.messages[:-1]
            ]

            selected_files = st.session_state.get("selected_files_list", [])
            
            stream_generator = api.chat_stream(prompt, chat_history, selected_files)
            
            for chunk in stream_generator:
                chunk_type = chunk.get("type")
                chunk_data = chunk.get("data")

                if chunk_type == "sources":
                    retrieved_sources = chunk_data
                elif chunk_type == "content":
                    full_response += chunk_data
                    message_placeholder.markdown(full_response + "▌")
                elif chunk_type == "error":
                    st.error(chunk_data)

            message_placeholder.markdown(full_response)
            
            if retrieved_sources:
                display_sources(retrieved_sources)
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": full_response,
                "sources": retrieved_sources
            })

def display_sources(sources):
    """Helper to render sources as HTML pills with tooltips."""
    
    # Start container
    html_content = '<div style="margin-top: 10px;">'
    html_content += '<span class="source-label">Sources:</span>'
    
    for src in sources:
        # Extract content
        content_raw = src.get('content', 'No content available.')
        filename = src.get('source', 'Unknown File')
        
        # Smart Title Logic (Button Label)
        display_text = src.get('display', filename)
        safe_display = html.escape(display_text)

        # Multi-line Tooltip Logic
        # 1. Clean the content (remove raw newlines that break Streamlit)
        clean_content = content_raw.replace('\n', ' ').strip()
        
        # 2. Truncate content to keep it manageable
        truncated_content = content_preview(clean_content, 500)
        
        # 3. Escape individual parts
        safe_filename = html.escape(filename).replace('"', '&quot;').replace('temp_', '')
        safe_content = html.escape(truncated_content).replace('"', '&quot;')
        
        # 4. Use '&#10;' to create a safe visual newline in the tooltip
        safe_tooltip = f"File: {safe_filename}&#10;&#10;{safe_content}"
        
        # Render pill
        html_content += f'<span class="source-pill" title="{safe_tooltip}">📄 {safe_display}</span>'
    
    html_content += "</div>"
    
    st.markdown(html_content, unsafe_allow_html=True)

def content_preview(text, limit=300):
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "..."