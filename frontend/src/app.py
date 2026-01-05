import streamlit as st
from src.api_client import APIClient
from src.components.file_manager import render_sidebar
from src.components.chat_interface import render_chat

# Page Config
st.set_page_config(
    page_title="Academic Buddy", 
    page_icon="🤖", 
    layout="wide"
)

def main():
    st.title("🤖 Academic Buddy")
    
    # Initialize the API Client once
    api = APIClient()

    # Render Components
    render_sidebar(api)
    render_chat(api)

if __name__ == "__main__":
    main()