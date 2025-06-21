import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
import os

st.set_page_config(layout="wide")
st.title("📊 California Burrito: Store Performance GPT Assistant")

# 🔑 Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔁 File upload section (multi-file)
uploaded_files = st.file_uploader("Upload one or more FY Excel files", type="xlsx", accept_multiple_files=True)

@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    df_all = pd.DataFrame()
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        df.columns = [str(c).strip() for c in df.columns]  # Clean col names
        if 'Store Name' in df.columns:
            df['Month'] = sheet
            df_all = pd.concat([df_all, df], ignore_index=True)
    return df_all

# 🔄 Load and combine all uploaded files
if uploaded_files:
    df_list = []
    for file in uploaded_files:
        df_loaded = load_data(file)
        df_list.append(df_loaded)

    df = pd.concat(df_list, ignore_index=True)
    st.success("✅ Data successfully loaded")

    # 🤖 Ask GPT
    st.subheader("🤖 Ask any question about store performance")
    user_question = st.text_input("Enter your complex question below:")

    if user_question:
        # Clean data before GPT
        clean_df = df.dropna(axis=1, how='all')
        clean_df = clean_df.loc[:, ~clean_df.columns.str.contains("Unnamed", case=False)]
        schema = ', '.join(clean_df.columns)

        sample_df = clean_df.head(5).copy()
        sample_df = sample_df.applymap(lambda x: str(x)[:100])
        sample_data = sample_df.to_csv(index=False)

        prompt = f"""
You are a data analyst bot for a QSR chain. You are given performance data of multiple stores over different months and years.
Use your reasoning to analyze the data and answer business questions logically and step-by-step.

Columns: {schema}
Sample Data (first 5 rows):
{sample_data}

Question: {user_question}
Answer:
"""

        with st.spinner("Thinking..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=600
                )
                output = response.choices[0].message.content
                st.markdown("### GPT Answer:")
                st.write(output)
            except Exception as e:
                st.error(f"OpenAI Error: {e}")

    # 📊 Explore Raw Data
    st.divider()
    st.subheader("📈 Explore Raw Data")

    store = st.selectbox("Select Store", ["All"] + sorted(df['Store Name'].dropna().unique()))
    month = st.selectbox("Select Month", ["All"] + sorted(df['Month'].dropna().unique()))

    filtered = df.copy()
    if store != "All":
        filtered = filtered[filtered['Store Name'] == store]
    if month != "All":
        filtered = filtered[filtered['Month'] == month]

    st.dataframe(filtered)

    if "Net Sales" in filtered.columns:
        plot_data = filtered.groupby("Month")["Net Sales"].sum().sort_index()
        st.line_chart(plot_data)

else:
    st.warning("Please upload one or more FY Excel files.")
