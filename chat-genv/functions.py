import streamlit as st
import os
from dotenv import load_dotenv

def get_secret(key):
    """
    Get a secret from Streamlit or fallback to .env for local development.
    This allows the app to run both on Streamlit Cloud and locally.
    
    Args:
        key (str): The name of the secret/environment variable to retrieve
        
    Returns:
        str: The value of the secret or None if not found
    """
    try:
        # First try Streamlit secrets (for cloud deployment)
        return st.secrets[key]
    except (AttributeError, KeyError, FileNotFoundError):
        try:
            # Fallback to .env file (for local development)
            load_dotenv()
            return os.getenv(key)
        except Exception as e:
            st.error(f"Error loading secret {key}: {str(e)}")
            return None

def reset_chat(complete_reset=True):
    """
    Reset the Streamlit chat session state with comprehensive cleanup.
    Handles both minimal reset (just chat history) and complete reset (all states).
    
    Args:
        complete_reset (bool): If True, resets all session state variables
                              If False, only resets chat history
    """
    # Always reset these core chat variables
    st.session_state.chat_history = []
    st.session_state.last_input = ""
    
    if complete_reset:
        # Reset all additional state variables
        st.session_state.example = False
        st.session_state.temperature = 0.7
        st.session_state.translation_enabled = True
        st.session_state.show_technical_terms = False
        
        # Clear any temporary files
        if 'audio_file' in st.session_state:
            try:
                os.remove(st.session_state.audio_file)
            except:
                pass
            del st.session_state.audio_file
    
    # Optional: Add visual confirmation
    if 'reset_confirmation' not in st.session_state:
        st.session_state.reset_confirmation = True
        st.toast("Chat history cleared!", icon="🔄")