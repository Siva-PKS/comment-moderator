import streamlit as st
import google.generativeai as genai
import importlib.metadata
import json
import re
import time

# --- App Config ---
st.set_page_config(page_title="Comment Moderation + Auto Response", page_icon="💬", layout="centered")
st.title("💬 Comment Moderation & Auto-Response Suggestion")

# --- Custom CSS ---
st.markdown("""
<style>
textarea.blink-red {
    border: 2px solid red !important;
    animation: blink 0.8s infinite;
}
@keyframes blink {
    50% { border-color: transparent; }
}
.custom-btn {
    background: linear-gradient(rgb(0, 86, 145), rgb(26, 103, 156));
    color: white !important;
    border-radius: 6px;
    padding: 8px;
    font-weight: 600;
    border: none;
    cursor: pointer;
}
.custom-btn:hover {
    filter: brightness(1.12);
}
.center-box {
    max-width: 550px;
    margin-left: auto;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)

# --- Version Info ---
try:
    genai_version = importlib.metadata.version("google-generativeai")
except importlib.metadata.PackageNotFoundError:
    genai_version = "Unknown"
st.caption(f"🧩 Google Generative AI SDK version: {genai_version}")

# --- Configure Gemini API ---
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- Initialize Session State ---
for key in ["comment", "suggested_response", "harmful_detected"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# --- Layout Container ---
st.markdown('<div class="center-box">', unsafe_allow_html=True)

# --- Text Area ---
text_area_class = "blink-red" if st.session_state.harmful_detected else ""
comment_input = st.text_area(
    "Enter your comment:",
    value=st.session_state.comment,
    placeholder="Type your comment here...",
    height=120,
    key="comment_box",
)

# --- Buttons Row ---
col1, col2, col3 = st.columns([1,1,1])
with col1:
    submit = st.button("Analyze", key="analyze_btn")
with col2:
    clear = st.button("Clear", key="clear_btn")
with col3:
    apply_resp = st.button("Apply Suggestion", key="apply_btn")

st.markdown("</div>", unsafe_allow_html=True)

# --- Category Setup ---
categories = [
    "Harsh/insulting", "Vulgar", "Harassment", "Threatening", "Out of context",
    "Sexual content", "Hate speech", "Self-harm", "Graphic violence",
    "Positive feedback", "Constructive criticism", "Neutral opinion",
    "Polite disagreement", "Clarification request", "Supportive"
]

harmful_set = {"Harsh/insulting", "Vulgar", "Harassment", "Threatening",
               "Sexual content", "Hate speech", "Self-harm", "Graphic violence"}

# --- Analyze Comment ---
if submit:
    if not comment_input.strip():
        st.warning("⚠️ Please enter a comment before analyzing.")
    else:
        st.session_state.comment = comment_input
        with st.spinner("Analyzing..."):
            time.sleep(1.5)
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")

                prompt = f"""
Classify the following comment into these categories:
{', '.join(categories)}

Return JSON:
{{
 "categories": ["<list>"],
 "summary": "<short summary>",
 "suggested_response": "<polite & professional reply>"
}}

Comment: {comment_input}
"""

                response = model.generate_content(prompt).text.strip()
                json_data = re.search(r"\{.*\}", response, re.DOTALL)

                result = json.loads(json_data.group()) if json_data else {"summary":"", "categories":[], "suggested_response":""}

                st.write("### 🧠 Summary")
                st.write(result.get("summary","No summary."))

                st.write("### 🏷️ Categories")
                cats = result.get("categories", [])
                for c in cats:
                    st.write(f"- {c}")

                # Store suggested response for Apply button
                st.session_state.suggested_response = result.get("suggested_response", "")

                # Harmful Check
                st.session_state.harmful_detected = any(c in harmful_set for c in cats)

                if st.session_state.harmful_detected:
                    st.error("🚫 Harmful or inappropriate content detected.")
                else:
                    st.success("✅ Content appears appropriate.")

            except Exception as e:
                st.error(f"API Error: {e}")

# --- Apply Suggestion ---
if apply_resp and st.session_state.suggested_response:
    st.session_state.comment = st.session_state.suggested_response
    st.session_state.harmful_detected = False
    st.rerun()

# --- Clear ---
if clear:
    st.session_state.comment = ""
    st.session_state.suggested_response = ""
    st.session_state.harmful_detected = False
    st.rerun()
