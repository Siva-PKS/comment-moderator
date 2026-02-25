import streamlit as st
from openai import OpenAI
import json
import re
import time

# --- App Config ---
st.set_page_config(page_title="Comment Categorizer", page_icon="💬", layout="centered")
st.title("💬 Comment Categorizer")

# --- Initialize OpenAI ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- Session State ---
if "comment" not in st.session_state:
    st.session_state.comment = ""

if "last_call" not in st.session_state:
    st.session_state.last_call = 0

# --- Text Area ---
comment_input = st.text_area(
    "Enter your comment:",
    value=st.session_state.comment,
    height=100,
    placeholder="Type your comment here..."
)

# --- Buttons ---
col1, col2 = st.columns([1, 1])
with col1:
    submit = st.button("Submit", use_container_width=True)
with col2:
    clear = st.button("Clear", use_container_width=True)

# --- Categories ---
categories = [
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

# --- Retry Wrapper ---
def call_openai_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a content moderation AI."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=150,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                wait_time = 2 ** attempt
                st.warning(f"⚠️ Rate limited. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise e
    raise Exception("Max retries exceeded")

# --- Submit Action ---
if submit:
    if not comment_input.strip():
        st.warning("⚠️ Please enter a comment before submitting.")
    else:
        # --- Simple client-side rate limit ---
        if time.time() - st.session_state.last_call < 2:
            st.warning("⏳ Please wait a moment before submitting again.")
            st.stop()

        st.session_state.last_call = time.time()
        st.session_state.comment = comment_input

        with st.spinner("Analyzing your comment..."):
            try:
                prompt = f"""
Classify the comment into one or more of these categories:
{', '.join(categories)}

Return ONLY valid JSON:
{{
  "categories": [],
  "summary": ""
}}

Comment: {comment_input}
"""

                text = call_openai_with_retry(prompt)

                # --- Extract JSON safely ---
                json_text = re.search(r"\{.*\}", text, re.DOTALL)
                if json_text:
                    try:
                        result = json.loads(json_text.group())
                    except json.JSONDecodeError:
                        result = {"categories": ["Unrecognized"], "summary": text}
                else:
                    result = {"categories": ["Unrecognized"], "summary": text}

                # --- Display results ---
                st.markdown(f"**🧠 Summary:** {result.get('summary', 'No summary available.')}")

                cats = result.get("categories", [])
                if cats:
                    st.markdown("**🏷️ Detected Categories:**")
                    for c in cats:
                        emoji = category_colors.get(c, "⚪")
                        st.markdown(f"{emoji} **{c}**")
                else:
                    st.write("No category detected.")

                harmful = {
                    "Harsh/insulting", "Vulgar", "Harassment", "Threatening",
                    "Sexual content", "Hate speech", "Self-harm", "Graphic violence"
                }

                if any(c in harmful for c in cats):
                    st.error("🚫 Potentially inappropriate or harmful content detected.")
                else:
                    st.success("✅ Comment appears appropriate or constructive.")

            except Exception as e:
                st.error(f"API Error: {e}")

# --- Clear Button ---
if clear:
    st.session_state.comment = ""
    st.rerun()
