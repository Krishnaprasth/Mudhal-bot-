import pandas as pd
import re
from openai import OpenAI
import os

# Load the store performance dataset
df_store = pd.read_csv("QSR_CEO_Complete_Lakhs.csv")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Month mapping: "june 24" → "24-Jun"
month_map = {
    'january 24': '24-Jan', 'february 24': '24-Feb', 'march 24': '24-Mar', 'april 24': '24-Apr',
    'may 24': '24-May', 'june 24': '24-Jun', 'july 24': '24-Jul', 'august 24': '24-Aug',
    'september 24': '24-Sep', 'october 24': '24-Oct', 'november 24': '24-Nov', 'december 24': '24-Dec',
    'january 25': '25-Jan', 'february 25': '25-Feb', 'march 25': '25-Mar', 'april 25': '25-Apr',
    'may 25': '25-May', 'june 25': '25-Jun', 'july 25': '25-Jul', 'august 25': '25-Aug',
    'september 25': '25-Sep', 'october 25': '25-Oct', 'november 25': '25-Nov', 'december 25': '25-Dec'
}

# Common keyword replacements
metric_aliases = {
    "revenue": "net sales",
    "sales": "net sales",
    "gross revenue": "gross sales",
    "ebitda": "ebitda",
    "rent": "rent",
    "commission": "aggregator commission",
    "labor": "labor cost",
    "labour": "labor cost"
}

# Normalize query for better matching
def normalize_query(text):
    text = text.lo
