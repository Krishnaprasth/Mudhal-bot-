import streamlit as st
import openai
import os
import PyPDF2
from fpdf import FPDF

# Set your OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Startup Investment Memo Generator", layout="centered")
st.title("📄 Startup Investment Memo Generator")
st.write("Upload a pitch deck or paste a founder note to generate a clean PDF memo.")

uploaded_file = st.file_uploader("📄 Upload pitch deck (PDF)", type=["pdf"])
startup_text = st.text_area("Or paste founder note / call summary", height=250)
submit = st.button("🚀 Generate Investment Memo")

# ✅ Extract text from uploaded PDF
def extract_text_from_pdf(file):
    pdf = PyPDF2.PdfReader(file)
    return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

# ✅ Clean unsupported characters for PDF
def clean_text(text):
    replacements = {
        '\u2018': "'", '\u2019': "'",    # single quotes
        '\u201c': '"', '\u201d': '"',    # double quotes
        '\u2013': '-', '\u2014': '-',    # dashes
        '\u2022': '*',                   # bullet
        '\u00a0': ' ',                   # non-breaking space
        '\u2192': '->',                  # arrow
        '\u2026': '...',                 # ellipsis
        '\u2122': '(TM)',                # trademark
        '\u00b7': '-',                   # middle dot
        '\u00e9': 'e'                    # é to e
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text

# ✅ Construct the prompt
def build_prompt(text):
    return f"""
You are a venture capital analyst. Based on the startup input below, write a detailed, well-formatted investment memo.

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
10. Investment Recommendation (score out of 10)

Include a scorecard:

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

Finish with:
**-> Composite Score: x.xx / 10**

Startup Input:
{text}
"""

# ✅ Generate PDF from memo
def generate_pdf(text):
    cleaned = clean_text(text)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", "", 12)
    for line in cleaned.split("\n"):
        if line.strip():
            pdf.multi_cell(0, 10, txt=line, align="L")
    output_path = "investment_memo_output.pdf"
    pdf.output(output_path)
    return output_path

# ✅ Main logic
if submit and (startup_text.strip() or uploaded_file):
    with st.spinner("🧠 Generating memo..."):
        try:
            content = extract_text_from_pdf(uploaded_file) if uploaded_file else startup_text.strip()
            prompt = build_prompt(content)

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a VC analyst writing a professional investment memo."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )

            result = response.choices[0].message.content

            st.markdown("### 📋 Memo Preview")
            st.text(result)

            pdf_path = generate_pdf(result)
            with open(pdf_path, "rb") as f:
                st.download_button("📥 Download as PDF", f, file_name="investment_memo.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
else:
    st.info("Please upload a PDF or paste founder note to begin.")
