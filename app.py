import streamlit as st
import openai
import os
import PyPDF2
from fpdf import FPDF

# Set your OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Startup Investment Memo Generator", layout="centered")
st.title("📄 Startup Investment Memo Generator")
st.write("Upload a pitch deck or paste a founder note to generate a formatted memo and download it as a PDF.")

# Input methods
uploaded_file = st.file_uploader("📄 Upload pitch deck (PDF)", type=["pdf"])
startup_text = st.text_area("Or paste founder note / call summary", height=250)
submit = st.button("🚀 Generate Investment Memo")

# Function to extract text from uploaded PDF
def extract_text_from_pdf(file):
    pdf = PyPDF2.PdfReader(file)
    return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

# GPT prompt for revised scoring and memo structure
def build_prompt(text):
    return f"""
You are a venture capital analyst. Based on the input below, write a detailed, well-formatted investment memo.

Include these sections:

1. Executive Summary  
2. Team (highlight relevant experience and time spent on this idea)  
3. Product  
4. Market  
5. Traction (users, revenue, pilot metrics)  
6. Business Model  
7. Profitability  
8. Go-to-Market Strategy  
9. Risks & Concerns  
10. Investment Recommendation (score out of 10 with rationale)

Also include this updated Scorecard:

| Category                   | Score (1–10) |
|----------------------------|--------------|
| Founder Experience         |              |
| Time Spent on Idea         |              |
| Product Quality            |              |
| Market Size                |              |
| Traction (Revenue/Users)   |              |
| Business Model Clarity     |              |
| Profitability Potential    |              |
| Go-to-Market Strategy      |              |
| Risk Level (lower = better)|              |

Conclude with:
**→ Weighted Composite Score: x.xx / 10**

Startup Input:
{text}
"""

# Function to generate PDF from GPT output
def generate_pdf(text):
    pdf = FPDF()
