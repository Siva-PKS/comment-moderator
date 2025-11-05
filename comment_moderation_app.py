import streamlit as st
import google.generativeai as genai
import importlib.metadata
import json
import re
import time

# --- Page Setup ---
st.set_page_config(page_title="Comment Moderation + Auto Response", page_icon="💬", layout="centered")
st.title("💬 Comment Moderation + Auto Response")

# --- Styling (Blinking Red Border When Harmful) ---
st.markdown("""
<style>
.blink-red {
    border: 2px solid red !important;
    animation: blink 1s infinite;
}
@keyframes blink {
    50% { border-color: transparent; }
}
textarea {
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# --- Version Info ---
try:
    genai_version = importlib.metadata.version("google-generativeai")
except:
    genai_version = "Unknown"
st.caption(f"Google Generative AI SDK version: {genai_version}")

# --- Configure Google Gemini API ---
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- Session State Variables ---
if "comment" not in st.session_state:
    st.session_state.comment = ""
if "suggested_response" not in st.session_state:
    st.session_state.suggested_response = ""
if "is_harmful" not in st.session_state:
    st.session_state.is_harmful = False

# --- Categories ---
categories = [
    "Harsh/insulting", "Vulgar", "Harassment", "Threatening", "Out of context",
    "Sexual content", "Hate speech", "Self-harm", "Graphic violence",
    "Positive feedback", "Constructive criticism", "Neutral opinion",
    "Polite disagreement", "Clarification request", "Supportive"
]

harmful_set = {"Harsh/insulting", "Vulgar", "Harassment", "Threatening",
               "Sexual content", "Hate speech", "Self-harm", "Graphic violence"}

# --- Text Area ---
text_area_class = "blink-red" if st.session_state.is_harmful else ""

comment_input = st.text_area(
    "Enter your comment:",
    value=st.session_state.comment,
    height=120,
    key="comment_input"
)

# Apply blinking class via JS patch
st.markdown(f"""
<script>
var textareas = window.parent.document.getElementsByTagName('textarea');
for (let t of textareas) {{
    t.className = "{text_area_class}";
}}
</script>
""", unsafe_allow_html=True)

# --- Buttons ---
col1, col2, col3 = st.columns([1,1,1])
with col1:
    submit = st.button("Analyze")
with col2:
    apply_resp = st.button("Apply Suggestion")
with col3:
    clear = st.button("Clear")

# --- Submit Logic ---
if submit:
    if not comment_input.strip():
        st.warning("⚠️ Please enter a comment before analyzing.")
    else:
        with st.spinner("Analyzing..."):
            time.sleep(1.5)
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")

                prompt = f"""
Classify the comment into categories:
{', '.join(categories)}

Return JSON:
{{
  "categories": ["list"],
  "summary": "short summary",
  "suggested_response": "helpful user-friendly reply"
}}

Comment: {comment_input}
                """

                response = model.generate_content(prompt)
                text = response.text.strip()

                match = re.search(r"\{.*\}", text, re.DOTALL)
                result = json.loads(match.group()) if match else {}

                summary = result.get("summary", "")
                detected = result.get("categories", [])
                suggestion = result.get("suggested_response", "")

                st.session_state.suggested_response = suggestion
                st.session_state.is_harmful = any(c in harmful_set for c in detected)

                st.markdown(f"### 📝 Summary\n{summary}")

                if detected:
                    st.markdown("### 🏷️ Categories Detected:")
                    for c in detected:
                        st.write(f"- **{c}**")

                if st.session_state.is_harmful:
                    st.error("🚫 Harmful or inappropriate content detected.")
                else:
                    st.success("✅ Comment appears appropriate.")

                if suggestion:
                    st.markdown("### 💡 Suggested Response:")
                    st.write(suggestion)

            except Exception as e:
                st.error(f"API Error: {e}")

# --- Apply Suggestion ---
if apply_resp and st.session_state.suggested_response:
    # Replace the text area content with the suggested response only
    st.session_state.comment = st.session_state.suggested_response
    st.session_state.is_harmful = False  # remove red highlight if present
    st.rerun()


# --- Clear ---
if clear:
    st.session_state.comment = ""
    st.session_state.suggested_response = ""
    st.session_state.is_harmful = False
    st.rerun()

