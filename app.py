import streamlit as st
import fitz  # PyMuPDF
import openai
import os

# 🔐 Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY") or "YOUR_OPENAI_API_KEY"

# Page settings
st.set_page_config(page_title="Factsheet Extractor", layout="wide")
st.title("📊 Factsheet Extractor – Investor Presentation Parser")
st.markdown("Upload investor decks (PDFs) to extract structured factsheets. Fields not found will be skipped.")

# Define factsheet sections and fields
SECTIONS = {
    "Startup Overview": ["Startup Name", "Sector", "Founded Year", "Product"],
    "Founders": ["Founders"],
    "Traction": ["Current Traction", "Monthly Active Users", "Key Customers"],
    "Financials": ["Revenue"],
    "Funding Details": ["Funds Raised", "Lead Investors", "Current Round", "Valuation", "Use of Funds"],
    "Market
