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

# --- Text Area ---
comment_input = st.text_area(
    "Enter your comment:",
    value=st.session_state.comment,
    height=100,width=500,
    placeholder="Type your comment here..."
)

# --- Buttons ---
col1, col2 = st.columns([1, 1])
with col1:
    submit = st.button("Leave a comment", use_container_width=True)
with col2:
    clear = st.button("Clear", use_container_width=True)

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

# --- Submit Action ---
if submit:
    if not comment_input.strip():
        st.warning("⚠️ Please enter a comment before submitting.")
    else:
        st.session_state.comment = comment_input
        with st.spinner("Analyzing your comment..."):
            time.sleep(2)
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")

                prompt = f"""
You are a content moderation AI. Classify the following user comment into one or more of these categories:
{', '.join(categories)}

Return a valid JSON object in this format:
{{
  "categories": ["<list of applicable categories>"],
  "summary": "<brief summary of the comment>"
}}

Comment: {comment_input}
                """

                response = model.generate_content(prompt)
                text = response.text.strip()

                # Try to extract JSON safely
                json_text = re.search(r"\{.*\}", text, re.DOTALL)
                if json_text:
                    try:
                        result = json.loads(json_text.group())
                    except json.JSONDecodeError:
                        result = {"categories": ["Unrecognized"], "summary": text}
                else:
                    result = {"categories": ["Unrecognized"], "summary": text}

                # Display results
                st.markdown(f"** Summary:** {result.get('summary', 'No summary available.')}")

                cats = result.get("categories", [])
                if cats:
                    st.markdown("** Detected Categories:**")
                    for c in cats:
                        emoji = category_colors.get(c, "⚪")
                        st.markdown(f"{emoji} **{c}**")
                else:
                    st.write("No category detected.")

                harmful = {"Harsh/insulting", "Vulgar", "Harassment", "Threatening",
                           "Sexual content", "Hate speech", "Self-harm", "Graphic violence"}
                if any(c in harmful for c in cats):
                    st.error("🚫 Potentially inappropriate or harmful content detected.")
                else:
                    st.success("✅ Comment appears appropriate or constructive.")

            except Exception as e:
                if "Resource exhausted" in str(e) or "429" in str(e):
                    st.warning("⚠️ API limit reached. Please wait a few moments before trying again.")
                else:
                    st.error(f"API Error: {e}")


# --- Clear Button Action ---
if clear:
    st.session_state.comment = ""
    st.rerun()


# Update session state when typing
if comment_input != st.session_state.comment:
    st.session_state.comment = comment_input
