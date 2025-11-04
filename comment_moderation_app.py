import streamlit as st
import google.generativeai as genai
import importlib.metadata
import json
import re

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

# --- Initialize Session State ---
if "comment" not in st.session_state:
    st.session_state.comment = ""

# --- Text Area (Compact) ---
st.text_area(
    "Enter your comment:",
    key="comment",
    height=100,
    placeholder="Type your comment here..."
)

# --- Buttons (Submit + Clear) ---
col1, col2 = st.columns([1, 1])
with col1:
    submit = st.button("Submit", use_container_width=True)
with col2:
    clear = st.button("Clear", use_container_width=True)

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

# --- Submit Action ---
if submit:
    if not st.session_state.comment.strip():
        st.warning("⚠️ Please enter a comment before submitting.")
    else:
        with st.spinner("Analyzing your comment..."):
            try:
                # Use Gemini 2.0 Flash (fast and accurate)
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

                # Try to extract JSON safely
                json_text = re.search(r"\{.*\}", text, re.DOTALL)
                if json_text:
                    try:
                        result = json.loads(json_text.group())
                    except json.JSONDecodeError:
                        result = {"categories": ["Unrecognized"], "summary": text}
                else:
                    result = {"categories": ["Unrecognized"], "summary": text}

                # Display results neatly (no debug info)
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
                harmful = {"Harsh/insulting", "Vulgar", "Harassment", "Threatening",
                           "Sexual content", "Hate speech", "Self-harm", "Graphic violence"}
                if any(c in harmful for c in cats):
                    st.error("🚫 Potentially inappropriate or harmful content detected.")
                else:
                    st.success("✅ Comment appears appropriate or constructive.")

            except Exception as e:
                # Improved error handling for quota/rate-limit errors
                if "Resource exhausted" in str(e) or "429" in str(e):
                    st.warning("⚠️ API limit reached. Please wait a few moments before trying again.")
                else:
                    st.error(f"API Error: {e}")

# --- Clear Button ---
if clear:
    st.session_state.comment = ""
    st.experimental_rerun()
