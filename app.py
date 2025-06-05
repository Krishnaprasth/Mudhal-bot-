import streamlit as st
import PyPDF2
import os
import json
from openai import OpenAI
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# --- Setup ---
st.set_page_config(page_title="Mudhal Evaluation", layout="centered")
st.title("📊 Mudhal Evaluation - VC Memo Generator")

OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Extract text from PDF ---
def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"
    return text

# --- GPT Prompt ---
def build_prompt(text):
    return f"""
You are a professional VC analyst for 'Mudhal Evaluation'. Analyze the pitch deck text below.

Return a JSON with:
1. "summary": A crisp one-paragraph summary on idea, founder, traction, funding, and status.
2. "scorecard": 50 parameters grouped in 9 categories, scores 0–10 (dict of dict).
3. "ask": bullets on raise amount, round type, valuation, use of funds.
4. "annexures": bullets on traction/revenue, financials, shareholding pattern, key customers. If data missing, say "Not Available".

Text:
{text}
"""

# --- PDF Generation ---
def generate_pdf(startup_name, summary, scorecard, ask, annexures):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(f"{startup_name}_memo.pdf", pagesize=A4)
    story = []

    # Header
    story.append(Paragraph(f"<b>{startup_name} – Investment Memo</b>", styles["Title"]))
    story.append(Paragraph("Mudhal Evaluation", styles["Heading2"]))
    story.append(Spacer(1, 12))

    # Summary
    story.append(Paragraph("📌 Summary", styles["Heading3"]))
    story.append(Paragraph(summary.replace("\n", "<br/>"), styles["BodyText"]))
    story.append(Spacer(1, 12))

    # Ask
    story.append(Paragraph("💸 Ask", styles["Heading3"]))
    for bullet in ask:
        story.append(Paragraph(f"• {bullet}", styles["BodyText"]))
    story.append(Spacer(1, 12))

    # Annexures
    story.append(Paragraph("📎 Annexures", styles["Heading3"]))
    for ann in annexures:
        story.append(Paragraph(f"• {ann}", styles["BodyText"]))
    story.append(PageBreak())

    # Scorecard Table
    story.append(Paragraph("📊 Scorecard", styles["Heading2"]))
    table_data = [["Category", "Parameter", "Score"]]
    total_score = 0
    count = 0
    for cat, items in scorecard.items():
        for param, score in items.items():
            table_data.append([cat, param, score])
            total_score += score
            count += 1
    table_data.append(["", "Composite Score", round(total_score / count, 2)])

    table = Table(table_data, repeatRows=1, colWidths=[130, 260, 80])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 1), (2, -1), "CENTER"),
    ]))
    story.append(table)

    doc.build(story)
    return f"{startup_name}_memo.pdf"

# --- Streamlit UI ---
uploaded_file = st.file_uploader("Upload Pitch Deck (PDF)", type=["pdf"])
if st.button("🔍 Analyze and Generate Memo") and uploaded_file:
    with st.spinner("Analyzing with GPT..."):
        try:
            raw_text = extract_text_from_pdf(uploaded_file)
            prompt = build_prompt(raw_text)

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a detail-oriented VC analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            result = json.loads(response.choices[0].message.content.strip())
            summary = result["summary"]
            scorecard = result["scorecard"]
            ask = result["ask"]
            annexures = result["annexures"]
            startup_name = uploaded_file.name.split(".")[0].replace("_", " ").title()

            pdf_file = generate_pdf(startup_name, summary, scorecard, ask, annexures)

            st.success("✅ Memo ready!")
            st.download_button("📥 Download Investment Memo", open(pdf_file, "rb"), file_name=pdf_file)

            st.subheader("🔎 Summary Preview")
            st.text_area("Summary", summary, height=200)

        except Exception as e:
            st.error(f"❌ Error: {e}")
