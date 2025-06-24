
import streamlit as st
from nlp_engine import nlp_router
import pandas as pd

st.set_page_config(page_title="QSR CEO Assistant", layout="wide")

# Initialize session state for Q&A history
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

# Sidebar: Question history and download
with st.sidebar:
    st.markdown("### 📜 Question History")
    for i, (q, a) in enumerate(st.session_state.qa_history):
        st.markdown(f"**Q{i+1}:** {q}")
        st.markdown(f"*A{i+1}:* {a}")

    if st.session_state.qa_history:
        df_history = pd.DataFrame(st.session_state.qa_history, columns=["Question", "Answer"])
        csv = df_history.to_csv(index=False)
        st.download_button("📥 Download Q&A", data=csv, file_name="qsr_ceo_qa_history.csv", mime="text/csv")

# Main UI
st.markdown("""<style>
    .block-container { padding-top: 2rem; }
    header, footer {visibility: hidden;}
    .stTextInput > div > div > input { font-size: 20px; padding: 12px; }
""", unsafe_allow_html=True)

user_input = st.text_input("", placeholder="Ask a question about store performance and press Enter")

if user_input:
    response = nlp_router(user_input)
    st.session_state.qa_history.append((user_input, response))
    st.markdown("#### Result")
    st.write(response)
