import streamlit as st
import openai
import os
import PyPDF2
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors

openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Startup One-Pager Generator", layout="centered")
st.title("📄 Startup Deal Snapshot Generator")
st.write("Upload a pitch deck or paste a founder note to generate a one-pager investment summary PDF.")

uploaded_file = st.file_uploader("📄 Upload pitch deck (PDF)", type=["pdf"])
startup_text = st.text_area("Or paste founder note / call summary", height=250)
submit = st.button("🚀 Generate One-Pager")

def extract_text_from_pdf(file):
    pdf = PyPDF2.PdfReader(file)
    return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

def build_prompt(text):
    return f"""
Act like a VC analyst. Read the founder input below and return a concise one-pager JSON with the following structure:

{{
  "startup_name": "",
  "one_liner": "",
  "team": [""],
  "product": [""],
  "market": "",
  "traction": [""],
  "business_model": "",
  "risks": [""],
  "scorecard": {{
    "Founder Experience": 0,
    "Market Size": 0,
    "Traction": 0,
    "Product Clarity": 0,
    "Revenue Potential": 0,
    "Risk Level (low=better)": 0,
    "Composite Score": 0.0
  }},
  "annexures": {{
    "funding_raised": "",
    "shareholding_pattern": "",
    "financial_metrics": "",
    "key_growth_metrics": ""
  }},
  "inconsistencies": [""]
}}

If any section is not available, explicitly say "Not Available". Use bullet points where applicable. Return ONLY valid JSON.

Founder Input:
{text}
"""

def generate_one_pager(data):
    doc_path = "deal_snapshot_one_pager.pdf"
    doc = SimpleDocTemplate(doc_path, pagesize=A4)
    styles = getSampleStyleSheet()
    styleN = styles['BodyText']
    styleH = styles['Heading4']
    redStyle = ParagraphStyle(name='RedText', parent=styleN, textColor=colors.red)
    story = []

    # Add logo if available
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=120, height=40)
        logo.hAlign = 'LEFT'
        story.append(logo)

    # Title
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>{data.get('startup_name', 'Startup')}</b>", styles['Title']))
    story.append(Paragraph(data.get("one_liner", ""), styleN))
    story.append(Spacer(1, 12))

    def bullet_section(title, items):
        story.append(Paragraph(f"<b>{title}</b>", styleH))
        for item in items:
            story.append(Paragraph(f"• {item}", styleN))
        story.append(Spacer(1, 8))

    bullet_section("Team", data.get("team", []))
    bullet_section("Product", data.get("product", []))
    story.append(Paragraph(f"<b>Market</b>", styleH))
    story.append(Paragraph(data.get("market", ""), styleN))
    story.append(Spacer(1, 8))
    bullet_section("Traction", data.get("traction", []))
    story.append(Paragraph(f"<b>Business Model</b>", styleH))
    story.append(Paragraph(data.get("business_model", ""), styleN))
    story.append(Spacer(1, 8))
    bullet_section("Risks", data.get("risks", []))

    # Scorecard table
    scorecard = data.get("scorecard", {})
    table_data = [["Metric", "Score"]] + [[k, str(v)] for k, v in scorecard.items()]
    table = Table(table_data, hAlign='LEFT', colWidths=[200, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Scorecard</b>", styleH))
    story.append(table)

    # Annexures
    annex = data.get("annexures", {})
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Annexures</b>", styleH))
    for label, value in annex.items():
        story.append(Paragraph(f"<b>{label.replace('_', ' ').title()}</b>", styleN))
        story.append(Paragraph(value if value.strip() else "Not Available", styleN))
        story.append(Spacer(1, 6))

    # Inconsistencies
    inconsistencies = data.get("inconsistencies", [])
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Inconsistencies Identified</b>", styleH))
    if inconsistencies:
        for item in inconsistencies:
            story.append(Paragraph(f"• {item}", redStyle))
    else:
        story.append(Paragraph("None Identified or Not Available", styleN))

    doc.build(story)
    return doc_path

if submit and (startup_text.strip() or uploaded_file):
    with st.spinner("🧠 Generating one-pager with annexures and inconsistencies..."):
        try:
            content = extract_text_from_pdf(uploaded_file) if uploaded_file else startup_text.strip()
            prompt = build_prompt(content)

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a VC associate."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            parsed = json.loads(response.choices[0].message.content.strip())
            st.markdown(f"### 🧾 Preview: {parsed.get('startup_name', 'Startup')}")
            st.markdown(parsed.get("one_liner", ""))

            pdf_path = generate_one_pager(parsed)
            with open(pdf_path, "rb") as f:
                st.download_button("📥 Download One-Pager PDF", f, file_name="deal_snapshot.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
else:
    st.info("Please upload a pitch deck or paste a note to generate one-pager.")
