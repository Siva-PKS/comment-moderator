import streamlit as st
import google.generativeai as genai
import importlib.metadata

# --- App Config ---
st.set_page_config(page_title="Comment Checker", page_icon="💬", layout="centered")
st.title("💬 Comment Checker")

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

# --- Button Actions ---
if submit:
    if not st.session_state.comment.strip():
        st.warning("⚠️ Please enter a comment before submitting.")
    else:
        with st.spinner("Analyzing your comment..."):
            try:
                model = genai.GenerativeModel("gemini-2.5-flash")

                prompt = (
                    "Analyze the following user comment and classify if it is:\n"
                    "- Offensive or harsh\n"
                    "- Out of context\n"
                    "- Vulgar\n"
                    "- Against rules or policy\n\n"
                    f"Comment:\n{st.session_state.comment}\n\n"
                    "Respond in one short sentence describing whether the comment is appropriate or not."
                )

                response = model.generate_content(prompt)
                result_text = response.text.strip()

                # Color-coded feedback
                if any(word in result_text.lower() for word in ["offensive", "vulgar", "inappropriate", "harsh", "against"]):
                    st.error("🚫 " + result_text)
                else:
                    st.success("✅ " + result_text)

            except Exception as e:
                st.error(f"API Error: {e}")

if clear:
    st.session_state.comment = ""
    st.experimental_rerun()
