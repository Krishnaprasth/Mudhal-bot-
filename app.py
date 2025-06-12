import streamlit as st
import fitz  # PyMuPDF
import openai
import os

# ✅ Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY") or "YOUR_OPENAI_API_KEY"

# ✅ Page configuration
st.set_page_config(page_title="Factsheet Extractor", layout="wide")
st.title("📊 Factsheet Extractor – Investor Presentation Parser")
st.markdown("Upload investor decks (PDFs) to extract a structured startup factsheet. Fields not found will be skipped.")

# ✅ Define the sections and fields
SECTIONS = {
    "Startup Overview": ["Startup Name", "Sector", "Founded Year", "Product"],
    "Founders": ["Founders"],
    "Traction": ["Current Traction", "Monthly Active Users", "Key Customers"],
    "Financials": ["Revenue"],
    "Funding Details": ["Funds Raised", "Lead Investors", "Current Round", "Valuation", "Use of Funds"],
    "Market and Competition": ["Market Size", "Competitors"],
    "Ask": ["Ask (Amount)"]
}

# ✅ Upload PDF files
uploaded_files = st.file_uploader("📁 Upload PDF Presentations", type=["pdf"], accept_multiple_files=True)

# ✅ Extract text from PDF using PyMuPDF
def extract_text_from_pdf(pdf_file):
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# ✅ Extract facts using OpenAI Chat API (v1.x syntax)
def extract_facts(text):
    fields = [f for group in SECTIONS.values() for f in group]
    prompt = f"""
From the following investor presentation text, extract only the available fields listed below:

{', '.join(fields)}

Format output as:
Field: Value

Do not guess or fabricate. Only include data explicitly mentioned.

Text:
{text[:4000]}
"""
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    result = response.choices[0].message.content.strip()
    facts = {}
    for line in result.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            facts[key.strip()] = val.strip()
    return facts

# ✅ Main logic
if uploaded_files:
    for pdf in uploaded_files:
        with st.expander(f"📘 {pdf.name}", expanded=True):
            with st.spinner("🔍 Extracting facts..."):
                text = extract_text_from_pdf(pdf)
                facts = extract_facts(text)

            for section, fields in SECTIONS.items():
                section_data = {field: facts[field] for field in fields if field in facts}
                if section_data:
                    st.markdown(f"### 🔹 {section}")
                    for field, value in section_data.items():
                        st.markdown(f"**{field}**: {value}")
