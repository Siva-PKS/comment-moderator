import streamlit as st
from openai import OpenAI
import os

# Load API key from Streamlit secrets
api_key = st.secrets["OPENAI_API_KEY"]

# Initialize client
client = OpenAI(api_key=api_key)

st.set_page_config(page_title="AI Comment Moderator", page_icon="💬")

st.title("💬 AI Comment Moderator")
st.write("Check if a comment is offensive, harsh, out of context, vulgar, or against community rules.")

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
            response = client.moderations.create(
                model="omni-moderation-latest",
                input=comment
            )
            result = response.results[0]

            if result.flagged:
                st.error("⚠️ Comment seems **offensive or violates rules.**")
                st.write("**Flagged categories:**")
                for category, flagged in result.categories.items():
                    if flagged:
                        st.write(f"• {category.replace('_', ' ').title()}")
            else:
                st.success("✅ Comment is safe to post!")
        except Exception as e:
            st.error(f"API Error: {e}")

elif check_btn and not comment.strip():
    st.warning("Please enter a comment before submitting.")
