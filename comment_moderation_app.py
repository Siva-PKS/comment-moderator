import streamlit as st
import google.generativeai as genai
import json
import re
import time

# --- Page Setup ---
st.set_page_config(page_title="Comment Moderator + Suggestion", page_icon="💬", layout="centered")
st.title("💬 Comment Moderation + Auto-Suggestion System")

# --- Configure Google Gemini API ---
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- Category Setup ---
categories = [
    "Harsh/insulting", "Vulgar", "Harassment", "Threatening", "Out of context",
    "Sexual content", "Hate speech", "Self-harm", "Graphic violence",
    "Positive feedback", "Constructive criticism", "Neutral opinion",
    "Polite disagreement", "Clarification request", "Supportive"
]

harmful_set = {
    "Harsh/insulting", "Vulgar", "Harassment", "Threatening",
    "Sexual content", "Hate speech", "Self-harm", "Graphic violence"
}

# --- Session State Initialization ---
if "comment" not in st.session_state:
    st.session_state.comment = ""

if "suggestion" not in st.session_state:
    st.session_state.suggestion = ""

if "is_harmful" not in st.session_state:
    st.session_state.is_harmful = False

# --- Styling for Text Area ---
st.markdown("""
<style>
textarea {
    border-width: 2px !important;
}
.danger {
    border: 2px solid red !important;
    animation: blink 1s infinite;
}
@keyframes blink {
    50% { border-color: transparent; }
}
</style>
""", unsafe_allow_html=True)

# --- Text Input Area ---
comment_input = st.text_area(
    "Enter your comment:",
    value=st.session_state.comment,
    height=140,
    key="comment_text",
)

# Buttons
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    analyze = st.button("Analyze")
with col2:
    apply_suggest = st.button("Apply Suggestion", disabled=(st.session_state.suggestion == ""))
with col3:
    clear = st.button("Clear")

# --- Analyze Button Logic ---
if analyze:
    if not comment_input.strip():
        st.warning("⚠️ Please enter text before analyzing.")
    else:
        st.session_state.comment = comment_input

        with st.spinner("Analyzing comment..."):
            time.sleep(1)

            # Correct model name
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
You are a content moderation AI. Analyze the user comment and return JSON ONLY in this format:
{{
  "categories": ["choose from this list only: {categories}"],
  "summary": "short meaning",
  "suggested_response": "polite helpful response"
}}
Comment: "{comment_input}"
"""

            try:
                response = model.generate_content(prompt)
                raw_text = response.text
            except Exception as e:
                st.error(f"Error calling generation API: {e}")
                raw_text = ""

        # Extract JSON response
        result = {"categories": [], "summary": "No summary", "suggested_response": ""}

        if raw_text:
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group())
                except:
                    try:
                        cleaned = re.sub(r",\s*}", "}", match.group())
                        cleaned = re.sub(r",\s*\]", "]", cleaned)
                        result = json.loads(cleaned)
                    except:
                        result = result

        detected_categories = result.get("categories", [])
        summary = result.get("summary", "No summary")
        suggestion = result.get("suggested_response", "")

        st.session_state.is_harmful = any(c in harmful_set for c in detected_categories)
        st.session_state.suggestion = suggestion

        # Show results
        st.markdown(f"### 📝 Summary\n{summary}")

        if detected_categories:
            st.markdown("### 🏷️ Categories Detected:")
            for c in detected_categories:
                st.write(f"- **{c}**")

        if st.session_state.is_harmful:
            st.error("🚫 Harmful or inappropriate content detected! Text area border turned RED.")
        else:
            st.success("✅ Content appears safe or constructive.")

        if suggestion:
            st.markdown("### 💡 Suggested Response")
            st.info(suggestion)

# --- Apply Suggestion ---
if apply_suggest and st.session_state.suggestion:
    st.session_state.comment = st.session_state.suggestion
    st.session_state.is_harmful = False
    st.experimental_rerun()

# --- Clear Button ---
if clear:
    st.session_state.comment = ""
    st.session_state.suggestion = ""
    st.session_state.is_harmful = False
    st.experimental_rerun()
