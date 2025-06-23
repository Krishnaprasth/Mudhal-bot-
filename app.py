import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
from dateutil import parser
import os

st.set_page_config(layout="wide")
st.title("📊 QSR CEO Assistant")

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

logic_blocks = []

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
         f"anomaly_{metric_safe}.csv"),

        (f"EBITDA for {metric.lower()}",
         lambda df: df.assign(EBITDA=df['Net Sales'] - df[['COGS (food +packaging)', 'Aggregator commission', 'Marketing & advertisement', 'store Labor Cost', 'Utility Cost', 'Other opex expenses']].sum(axis=1))[['Month', 'Store', 'EBITDA']],
         f"ebitda.csv"),

        (f"gross margin % for {metric.lower()}",
         lambda df: df.assign(Gross_Margin_Pct=100 * df['Gross margin'] / df['Gross Sales'])[['Month', 'Store', 'Gross_Margin_Pct']],
         f"gross_margin_pct.csv"),

        (f"store profitability ranking by {metric.lower()}",
         lambda df: df.groupby('Store')['Net Sales'].sum().sort_values(ascending=False).reset_index().rename(columns={'Net Sales': 'Total Revenue'}),
         f"profit_ranking_{metric_safe}.csv")
    ])

query = st.text_input("Ask a question about store performance:")

if query:
    found = False
    store_match = extract_store(query)
    if store_match and "sales" in query.lower():
        df_temp = df[df['Store'] == store_match][['Month', 'Store', 'Net Sales']].sort_values(by='Month')
        st.dataframe(df_temp)
        st.download_button("📥 Download Table as CSV", df_temp.to_csv(index=False), file_name=f"{store_match}_sales.csv")
        found = True
    else:
        for pattern, logic_fn, filename in logic_blocks:
            if pattern in query.lower():
                df_temp = logic_fn(df)
                st.dataframe(df_temp)
                st.download_button("📥 Download Table as CSV", df_temp.to_csv(index=False), file_name=filename)
                found = True
                break

    if not found:
        st.warning(fallback_message)
        st.markdown("**Try one of the following:**")
        for tip in suggestions:
            st.markdown(f"- {tip}")
