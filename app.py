import streamlit as st
from nlp_engine import nlp_router
import pandas as pd

st.set_page_config(page_title="QSR CEO Assistant", layout="wide")

if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

with st.sidebar:
    st.markdown("### 📜 Question History")
    for i, (q, a) in enumerate(st.session_state.qa_history):
        st.markdown(f"**Q{i+1}:** {q}")
        st.markdown(f"*A{i+1}:* {a}")
    if st.session_state.qa_history:
        df = pd.DataFrame(st.session_state.qa_history, columns=["Question", "Answer"])
        st.download_button("📥 Download Q&A", df.to_csv(index=False), "qsr_qa_history.csv", "text/csv")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    header, footer {visibility: hidden;}
    .stTextInput > div > div > input { font-size: 20px; padding: 12px; }
    </style>
""", unsafe_allow_html=True)

user_input = st.text_input("", placeholder="Ask a question about store performance and press Enter")

if user_input:
    response = nlp_router(user_input)
    st.session_state.qa_history.append((user_input, response))
    st.markdown("#### Result")
    st.write(response)
