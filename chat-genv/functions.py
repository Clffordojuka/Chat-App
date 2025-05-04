import streamlit as st
import os
import io
import tempfile
import platform
from dotenv import load_dotenv
from typing import Optional
from pydub import AudioSegment
import speech_recognition as sr

def get_secret(key: str) -> Optional[str]:
    """
    Enhanced secret manager with Windows compatibility
    """
    try:
        return st.secrets[key]
    except Exception:
        load_dotenv()
        return os.getenv(key)

def reset_chat(complete_reset: bool = True) -> None:
    """
    Reset chat with Windows-specific cleanup
    """
    st.session_state.chat_history = []
    if complete_reset:
        st.session_state.update({
            'audio_file': None,
            'audio_processed': False
        })
        if 'audio_file' in st.session_state and st.session_state.audio_file:
            try:
                if os.path.exists(st.session_state.audio_file):
                    os.remove(st.session_state.audio_file)
            except Exception as e:
                st.warning(f"Couldn't clean audio file: {e}")

def transcribe_audio(audio_bytes: bytes) -> Optional[str]:
    """
    Windows-compatible audio transcription with robust error handling
    """
    try:
        # Initialize recognizer
        r = sr.Recognizer()
        
        # Create temporary file path with explicit directory
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"audio_{os.getpid()}.wav")
        
        # Convert and save audio with Windows-specific settings
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        
        # Handle Windows-specific audio format requirements
        if platform.system() == "Windows":
            audio = audio.set_frame_rate(16000).set_channels(1)
            audio.export(temp_path, format="wav", codec="pcm_s16le")
        else:
            audio.export(temp_path, format="wav")
        
        # Process audio with explicit file handling
        with open(temp_path, 'rb') as audio_file:
            with sr.AudioFile(audio_file) as source:
                audio_data = r.record(source)
                text = r.recognize_google(audio_data)
                return text
                
    except sr.UnknownValueError:
        st.error("Couldn't understand audio. Please speak clearly.")
    except sr.RequestError as e:
        st.error(f"Speech service error: {e}")
    except Exception as e:
        st.error(f"Audio processing failed: {e}")
    finally:
        # Ensure file cleanup
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                st.warning(f"Couldn't clean temp file: {e}")
    return None

def windows_audio_setup():
    """
    Windows-specific audio setup checks and instructions
    """
    if platform.system() == "Windows":
        st.sidebar.markdown("### Windows Audio Setup")
        if not os.path.exists(os.path.join(os.getenv('SystemRoot'), 'System32', 'Speech')):
            st.sidebar.warning("""
            **Required Windows Components Missing**:
            1. Open 'Turn Windows features on or off'
            2. Enable 'Windows Media Player' and 'Speech Recognition'
            3. Restart your computer
            """)
        if not os.path.exists(os.path.join(os.getenv('ProgramFiles'), 'Windows Media Player')):
            st.sidebar.warning("Windows Media Player required for audio processing")