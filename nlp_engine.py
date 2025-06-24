import pandas as pd
import re
from openai import OpenAI
import os

# Load data
df_store = pd.read_csv("QSR_CEO_Complete_Lakhs.csv")
question_df = pd.read_csv("qsr_ceo_100000_questions_storecodes.csv")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Helper functions ---
def normalize_question(text):
    text = text.lower()
    replacements = {
        r"sales": "net sales",
        r"gross sales": "gross sales",
        r"online sales": "online sales",
        r"offline sales": "offline sales",
        r"ebitda": "ebitda",
        r"gst": "gst",
        r"rent": "rent",
        r"labour|labor": "labor cost",
        r"aggregator": "aggregator commission",
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    return text

def extract_store_codes(text, store_list):
    return [store for store in store_list if store.lower() in text.lower()]

def get_top_store_by_metric(month, metric):
    df_month = df_store[
        (df_store['Month'].str.lower() == month.lower()) &
        (df_store['Metric'].str.lower() == metric.lower())
    ]
    if df_month.empty:
        return "No data found for that month/metric."
    top_row = df_month.sort_values(by="Amount", ascending=False).iloc[0]
    return f"Top store by {metric} in {month} is {top_row['Store']} with ₹{top_row['Amount']:.1f} lakhs."

# GPT fallback
def gpt_fallback(query):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that answers questions on QSR store data. "
                    "The data includes columns: Month, Store, Metric, and Amount (in lakhs)."
                )
            },
            {"role": "user", "content": query}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content

# --- NLP Router ---
def nlp_router(user_query):
    query = normalize_question(user_query)
    store_codes = df_store['Store'].unique().tolist()
    matched_stores = extract_store_codes(query, store_codes)

    month_match = None
    metric_match = None

    for month in df_store['Month'].unique():
        if month.lower() in query:
            month_match = month
            break

    for metric in df_store['Metric'].unique():
        if metric.lower() in query:
            metric_match = metric
            break

    if any(word in query for word in ["max", "highest", "top"]) and month_match and metric_match:
        return get_top_store_by_metric(month_match, metric_match)

    if month_match and metric_match:
        return get_top_store_by_metric(month_match, metric_match)

    # GPT fallback
    return gpt_fallback(user_query)
