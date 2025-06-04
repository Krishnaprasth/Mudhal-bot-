import streamlit as st
import openai
import os
import PyPDF2

# Set your OpenAI API key from Streamlit Secrets
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Deal Evaluation Bot", layout="centered")
st.title("🧠 Startup Deal Evaluation Bot")
st.write("Upload a PDF pitch deck or paste a founder note to evaluate the deal.")

# Upload or paste input
uploaded_file = st.file_uploader("📄 Upload pitch deck (PDF)", type=["pdf"])
startup_text = st.text_area("Or paste pitch summary or founder note", height=250)
submit = st.button("🚀 Evaluate Deal")

# Extract text from PDF
def extract_text_from_pdf(file):
    pdf = PyPDF2.PdfReader(file)
    return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

# Prompt template
def build_prompt(text):
    return f"""
You are a startup analyst. Based on the input below, evaluate the startup using this rubric:
- Team (20%)
- Traction (20%)
- Business Model (20%)
- Market (20%)
- Product (10%)
- Risks (10%)

Give a 1–10 score for each category, then calculate a weighted total score (/10). 
Also provide a 2–3 line summary and highlight red flags or missing information.

Input:
{text}

Respond in this format:

Summary:
- [2-3 line summary]

Scores:
- Team: x/10
- Traction: x/10
- Business Model: x/10
- Market: x/10
- Product: x/10
- Risks: x/10

Weighted Score: x.xx / 10

Red Flags:
- [List of any concerns or missing data]
"""

# Evaluate logic
if submit and (uploaded_file or startup_text.strip()):
    with st.spinner("Reading and evaluating the startup..."):
        try:
            content = startup_text.strip()
            if uploaded_file:
                content = extract_text_from_pdf(uploaded_file)

            prompt = build_prompt(content)
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a startup investment analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            result = response.choices[0].message.content
            st.markdown("---")
            st.markdown("### 📋 Evaluation Output")
            st.text(result)
            st.download_button("📥 Download Evaluation", result, file_name="deal_evaluation.txt")
        except Exception as e:
            st.error(f"Error: {str(e)}")
else:
    st.info("Please upload a PDF or paste some text to evaluate.")
