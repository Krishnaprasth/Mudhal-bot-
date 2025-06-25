import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

# Load your cleaned data from the correct CSV file
@st.cache_data
def load_data():
    return pd.read_csv("QSR_CEO_CLEANED_READY.csv")

df = load_data()

st.set_page_config(layout="wide")
st.title("📊 Store Metrics HQ – Your Query Buddy")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_q = st.text_input(
    "Ask a question about store performance:",
    placeholder="e.g., Which store took the longest to turn EBITDA positive?",
    key="q",
)

def detect_store_name(q):
    for store in df["store"].unique():
        if store.lower() in q.lower():
            return store
    return None

def gpt_fallback_query(user_q, df_sample, columns):
    prompt = f"""
You are a data analyst for a restaurant chain with monthly store data.

Columns: {columns}
Sample data (CSV):
{df_sample}

User question: "{user_q}"

Write Python pandas code (using variable 'df_sample' as the DataFrame) to answer the question.
Assign your final result (DataFrame or scalar) to a variable named 'result'.

After the code, provide a brief summary of findings separated by a line '---SUMMARY---'.

Return only the code and the summary.
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    content = response.choices[0].message.content

    if "---SUMMARY---" in content:
        code, summary = content.split("---SUMMARY---", 1)
    else:
        code, summary = content, ""

    return code.strip(), summary.strip()

def safe_exec(code_str, local_vars):
    exec(code_str, {"__builtins__": None, "pd": pd, "np": np}, local_vars)

def execute_gpt_code(user_q):
    df_sample = df.head(20).to_csv(index=False)
    columns = list(df.columns)

    code, summary = gpt_fallback_query(user_q, df_sample, columns)

    local_vars = {"df_sample": df.copy()}
    try:
        safe_exec(code, local_vars)
        result = local_vars.get("result", None)
        if isinstance(result, pd.DataFrame):
            st.dataframe(result)
        else:
            st.write(result)
    except Exception as e:
        st.error(f"Error executing GPT code: {e}")
        st.text(f"Code tried to execute:\n{code}")

    if summary:
        st.markdown(f"**Insight:** {summary}")

def get_slowest_to_profit():
    df_copy = df.copy()
    df_copy["month_parsed"] = pd.to_datetime(df_copy["month"], format="%B %Y")
    df_sorted = df_copy.sort_values("month_parsed")

    time_to_profit = {}
    for store, group in df_sorted.groupby("store"):
        group = group.sort_values("month_parsed")
        group["cum_ebitda"] = group["outlet_ebitda"].cumsum()
        profit_month = group[group["cum_ebitda"] > 0]
        if not profit_month.empty:
            start = group["month_parsed"].min()
            end = profit_month["month_parsed"].iloc[0]
            time_to_profit[store] = (end - start).days

    if not time_to_profit:
        return "❌ No stores turned profitable yet"

    slowest = max(time_to_profit, key=time_to_profit.get)
    days_taken = time_to_profit[slowest]
    store_df = df_sorted[df_sorted["store"] == slowest].sort_values("month_parsed")
    commentary = gpt_generate_commentary(store_df, "why it took the store so long to turn EBITDA positive")
    return f"🐢 **{slowest}** took the longest to turn EBITDA positive – **{days_taken // 30} months approx**\n\n🧠 GPT Insight: {commentary}"

def gpt_generate_commentary(store_df, topic):
    prompt = f"""
You are a data analyst for a QSR chain. Given the following store data:

{store_df.to_string(index=False)}

Write a short 2-3 sentence insight about: {topic}. Mention key patterns using available metrics.
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()

def get_store_pl():
    store = detect_store_name(user_q) or (st.session_state.chat_history[-1]["store"] if st.session_state.chat_history else None)
    if not store:
        return "❌ Please mention a valid store name."

    df_copy = df.copy()
    df_copy["month_parsed"] = pd.to_datetime(df_copy["month"], format="%B %Y")
    df_copy = df_copy[(df_copy["month_parsed"] >= "2023-04-01") & (df_copy["month_parsed"] <= "2024-03-31")]
    df_store = df_copy[df_copy["store"].str.lower() == store.lower()].sort_values("month_parsed")

    if df_store.empty:
        return f"❌ No data found for {store} in FY24."

    st.dataframe(df_store[["month", "net_sales", "gross_sales", "outlet_ebitda", "rent"]].reset_index(drop=True))
    return f"📊 P&L data shown for **{store}** for FY24. Use download option for full table."

def semantic_match(query):
    q = query.lower()
    if "turn" in q and "ebitda positive" in q:
        return "get_slowest_to_profit()"
    if "p&l" in q or "pl" in q:
        return "get_store_pl()"
    return None

if user_q:
    last_store = detect_store_name(user_q) or (st.session_state.chat_history[-1]["store"] if st.session_state.chat_history else None)
    logic = semantic_match(user_q)
    if logic:
        with st.spinner("Running structured logic..."):
            result = eval(logic)
        st.session_state.chat_history.append({"q": user_q, "a": result, "store": last_store})
        st.markdown(result)
    else:
        with st.spinner("Generating answer with GPT fallback..."):
            execute_gpt_code(user_q)
        st.session_state.chat_history.append({"q": user_q, "a": "Answered by GPT fallback", "store": last_store})

if st.session_state.chat_history:
    st.markdown("---")
    for i, entry in enumerate(reversed(st.session_state.chat_history[-5:])):
        st.markdown(f"**Q{i+1}:** {entry['q']}")
        st.markdown(f"**A{i+1}:** {entry['a']}")
