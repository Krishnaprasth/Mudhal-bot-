import streamlit as st
import fitz  # PyMuPDF
import openai

# Set your OpenAI API Key
openai.api_key = "YOUR_OPENAI_API_KEY"

st.set_page_config(page_title="Factsheet Extractor", layout="wide")
st.title("📊 Factsheet Extractor – Investor Presentation Parser")
st.markdown("Upload one or more investor decks (PDF), and we’ll extract a structured factsheet for each.")

# Define the sections to extract
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

def extract_text_from_pdf(pdf_file):
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_facts(text):
    prompt = f"""
From the following investor deck text, extract a structured factsheet for the startup. Only include fields if data is clearly present.

Fields to extract:
{', '.join([field for group in SECTIONS.values() for field in group])}

Respond with one line per field in format:
Field: Value

Text:
{text[:4000]}  # Truncated to stay within token limits
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
