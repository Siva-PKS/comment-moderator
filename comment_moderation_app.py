import streamlit as st
import google.generativeai as genai
import importlib.metadata

# --- App Config ---
st.set_page_config(page_title="Comment Checker", page_icon="💬", layout="centered")
st.title("💬 Comment Checker")

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

# --- Buttons ---
col1, col2 = st.columns([1, 1])
with col1:
    submit = st.button("Submit", use_container_width=True)
with col2:
    clear = st.button("Clear", use_container_width=True)

# --- On Submit ---
if submit:
    if not st.session_state.comment.strip():
        st.warning("⚠️ Please enter a comment before submitting.")
    else:
        with st.spinner("Analyzing your comment..."):
            try:
                # Use Gemini 2.0 Flash
                model = genai.GenerativeModel("gemini-2.0-flash")

                prompt = f"""
You are a comment moderation AI.
Analyze the following comment and provide ONLY a concise JSON object:
{{
  "summary": "<brief summary of the comment content>"
}}

Comment: {st.session_state.comment}
                """

                response = model.generate_content(prompt)
                text = response.text.strip()

                # Try to extract the summary text
                import re, json
                match = re.search(r'\{.*\}', text, re.DOTALL)
                summary_text = ""
                if match:
                    try:
                        data = json.loads(match.group())
                        summary_text = data.get("summary", "")
                    except json.JSONDecodeError:
                        summary_text = text
                else:
                    summary_text = text

                if summary_text:
                    st.subheader("🧠 Summary")
                    st.write(summary_text)
                else:
                    st.info("No summary could be generated.")

            except Exception as e:
                st.error(f"API Error: {e}")

# --- Clear Button ---
if clear:
    st.session_state.comment = ""
    st.experimental_rerun()
