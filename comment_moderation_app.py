import streamlit as st
import google.generativeai as genai
import importlib.metadata
import json
import re
import time

# --- App Config ---
st.set_page_config(page_title="Comment Categorizer", page_icon="💬", layout="centered")
st.title("💬 Comment Categorizer")

# --- Version Info ---
try:
    genai_version = importlib.metadata.version("google-generativeai")
except importlib.metadata.PackageNotFoundError:
    genai_version = "Unknown"

st.caption(f"🧩 Google Generative AI SDK version: {genai_version}")

# --- Configure Google Gemini API ---
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- Category List ---
categories = [
    "Harsh/insulting", "Vulgar", "Harassment", "Threatening", "Out of context",
    "Sexual content", "Hate speech", "Self-harm", "Graphic violence",
    "Positive feedback", "Constructive criticism", "Neutral opinion",
    "Polite disagreement", "Clarification request", "Supportive"
]

# --- Category Colors ---
category_colors = {
    "Harsh/insulting": "🔴",
    "Vulgar": "🔴",
    "Harassment": "🔴",
    "Threatening": "🔴",
    "Sexual content": "🟠",
    "Hate speech": "🔴",
    "Self-harm": "🟣",
    "Graphic violence": "🔴",
    "Out of context": "🟡",
    "Positive feedback": "🟢",
    "Constructive criticism": "🟢",
    "Neutral opinion": "⚪",
    "Polite disagreement": "🟢",
    "Clarification request": "🔵",
    "Supportive": "🟢"
}

# --- Initialize Session State ---
if "comment" not in st.session_state:
    st.session_state.comment = ""
if "result" not in st.session_state:
    st.session_state.result = None

# --- Text Area (Compact + Linked to Session) ---
comment_input = st.text_area(
    "Enter your comment:",
    value=st.session_state.comment,
    height=100,
    placeholder="Type your comment here..."
)
st.session_state.comment = comment_input

# --- Buttons (Submit + Clear) ---
col1, col2 = st.columns([1, 1])
with col1:
    submit = st.button("Submit", use_container_width=True)
with col2:
    clear = st.button("Clear", use_container_width=True)

# --- Submit Action ---
if submit:
    if not st.session_state.comment.strip():
        st.warning("⚠️ Please enter a comment before submitting.")
    else:
        with st.spinner("Analyzing your comment..."):
            try:
                # Optional short delay (helps rate limiting)
                time.sleep(1)

                # Use Gemini 2.0 Flash model
                model = genai.GenerativeModel("gemini-2.0-flash")

                prompt = f"""
You are a content moderation AI. Classify the following user comment into one or more of these categories:
{', '.join(categories)}

Return a valid JSON object in this format:
{{
  "categories": ["<list of applicable categories>"],
  "summary": "<brief summary of the comment>"
}}

Comment: {st.session_state.comment}
                """

                response = model.generate_content(prompt)
                text = response.text.strip()

                # Try extracting JSON
                json_text = re.search(r"\{.*\}", text, re.DOTALL)
                if json_text:
                    try:
                        result = json.loads(json_text.group())
                    except json.JSONDecodeError:
                        result = {"categories": ["Unrecognized"], "summary": text}
                else:
                    result = {"categories": ["Unrecognized"], "summary": text}

                st.session_state.result = result

            except Exception as e:
                if "Resource exhausted" in str(e) or "429" in str(e):
                    st.warning("⚠️ API limit reached. Please wait a few moments before trying again.")
                else:
                    st.error(f"API Error: {e}")

# --- Display Results (if any) ---
if st.session_state.result:
    result = st.session_state.result
    st.subheader("🧠 Summary")
    st.write(result.get("summary", "No summary available."))

    st.subheader("🏷️ Detected Categories")
    cats = result.get("categories", [])
    if cats:
        for c in cats:
            emoji = category_colors.get(c, "⚪")
            st.markdown(f"{emoji} **{c}**")
    else:
        st.write("No category detected.")

    # Mark harmful categories
    harmful = {
        "Harsh/insulting", "Vulgar", "Harassment", "Threatening",
        "Sexual content", "Hate speech", "Self-harm", "Graphic violence"
    }
    if any(c in harmful for c in cats):
        st.error("🚫 Potentially inappropriate or harmful content detected.")
    else:
        st.success("✅ Comment appears appropriate or constructive.")

# --- Clear Button Logic (Safe) ---
if clear:
    st.session_state.comment = ""
    st.session_state.result = None
    st.rerun()
