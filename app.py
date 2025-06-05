import streamlit as st
import PyPDF2
import os
import json
from openai import OpenAI
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# --- Streamlit UI Branding ---
st.set_page_config(page_title="Mudhal Evaluation", layout="centered")

st.markdown(
    """
    <style>
        .reportview-container {
            background-color: #f7f9fa;
            padding: 2rem;
        }
        h1 {
            font-family: 'Segoe UI', sans-serif;
            color: #003262;
        }
        .stButton>button {
            background-color: #003262;
            color: white;
            border-radius: 6px;
            padding: 0.5rem 1.5rem;
        }
        .stButton>button:hover {
            background-color: #005b96;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("## 📊 Mudhal Evaluation")
st.markdown("**A comprehensive one-pager startup analysis report**")
st.write("---")

# --- Setup OpenAI API Key ---
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

# --- GPT Prompt Builder ---
def build_prompt(text):
    return f"""
You are a professional startup analyst at 'Mudhal Evaluation'.

Based on the pitch deck text below, prepare a comprehensive analysis report that includes:

1. "summary": A full-page write-up covering:
   - The startup’s core idea and problem it solves
   - Founders' backgrounds, experience, and commitment
   - Current business status: traction, users, revenue, customers
   - Competitive landscape and market opportunity
   - Any standout strengths or weaknesses from the deck

2. "scorecard": A dictionary of 50 evaluation parameters grouped under categories (each parameter scored 0–10).

3. "ask": Bullet points on:
   - Amount being raised
   - Round type (Pre-seed, Seed, Series A etc.)
   - Intended use of funds
   - Pre-money or post-money valuation if available

4. "annexures": Bullet points on:
   - Traction or revenue figures
   - Financial metrics
   - Shareholding pattern or cap table
   - Key customers or partnerships
   (If not found, respond with “Not Available”)

Only return a valid JSON object with keys: summary, scorecard, ask, annexures.

Pitch Deck Text:
{text}
"""

# --- PDF Generation ---
def generate_pdf(startup_name, summary, scorecard, ask, annexures):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(f"{startup_name}_mudhal_report.pdf", pagesize=A4)
    story = []

    # Header
    story.append(Paragraph(f"<b>{startup_name} – Mudhal Evaluation Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    # Summary
    story.append(Paragraph("📄 Descriptive Summary", styles["Heading3"]))
    story.append(Paragraph(summary.replace("\n", "<br/>"), styles["BodyText"]))
    story.append(PageBreak())

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

    # Scorecard
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
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003262")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 1), (2, -1), "CENTER"),
    ]))
    story.append(table)

    doc.build(story)
    return f"{startup_name}_mudhal_report.pdf"

# --- Streamlit App Flow ---
uploaded_file = st.file_uploader("Upload Pitch Deck (PDF)", type=["pdf"])
if st.button("📥 Generate Full Report") and uploaded_file:
    with st.spinner("Analyzing pitch deck with GPT..."):
        try:
            raw_text = extract_text_from_pdf(uploaded_file)
            prompt = build_prompt(raw_text)

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a detail-oriented startup analyst."},
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

            st.success("✅ Mudhal Evaluation Report is ready!")
            st.download_button("📄 Download Report", open(pdf_file, "rb"), file_name=pdf_file)

            st.subheader("📌 Summary Preview")
            st.text_area("Summary", summary, height=400)

        except Exception as e:
            st.error(f"❌ Error: {e}")
