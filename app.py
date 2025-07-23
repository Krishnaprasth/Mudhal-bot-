import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import os

st.title("QSR CEO Bot MVP")

# Try loading committed CSV first
DATA_PATH = "data/sales_data.csv"
if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
else:
    uploaded_file = st.file_uploader("Upload cleaned QSR dataset (CSV)", type=["csv"])
    if not uploaded_file:
        st.info("Either commit your CSV to `data/qsr_data.csv` or upload it here.")
        st.stop()
    df = pd.read_csv(uploaded_file)

df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
df = df.dropna(subset=['Amount'])

# Filters
stores = st.multiselect(
    "Select Stores",
    sorted(df['Store'].unique()),
    default=list(df['Store'].unique())
)
fy = st.selectbox("Select Financial Year", sorted(df['FY'].unique()))
metric_options = [
    "Net Sales", "Rent", "Labor Cost", "CAM",
    "Utility Cost", "Aggregator commission", "Marketing & advertisement"
]
metric = st.selectbox("Select Metric for Trend", metric_options)

filtered = df[(df['Store'].isin(stores)) & (df['FY'] == fy)]

# Pivot & KPIs
pivot = (
    filtered
    .pivot_table(index=['Store','Month'], columns='Metric', values='Amount', aggfunc='sum')
    .fillna(0)
)
pivot['Rent/Sales %']       = pivot['Rent']       / pivot['Net Sales'].replace(0, np.nan) * 100
pivot['Labor/Sales %']      = pivot['Labor Cost'] / pivot['Net Sales'].replace(0, np.nan) * 100
pivot['CAM/Sales %']        = pivot['CAM']        / pivot['Net Sales'].replace(0, np.nan) * 100
pivot['Utility/Sales %']    = pivot['Utility Cost']/ pivot['Net Sales'].replace(0, np.nan) * 100
pivot['Aggregator/Sales %'] = pivot['Aggregator commission'] / pivot['Net Sales'].replace(0, np.nan) * 100
pivot['Marketing/Sales %']  = pivot['Marketing & advertisement'] / pivot['Net Sales'].replace(0, np.nan) * 100

pivot['Contribution Margin'] = (
    pivot['Net Sales']
    - (
        pivot['Rent'] +
        pivot['Labor Cost'] +
        pivot['CAM'] +
        pivot['Utility Cost'] +
        pivot['Aggregator commission'] +
        pivot['Marketing & advertisement']
      )
)

# Same Store Sales Growth (YoY)
years = sorted(df['FY'].unique())
sssg = None
if len(years) >= 2:
    base_year    = years[-2]
    compare_year = years[-1]
    base = (
        df[(df['FY'] == base_year) & (df['Metric'] == 'Net Sales')]
        .groupby('Store')['Amount'].sum()
    )
    comp = (
        df[(df['FY'] == compare_year) & (df['Metric'] == 'Net Sales')]
        .groupby('Store')['Amount'].sum()
    )
    common_stores = base.index.intersection(comp.index)
    sssg = ((comp.loc[common_stores] - base.loc[common_stores]) / base.loc[common_stores]) * 100
    sssg = sssg.sort_values(ascending=False)

# Display
st.subheader("Cost Ratios & Contribution Margin")
st.dataframe(pivot.reset_index())

if sssg is not None:
    st.subheader("Same Store Sales Growth (YoY)")
    st.table(sssg)

st.subheader(f"{metric} Trend")
trend = (
    filtered[filtered['Metric'] == metric]
    .groupby('Month')['Amount']
    .sum()
)
fig, ax = plt.subplots()
trend.plot(ax=ax, marker='o')
ax.set_title(f"{metric} Trend ({fy})")
ax.set_ylabel("Amount (Lakhs)")
ax.set_xlabel("Month")
plt.xticks(rotation=45)
st.pyplot(fig)

# Download Excel
buffer = io.BytesIO()
pivot.to_excel(buffer, index=True, engine='openpyxl')
st.download_button(
    "Download Analysis (Excel)",
    data=buffer.getvalue(),
    file_name="qsr_mvp_analysis.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
