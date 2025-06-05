import streamlit as st
import PyPDF2
import json
import os
from openai import OpenAI
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Load API key
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=OPENAI_API_KEY)

def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    return full_text

def build_prompt_for_summary_and_scores(text):
    return f"""
You are a venture analyst. Based on the pitch deck text below, return a JSON object with:

1. "summary": A crisp half-page summary (max 200 words) on the startup idea, founders, current status, traction, funding, and key facts.
2. "scorecard": A nested dictionary with the following structure:
{{
  "Founders & Team (20%)": {{
    "Founder relevant experience": 0,
    "Founder full-time": 0,
    "Team complementarity": 0,
    "Past startup/domain experience": 0,
    "Team size": 0,
    "Key hires": 0,
    "Cap table sanity": 0,
    "Founder insight": 0,
    "Motivation/resilience": 0,
    "Execution bias": 0
  }},
  "Problem-Solution Fit (10%)": {{
    "Problem clarity": 0,
    "Pain severity": 0,
    "Solution uniqueness": 0,
    "Must-have need": 0,
    "Simplicity": 0
  }},
  "Product & Tech (10%)": {{
    "Product clarity": 0,
    "Working MVP": 0,
    "Tech moat": 0,
    "Scalability": 0,
    "Defensibility": 0
  }},
  "Market & Timing (10%)": {{
    "TAM size": 0,
    "Market growth": 0,
    "Timing fit": 0,
    "Customer urgency": 0,
    "Competition": 0
  }},
  "Traction (15%)": {{
    "Revenue run rate": 0,
    "Growth rate": 0,
    "User/customer base": 0,
    "Retention": 0,
    "CAC": 0,
    "LTV": 0,
    "Gross margins": 0,
    "Customer proof": 0
  }},
  "Business Model (10%)": {{
    "Revenue model": 0,
    "Pricing power": 0,
    "Path to profitability": 0,
    "Monetization": 0,
    "Gross margin potential": 0
  }},
  "Financials (10%)": {{
    "Cash runway": 0,
    "Burn rate": 0,
    "Unit economics": 0,
    "Use of funds": 0,
    "Capital efficiency": 0
  }},
  "Go-to-Market (5%)": {{
    "Acquisition channels": 0,
    "Sales strategy": 0,
    "Distribution partnerships": 0
  }},
  "Risk (5%)": {{
    "Regulatory": 0,
    "Founder dependence": 0,
    "Competition risk": 0,
    "Legal/IP risk": 0,
    "Data inconsistency": 0
  }}
}}

Each parameter must be scored 0–10. Output valid JSON only.
Input:
{text}
"""

def generate_pdf(summary_text, scores):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate("investment_memo.pdf", pagesize=A4)
    story = []

    # Title
    story.append(Paragraph("🚀 Investment Memo", styles["Title"]))
    story.append(Spacer(1, 12))

    # Summary
    story.append(Paragraph("Summary", styles["Heading2"]))
    story.append(Paragraph(summary_text.replace("\n", "<br/>"), styles["BodyText"]))
    story.append(PageBreak())

    # Scorecard
    story.append(Paragraph("Scorecard", styles["Heading2"]))
    table_data = [["Category", "Parameter", "Score"]]
    total_score = 0
    count = 0
    for category, params in scores.items():
        for param, score in params.items():
            table_data.append([category, param, score])
            total_score += score
            count += 1

    table_data.append(["", "<b>Composite Score</b>", round(total_score / count, 2)])
    table = Table(table_data, repeatRows=1, colWidths=[130, 250, 80])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")
    ]))
    story.append(table)

    doc.build(story)
    return "investment_memo.pdf"

# Streamlit App UI
st.set_page_config(page_title="GPT Investment Memo Builder", layout="centered")
st.title("📄 VC Memo Generator with GPT")

uploaded_file = st.file_uploader("Upload a pitch deck (PDF)", type=["pdf"])
if st.button("Generate Memo") and uploaded_file:
    with st.spinner("Extracting and analyzing the pitch deck..."):
        try:
            deck_text = extract_text_from_pdf(uploaded_file)
            prompt = build_prompt_for_summary_and_scores(deck_text)

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional venture capital analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            result = json.loads(response.choices[0].message.content.strip())
            summary_text = result["summary"]
            scorecard = result["scorecard"]
            pdf_path = generate_pdf(summary_text, scorecard)

            st.subheader("📝 Summary")
            st.text_area("Crisp Overview", summary_text, height=200)

            with open(pdf_path, "rb") as f:
                st.download_button("📥 Download Investment Memo", f, file_name="investment_memo.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"❌ Error: {e}")
