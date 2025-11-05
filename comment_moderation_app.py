import streamlit as st
import google.generativeai as genai
import importlib.metadata
import json
import re
import time

# --- App Config ---
st.set_page_config(page_title="Comment Categorizer", page_icon="💬", layout="centered")
st.title("Comment Categorizer")

# Custom Button Styling
button_css = """
<style>
div.stButton > button {
    width: 200px !important;
}
div.stButton > button {
    background: linear-gradient(rgb(0, 86, 145) 0%, rgb(0, 86, 145) 50%, 
                               rgb(26, 103, 156) 50%, rgb(26, 103, 156) 100%) 0px 0px / 100% 200%;
    color: white !important;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: 600;
    cursor: pointer;
}
div.stButton > button:hover {
    filter: brightness(1.12);
}
</style>
"""
st.markdown(button_css, unsafe_allow_html=True)

# --- Version Info ---
try:
    genai_version = importlib.metadata.version("google-generativeai")
except importlib.metadata.PackageNotFoundError:
    genai_version = "Unknown"

st.caption(f" Google Generative AI SDK version: {genai_version}")

# --- Configure Google Gemini API ---
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- Initialize Session State ---
if "comment" not in st.session_state:
    st.session_state.comment = ""

# --- Fixed Container for UI Alignment ---
st.markdown("""
<style>
.center-box {
    max-width: 550px;
    margin-left: auto;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="center-box">', unsafe_allow_html=True)

# --- Text Area ---
comment_input = st.text_area(
    "Enter your comment:",
    value=st.session_state.comment,
    height=100,
    placeholder="Type your comment here..."
)

# Buttons (Aligned)
col1, col2 = st.columns(2)
with col1:
    submit = st.button("Leave a comment")
with col2:
    clear = st.button("Clear")

st.markdown("</div>", unsafe_allow_html=True)

# --- Category Setup ---
categories = [
    "Harsh/insulting", "Vulgar", "Harassment", "Threatening", "Out of context",
    "Sexual content", "Hate speech", "Self-harm", "Graphic violence",
    "Positive feedback", "Constructive criticism", "Neutral opinion",
    "Polite disagreement", "Clarification request", "Supportive"
]

category_colors = {
    "Harsh/insulting": "🔴", "Vulgar": "🔴", "Harassment": "🔴",
    "Threatening": "🔴", "Sexual content": "🟠", "Hate speech": "🔴",
    "Self-harm": "🟣", "Graphic violence": "🔴", "Out of context": "🟡",
    "Positive feedback": "🟢", "Constructive criticism": "🟢",
    "Neutral opinion": "⚪", "Polite disagreement": "🟢",
    "Clarification request": "🔵", "Supportive": "🟢"
}

# --- Submit Logic ---
if submit:
    if not comment_input.strip():
        st.warning("⚠️ Please enter a comment before submitting.")
    else:
        st.session_state.comment = comment_input

        with st.spinner("Analyzing your comment..."):
            time.sleep(2)
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")

                # UPDATED PROMPT FOR AUTO RESPONSE GENERATION
                prompt = f"""
You are a comment moderation and customer response assistant.

1. Classify the comment into one or more of these categories:
{', '.join(categories)}

2. Write a short summary of the comment.

3. Suggest a professional and polite auto-response:
   - If negative: acknowledge, apologize, and offer help.
   - If positive: thank them.
   - If neutral: acknowledge and invite clarification.

Return only valid JSON:
{{
  "categories": ["<list>"],
  "summary": "<short summary>",
  "suggested_response": "<professional reply>"
}}

Comment: {comment_input}
"""

                response = model.generate_content(prompt)
                text = response.text.strip()

                # Parse JSON safely
                json_text = re.search(r"\{.*\}", text, re.DOTALL)
                if json_text:
                    try:
                        result = json.loads(json_text.group())
                    except:
                        result = {"categories": ["Unrecognized"], "summary": text, "suggested_response": ""}
                else:
                    result = {"categories": ["Unrecognized"], "summary": text, "suggested_response": ""}

                # Display Summary
                st.markdown(f"**🧠 Summary:** {result.get('summary', 'No summary available.')}")

                # Display Categories
                cats = result.get("categories", [])
                if cats:
                    st.markdown("**🏷️ Categories Detected:**")
                    for c in cats:
                        st.markdown(f"{category_colors.get(c, '⚪')} **{c}**")

                # Display Suggested Response
                suggested = result.get("suggested_response", "")
                if suggested:
                    st.markdown("**📝 Suggested Response:**")
                    st.info(suggested)

                # Warning for Harmful
                harmful = {"Harsh/insulting", "Vulgar", "Harassment", "Threatening",
                           "Sexual content", "Hate speech", "Self-harm", "Graphic violence"}

                if any(c in harmful for c in cats):
                    st.error("🚫 Potentially inappropriate or harmful content detected.")
                else:
                    st.success("✅ Comment appears appropriate or constructive.")

            except Exception as e:
                if "429" in str(e):
                    st.warning("⚠️ API limit reached. Please wait before retrying.")
                else:
                    st.error(f"API Error: {e}")

# Clear Action
if clear:
    st.session_state.comment = ""
    st.rerun()

# Live State Sync
if comment_input != st.session_state.comment:
    st.session_state.comment = comment_input
