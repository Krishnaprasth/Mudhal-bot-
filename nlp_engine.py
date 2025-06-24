
import pandas as pd
import re
from openai import OpenAI
import os

df_store = pd.read_csv("QSR_CEO_Complete_Lakhs.csv")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

month_map = {'january 24': '24-Jan', 'february 24': '24-Feb', 'march 24': '24-Mar', 'april 24': '24-Apr', 'may 24': '24-May', 'june 24': '24-Jun', 'july 24': '24-Jul', 'august 24': '24-Aug', 'september 24': '24-Sep', 'october 24': '24-Oct', 'november 24': '24-Nov', 'december 24': '24-Dec', 'january 25': '25-Jan', 'february 25': '25-Feb', 'march 25': '25-Mar', 'april 25': '25-Apr', 'may 25': '25-May', 'june 25': '25-Jun', 'july 25': '25-Jul', 'august 25': '25-Aug', 'september 25': '25-Sep', 'october 25': '25-Oct', 'november 25': '25-Nov', 'december 25': '25-Dec'}
metric_aliases = {'revenue': 'net sales', 'sales': 'net sales', 'gross revenue': 'gross sales', 'ebitda': 'ebitda', 'rent': 'rent', 'commission': 'aggregator commission', 'labor': 'labor cost', 'labour': 'labor cost'}

def normalize_query(text):
    text = text.lower()
    for k, v in metric_aliases.items():
        text = text.replace(k, v)
    return text

def extract_month(text):
    for k, v in month_map.items():
        if k in text:
            return v
    return None

def extract_metric(text):
    for m in df_store['Metric'].unique():
        if m.lower() in text:
            return m
    return None

def get_top_store_by_metric(month, metric):
    df = df_store[(df_store['Month'].str.lower() == month.lower()) & (df_store['Metric'].str.lower() == metric.lower())]
    if df.empty:
        return "No data found for {} in {}.".format(metric, month)
    top = df.sort_values("Amount", ascending=False).iloc[0]
    return "Top store by {} in {} is {} with ₹{:.1f} lakhs.".format(metric, month, top['Store'], top['Amount'])

def gpt_fallback(query):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for analyzing QSR store data with columns Month, Store, Metric, and Amount (in lakhs)."},
            {"role": "user", "content": query}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content

def nlp_router(user_query):
    query = normalize_query(user_query)
    month = extract_month(query)
    metric = extract_metric(query)

    if "max" in query or "highest" in query or "top" in query:
        if month and metric:
            return get_top_store_by_metric(month, metric)

    if month and metric:
        return get_top_store_by_metric(month, metric)

    return gpt_fallback(user_query)
