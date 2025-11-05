import streamlit as st
import google.generativeai as genai
import importlib.metadata
import json
import re
import time

# --- App Config ---
st.set_page_config(page_title="Comment Moderation + Auto-Responder", page_icon="💬", layout="centered")
st.title("Comment Moderation + Auto-Response Suggestion")


# Session State Initialization
if "comment_input" not in st.session_state:
    st.session_state.comment_input = ""

if "show_popup" not in st.session_state:
    st.session_state.show_popup = False

if "summary" not in st.session_state:
    st.session_state.summary = ""

if "categories" not in st.session_state:
    st.session_state.categories = []

if "suggested_response" not in st.session_state:
    st.session_state.suggested_response = ""


# Custom Button Styling
button_css = """
<style>
div.stButton > button {
    width: 200px !important;
}
div.stButton > button {
    background: linear-gradient(rgb(0, 86, 145), rgb(26, 103, 156));
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


# Version Info
try:
    genai_version = importlib.metadata.version("google-generativeai")
except importlib.metadata.PackageNotFoundError:
    genai_version = "Unknown"

st.caption(f"Google Generative AI SDK version: {genai_version}")

# Configure Google Gemini API
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])


# Categories
categories_list = [
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

# Text Input
st.session_state.comment_input = st.text_area(
    "Enter your comment:",
    value=st.session_state.comment_input,
    height=150,
    placeholder="Type or paste a detailed comment here..."
)


col1, col2 = st.columns(2)
with col1:
    submit = st.button("Analyze & Suggest Response")
with col2:
    clear = st.button("Clear")


# --- Submit Action ---
if submit:
    if not st.session_state.comment_input.strip():
        st.warning("⚠️ Please enter a comment before submitting.")
    else:
        with st.spinner("Analyzing your comment..."):
            time.sleep(1)

            try:
                model = genai.GenerativeModel("gemini-2.0-flash")

                prompt = f"""
Classify the comment into the following categories:
{', '.join(categories_list)}

Return JSON in this format:
{{
  "categories": ["<list>"],
  "summary": "<short summary of tone>",
  "suggested_response": "<polite suggested reply to user>"
}}

Comment: {st.session_state.comment_input}
"""

                response = model.generate_content(prompt)
                raw = response.text.strip()
                json_data = re.search(r"\{.*\}", raw, re.DOTALL)

                if json_data:
                    data = json.loads(json_data.group())
                else:
                    data = {"categories": ["Unrecognized"], "summary": raw, "suggested_response": ""}

                st.session_state.summary = data.get("summary", "")
                st.session_state.categories = data.get("categories", [])
                st.session_state.suggested_response = data.get("suggested_response", "")

                st.session_state.show_popup = True

            except Exception as e:
                st.error(f"API Error: {e}")


# Clear Button
if clear:
    st.session_state.comment_input = ""
    st.session_state.show_popup = False
    st.rerun()


# --- Popup Modal ---
if st.session_state.show_popup:
    with st.modal("Comment Analysis Result"):
        st.write("### 📝 Summary")
        st.write(st.session_state.summary)

        st.write("### 🏷️ Categories Detected")
        for c in st.session_state.categories:
            st.write(f"{category_colors.get(c,'⚪')} **{c}**")

        st.write("### 💡 Suggested Response")
        st.write(st.session_state.suggested_response)

        colA, colB = st.columns(2)
        with colA:
            if st.button("✅ Apply Response"):
                st.session_state.comment_input += "\n\n" + st.session_state.suggested_response
                st.session_state.show_popup = False
                st.rerun()

        with colB:
            if st.button("❌ Cancel"):
                st.session_state.show_popup = False
                st.rerun()
