import streamlit as st
import google.generativeai as genai
import time

st.set_page_config(page_title="Comment Moderator", layout="centered")

# --- Google API Key ---
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)

# --- Initialize State ---
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "suggested_text" not in st.session_state:
    st.session_state.suggested_text = ""
if "comment_input" not in st.session_state:
    st.session_state.comment_input = ""

# --- Styling ---
st.markdown("""
<style>
textarea {
    border: 2px solid #ccc !important;
}
textarea.red-border {
    border: 3px solid red !important;
    animation: blink 1s infinite;
}
@keyframes blink {
    50% { border-color: transparent; }
}
</style>
""", unsafe_allow_html=True)

st.title("📝 Comment Quality & Tone Improver")

# --- Text Area ---
def render_text_area():
    border_class = "red-border" if st.session_state.get("flag_issue", False) else ""
    return st.text_area(
        "Enter your comment:",
        value=st.session_state.comment_input,
        height=200,
        key="comment_box",
        placeholder="Type your comment here...",
        help="Write any comment and click Analyze."
    )

comment_input = render_text_area()

# --- Buttons ---
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    analyze = st.button("Analyze", use_container_width=True)

with col2:
    apply_suggestion = st.button("Apply Suggestion", use_container_width=True)

with col3:
    clear = st.button("Clear", use_container_width=True)


# --- Clear Button Logic ---
if clear:
    st.session_state.comment_input = ""
    st.session_state.analysis = None
    st.session_state.flag_issue = False
    st.experimental_rerun()


# --- Analyze Button Logic ---
if analyze:
    if not comment_input.strip():
        st.warning("Please enter text before analyzing.")
    else:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""
            Analyze the following user comment and output JSON:
            1. Summary of meaning
            2. Category tags such as Positive, Negative, Supportive, Harassing, Sexual, Toxic, etc.
            3. A polite rewritten improved response.

            Comment: "{comment_input}"
            """

            result = model.generate_content(prompt)
            response_text = result.text

            # parse response safely
            import re
            summary = re.search(r"Summary:(.*)", response_text)
            categories = re.findall(r"- (.*)", response_text)
            suggestion = re.search(r"Suggested Response:(.*)", response_text)

            st.session_state.analysis = {
                "summary": summary.group(1).strip() if summary else "Not found",
                "categories": categories,
                "suggested": suggestion.group(1).strip() if suggestion else comment_input
            }

            st.session_state.suggested_text = st.session_state.analysis["suggested"]
            st.session_state.flag_issue = any(x.lower() in ["sexual", "abusive", "toxic", "harassing"] for x in categories)

            time.sleep(1)
            st.experimental_rerun()

        except Exception as e:
            st.error(f"Error: {e}")


# --- Apply Suggestion Logic ---
if apply_suggestion and st.session_state.suggested_text:
    st.session_state.comment_input = st.session_state.suggested_text  # replace text fully
    st.session_state.flag_issue = False
    st.experimental_rerun()


# --- Show Analysis Result ---
if st.session_state.analysis:
    st.subheader("✅ Analysis Result")
    st.write(f"**Summary:** {st.session_state.analysis['summary']}")
    st.write("**Categories Detected:**")
    for tag in st.session_state.analysis["categories"]:
        st.write(f"- {tag}")
    st.write("**Suggested Response:**")
    st.code(st.session_state.analysis["suggested"])
