import streamlit as st
import openai
import os
import PyPDF2

# Set your OpenAI API key from Streamlit Secrets
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Comprehensive Deal Evaluation", layout="centered")
st.title("🧠 Comprehensive Startup Deal Evaluator")
st.write("Upload a pitch deck or paste notes to generate a full investment memo with scorecard.")

uploaded_file = st.file_uploader("📄 Upload pitch deck (PDF)", type=["pdf"])
startup_text = st.text_area("Or paste founder note / call summary", height=250)
submit = st.button("🚀 Generate Investment Memo")

# Function to extract text from uploaded PDF
def extract_text_from_pdf(file):
    pdf = PyPDF2.PdfReader(file)
    return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

# Function to generate the GPT prompt with memo +
