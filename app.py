import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from openai import OpenAI
import os
import io
from fpdf import FPDF
from PIL import Image
import base64
from io import BytesIO

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
        df.columns = [str(c).strip() for c in df.columns]

        # Normalize critical column names
        col_map = {}
        for col in df.columns:
            lower_col = col.lower()
            if 'store' in lower_col and 'name' in lower_col:
                col_map[col] = 'Store Name'
            elif 'net' in lower_col and 'sales' in lower_col:
                col_map[col] = 'Net Sales'
            elif 'gross' in lower_col and 'sales' in lower_col:
                col_map[col] = 'Gross Sales'
            elif 'cogs' in lower_col:
                col_map[col] = 'COGS'
            elif 'rent' in lower_col:
                col_map[col] = 'Rent'
            elif 'aggregator' in lower_col and 'commission' in lower_col:
                col_map[col] = 'Aggregator commission'
            elif 'online' in lower_col and 'sales' in lower_col:
                col_map[col] = 'Online Sales'
            elif 'ebitda' in lower_col:
                col_map[col] = 'EBITDA'
        df.rename(columns=col_map, inplace=True)

        if 'Store Name' in df.columns:
            df['Month'] = sheet
            df_all = pd.concat([df_all, df], ignore_index=True)
    return df_all

if uploaded_files:
    df_list = [load_data(file) for file in uploaded_files]
    df = pd.concat(df_list, ignore_index=True)
    st.success("✅ Data successfully loaded")

    st.sidebar.header("🔍 Smart Filters")
    store = st.sidebar.selectbox("Select Store", ["All"] + sorted(df['Store Name'].dropna().unique()))
    month = st.sidebar.selectbox("Select Month", ["All"] + sorted(df['Month'].dropna().unique()))

    filtered = df.copy()
    if store != "All":
        filtered = filtered[filtered['Store Name'] == store]
    if month != "All":
        filtered = filtered[filtered['Month'] == month]

    st.subheader("📈 Explore Raw Data")
    st.dataframe(filtered)

    if "Net Sales" in filtered.columns:
        plot_data = filtered.groupby("Month")["Net Sales"].sum().sort_index()
        st.line_chart(plot_data)

    st.subheader("🔮 Store Metrics Summary")
    col1, col2 = st.columns(2)
    with col1:
        if "COGS" in filtered.columns and "Net Sales" in filtered.columns:
            filtered["COGS %"] = (filtered["COGS"] / filtered["Net Sales"]) * 100
            st.metric("Avg COGS %", f"{filtered['COGS %'].mean():.2f}%")

        if "Rent" in filtered.columns and "Net Sales" in filtered.columns:
            filtered["Rent %"] = (filtered["Rent"] / filtered["Net Sales"]) * 100
            st.metric("Avg Rent %", f"{filtered['Rent %'].mean():.2f}%")

    with col2:
        if "Aggregator commission" in filtered.columns and "Online Sales" in filtered.columns:
            filtered["Agg Comm %"] = (filtered["Aggregator commission"] / filtered["Online Sales"]) * 100
            st.metric("Agg. Commission %", f"{filtered['Agg Comm %'].mean():.2f}%")

    if 'EBITDA' in filtered.columns:
        st.metric("Avg EBITDA", f"₹{filtered['EBITDA'].mean():,.0f}")

    # 🔥 COGS % Heatmap
    if 'COGS %' in df.columns:
        st.subheader("🔥 COGS % Heatmap")
        heatmap_df = df.dropna(subset=['Store Name', 'Month', 'COGS', 'Net Sales']).copy()
        heatmap_df['COGS %'] = (heatmap_df['COGS'] / heatmap_df['Net Sales']) * 100
        pivot = heatmap_df.pivot_table(index="Store Name", columns="Month", values="COGS %")
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.heatmap(pivot, annot=True, fmt=".1f", cmap="Reds", ax=ax)
        st.pyplot(fig)

    # 🥇 Ranking Stores by Net Sales
    if "Store Name" in df.columns and "Net Sales" in df.columns:
        st.subheader("🏆 Top Performing Stores by Revenue")
        top_rev = df.groupby("Store Name")["Net Sales"].sum().sort_values(ascending=False).head(10)
        st.bar_chart(top_rev)

    # 🧮 Ranking by EBITDA
    if "EBITDA" in df.columns:
        st.subheader("💰 Stores Ranked by EBITDA")
        top_ebitda = df.groupby("Store Name")["EBITDA"].sum().sort_values(ascending=False)
        st.bar_chart(top_ebitda.head(10))

    # 🤖 Ask GPT
    st.subheader("🤖 Ask any question about store performance")
    user_question = st.text_input("Enter your complex question below:")

    if user_question:
        clean_df = df.dropna(axis=1, how='all')
        clean_df = clean_df.loc[:, ~clean_df.columns.astype(str).str.contains("Unnamed", case=False)]
        schema = ', '.join(clean_df.columns)

        sample_df = clean_df.head(5).copy()
        sample_df = sample_df.applymap(lambda x: str(x)[:100])
        sample_data = sample_df.to_csv(index=False)

        prompt = f"""
You are a senior business analyst specializing in retail and QSR metrics.
Use the data below to detect trends, highlight anomalies, or surface opportunities.

Your job is to give:
- Revenue drivers
- Store-level profit issues
- Recommendations
- Growth opportunities
- Correlation between metrics (like high rent and low EBITDA)

Columns: {schema}
Sample Data (first 5 rows):
{sample_data}

User question: {user_question}
Answer:
"""

        with st.spinner("Thinking..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1500
                )
                output = response.choices[0].message.content
                st.markdown("### GPT Answer:")
                st.write(output)

                st.download_button("📥 Download Answer as TXT", data=output, file_name="answer.txt")

                excel_data = pd.DataFrame({"GPT Answer": [output]})
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    excel_data.to_excel(writer, index=False)
                st.download_button("📥 Download Answer as Excel", data=excel_buffer.getvalue(), file_name="gpt_answer.xlsx")

                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                for line in output.split('\n'):
                    pdf.multi_cell(0, 10, line)
                pdf_buffer = io.BytesIO()
                pdf.output(pdf_buffer)
                pdf_buffer.seek(0)
                st.download_button("📥 Download Answer as PDF", data=pdf_buffer, file_name="gpt_answer.pdf")

                if '|' in output or ',' in output:
                    try:
                        from io import StringIO
                        csv_guess = pd.read_csv(StringIO(output))
                        csv_bytes = csv_guess.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download as CSV", data=csv_bytes, file_name="gpt_output.csv")
                    except:
                        pass

            except Exception as e:
                st.error(f"OpenAI Error: {e}")

    st.divider()
    st.markdown("""
    ### 💡 Things you can ask this bot:
    - What is the best performing store by EBITDA over time?
    - How does rent as a % of sales trend for EGL store?
    - Which month had the lowest COGS % across all stores?
    - Compare Net Sales trends between ARK and EGL.
    - List stores with negative EBITDA.
    - Show months where marketing spend was highest.
    - Are there stores with high online sales but low profitability?
    - How do stores perform during festival months?
    """)
else:
    st.warning("Please upload one or more FY Excel files.")
