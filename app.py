import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import base64

st.set_page_config(layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv("cleaned_store_data_embedded.csv")

df = load_data()
st.title("📊 QSR CEO Performance Bot")

st.markdown("Ask any question about store performance:")

query = st.text_input("💬 Enter your question", key="input")

if query:
    with st.spinner("Analyzing your query..."):
        df.columns = df.columns.str.strip()

        def normalize_months(df):
            month_col = df['Month'].astype(str).str.strip()
            df['Month'] = month_col.str.replace(r'[-]', ' ', regex=True).str.replace(r'[^\w\s]', '', regex=True).str.lower()
            df['Month'] = df['Month'].str.replace(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*([0-9]{2,4})',
                                                   lambda m: pd.to_datetime(f"01 {m.group(1)} {m.group(2)}", errors='coerce').strftime('%b %y')
                                                   if pd.to_datetime(f"01 {m.group(1)} {m.group(2)}", errors='coerce') else m.group(0),
                                                   regex=True)
            return df

        df = normalize_months(df)

        logic_blocks = []

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

                (f"EBITDA calculation",
                 lambda df: df.assign(EBITDA=df['Net Sales'] - df[['COGS (food +packaging)', 'Aggregator commission', 'Marketing & advertisement', 'store Labor Cost', 'Utility Cost', 'Other opex expenses']].sum(axis=1))[["Month", "Store", "EBITDA"]],
                 f"ebitda.csv"),

                (f"gross margin %",
                 lambda df: df.assign(Gross_Margin_Pct=100 * df['Gross margin'] / df['Gross Sales'])[["Month", "Store", "Gross_Margin_Pct"]],
                 f"gross_margin_pct.csv"),

                (f"store profitability ranking",
                 lambda df: df.groupby('Store')['Net Sales'].sum().sort_values(ascending=False).reset_index().rename(columns={'Net Sales': 'Total Revenue'}),
                 f"store_profitability.csv")
            ])

        match_found = False
        for keyword, func, filename in logic_blocks:
            if keyword in query.lower():
                try:
                    df_temp = func(df)
                    st.success(f"🔍 Answer for: {keyword}")
                    st.dataframe(df_temp)

                    csv = df_temp.to_csv(index=False)
                    st.download_button("📥 Download Table as CSV", csv, file_name=filename)

                    # Plot
                    if len(df_temp.columns) >= 3 and df_temp.dtypes[-1] in [float, int]:
                        fig, ax = plt.subplots(figsize=(10, 4))
                        df_temp.plot(kind='bar', x=df_temp.columns[1], y=df_temp.columns[2], ax=ax)
                        st.pyplot(fig)
                    match_found = True
                    break
                except Exception as e:
                    st.error(f"Logic failed: {e}")
                    match_found = True
                    break

        if not match_found:
            st.warning("🤖 No logic matched. Please rephrase the question or try a simpler query.")
