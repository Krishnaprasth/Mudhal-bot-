import streamlit as st
import pandas as pd
import numpy as np
import re
import io
from openai import OpenAI

client = OpenAI()

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
    placeholder="e.g., Which store had the highest gross sales in December 2024?",
    key="q",
)

METRICS_MAP = {
    "gross sales": "gross_sales",
    "net sales": "net_sales",
    "sales": "net_sales",
    "revenue": "gross_sales",
    "ebitda": "outlet_ebitda",
    "rent": "rent",
    "cogs": "cogs_food_pluspackaging",
    "cost of goods sold": "cogs_food_pluspackaging",
    "labor cost": "store_labor_cost",
    "utility cost": "utility_cost",
    "marketing": "marketing_&_advertisement",
    "aggregator commission": "aggregator_commission",
    "cam": "cam",
    "other opex": "other_opex_expenses",
    "margin": "gross_margin",  # adjust if you have this column
}

STORE_NAMES = [s.lower() for s in df["store"].unique()]

def extract_metric(question):
    for key in METRICS_MAP.keys():
        if key in question:
            return METRICS_MAP[key]
    return None

def extract_store(question):
    for store in STORE_NAMES:
        if store in question:
            return store
    return None

def extract_time_period(question):
    month_year_match = re.search(r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t)?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s?(\d{2,4})", question, re.IGNORECASE)
    if month_year_match:
        month = month_year_match.group(1).capitalize()
        year = month_year_match.group(2)
        if len(year) == 2:
            year = "20" + year
        return f"{month} {year}"
    qfy_match = re.search(r"(q[1-4])\s*fy\s*(\d{2,4})", question, re.IGNORECASE)
    if qfy_match:
        quarter = qfy_match.group(1).upper()
        fy_year = qfy_match.group(2)
        if len(fy_year) == 2:
            fy_year = "20" + fy_year
        return f"{quarter} FY{fy_year[-2:]}"
    fy_year_match = re.search(r"fy\s*(\d{2,4})", question, re.IGNORECASE)
    if fy_year_match:
        fy_year = fy_year_match.group(1)
        if len(fy_year) == 2:
            fy_year = "20" + fy_year
        return f"FY{fy_year[-2:]}"
    return None

def filter_df_by_time(df_local, time_period):
    if time_period is None:
        return df_local
    if re.match(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", time_period):
        return df_local[df_local["month"].str.lower() == time_period.lower()]
    qfy_match = re.match(r"^(Q[1-4]) FY(\d{2})$", time_period, re.IGNORECASE)
    if qfy_match:
        quarter = qfy_match.group(1).upper()
        fy = int("20"+qfy_match.group(2))
        quarter_months = {
            "Q1": ["April", "May", "June"],
            "Q2": ["July", "August", "September"],
            "Q3": ["October", "November", "December"],
            "Q4": ["January", "February", "March"]
        }
        months = quarter_months.get(quarter, [])
        df_local["month_parsed"] = pd.to_datetime(df_local["month"], format="%B %Y", errors='coerce')
        return df_local[
            (df_local["month_parsed"].dt.year == fy) &
            (df_local["month_parsed"].dt.month.isin([pd.to_datetime(m, format="%B").month for m in months]))
        ]
    fy_match = re.match(r"^FY(\d{2})$", time_period, re.IGNORECASE)
    if fy_match:
        fy = int("20"+fy_match.group(1))
        df_local["month_parsed"] = pd.to_datetime(df_local["month"], format="%B %Y", errors='coerce')
        start = pd.Timestamp(year=fy, month=4, day=1)
        end = pd.Timestamp(year=fy+1, month=3, day=31)
        return df_local[(df_local["month_parsed"] >= start) & (df_local["month_parsed"] <= end)]
    return df_local

def generate_commentary(store, metric, df_filtered):
    avg_val = df_filtered[metric].mean()
    max_val = df_filtered[metric].max()
    max_month = df_filtered.loc[df_filtered[metric].idxmax()]["month"] if not df_filtered.empty else "N/A"
    return (
        f"The average {metric.replace('_',' ')} for store {store.upper()} in the selected period is ₹{avg_val:,.2f}. "
        f"The highest was ₹{max_val:,.2f} in {max_month}."
    )

def dynamic_query_answer(question):
    question_lc = question.lower()

    metric = extract_metric(question_lc)
    store = extract_store(question_lc)
    time_period = extract_time_period(question_lc)

    if metric is None:
        return None, None, "Sorry, I couldn't identify the metric you're asking about."

    df_filtered = df.copy()
    if store:
        df_filtered = df_filtered[df_filtered["store"].str.lower() == store]
    df_filtered = filter_df_by_time(df_filtered, time_period)

    if df_filtered.empty:
        return None, None, f"No data available for your query parameters (store: {store or 'all'}, period: {time_period or 'all'})."

    if ("which" in question_lc or "what" in question_lc) and ("highest" in question_lc or "max" in question_lc):
        if not store:
            rev_by_store = df_filtered.groupby("store")[metric].sum()
            top_store = rev_by_store.idxmax()
            top_val = rev_by_store.max()
            answer_text = f"🏆 Highest {metric.replace('_',' ')} store in the selected period is **{top_store.upper()}** with total ₹{top_val:,.2f}."
            commentary = "This store has led the metric among peers for the specified time frame."
            return answer_text, None, commentary

    total = df_filtered[metric].sum()
    answer_text = f"The total {metric.replace('_',' ')} for "
    if store:
        answer_text += f"store **{store.upper()}** "
    else:
        answer_text += "all stores "
    if time_period:
        answer_text += f"during **{time_period}** "
    answer_text += f"is ₹{total:,.2f}."

    commentary = generate_commentary(store or "all stores", metric, df_filtered)
    return answer_text, df_filtered[["month","store",metric]], commentary

def to_excel_bytes(df):
    output = io.BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

def display_answer(answer_text, df_result=None, commentary=None):
    st.markdown(answer_text)
    if commentary:
        st.markdown(f"🧠 Insight: {commentary}")
    if df_result is not None:
        st.dataframe(df_result)
        excel_bytes = to_excel_bytes(df_result)
        st.download_button(
            label="📥 Download data as Excel",
            data=excel_bytes,
            file_name="query_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def gpt_fallback(user_q):
    df_sample = df.head(20).to_csv(index=False)
    columns = list(df.columns)
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

    def clean_code(code_str):
        lines = code_str.strip().splitlines()
        while lines and (lines[0].strip().startswith("```") or lines[0].strip().lower().startswith("```python") or lines[0].strip().lower() == "code:" or lines[0].strip() == ""):
            lines.pop(0)
        while lines and lines[-1].strip().startswith("```"):
            lines.pop()
        return "\n".join(lines).strip()

    if "---SUMMARY---" in content:
        code, summary = content.split("---SUMMARY---", 1)
    else:
        code, summary = content, ""

    code = clean_code(code)

    local_vars = {"df_sample": df.copy()}
    try:
        exec(code, {"__builtins__": None, "pd": pd, "np": np}, local_vars)
        result = local_vars.get("result", None)

        if isinstance(result, pd.DataFrame):
            answer_text = summary or "Here is the data you requested:"
            display_answer(answer_text, result)
            return answer_text, result, summary

        elif isinstance(result, pd.Series):
            if result.empty:
                answer_text = "No matching data found for your query."
            else:
                unique_vals = result.dropna().unique()
                if len(unique_vals) == 1:
                    answer_text = str(unique_vals[0])
                else:
                    answer_text = ", ".join(str(x) for x in unique_vals)
            if summary:
                answer_text += f"\n\n🧠 Insight: {summary}"
            st.markdown(answer_text)
            return answer_text, None, summary

        elif result is not None:
            answer_text = str(result)
            if summary:
                answer_text += f"\n\n🧠 Insight: {summary}"
            st.markdown(answer_text)
            return answer_text, None, summary

        else:
            answer_text = "No result returned from GPT code."
            st.markdown(answer_text)
            return answer_text, None, summary

    except Exception as e:
        st.error(f"Error executing GPT code: {e}")
        st.text(f"Code tried to execute:\n{code}")
        return f"Error executing GPT code: {e}", None, None

def main():
    if user_q:
        answer_text, df_result, commentary = dynamic_query_answer(user_q)
        if answer_text is None:
            answer_text, df_result, commentary = gpt_fallback(user_q)
        display_answer(answer_text, df_result, commentary)
        st.session_state.chat_history.append({"q": user_q, "a": answer_text})

    if st.session_state.chat_history:
        st.markdown("---")
        for i, entry in enumerate(reversed(st.session_state.chat_history[-5:])):
            st.markdown(f"**Q{i+1}:** {entry['q']}")
            st.markdown(f"**A{i+1}:** {entry['a']}")

if __name__ == "__main__":
    main()
