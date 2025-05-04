import streamlit as st
import os
from dotenv import load_dotenv
import io
import tempfile
from pydub import AudioSegment
import speech_recognition as sr
from typing import Optional, Union

def get_secret(key: str) -> Optional[str]:
    """
    Enhanced secret manager with better error handling and type hints
    
    Args:
        key: The secret/environment variable name to retrieve
        
    Returns:
        The secret value or None if not found
    """
    try:
        # Try Streamlit secrets (for cloud)
        if hasattr(st, 'secrets'):
            return st.secrets[key]
        raise KeyError("Streamlit secrets not available")
    except (KeyError, AttributeError, FileNotFoundError):
        try:
            # Fallback to .env file (for local)
            load_dotenv()
            value = os.getenv(key)
            if not value:
                st.warning(f"Secret {key} is empty in .env file")
            return value
        except Exception as e:
            st.error(f"Error loading secret {key}: {str(e)}")
            return None

def reset_chat(complete_reset: bool = True) -> None:
    """
    Comprehensive chat reset with audio cleanup
    
    Args:
        complete_reset: If True, resets all session variables
                       If False, only resets chat history
    """
    # Core chat reset
    st.session_state.chat_history = []
    
    if complete_reset:
        # Extended state cleanup
        st.session_state.update({
            'example': False,
            'temperature': 0.7,
            'translation_enabled': True,
            'show_technical_terms': False,
            'audio_processing': False,
            'user_input': None
        })
        
        # Clean up temporary files
        if 'audio_file' in st.session_state:
            try:
                if os.path.exists(st.session_state.audio_file):
                    os.remove(st.session_state.audio_file)
            except Exception as e:
                st.error(f"Error cleaning audio file: {str(e)}")
            finally:
                if 'audio_file' in st.session_state:
                    del st.session_state.audio_file
    
    # Visual confirmation
    st.toast("Chat history cleared!", icon="🔄")

def transcribe_audio(audio_bytes: bytes) -> Optional[str]:
    """
    Robust audio transcription with format conversion and error handling
    
    Args:
        audio_bytes: Raw audio data in bytes
        
    Returns:
        Transcribed text or None if failed
    """
    try:
        # Initialize recognizer
        r = sr.Recognizer()
        
        # Create temporary file path
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Convert bytes to AudioSegment
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
            
            # Export as WAV with proper settings
            audio.set_frame_rate(16000).set_channels(1).export(
                tmp_path,
                format="wav",
                codec="pcm_s16le"
            )
            
            # Process audio file
            with sr.AudioFile(tmp_path) as source:
                audio_data = r.record(source)
                text = r.recognize_google(audio_data)
                return text
                
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except sr.UnknownValueError:
        st.error("Could not understand audio. Please speak clearly.")
        return None
    except sr.RequestError as e:
        st.error(f"Speech recognition service error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Audio processing failed: {str(e)}")
        return None

def save_audio_to_temp(audio_bytes: bytes) -> Optional[str]:
    """
    Save audio bytes to temporary file and return path
    
    Args:
        audio_bytes: Raw audio data
        
    Returns:
        Path to temporary file or None if failed
    """
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp.write(audio_bytes)
            return tmp.name
    except Exception as e:
        st.error(f"Failed to save audio: {str(e)}")
        return None