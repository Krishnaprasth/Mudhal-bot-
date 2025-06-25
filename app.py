import streamlit as st
import pandas as pd
import openai

# Load your cleaned data
@st.cache_data
def load_data():
    return pd.read_csv("QSR_CEO_CLEANED_FULL.csv")

df = load_data()

st.set_page_config(layout="wide")
st.title("📊 Store Metrics HQ – Your Query Buddy")

# Store conversation state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Get user input
user_q = st.text_input("Ask a question about store performance:", placeholder="e.g., Which store took the longest to turn EBITDA positive?", key="q")

# Track referenced store
def detect_store_name(q):
    for store in df["Store"].unique():
        if store.lower() in q.lower():
            return store
    return None

# GPT fallback logic
def gpt_fallback_query(user_q, last_store=None):
    store_hint = f" You may reference the store '{last_store}'." if last_store else ""
    prompt = f"""
You are helping answer CEO queries about QSR store data. Given this question:{store_hint}

\"{user_q}\"

Suggest the best Python function call from the following dataset:
- Columns: 'Net Sales', 'Gross margin', 'COGS (food +packaging)', 'Outlet EBITDA', 'Rent', 'CAM', 'Utility Cost', 'Aggregator commission', 'Marketing & advertisement', 'Other opex expenses', 'Month', 'Store'
- Use logical function names like get_store_pl(), get_top_n(), get_ratio(), get_slowest_to_profit(), etc.

Return only the function call. Do NOT explain it.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

# GPT commentary engine
def gpt_generate_commentary(store_df, topic):
    prompt = f"""
You are a data analyst for a QSR chain. Given the following store data:

{store_df.to_string(index=False)}

Write a short 2-3 sentence insight about: {topic}. Mention key patterns using available metrics.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

# Logic: Slowest to EBITDA positive
def get_slowest_to_profit():
    df_copy = df.copy()
    df_copy["Month_Parsed"] = pd.to_datetime(df_copy["Month"], format="%B %Y")
    df_sorted = df_copy.sort_values("Month_Parsed")

    store_groups = df_sorted.groupby("Store")
    time_to_profit = {}

    for store, group in store_groups:
        group = group.sort_values("Month_Parsed")
        group["Cum_EBITDA"] = group["Outlet EBITDA"].cumsum()
        profit_month = group[group["Cum_EBITDA"] > 0]
        if not profit_month.empty:
            start = group["Month_Parsed"].min()
            end = profit_month["Month_Parsed"].iloc[0]
            time_to_profit[store] = (end - start).days

    if not time_to_profit:
        return "❌ No stores turned profitable yet"

    slowest = max(time_to_profit, key=time_to_profit.get)
    days_taken = time_to_profit[slowest]
    store_df = df_sorted[df_sorted["Store"] == slowest].sort_values("Month_Parsed")
    commentary = gpt_generate_commentary(store_df, "why it took the store so long to turn EBITDA positive")
    return f"🐢 **{slowest}** took the longest to turn EBITDA positive – **{days_taken // 30} months approx**\n\n🧠 GPT Insight: {commentary}"

# Logic: Store P&L for FY24

def get_store_pl():
    # Reference latest question or history for store name
    store = detect_store_name(user_q) or (st.session_state.chat_history[-1]["store"] if st.session_state.chat_history else None)
    if not store:
        return "❌ Please mention a valid store name."
    
    df_copy = df.copy()
    df_copy["Month_Parsed"] = pd.to_datetime(df_copy["Month"], format="%B %Y")
    df_copy = df_copy[(df_copy["Month_Parsed"] >= "2023-04-01") & (df_copy["Month_Parsed"] <= "2024-03-31")]
    df_store = df_copy[df_copy["Store"].str.lower() == store.lower()].sort_values("Month_Parsed")

    if df_store.empty:
        return f"❌ No data found for {store} in FY24."

    st.dataframe(df_store[["Month", "Net Sales", "Gross margin", "Outlet EBITDA", "Rent"]].reset_index(drop=True))
    return f"📊 P&L data shown for **{store}** for FY24. Use download option for full table."

# Semantic match (basic)
def semantic_match(query):
    query_lower = query.lower()
    if "turn" in query_lower and "ebitda positive" in query_lower:
        return "get_slowest_to_profit()"
    if "p&l" in query_lower or "pl" in query_lower:
        return "get_store_pl()"
    return None

# Main logic
if user_q:
    last_store = detect_store_name(user_q) or (st.session_state.chat_history[-1]["store"] if st.session_state.chat_history else None)
    logic = semantic_match(user_q)
    if not logic:
        logic = gpt_fallback_query(user_q, last_store)

    try:
        with st.spinner("Thinking..."):
            result = eval(logic)
        st.session_state.chat_history.append({"q": user_q, "a": result, "store": last_store})
        st.markdown(result)
    except Exception as e:
        st.error(f"❌ Error running: {logic}\n{e}")

# Chat history display
if st.session_state.chat_history:
    st.markdown("---")
    for i, entry in enumerate(reversed(st.session_state.chat_history[-5:])):
        st.markdown(f"**Q{i+1}:** {entry['q']}")
        st.markdown(f"**A{i+1}:** {entry['a']}")
