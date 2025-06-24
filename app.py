
import streamlit as st
from nlp_engine import nlp_router

st.set_page_config(page_title="QSR CEO Bot", layout="centered")

# Sidebar for Q&A history
if "history" not in st.session_state:
    st.session_state.history = []

st.sidebar.title("🧠 Q&A History")
for q, a in st.session_state.history:
    st.sidebar.markdown(f"**Q:** {q}\n**A:** {a}")

st.title("🍔 QSR CEO Performance Bot")

user_input = st.text_input("Ask a question about your stores:", placeholder="e.g. Which store had highest EBITDA in May 2025?")
if user_input:
    response = nlp_router(user_input)
    st.write("### Answer")
    st.write(response)
    st.session_state.history.append((user_input, response))

if st.sidebar.button("Download Q&A Log"):
    import pandas as pd
    df_log = pd.DataFrame(st.session_state.history, columns=["Question", "Answer"])
    df_log.to_csv("qna_log.csv", index=False)
    st.sidebar.download_button("Download", data=open("qna_log.csv", "rb"), file_name="QSR_QnA_Log.csv")
