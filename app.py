import streamlit as st
import openai
import os
import PyPDF2
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# Set OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Startup Investment Memo Generator", layout="centered")
st.title("📄 Structured Investment Memo Generator")
st.write("Upload a pitch deck or paste a founder note to generate a clean, structured investment memo PDF.")

uploaded_file = st.file_uploader("📄 Upload pitch deck (PDF)", type=["pdf"])
startup_text = st.text_area("Or paste founder note / call summary", height=250)
submit = st.button("🚀 Generate Memo")

# Extract text from uploaded PDF
def extract_text_from_pdf(file):
    pdf = PyPDF2.PdfReader(file)
    return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

# Clean unsupported characters
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

# Build structured GPT prompt
def build_prompt(text):
    return f"""
You are a venture capital analyst. Based on the startup information below, write an investment memo in structured JSON format with the following keys:

{{
  "executive_summary": "",
  "team": {{
    "overview": "",
    "founder_experience": "",
    "time_on_idea": ""
  }},
  "product": "",
  "market": "",
  "traction": {{
    "users": "",
    "revenue": "",
    "growth_metrics": ""
  }},
  "business_model": "",
  "profitability": "",
  "go_to_market": "",
  "risks": "",
  "investment_recommendation": "",
  "scorecard": {{
    "Founder Experience": 0,
    "Time Spent on Idea": 0,
    "Product Quality": 0,
    "Market Size": 0,
    "Traction (Revenue/Users)": 0,
    "Business Model Clarity": 0,
    "Profitability Potential": 0,
    "Go-to-Market Strategy": 0,
    "Risk Level (lower is better)": 0,
    "Composite Score": 0.0
  }}
}}

Only return valid JSON. Use the following startup description to populate the memo:

{text}
"""

# Generate formatted PDF using reportlab
def generate_pdf(data):
    doc_path = "structured_memo_output.pdf"
    doc = SimpleDocTemplate(doc_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    def section(title, body):
        story.append(Paragraph(f"<b>{title}</b>", styles['Heading4']))
        story.append(Paragraph(clean_text(body), styles['BodyText']))
        story.append(Spacer(1, 12))

    # Add each structured section
    section("Executive Summary", data.get("executive_summary", ""))

    team = data.get("team", {})
    section("Team Overview", team.get("overview", ""))
    section("Founder Experience", team.get("founder_experience", ""))
    section("Time on Idea", team.get("time_on_idea", ""))

    section("Product", data.get("product", ""))
    section("Market", data.get("market", ""))

    traction = data.get("traction", {})
    section("Traction - Users", traction.get("users", ""))
    section("Traction - Revenue", traction.get("revenue", ""))
    section("Growth Metrics", traction.get("growth_metrics", ""))

    section("Business Model", data.get("business_model", ""))
    section("Profitability", data.get("profitability", ""))
    section("Go-to-Market Strategy", data.get("go_to_market", ""))
    section("Risks & Concerns", data.get("risks", ""))
    section("Investment Recommendation", data.get("investment_recommendation", ""))

    # Scorecard table
    scorecard = data.get("scorecard", {})
    table_data = [["Metric", "Score"]]
    for k, v in scorecard.items():
        table_data.append([k, str(v)])

    table = Table(table_data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Scorecard</b>", styles['Heading4']))
    story.append(table)

    doc.build(story)
    return doc_path

# Streamlit app logic
if submit and (startup_text.strip() or uploaded_file):
    with st.spinner("🧠 Generating structured memo..."):
        try:
            content = extract_text_from_pdf(uploaded_file) if uploaded_file else startup_text.strip()
            prompt = build_prompt(content)

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a VC analyst writing a professional investment memo."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            raw_output = response.choices[0].message.content.strip()
            parsed = json.loads(raw_output)

            st.markdown("### 🧾 Preview: Executive Summary")
            st.text(parsed.get("executive_summary", "[No summary returned]"))

            pdf_path = generate_pdf(parsed)
            with open(pdf_path, "rb") as f:
                st.download_button("📥 Download Structured Memo as PDF", f, file_name="investment_memo.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
else:
    st.info("Please upload a pitch deck or paste a note to generate memo.")
