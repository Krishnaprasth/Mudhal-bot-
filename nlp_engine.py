
import pandas as pd
import re
import openai

# Load data from CSV
df_store = pd.read_csv("QSR_CEO_Complete_Lakhs.csv")
question_df = pd.read_csv("qsr_ceo_100000_questions_storecodes.csv")

# NLP Parsing Helper Functions
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
        r"labor": "labor cost",
        r"aggregator": "aggregator commission",
        r"store": "store",
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    return text

def extract_store_codes(text, store_list):
    mentioned = [store for store in store_list if store.lower() in text.lower()]
    return mentioned

# Sample Logic Function
def get_top_store_by_metric(month, metric):
    df_month = df_store[(df_store['Month'].str.lower() == month.lower()) & (df_store['Metric'].str.lower() == metric.lower())]
    if df_month.empty:
        return "No data found for that month/metric."
    top_row = df_month.sort_values(by="Amount", ascending=False).iloc[0]
    return f"Top store by {metric} in {month} is {top_row['Store']} with ₹{top_row['Amount']} lakhs."

# GPT fallback if no match is found
def gpt_fallback(query):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for analyzing QSR store financial data."},
            {"role": "user", "content": query}
        ],
        temperature=0.2
    )
    return response.choices[0].message["content"]

# NLP Router
def nlp_router(user_query):
    query = normalize_question(user_query)
    store_codes = df_store['Store'].unique().tolist()
    matched_stores = extract_store_codes(query, store_codes)

    for month in df_store['Month'].unique():
        if month.lower() in query:
            for metric in df_store['Metric'].unique():
                if metric.lower() in query:
                    return get_top_store_by_metric(month, metric)

    # GPT fallback
    return gpt_fallback(user_query)
