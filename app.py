import streamlit as st
import openai
import os
import PyPDF2

# 🔐 Get API key from Streamlit Secrets
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Startup Deal Memo Generator", layout="centered")
st.title("🧠 Comprehensive Startup Deal Evaluator")
st.write("Upload a pitch deck or paste a founder note to generate a full investment memo with scorecard.")

# Upload or paste pitch content
uploaded_file = st.file_uploader("📄 Upload pitch deck (PDF)", type=["pdf"])
startup_text = st.text_area("Or paste founder note / call summary", height=250)
submit = st.button("🚀 Generate Investment Memo")

# PDF to text
