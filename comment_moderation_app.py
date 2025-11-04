import streamlit as st
import google.generativeai as genai
import importlib.metadata

# --- App Config ---
st.set_page_config(page_title="Comment Categorizer", page_icon="💬", layout="centered")
st.title("💬 Comment Categorizer")

# --- Version Information ---
try:
    genai_version = importlib.metadata.version("google-generativeai")
except importlib.metadata.PackageNotFoundError:
    genai_version = "Unknown"

st.caption(f"🧩 Google Generative AI SDK version: {genai_version}")

# --- Configure Google Gemini API ---
# Make sure to set GOOGLE_API_KEY in Streamlit Cloud → Settings → Secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- Initialize session state ---
if "comment" not in st.session_state:
    st.session_state.comment = ""

# --- Text Area (Smaller Height) ---
st.text_area(
    "Enter your comment:",
    key="comment",
    height=100,
    placeholder="Type your comment here..."
)

# --- Buttons (Submit + Clear Side by Side) ---
col1, col2 = st.columns([1, 1])
with col1:
    submit = st.button("Submit", use_container_width=True)
with col2:
    clear = st.button("Clear", use_container_width=True)

# --- Available Categories ---
categories = [
    "Harsh/insulting",
    "Vulgar",
    "Harassment",
    "Threatening",
    "Out of context",
    "Sexual content",
    "Hate speech",
    "Self-harm",
    "Graphic violence",
    "Positive feedback",
    "Constructive criticism",
    "Neutral opinion",
    "Polite disagreement",
    "Clarification request",
    "Supportive"
]

# --- Button Actions ---
if submit:
    if not st.session_state.comment.strip():
        st.warning("⚠️ Please enter a comment before submitting.")
    else:
        with st.spinner("Analyzing your comment..."):
            try:
                # Use Gemini 2.0 Flash (fast & accurate)
                model = genai.GenerativeModel("gemini-2.0-flash")

                prompt = f"""
You are a comment moderation assistant. 
Analyze the given comment and classify it into one or more of the following categories:

{', '.join(categories)}

Return your response strictly in this JSON format:
{{
  "categories": ["<list of categories that apply>"],
  "summary": "<one-line summary>"
}}

Comment: {st.session_state.comment}
                """

                response = model.generate_content(prompt)
                text = response.text.strip()

                # Display formatted output
                st.subheader("🧠 AI Classification Result")
                st.code(text, language="json")

                # Highlight if it's harmful
                harmful_keywords = [
                    "harsh", "insult", "vulgar", "harassment", "threatening",
                    "sexual", "hate", "self-harm", "violence"
                ]
                if any(word in text.lower() for word in harmful_keywords):
                    st.error("🚫 Potentially inappropriate or harmful content detected.")
                else:
                    st.success("✅ Comment appears appropriate or constructive.")

            except Exception as e:
                st.error(f"API Error: {e}")

# --- Clear Button ---
if clear:
    st.session_state.comment = ""
    st.experimental_rerun()
