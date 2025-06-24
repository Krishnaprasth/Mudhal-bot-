import streamlit as st
import pandas as pd
from pathlib import Path

# ========== DATA LOADING ==========
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(Path(__file__).parent / "QSR_CEO_CLEANED_FULL.csv")
        
        # Convert Month-Year to separate columns
        df[['MonthName','Year']] = df['Month'].str.split(' ', expand=True)
        df['Year'] = df['Year'].astype(int)
        
        # Calculate GST and sales channels (new logic)
        if 'Gross Sales' in df.columns and 'Net Sales' in df.columns:
            df['GST'] = df['Gross Sales'] - df['Net Sales']
            df['Offline Sales'] = df['GST'] / 0.05  # GST is 5% of offline sales
            df['Online Sales'] = df['Net Sales'] - df['Offline Sales']
        
        return df
    except Exception as e:
        st.error(f"Data loading failed: {str(e)}")
        return None

df = load_data()

# ========== SALES ANALYSIS ==========
def analyze_sales(month, year):
    if df is None:
        return None, None, None
    
    monthly_data = df[(df['MonthName'] == month) & (df['Year'] == year)]
    
    if monthly_data.empty:
        return None, None, None
    
    # GST and Channel calculations
    result = {
        'total_gst': monthly_data['GST'].sum(),
        'offline_sales': monthly_data['Offline Sales'].sum(),
        'online_sales': monthly_data['Online Sales'].sum(),
        'top_store': monthly_data.loc[monthly_data['Amount (₹ Lakhs)'].idxmax()]['Store']
    }
    
    return result

# ========== STREAMLIT UI ==========
st.title("🌯 QSR Sales Analyzer")
st.header("GST and Sales Channel Breakdown")

if df is not None:
    # Month-Year Selector
    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox("Select Month", df['MonthName'].unique())
    with col2:
        year = st.selectbox("Select Year", df['Year'].unique())
    
    if st.button("Analyze"):
        analysis = analyze_sales(month, year)
        
        if analysis:
            # Display Metrics
            st.subheader(f"Results for {month} {year}")
            
            cols = st.columns(3)
            cols[0].metric("Total GST", f"₹{analysis['total_gst']:,.2f}L")
            cols[1].metric("Offline Sales", f"₹{analysis['offline_sales']:,.2f}L")
            cols[2].metric("Online Sales", f"₹{analysis['online_sales']:,.2f}L")
            
            st.divider()
            st.subheader(f"🏆 Top Performing Store: {analysis['top_store']}")
            
            # Visualization
            channel_data = pd.DataFrame({
                'Channel': ['Offline', 'Online'],
                'Sales': [analysis['offline_sales'], analysis['online_sales']]
            })
            st.bar_chart(channel_data.set_index('Channel'))
        else:
            st.warning(f"No data available for {month} {year}")
else:
    st.error("Data not loaded. Please check your CSV file.")

# Data Preview
if df is not None:
    with st.expander("📊 View Processed Data"):
        st.dataframe(df)
