import streamlit as st
import google.generativeai as genai
from googletrans import Translator  
from functions import get_secret, reset_chat  

# --- Configuration ---
api_key = get_secret("API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

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

# --- Session State Setup ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
if "target_lang" not in st.session_state:
    st.session_state.target_lang = "en"

# --- Sidebar Controls ---
with st.sidebar:
    st.title("Settings")
    
    # Language Selection
    st.session_state.target_lang = st.selectbox(
        "Output Language",
        options=list(LANGUAGES.keys()),
        index=1,  # Default to English
        key="lang_select"
    )
    
    # Temperature Control
    temperature = st.slider(
        "Response Creativity",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        help="Lower = More Factual, Higher = More Creative"
    )
    
    if st.button("Reset Chat"):
        reset_chat()

# --- Chat Interface ---
st.title("🌍 Bilingual Programming Tutor")

# Display chat history
for role, message in st.session_state.chat_history:
    st.chat_message(role).write(message)

# --- Chat Logic ---
user_input = st.chat_input("Ask your programming question...")

if user_input:
    # Append user message to history (in original language)
    st.chat_message("user").write(user_input)
    st.session_state.chat_history.append(("user", user_input))
    
    # Detect input language if not auto
    input_lang = "en"  # Default to English
    if LANGUAGES[st.session_state.target_lang] == "auto":
        try:
            translator = Translator()
            input_lang = translator.detect(user_input).lang
        except:
            input_lang = "en"
    
    # System prompt with translation instructions
    system_prompt = f"""
    You are a bilingual programming tutor with these rules:
    
    1. USER'S LANGUAGE: {input_lang.upper()}
    2. TARGET LANGUAGE: {LANGUAGES[st.session_state.target_lang].upper()}
    
    RESPONSE FORMAT:
    - If target language is English or same as input: Answer directly
    - Otherwise: Provide answer in target language BUT:
      * Keep all code/technical terms in English
      * Include English terms in parentheses when needed
      * Example: "Use un bucle (loop) for..."
    
    CONTENT RULES:
    - Always prioritize technical accuracy
    - Simplify complex concepts
    - Provide code examples when helpful
    - If question isn't programming-related, say:
      "I specialize in programming questions. Could you ask about coding?"
    """
    
    # Generate response
    with st.spinner("Thinking..."):
        try:
            response = model.generate_content(
                contents=[{"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_input}]}],
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": 1500
                }
            )
            reply = response.text
            
            # Store and display
            st.chat_message("assistant").write(reply)
            st.session_state.chat_history.append(("assistant", reply))
            
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")