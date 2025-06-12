import streamlit as st
import fitz  # PyMuPDF
import openai
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY") or "YOUR_OPENAI_API_KEY"

# Page config
st.set_page_config(page_title="Factsheet Extractor", layout="wide")
st.title("📊 Factsheet Extractor – Investor Presentation Parser")
st.markdown("Upload investor decks (PDFs) to extract a structured startup factsheet.")

# Fixed 50 key parameters (including website and LinkedIn profiles)
FIELDS = [
    "Startup Name", "Founded Year", "Sector", "Product", "Business Model", "Website", "Headquarters",
    "Founders", "Founder Backgrounds", "LinkedIn Profiles", "Team Size", "Key Hires", "Org Structure",
    "Users", "Monthly Active Users", "Daily Active Users", "Revenue", "ARR", "MRR", "Retention", "Churn Rate", "GMV", "Key Customers",
    "Burn Rate", "Runway", "Profit Margin", "CAC", "LTV", "Unit Economics", "Gross Margin", "EBITDA",
    "Market Size", "Target Geography", "TAM", "SAM", "SOM", "Competition", "Market Share",
    "Funds Raised", "Lead Investors", "Current Round", "Ask Amount", "Valuation", "Use of Funds", "Exit Strategy",
    "Sales Conversion Rate", "Avg Order Value", "Payback Period", "Revenue Growth %"
]

# Categorize fields for grouping
SECTIONS = {
    "Company Info": ["Startup Name", "Founded Year", "Sector", "Product", "Business Model", "Website", "Headquarters"],
    "Team": ["Founders", "Founder Backgrounds", "LinkedIn Profiles", "Team Size", "Key Hires", "Org Structure"],
    "Traction": ["Users", "Monthly Active Users", "Daily Active Users", "Key Customers", "GMV", "Revenue", "ARR", "MRR", "Retention", "Churn Rate"],
    "Financials": ["Burn Rate", "Runway", "Profit Margin", "Gross Margin", "Unit Economics", "EBITDA"],
    "Metrics": ["CAC", "LTV", "Sales Conversion Rate", "Avg Order Value", "Payback Period", "Revenue Growth %"],
    "Market": ["Market Size", "Target Geography", "TAM", "SAM", "SOM", "Competition", "Market Share"],
    "Fundraising": ["Funds Raised", "Lead Investors", "Current Round", "Ask Amount", "Valuation", "Use of Funds", "Exit Strategy"]
}

# PDF Text Extractor
def extract_text_from_pdf(pdf_file):
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# GPT Extractor with improved prompt

def extract_facts_and_summary(text):
    prompt = f"""
You are an AI analyst extracting facts from an investor deck.

Return two parts:
1. A 5–10 point factual bullet summary
2. A list of only those fields from the following that are clearly implied or explicitly stated. Format: Field: Value
Use context — match synonyms or indirect language if the concept is obvious (e.g. 'team size ~50' → Team Size).
Do NOT guess — only include if there's supporting evidence.

Fields:
{', '.join(FIELDS)}

Text:
{text[:4000]}
"""
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    content = response.choices[0].message.content.strip()

    summary = []
    facts = {}
    lines = content.splitlines()
    parsing_summary = True

    for line in lines:
        if parsing_summary and line.strip().startswith("-"):
            summary.append(line.strip())
        elif ":" in line:
            parsing_summary = False
            key, val = line.split(":", 1)
            if key.strip() in FIELDS:
                facts[key.strip()] = val.strip()

    return summary, facts, text[:3000], content

# PDF Generator

def generate_pdf(summary, facts):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Startup Factsheet")
    y -= 30

    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, "Summary")
    y -= 20
    c.setFont("Helvetica", 12)
    for bullet in summary:
        c.drawString(60, y, bullet)
        y -= 16
        if y < 80:
            c.showPage()
            y = height - 50

    for section, fields in SECTIONS.items():
        section_data = {field: facts[field] for field in fields if field in facts}
        if section_data:
            c.setFont("Helvetica-Bold", 13)
            c.drawString(50, y, f"{section}")
            y -= 20
            c.setFont("Helvetica", 12)
            for field, value in section_data.items():
                for line in wrap_text(f"{field}: {value}", 90):
                    c.drawString(60, y, line)
                    y -= 16
                    if y < 80:
                        c.showPage()
                        y = height - 50

    c.save()
    buffer.seek(0)
    return buffer

# Text wrap utility

def wrap_text(text, max_chars):
    words = text.split()
    lines, current_line = [], ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars:
            current_line += (" " if current_line else "") + word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

# App Logic
if uploaded_files := st.file_uploader("Upload PDF", type="pdf", accept_multiple_files=True):
    for file in uploaded_files:
        with st.expander(f"📘 {file.name}", expanded=True):
            with st.spinner("Extracting facts..."):
                raw_text = extract_text_from_pdf(file)
                summary, facts, extracted_text, gpt_output = extract_facts_and_summary(raw_text)

            st.markdown("### 🔹 Summary")
            for bullet in summary:
                st.markdown(f"- {bullet}")

            for section, fields in SECTIONS.items():
                section_data = {field: facts[field] for field in fields if field in facts}
                if section_data:
                    st.markdown(f"### 🔹 {section}")
                    for field, value in section_data.items():
                        st.markdown(f"**{field}**: {value}")

            pdf_bytes = generate_pdf(summary, facts)
            st.download_button("📄 Download Factsheet PDF", pdf_bytes, file_name=f"{file.name.replace('.pdf','')}_factsheet.pdf", mime="application/pdf")

            with st.expander("🛠 Debug (Extracted Text & GPT Output)"):
                st.text_area("Extracted Text", extracted_text, height=300)
                st.text_area("GPT Output", gpt_output, height=300)
