import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
from dateutil import parser
import os
import json
from openai import OpenAI

st.set_page_config(layout="wide")
st.title("📊 QSR CEO Assistant")

client = OpenAI()

@st.cache_data
def load_data():
    default_path = "cleaned_store_data_embedded.csv"
    if os.path.exists(default_path):
        return pd.read_csv(default_path)
    else:
        uploaded_file = st.file_uploader("📤 Upload your cleaned store data CSV", type=["csv"])
        if uploaded_file is not None:
            return pd.read_csv(uploaded_file)
        else:
            st.warning("⚠️ Please upload a cleaned_store_data_embedded.csv file to proceed.")
            return pd.DataFrame()

# Load data
df = load_data()
if df.empty:
    st.stop()

month_list = df['Month'].dropna().unique().tolist()
store_list = df['Store'].dropna().unique().tolist()

metric_synonyms = {
    "revenue": "Net Sales",
    "sales": "Net Sales",
    "turnover": "Net Sales",
    "ebitda": "EBITDA",
    "gross margin": "Gross margin",
    "gross margin %": "Gross_Margin_Pct",
    "profit": "EBITDA"
}

def extract_standard_month(text, month_list):
    text = text.lower().replace("'", "").replace(",", "").replace("-", " ").replace("/", " ").replace(".", " ")
    candidates = re.findall(r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s]*[0-9]{2,4})|(?:[0-9]{2,4}[\s]*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*)", text)
    for cand in candidates:
        try:
            parsed = parser.parse(cand, fuzzy=True, dayfirst=True)
            normalized = parsed.strftime('%b %y')
            if normalized in month_list:
                return normalized
        except:
            continue
    return None

def extract_store(text):
    for store in store_list:
        if store.lower() in text.lower():
            return store
    return None

def gpt_interpret_query(user_input):
    prompt = f"""You are an analyst assistant. Given the user's question, extract and return what they are asking using structured language.

    Question: \"{user_input}\"

    Respond in JSON with fields: 
    - metric (e.g. \"Net Sales\", \"Gross margin\", etc.),
    - store (e.g. \"VEL\", if mentioned),
    - month (e.g. \"June 24\", if mentioned),
    - intent (e.g. \"top_store_by_metric\", \"store_trend\", \"compare_stores\", etc.)

    Only respond with JSON."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        reply = response.choices[0].message.content.strip()
        result = json.loads(reply)

        if "metric" in result:
            result["metric"] = metric_synonyms.get(result["metric"].lower(), result["metric"])
        return result

    except Exception as e:
        st.warning(f"GPT interpretation failed: {e}")
        return None

logic_blocks = []

if "Net Sales" in df.columns:
    logic_blocks.append(
        ("which store did max revenue in",
         lambda df: df[df['Net Sales'] == df['Net Sales'].max()][['Month', 'Store', 'Net Sales']],
         "max_net_sales.csv")
    )

fallback_message = "🤖 No logic matched. Try queries like:\n- Top 5 stores by Net Sales\n- MoM change in Gross margin\n- EBITDA for ANN store\n- Trend of revenue for EGL"

suggestions = [
    "Top 5 stores by Net Sales",
    "Gross margin % for EGL",
    "MoM change in Marketing & advertisement",
    "Anomaly in Utility Cost",
    "Store profitability ranking by EBITDA"
]

all_metrics = [c for c in df.columns if c not in ["Month", "Store"]]

for metric in all_metrics:
    metric_safe = metric.replace(" ", "_").lower()
    logic_blocks.extend([
        (f"highest {metric.lower()}",
         lambda df, m=metric: df[df[m] == df[m].max()][["Month", "Store", m]],
         f"highest_{metric_safe}.csv"),

        (f"lowest {metric.lower()}",
         lambda df, m=metric: df[df[m] == df[m].min()][["Month", "Store", m]],
         f"lowest_{metric_safe}.csv"),

        (f"top stores by {metric.lower()}",
         lambda df, m=metric: df.sort_values(by=m, ascending=False)[["Month", "Store", m]].head(10),
         f"top_stores_{metric_safe}.csv"),

        (f"{metric.lower()} as % of sales",
         lambda df, m=metric: df.assign(**{f"{metric} %": 100 * df[m] / df['Net Sales']}).sort_values(by=f"{metric} %", ascending=False)[["Month", "Store", f"{metric} %"]],
         f"percent_sales_{metric_safe}.csv"),

        (f"MoM change in {metric.lower()}",
         lambda df, m=metric: df.sort_values(['Store', 'Month']).groupby('Store')[m].pct_change().rename("MoM Change").reset_index().join(df[['Month', 'Store']], how='left', lsuffix='_drop').drop(columns=['index_drop']),
         f"mom_change_{metric_safe}.csv"),

        (f"YoY growth in {metric.lower()}",
         lambda df, m=metric: df.sort_values(['Store', 'Month']).groupby('Store')[m].pct_change(periods=12).rename("YoY Growth").reset_index().join(df[['Month', 'Store']], how='left', lsuffix='_drop').drop(columns=['index_drop']),
         f"yoy_growth_{metric_safe}.csv"),

        (f"anomaly in {metric.lower()}",
         lambda df, m=metric: df[(df[m] - df[m].mean()).abs() > 3 * df[m].std()][["Month", "Store", m]],
         f"anomaly_{metric_safe}.csv")
    ])

# Special logic for EBITDA and Gross Margin %
if set(['Net Sales', 'Gross margin', 'Gross Sales']).issubset(df.columns):
    logic_blocks.extend([
        ("EBITDA for store",
         lambda df: df.assign(EBITDA=df['Net Sales'] - df[['COGS (food +packaging)', 'Aggregator commission', 'Marketing & advertisement', 'store Labor Cost', 'Utility Cost', 'Other opex expenses']].sum(axis=1))[['Month', 'Store', 'EBITDA']],
         "ebitda.csv"),

        ("gross margin %",
         lambda df: df.assign(Gross_Margin_Pct=100 * df['Gross margin'] / df['Gross Sales'])["Month", "Store", "Gross_Margin_Pct"]],
         "gross_margin_pct.csv")
    ])

query = st.text_input("Ask a question about store performance:")

if query:
    found = False
    interpretation = gpt_interpret_query(query)

    if interpretation:
        metric = interpretation.get("metric")
        store = interpretation.get("store")
        month = interpretation.get("month")
        intent = interpretation.get("intent")

        if intent == "top_store_by_metric" and metric and month:
            df_temp = df[df['Month'] == month].sort_values(by=metric, ascending=False).head(1)
            st.dataframe(df_temp)
            st.download_button("📥 Download Table as CSV", df_temp.to_csv(index=False), file_name=f"top_store_{metric}_{month}.csv")
            found = True

        elif intent == "store_trend" and metric and store:
            df_temp = df[df['Store'] == store][['Month', 'Store', metric]].sort_values(by='Month')
            st.dataframe(df_temp)
            st.download_button("📥 Download Table as CSV", df_temp.to_csv(index=False), file_name=f"{store}_{metric}_trend.csv")
            found = True

    if not found:
        for pattern, logic_fn, filename in logic_blocks:
            if pattern in query.lower():
                try:
                    df_temp = logic_fn(df)
                    st.dataframe(df_temp)
                    st.download_button("📥 Download Table as CSV", df_temp.to_csv(index=False), file_name=filename)
                except Exception as e:
                    st.error(f"❌ Error in logic block: {e}")
                found = True
                break

    if not found:
        st.warning(fallback_message)
        st.markdown("**Try one of the following:**")
        for tip in suggestions:
            st.markdown(f"- {tip}")
