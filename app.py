import streamlit as st
import fitz  # PyMuPDF
import openai
import os

# Set your OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY") or "YOUR_OPENAI_API_KEY"

# UI Config
st.set_page_config(page_title="Factsheet Extractor", layout="wide")
st.title("📊 Factsheet Extractor – Investor Presentation Parser")
st.markdown("Upload investor decks in PDF format and extract a structured startup factsheet. Missing data will be skipped.")

# Fields to Extract
SECTIONS = {
    "Startup Overview": ["Startup Name", "Sector", "Founded Year", "Product"],
    "Founders": ["Founders"],
    "Traction": ["Current Traction", "Monthly Active Users", "Key Customers"],
    "Financials": ["Revenue"],
    "Funding Details": ["Funds Raised", "Lead Investors", "Current Round", "Valuation", "Use of Funds"],
    "Market and Competition": ["Market Size", "Competitors"],
    "Ask": ["Ask (Amount)"]
}

# Upload PDFs
uploaded_files = st.file_uploader("📁 Upload PDF Presentations", type=["pdf"], accept_multiple_files=True)

# PDF Text Extraction
def extract_text_from_pdf(pdf_file):
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# GPT-Based Fact Extraction
def extract_facts(text):
    fields = [f for group in SECTIONS.values() for f in group]
    prompt = f"""
From the below investor presentation text, extract a structured startup factsheet with only available fields:

{', '.join(fields)}

Format the output as:
Field: Value
Do not include any fields not mentioned in the text.

Text:
{text[:4000]}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    content = response.choices[0].message.content.strip()
    facts = {}
    for line in content.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            facts[key.strip()] = val.strip()
    return facts

# UI Display Logic
if uploaded_files:
    for pdf in uploaded_files:
        with st.expander(f"📘 {pdf.name}", expanded=True):
            with st.spinner("Extracting facts..."):
                text = extract_text_from_pdf(pdf)
                facts = extract_facts(text)

            for section, fields in SECTIONS.items():
                section_data = {field: facts[field] for field in fields if field in facts}
                if section_data:
                    st.markdown(f"### 🔹 {section}")
                    for field, value in section_data.items():
                        st.markdown(f"**{field}**: {value}")
