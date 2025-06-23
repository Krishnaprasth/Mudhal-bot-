import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_store_data_embedded.csv")
    df["Month"] = df["Month"].astype(str).str.strip().str.replace(r'[-]', ' ', regex=True).str.replace(r'\s+', ' ', regex=True)
    df["Month"] = df["Month"].str.replace("24", "2024").str.replace("25", "2025")
    return df

df = load_data()

st.title("🧠 Store Performance Analyst (CEO Bot)")
query = st.text_input("Ask your question about store performance:")

if query:
    query_lower = query.lower()

    logic_blocks = []

    all_metrics = [c for c in df.columns if c not in ["Month", "Store"]]
    for metric in all_metrics:
        metric_safe = metric.replace(" ", "_").lower()
        logic_blocks.extend([
            (f"sales of", 
             lambda df, m=metric: df.pivot_table(index="Month", columns="Store", values=m, aggfunc="sum").reset_index(),
             f"{metric_safe}_trend.csv"),

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
             lambda df, m=metric: df.assign(**{f"{metric} %": 100 * df[m] / df['Net Sales']})\
             .sort_values(by=f"{metric} %", ascending=False)[["Month", "Store", f"{metric} %"]],
             f"percent_sales_{metric_safe}.csv"),

            (f"anomaly in {metric.lower()}",
             lambda df, m=metric: df[(df[m] - df[m].mean()).abs() > 3 * df[m].std()][["Month", "Store", m]],
             f"anomaly_{metric_safe}.csv"),

            (f"MoM change in {metric.lower()}",
             lambda df, m=metric: df.sort_values(['Store', 'Month']).groupby('Store')[m].pct_change().rename("MoM Change").reset_index().join(df[['Month', 'Store']], how='left', lsuffix='_drop').drop(columns=['index_drop']),
             f"mom_change_{metric_safe}.csv"),

            (f"YoY growth in {metric.lower()}",
             lambda df, m=metric: df.sort_values(['Store', 'Month']).groupby('Store')[m].pct_change(periods=12).rename("YoY Growth").reset_index().join(df[['Month', 'Store']], how='left', lsuffix='_drop').drop(columns=['index_drop']),
             f"yoy_growth_{metric_safe}.csv"),
        ])

    # Try matching logic
    matched = False
    for pattern, func, fname in logic_blocks:
        if pattern in query_lower:
            df_temp = func(df)
            st.success("✅ Answer below")
            st.dataframe(df_temp, use_container_width=True)

            # Download button
            csv = df_temp.to_csv(index=False)
            st.download_button("📥 Download CSV", csv, file_name=fname)

            # Optional plot
            if "Month" in df_temp.columns and any(col for col in df_temp.columns if col not in ["Month", "Store"]):
                plot_cols = [col for col in df_temp.columns if col not in ["Month", "Store"]]
                fig, ax = plt.subplots(figsize=(12, 5))
                df_temp.set_index("Month")[plot_cols].plot(ax=ax)
                st.pyplot(fig)
            matched = True
            break

    if not matched:
        st.warning("🤖 No logic matched. Please rephrase the question or try a simpler query.")
