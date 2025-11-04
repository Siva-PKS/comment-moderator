import streamlit as st
import google.generativeai as genai

import streamlit as st
import subprocess

with st.expander("Check installed google-generativeai version"):
    version = subprocess.run(
        ["pip", "show", "google-generativeai"],
        capture_output=True, text=True
    )
    st.code(version.stdout)




# Configure Google API key from Streamlit secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.set_page_config(page_title="AI Comment Checker", page_icon="💬")

st.title("💬 AI Comment Checker (Google Gemini)")
st.write("Automatically checks if a comment is offensive, harsh, vulgar, or out of context before posting.")

# Text area for comment input
comment = st.text_area("Enter your comment:", height=100)

col1, col2 = st.columns(2)
with col1:
    check_btn = st.button("Submit")
with col2:
    clear_btn = st.button("Clear")

if clear_btn:
    st.session_state["comment"] = ""
    st.experimental_rerun()

if check_btn and comment.strip():
    with st.spinner("Analyzing your comment..."):
        try:
            # Use Gemini model for content moderation-like analysis
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
You are a content moderation AI. Analyze the following user comment and decide if it is:
1. Offensive or harsh
2. Vulgar or inappropriate
3. Out of context or spam
4. Safe and acceptable

Comment: "{comment}"

Respond strictly in JSON format:
{{"offensive": true/false, "reason": "short explanation"}}
            """
            response = model.generate_content(prompt)
            
            # Extract text safely
            analysis = response.text.strip()
            st.write("🧠 **AI Analysis:**")
            st.code(analysis, language="json")

            if "true" in analysis.lower():
                st.error("⚠️ Comment seems **offensive or violates rules.**")
            else:
                st.success("✅ Comment appears safe to post!")
        except Exception as e:
            st.error(f"API Error: {e}")

elif check_btn and not comment.strip():
    st.warning("Please enter a comment before submitting.")
