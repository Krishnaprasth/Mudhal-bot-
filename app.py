import streamlit as st
import requests
import json
import os
from openai import OpenAI
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Load API keys
OCR_API_KEY = st.secrets.get("OCR_API_KEY", os.getenv("OCR_API_KEY"))
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=OPENAI_API_KEY)

# OCR using OCR.Space
def extract_text_via_ocr_space(file):
    url = "https://api.ocr.space/parse/image"
    result = requests.post(
        url,
        files={"file": file},
        data={"apikey": OCR_API_KEY, "language": "eng", "isOverlayRequired": False}
    )
    result.raise_for_status()
    data = result.json()
    parsed_text = "\n".join([r["ParsedText"] for r in data.get("ParsedResults", [])])
    return parsed_text

# GPT prompt
def build_prompt(text):
    return f"""Act like a VC analyst. Read the input below and return JSON:
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
If any section is not available, say "Not Available". Only output valid JSON.
Input:
{text}"""

# Generate PDF memo
def generate_pdf(data):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate("memo.pdf", pagesize=A4)
    story = []
    styleN, styleH = styles["BodyText"], styles["Heading4"]
    redStyle = ParagraphStyle(name='RedText', parent=styleN, textColor=colors.red)

    company_name = data.get("startup_name", "Startup")
    story.append(Paragraph(f"<b>{company_name} - Investment Memo</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    table_data = [
        ["Company Name", company_name],
        ["Founders", ", ".join(data.get("founder_names", []))],
        ["Experience", data.get("experience_summary", "")],
        ["Idea", data.get("idea", "")],
        ["Product", data.get("product", "")],
        ["Traction", data.get("traction", "")]
    ]
    table = Table(table_data, colWidths=[120, 400])
    table.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Annexures", styleH))
    for k, v in data.get("annexures", {}).items():
        story.append(Paragraph(f"{k.replace('_',' ').title()}: {v or 'Not Available'}", styleN))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Scorecard", styleH))
    score_data = [["Metric", "Score"]] + [[k, v] for k, v in data.get("scorecard", {}).items()]
    score = Table(score_data, colWidths=[220, 80])
    score.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.append(score)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Inconsistencies", styleH))
    for i in data.get("inconsistencies", []) or ["None found"]:
        story.append(Paragraph(f"• {i}", redStyle))

    doc.build(story)
    return "memo.pdf"

# Streamlit UI
st.set_page_config(page_title="Startup Memo Bot with OCR")
st.title("📄 GPT Investment Memo Generator (with OCR)")

uploaded_file = st.file_uploader("Upload scanned pitch deck (PDF)", type=["pdf"])
if st.button("Generate Memo") and uploaded_file:
    with st.spinner("Extracting text and analyzing deck..."):
        try:
            text = extract_text_via_ocr_space(uploaded_file)
            if not text.strip():
                st.error("❌ No text could be extracted via OCR.")
            else:
                st.text_area("Extracted Text", text[:2000], height=200)
                prompt = build_prompt(text)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a VC analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                memo = json.loads(response.choices[0].message.content.strip().strip("`"))
                pdf_path = generate_pdf(memo)
                with open(pdf_path, "rb") as f:
                    st.download_button("📥 Download Memo", f, file_name="startup_memo.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"❌ Error: {e}")
