import streamlit as st
import openai
import os

# Set your OpenAI API key (make sure you add this in Streamlit Cloud under 'Secrets')
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Deal Evaluation Bot", layout="centered")
st.title("🧠 Startup Deal Evaluation Bot")
st.write("Evaluate early-stage startups using a structured scoring rubric.")

# User input
startup_text = st.text_area("Paste founder note, pitch summary, or transcript here", height=300)
submit = st.button("🚀 Evaluate Deal")

# Rubric weights
rubric = {
    "Team": 20,
    "Traction": 20,
    "Business Model": 20,
    "Market": 20,
    "Product": 10,
    "Risks": 10
}

# Prompt template
prompt_templa_
