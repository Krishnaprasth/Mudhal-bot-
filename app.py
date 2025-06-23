import streamlit as st
import pandas as pd
import openai
import matplotlib.pyplot as plt
import io

st.set_page_config(layout="wide")

# --- Load Data ---
@st.cache_data
def load_data():
    return pd.read_csv("cleaned_store_data_final.csv")

df = load_data()

# --- Sidebar ---
st.sidebar.title("🧠 QSR CEO Q&A Bot")
openai.api_key = st.secrets["OPENAI_API_KEY"]

if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

# --- Title ---
st.markdown("<h2 style='text-align:center;'>QSR CEO Intelligence Bot</h2>", unsafe_allow_html=True)

# --- User Question ---
user_question = st.text_input("Ask any store-level performance question:", placeholder="E.g. Which store had highest revenue in May 2025?")

# --- GPT Logic Bank ---
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

        (f"gross margin % for {metric.lower()}",
         lambda df: df.assign(Gross_Margin_Pct=100 * df['Gross margin'] / df['Gross Sales'])[["Month", "Store", "Gross_Margin_Pct"]],
         f"gross_margin_pct.csv"),

        (f"store profitability ranking by {metric.lower()}",
         lambda df: df.groupby('Store')['Net Sales'].sum().sort_values(ascending=False).reset_index().rename(columns={'Net Sales': 'Total Revenue'}),
         f"profit_ranking_{metric_safe}.csv")
    ])

# --- Bot Logic ---
if user_question:
    user_input = user_question.lower()
    answer = None
    matched_logic = None

    for phrase, logic_func, fname in logic_blocks:
        if phrase in user_input:
            try:
                answer_df = logic_func(df)
                answer = f"Answer for: **{phrase}**"
                matched_logic = (answer_df, fname)
                break
            except Exception as e:
                answer = f"⚠️ Logic failed: {str(e)}"
                break

    if matched_logic:
        df_temp, fname = matched_logic
        st.write(answer)
        st.dataframe(df_temp)

        # Optional Chart
        if df_temp.shape[1] == 3:
            fig, ax = plt.subplots()
            df_temp.plot(x="Store", y=df_temp.columns[-1], kind="bar", ax=ax)
            st.pyplot(fig)

        # Download
        csv_bytes = df_temp.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", data=csv_bytes, file_name=fname, mime="text/csv")

    else:
        # Fallback to GPT
        with st.spinner("Thinking..."):
            try:
                messages = [
                    {"role": "system", "content": "You are a helpful business analyst."},
                    {"role": "user", "content": f"DataFrame:\n{df.head(100).to_csv(index=False)}\n\nQuestion: {user_question}"}
                ]
                completion = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=messages,
                    temperature=0.2
                )
                response = completion.choices[0].message.content.strip()
                st.markdown(response)
            except Exception as e:
                st.error(f"GPT failed: {e}")

    st.session_state.qa_history.append((user_question, answer))

# --- Sidebar History ---
if st.session_state.qa_history:
    st.sidebar.markdown("### 🕓 Q&A History")
    for q, a in reversed(st.session_state.qa_history[-10:]):
        st.sidebar.markdown(f"**Q:** {q}  \n**A:** {a or 'No answer'}")

