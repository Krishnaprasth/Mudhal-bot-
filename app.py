import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
from io import StringIO
import re

@st.cache_data
def load_data():
    csv_data = open("cleaned_store_data_embedded.csv", "r").read()
    return pd.read_csv(StringIO(csv_data))

df_raw = load_data()

# Fix Month formatting like '24-Apr' → 'Apr 24'
df_raw['Month'] = pd.to_datetime(df_raw['Month'], errors='coerce').dt.strftime('%b %y')
df_raw = df_raw[df_raw['Metric'].notna() & df_raw['Amount'].notna()]

try:
    df = df_raw.pivot_table(index=['Month', 'Store'], columns='Metric', values='Amount').reset_index()
except Exception as e:
    st.error("Data pivoting failed. Please check if the raw CSV is clean.")
    st.stop()

api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else "sk-your-key"
client = OpenAI(api_key=api_key)

st.set_page_config(layout="wide")
st.markdown("""
    <style>
    textarea, .stTextInput input {font-size: 18px;}
    .stDownloadButton button {margin-top: 10px;}
    .stDataFrame, .dataframe {margin-bottom: 1rem;}
    </style>
    """, unsafe_allow_html=True)

query = st.text_input("", placeholder="Ask a store performance question...", label_visibility="collapsed")

if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

if query:
    try:
        months = df['Month'].dropna().unique().tolist()
        stores = df['Store'].dropna().unique().tolist()

        def normalize(text):
            return re.sub(r"[^a-z0-9]", "", text.lower())

        query_norm = normalize(query)
        query_months = [m for m in months if normalize(m) in query_norm or normalize(m).replace(" ", "") in query_norm]
        query_stores = [s for s in stores if normalize(s) in query_norm]

        filtered_df = df.copy()
        if query_months:
            filtered_df = filtered_df[filtered_df['Month'].isin(query_months)]
        if query_stores:
            filtered_df = filtered_df[filtered_df['Store'].isin(query_stores)]

        if not query_months and not query_stores:
            filtered_df = filtered_df.head(200)

        if filtered_df.empty:
            st.warning("No data found matching the filters in your question. Please check store/month spelling.")
        else:
            response_shown = False

            logic_blocks = [
                ("highest sales", lambda df: df[df['Gross Sales'] == df['Gross Sales'].max()][['Month', 'Store', 'Gross Sales']], "top_store_sales.csv"),
                ("lowest sales", lambda df: df[df['Gross Sales'] == df['Gross Sales'].min()][['Month', 'Store', 'Gross Sales']], "lowest_store_sales.csv"),
                ("sort by gross sales", lambda df: df.sort_values(by='Gross Sales', ascending=False)[['Month', 'Store', 'Gross Sales']], "sorted_gross_sales.csv"),
                ("highest revenue store across all months", lambda df: pd.DataFrame({"Store": [df.groupby('Store')['Net Sales'].sum().idxmax()], "Total Net Sales": [df.groupby('Store')['Net Sales'].sum().max()]}), "highest_total_revenue.csv"),
                ("highest ebitda", lambda df: df.assign(EBITDA=df['Net Sales'] - (df['COGS (food +packaging)'] + df['Marketing & advertisement'] + df['Other opex expenses'] + df['Utility Cost'] + df['store Labor Cost'] + df['Aggregator commission'] + df['Rent'] + df['CAM'])).query("EBITDA == EBITDA.max()")[["Month", "Store", "EBITDA"]], "top_ebitda.csv"),
                ("lowest ebitda", lambda df: df.assign(EBITDA=df['Net Sales'] - (df['COGS (food +packaging)'] + df['Marketing & advertisement'] + df['Other opex expenses'] + df['Utility Cost'] + df['store Labor Cost'] + df['Aggregator commission'] + df['Rent'] + df['CAM'])).query("EBITDA == EBITDA.min()")[["Month", "Store", "EBITDA"]], "lowest_ebitda.csv"),
                ("highest margin", lambda df: df.assign(**{"Margin %": 100 * df['Gross margin'] / df['Net Sales']}).query("`Margin %` == `Margin %`.max()")[["Month", "Store", "Margin %"]], "top_margin.csv"),
                ("lowest margin", lambda df: df.assign(**{"Margin %": 100 * df['Gross margin'] / df['Net Sales']}).query("`Margin %` == `Margin %`.min()")[["Month", "Store", "Margin %"]], "lowest_margin.csv"),
                ("rent trend", lambda df: df.groupby("Month")["Rent"].sum().reset_index(), "monthly_rent_trend.csv"),
                ("cost breakdown", lambda df: df[["Store", "COGS (food +packaging)", "store Labor Cost", "Utility Cost", "Marketing & advertisement", "Other opex expenses"]].groupby("Store").sum().reset_index(), "cost_breakdown.csv"),
                ("ebitda trend", lambda df: df.assign(EBITDA=df['Net Sales'] - (df['COGS (food +packaging)'] + df['Marketing & advertisement'] + df['Other opex expenses'] + df['Utility Cost'] + df['store Labor Cost'] + df['Aggregator commission'] + df['Rent'] + df['CAM'])).groupby("Month")["EBITDA"].sum().reset_index(), "ebitda_trend.csv"),
                ("gross sales trend", lambda df: df.groupby("Month")["Gross Sales"].sum().reset_index(), "gross_sales_trend.csv"),
                ("anomaly", lambda df: df[df['Gross Sales'] > df['Gross Sales'].mean() + 2 * df['Gross Sales'].std()][["Month", "Store", "Gross Sales"]], "anomalies.csv"),
                ("highest labor cost", lambda df: df[df['store Labor Cost'] == df['store Labor Cost'].max()][['Month', 'Store', 'store Labor Cost']], "top_labor_cost.csv"),
                ("lowest labor cost", lambda df: df[df['store Labor Cost'] == df['store Labor Cost'].min()][['Month', 'Store', 'store Labor Cost']], "lowest_labor_cost.csv"),
                ("top utilities", lambda df: df[df['Utility Cost'] == df['Utility Cost'].max()][['Month', 'Store', 'Utility Cost']], "top_utility_cost.csv")
            ]

            for keyword, logic_fn, filename in logic_blocks:
                if not response_shown and all(k in query.lower() for k in keyword.split()):
                    try:
                        df_output = logic_fn(filtered_df)
                        if df_output.empty and len(filtered_df) == 1:
                            df_output = filtered_df
                        st.markdown(f"### 🔍 {keyword.title()} Result")
                        st.dataframe(df_output, use_container_width=True)
                        st.download_button("📥 Download as CSV", df_output.to_csv(index=False), file_name=filename)
                        st.session_state.qa_history.append((query, df_output.to_markdown(index=False)))
                        response_shown = True
                    except Exception as e:
                        st.warning(f"Logic failed: {e}")

            if not response_shown:
                df_str = filtered_df.fillna(0).to_string(index=False)
                user_message = f"DataFrame:\n{df_str}\n\nNow answer this question using pandas dataframe logic only:\n{query}"

                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful data analyst for a QSR company. You analyze the provided pandas dataframe and return structured answers, especially tables if relevant. Keep the markdown tight, crisp and visual if useful."},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.1
                )
                answer = response.choices[0].message.content
                st.markdown(answer)

                if "|" in answer:
                    import io
                    try:
                        df_temp = pd.read_csv(io.StringIO(answer.split("\n\n")[-1]), sep="|").dropna(axis=1, how="all")
                        if len(df_temp.columns) >= 2:
                            fig2, ax2 = plt.subplots()
                            df_temp.iloc[:, 1:].plot(kind="bar", ax=ax2)
                            ax2.set_title("Visual Summary")
                            st.pyplot(fig2)
                            st.download_button("📥 Download Answer CSV", df_temp.to_csv(index=False), file_name="answer_table.csv")
                    except: pass

                st.session_state.qa_history.append((query, answer))
    except Exception as e:
        st.error(f"Error: {str(e)}")

with st.sidebar:
    st.markdown("### 🔁 Past Questions")
    for q, a in st.session_state.qa_history[-10:]:
        st.markdown(f"**Q:** {q}\n\n*A:* {a}")
