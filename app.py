import streamlit as st
import os
import json
import tempfile
import pytesseract
from pdf2image import convert_from_bytes
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="Startup One-Pager Generator", layout="centered")
st.title("📄 Startup Deal Snapshot Generator")

uploaded_file = st.file_uploader("📄 Upload pitch deck (PDF)", type=["pdf"])
startup_text = st.text_area("Or paste founder note / call summary", height=250)
submit = st.button("🚀 Generate One-Pager")

def extract_text_with_ocr(file):
    images = convert_from_bytes(file.read())
    extracted_text = "\n".join([pytesseract.image_to_string(img) for img in images])
    return extracted_text

def build_prompt(text):
    return f"""
Act like a VC analyst. Read the founder input below and return a structured JSON like this:

{{
  "startup_name": "",
  "founder_names": [""],
  "experience_summary": "",
  "idea": "",
  "product": "",
  "traction": "",
  "annexures": {{
    "funding_raised": "",
    "shareholding_pattern": "",
    "financial_metrics": "",
    "key_growth_metrics": ""
  }},
  "scorecard": {{
    "Founder Experience": 0,
    "Market Size": 0,
    "Traction": 0,
    "Product Clarity": 0,
    "Revenue Potential": 0,
    "Risk Level (low=better)": 0,
    "Composite Score": 0.0
  }},
  "inconsistencies": [""]
}}

If any section is not available, clearly state "Not Available". Return only valid JSON.

Founder Input:
{text}
"""

def generate_pdf(data):
    styles = getSampleStyleSheet()
    styleN = styles["BodyText"]
    styleH = styles["Heading4"]
    redStyle = ParagraphStyle(name='RedText', parent=styleN, textColor=colors.red)
    doc_path = "one_pager_summary.pdf"
    doc = SimpleDocTemplate(doc_path, pagesize=A4)
    story = []

    fields = [
        ["Company Name", data.get("startup_name", "")],
        ["Founder(s)", ", ".join(data.get("founder_names", []))],
        ["Experience", data.get("experience_summary", "")],
        ["Idea", data.get("idea", "")],
        ["Product", data.get("product", "")],
        ["Traction", data.get("traction", "")]
    ]
    table = Table(fields, colWidths=[120, 380])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica')
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Annexures</b>", styleH))
    for label, val in data.get("annexures", {}).items():
        story.append(Paragraph(f"<b>{label.replace('_', ' ').title()}</b>: {val if val else 'Not Available'}", styleN))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Scorecard</b>", styleH))
    scorecard = data.get("scorecard", {})
    score_data = [["Metric", "Score"]] + [[k, str(v)] for k, v in scorecard.items()]
    score_table = Table(score_data, colWidths=[220, 80])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    story.append(score_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Inconsistencies Identified</b>", styleH))
    inconsistencies = data.get("inconsistencies", [])
    if inconsistencies:
        for item in inconsistencies:
            story.append(Paragraph(f"• {item}", redStyle))
    else:
        story.append(Paragraph("None Identified or Not Available", styleN))

    doc.build(story)
    return doc_path

if submit and (startup_text.strip() or uploaded_file):
    with st.spinner("Generating one-pager memo..."):
        try:
            content = extract_text_with_ocr(uploaded_file) if uploaded_file else startup_text.strip()
            st.markdown("### 🔍 Extracted Text Preview")
            st.text_area("Input Sent to GPT", content[:3000], height=200)

            prompt = build_prompt(content)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a VC analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            raw_response = response.choices[0].message.content.strip()
            if raw_response.startswith("```"):
                raw_response = raw_response.strip("`").strip("json").strip()

            try:
                parsed = json.loads(raw_response)
            except json.JSONDecodeError:
                st.error("⚠️ GPT response is not valid JSON.")
                st.text_area("Raw GPT Output", raw_response, height=300)
                st.stop()

            st.markdown(f"### 🧾 Memo Preview: {parsed.get('startup_name', 'Startup')}")
            pdf_path = generate_pdf(parsed)
            with open(pdf_path, "rb") as f:
                st.download_button("📥 Download One-Pager PDF", f, file_name="deal_snapshot.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
else:
    st.info("Please upload a PDF or paste startup note to generate the memo.")
