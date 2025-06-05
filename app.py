import streamlit as st
import openai
import os
import PyPDF2
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# Set your OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Startup Investment Memo Generator", layout="centered")
st.title("📄 Startup Investment Memo Generator")
st.write("Upload a pitch deck or paste a founder note to generate a clean, formatted investment memo PDF.")

uploaded_file = st.file_uploader("📄 Upload pitch deck (PDF)", type=["pdf"])
startup_text = st.text_area("Or paste founder note / call summary", height=250)
submit = st.button("🚀 Generate Investment Memo")

# Extract text from uploaded PDF
def extract_text_from_pdf(file):
    pdf = PyPDF2.PdfReader(file)
    return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

# Clean unsupported Unicode characters
def clean_text(text):
    replacements = {
        '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-',
        '\u2022': '*', '\u00a0': ' ',
        '\u2192': '->', '\u2026': '...',
        '\u2122': '(TM)', '\u00b7': '-', '\u00e9': 'e'
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text

# GPT prompt builder
def build_prompt(text):
    return f"""
You are a venture capital analyst. Based on the startup input below, write a detailed investment memo.

Include:
1. Executive Summary
2. Team (highlight relevant experience and time spent on this idea)
3. Product
4. Market
5. Traction (users, revenue, pilots)
6. Business Model
7. Profitability
8. Go-to-Market Strategy
9. Risks & Concerns
10. Investment Recommendation (score out of 10)

Include a scorecard:
| Category | Score (1–10) |
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

**-> Composite Score: x.xx / 10**

Startup Input:
{text}
"""

# PDF generation using reportlab
def generate_pdf(content):
    cleaned = clean_text(content)
    doc_path = "investment_memo_output.pdf"
    doc = SimpleDocTemplate(doc_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    for section in cleaned.split("\n\n"):
        if section.strip():
            lines = section.strip().split("\n")
            story.append(Paragraph(f"<b>{lines[0]}</b>", styles['Heading4']))
            for line in lines[1:]:
                story.append(Paragraph(line.strip(), styles['BodyText']))
            story.append(Spacer(1, 12))

    # Scorecard table if present
    if '| Category' in content:
        try:
            start = content.index('| Category')
            end = content.index('**-> Composite')
            table_data = content[start:end].strip().split('\n')[2:]  # skip headers
            formatted = [['Category', 'Score (1–10)']]
            for row in table_data:
                parts = [part.strip() for part in row.strip('|').split('|')]
                if len(parts) == 2:
                    formatted.append(parts)
            table = Table(formatted, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(Spacer(1, 12))
            story.append(Paragraph("<b>Scorecard</b>", styles['Heading4']))
            story.append(table)
        except Exception as e:
            print("Table formatting failed:", e)

    doc.build(story)
    return doc_path

# App logic
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
            st.text(result[:3000] + ("..." if len(result) > 3000 else ""))

            pdf_path = generate_pdf(result)
            with open(pdf_path, "rb") as f:
                st.download_button("📥 Download as PDF", f, file_name="investment_memo.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
else:
    st.info("Please upload a PDF or paste founder note to begin.")
