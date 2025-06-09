import streamlit as st
import PyPDF2
import os
import json
import re
from openai import OpenAI
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Mudhal Evaluation", layout="centered")
st.title("📊 Mudhal Evaluation")
st.markdown("Upload a pitch deck to generate a **fact-only** investment evaluation report.")

OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=OPENAI_API_KEY)

def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"
    return text

def build_prompt(text):
    return f"""
You are a fact-based analyst from 'Mudhal Evaluation'.

From the pitch deck text below, extract only what is explicitly mentioned (NO assumptions):
1. "summary": A factual summary only based on the deck.
2. "ask": Round, amount, valuation, use of funds etc.
3. "annexures": Traction, revenue, financials, shareholding pattern, key customers – or say 'Not Available'.
4. "checklist": For each of these, mark "✅" if found, else "❌":
   - Traction
   - Revenue
   - Financial Metrics
   - Shareholding Pattern
   - Key Customers

Output JSON with keys: summary, ask, annexures, checklist.

Deck:
{text}
"""

def generate_fact_only_pdf(startup_name, summary, checklist, ask, annexures):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CompactBody", fontSize=10.5, leading=13))
    styles.add(ParagraphStyle(name="RedFlag", fontSize=10.5, textColor=colors.red, leading=13))

    doc = SimpleDocTemplate(f"/mnt/data/{startup_name}_mudhal_fact_report.pdf", pagesize=A4, topMargin=36, bottomMargin=36, leftMargin=36, rightMargin=36)
    story = []

    story.append(Paragraph(f"{startup_name} – Mudhal Evaluation Report", styles["Title"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("📄 Summary", styles["Heading2"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(summary.replace("\n", "<br/>"), styles["CompactBody"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("📋 Missing Information Checklist", styles["Heading2"]))
    story.append(Spacer(1, 6))
    for item, status in checklist.items():
        style = styles["CompactBody"] if status == "✅" else styles["RedFlag"]
        story.append(Paragraph(f"{item}: {status}", style))
    story.append(PageBreak())

    story.append(Paragraph("💸 Ask", styles["Heading2"]))
    story.append(Spacer(1, 4))
    for bullet in ask:
        story.append(Paragraph(f"• {bullet}", styles["CompactBody"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("📎 Annexures", styles["Heading2"]))
    story.append(Spacer(1, 4))
    for ann in annexures:
        story.append(Paragraph(f"• {ann}", styles["CompactBody"]))

    doc.build(story)
    return f"/mnt/data/{startup_name}_mudhal_fact_report.pdf"

uploaded_file = st.file_uploader("Upload Pitch Deck (PDF)", type=["pdf"])
if st.button("📥 Generate Fact-Only Report") and uploaded_file:
    with st.spinner("Analyzing deck with GPT..."):
        try:
            raw_text = extract_text_from_pdf(uploaded_file)
            prompt = build_prompt(raw_text)

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a factual analyst. Do not assume."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            raw_content = response.choices[0].message.content.strip()
            cleaned = re.sub(r"[\x00-\x1F\x7F]", "", raw_content)
            result = json.loads(cleaned)

            summary = result.get("summary", "")
            ask = result.get("ask", [])
            annexures = result.get("annexures", [])
            checklist = result.get("checklist", {})
            startup_name = uploaded_file.name.split(".")[0].replace("_", " ").title()

            pdf_file = generate_fact_only_pdf(startup_name, summary, checklist, ask, annexures)

            st.success("✅ Report Ready!")
            st.download_button("📄 Download Report", open(pdf_file, "rb"), file_name=pdf_file)
            st.subheader("📌 Summary Preview")
            st.text_area("Summary", summary, height=400)
            st.subheader("📋 Missing Info Checklist")
            for k, v in checklist.items():
                st.markdown(f"**{k}**: {'✅' if v == '✅' else '❌'}")

        except Exception as e:
            st.error(f"❌ Error: {e}")
