import streamlit as st
import pandas as pd
import openai
from tabulate import tabulate

st.set_page_config(layout="centered")
st.markdown("""
    <style>
        .block-container {padding-top: 1rem;}
        header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_data
def load_data():
    return pd.read_csv("cleaned_store_data_embedded.csv")

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"❌ Could not load data: {e}")
    st.stop()

try:
    df_pivot = df_raw.pivot_table(
        index=["Month", "Store"],
        columns="Metric",
        values="Amount"
    ).reset_index()
except Exception as e:
    st.error(f"❌ Pivoting failed: {e}")
    st.stop()

months_text = ", ".join(sorted(df_raw["Month"].dropna().unique()))
stores_text = ", ".join(sorted(df_raw["Store"].dropna().unique()))
preview_table = tabulate(df_pivot.head(), headers="keys", tablefmt="github", showindex=False)

if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

with st.sidebar:
    st.markdown("### 🕑 History")
    for i, (q, a) in enumerate(reversed(st.session_state.qa_history[-10:]), 1):
        st.markdown(f"**{i}. {q}**")
        st.markdown(f"➤ {a[:500]}" if isinstance(a, str) else "➤ [table response]")

# -------------- Logic Engine Blocks ----------------
def logic_gm_percent_top_month():
    df_gm = df_raw.pivot_table(index="Month", columns="Metric", values="Amount", aggfunc="sum").reset_index()
    df_gm = df_gm.dropna(subset=["Net Sales", "Gross margin"])
    df_gm["Gross Margin %"] = df_gm["Gross margin"] / df_gm["Net Sales"] * 100
    best_month = df_gm.loc[df_gm["Gross Margin %"].idxmax()]
    return f"{best_month['Month']}, {best_month['Gross Margin %']:.2f}%", df_gm.set_index("Month")["Gross Margin %"]

def logic_top_ebitda_stores(month="May 24", top_n=5):
    df_month = df_pivot[df_pivot["Month"] == month].copy()
    df_month["EBITDA %"] = df_month["Outlet EBITDA"] / df_month["Net Sales"] * 100
    df_month = df_month.sort_values("EBITDA %", ascending=False).head(top_n)
    return f"🏆 Top {top_n} stores by EBITDA % in {month}", df_month[["Store", "EBITDA %"]].set_index("Store")

def logic_top_ebitda_store_overall():
    df_wide = df_raw.pivot_table(index=["Month", "Store"], columns="Metric", values="Amount", aggfunc="sum").reset_index()
    for col in ["COGS (food +packaging)", "Marketing & advertisement", "Other opex expenses", "Utility Cost", "store Labor Cost"]:
        if col not in df_wide.columns:
            df_wide[col] = 0
    df_wide["EBITDA"] = df_wide["Net Sales"] - df_wide[["COGS (food +packaging)", "Marketing & advertisement", "Other opex expenses", "Utility Cost", "store Labor Cost"]].sum(axis=1)
    store_ebitda_total = df_wide.groupby("Store")["EBITDA"].sum()
    top_store = store_ebitda_total.idxmax()
    top_value = store_ebitda_total.max()
    return f"{top_store}, ₹{top_value/1e7:.2f} Cr", store_ebitda_total.reset_index().sort_values("EBITDA", ascending=False)

logic_map = {
    "highest gross margin": logic_gm_percent_top_month,
    "top 5 stores by ebitda": lambda: logic_top_ebitda_stores("May 24"),
    "top stores by ebitda": lambda: logic_top_ebitda_stores("May 24"),
    "store with highest ebitda overall": logic_top_ebitda_store_overall,
    "highest ebitda overall": logic_top_ebitda_store_overall,
}

user_query = st.chat_input("Ask your store performance question")

if user_query:
    with st.spinner("Analyzing..."):
        try:
            matched = False
            for key in logic_map:
                if key in user_query.lower():
                    result_text, result_data = logic_map[key]()
                    st.success(result_text)
                    st.dataframe(result_data)
                    st.session_state.qa_history.append((user_query, result_text))
                    matched = True
                    break

            if not matched:
                prompt = f"""
You are a data analyst for a QSR chain. The dataset contains store-level monthly financial performance metrics.

Available months: {months_text}
Available stores: {stores_text}

DataFrame structure:
{preview_table}

User asked: "{user_query}"

Use only available data. If a month or store isn't in the dataset, mention that clearly.
Prefer concise summaries, tables, or code suggestions. Do not assume missing values are zero.
"""

                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful data analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                )

                answer = response.choices[0].message.content
                st.markdown(answer)
                st.session_state.qa_history.append((user_query, answer))

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
