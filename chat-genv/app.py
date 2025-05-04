import streamlit as st
import google.generativeai as genai
from googletrans import Translator
import speech_recognition as sr
from functions import get_secret, reset_chat
from audio_recorder_streamlit import audio_recorder

# --- Configuration ---
api_key = get_secret("API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")
translator = Translator()

# Language Support
LANGUAGES = {
    "Auto": "auto",
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Chinese": "zh-cn",
    "Japanese": "ja",
    "Russian": "ru",
    "Hindi": "hi",
    "Arabic": "ar"
}

# Technical Glossary (term: [translations])
GLOSSARY = {
    "loop": {"es": "bucle", "fr": "boucle", "de": "Schleife"},
    "function": {"es": "función", "fr": "fonction", "de": "Funktion"},
    # Add more terms as needed
}

# --- Session State Setup ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "target_lang" not in st.session_state:
    st.session_state.target_lang = "en"
if "show_original" not in st.session_state:
    st.session_state.show_original = False

# --- Sidebar Controls ---
with st.sidebar:
    st.title("🌐 Language Settings")
    
    # Language Selection
    st.session_state.target_lang = st.selectbox(
        "Output Language",
        options=list(LANGUAGES.keys()),
        index=1,
        key="lang_select"
    )
    
    # Translation Toggle
    st.session_state.show_original = st.toggle(
        "Show Original English",
        help="Display original English alongside translation"
    )
    
    # Audio Input
    st.title("🎤 Speech Input")
    audio_bytes = audio_recorder(
        pause_threshold=2.0,
        text="Click to speak",
        key="audio_recorder"
    )
    
    # Technical Glossary
    st.title("📚 Code Glossary")
    with st.expander("View Technical Terms"):
        for term, translations in GLOSSARY.items():
            st.write(f"**{term}**: {', '.join(f'{k} ({v})' for k,v in translations.items())}")
    
    # System Settings
    st.title("⚙️ System")
    temperature = st.slider(
        "Response Creativity",
        0.0, 1.0, 0.7
    )
    if st.button("Reset Chat"):
        reset_chat()

# --- Audio Processing ---
def transcribe_audio(audio_bytes):
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_bytes) as source:
            audio = r.record(source)
            return r.recognize_google(audio)
    except Exception as e:
        st.error(f"Speech recognition failed: {e}")
        return None

# --- Chat Interface ---
st.title("💻 Bilingual Code Tutor")

# Display chat history with toggle
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        if role == "assistant" and st.session_state.show_original and "ORIGINAL:" in message:
            parts = message.split("ORIGINAL:")
            st.write(parts[0])  # Translated part
            with st.expander("Show Original"):
                st.write(parts[1])  # English original
        else:
            st.write(message)

# --- Input Processing ---
user_input = ""
if audio_bytes:
    user_input = transcribe_audio(audio_bytes)
else:
    user_input = st.chat_input("Type or speak your question...")

if user_input:
    # Append user message
    st.chat_message("user").write(user_input)
    st.session_state.chat_history.append(("user", user_input))
    
    # Detect input language
    input_lang = "en"
    if LANGUAGES[st.session_state.target_lang] == "auto":
        try:
            input_lang = translator.detect(user_input).lang
        except:
            input_lang = "en"
    
    # Enhanced System Prompt
    system_prompt = f"""
    BILINGUAL PROGRAMMING TUTOR INSTRUCTIONS:
    
    INPUT LANGUAGE: {input_lang.upper()}
    TARGET LANGUAGE: {LANGUAGES[st.session_state.target_lang].upper()}
    
    RESPONSE RULES:
    1. Preserve ALL code blocks and technical terms in original English
    2. For non-English outputs:
       - Include English terms in parentheses when helpful
       - Example: "Use 'for loops' (bucles for) for iteration"
    3. Format:
       [TRANSLATED RESPONSE]
       ORIGINAL: [ENGLISH VERSION]
    
    CONTENT RULES:
    - Prioritize technical accuracy over perfect translation
    - Simplify complex concepts with examples
    - For non-programming questions, respond:
      "I specialize in programming questions. Could you ask about coding?"
    """
    
    # Generate response
    with st.spinner("Generating response..."):
        try:
            response = model.generate_content(
                contents=[{"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_input}]}],
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": 2000
                }
            )
            reply = response.text
            
            # Post-processing
            if "ORIGINAL:" not in reply and LANGUAGES[st.session_state.target_lang] != "en":
                reply = reply + f"\nORIGINAL: {reply}"
            
            # Store and display
            st.chat_message("assistant").write(reply)
            st.session_state.chat_history.append(("assistant", reply))
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

# --- Translate Last Message Button ---
if st.session_state.chat_history and st.session_state.chat_history[-1][0] == "assistant":
    last_msg = st.session_state.chat_history[-1][1]
    if "ORIGINAL:" in last_msg:
        original = last_msg.split("ORIGINAL:")[1].strip()
        
        target_lang_code = LANGUAGES[st.session_state.target_lang]
        if st.button(f"Re-translate to {st.session_state.target_lang}"):
            try:
                translated = translator.translate(original, dest=target_lang_code).text
                updated_msg = f"{translated}\nORIGINAL: {original}"
                st.session_state.chat_history[-1] = ("assistant", updated_msg)
                st.rerun()
            except Exception as e:
                st.error(f"Translation failed: {e}")