import streamlit as st
import pandas as pd
import plotly.express as px
import openai
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Retail Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {padding: 2rem;}
    .stTextInput input {font-size: 16px !important;}
    .stDataFrame {border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load data from CSV with error handling"""
    try:
        df = pd.read_csv('sales_data.csv')
        # Convert Month to datetime if needed
        if 'Month' in df.columns:
            df['Month'] = pd.to_datetime(df['Month'], format='%Y-%b', errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

def initialize_openai():
    """Initialize OpenAI API key"""
    if 'OPENAI_API_KEY' in st.secrets:
        openai.api_key = st.secrets['OPENAI_API_KEY']
    elif 'openai_api_key' in st.session_state:
        openai.api_key = st.session_state.openai_api_key
    else:
        openai.api_key = None

def analyze_with_openai(query, df):
    """Use OpenAI to interpret natural language queries"""
    if not openai.api_key:
        return None
        
    prompt = f"""
    Analyze this retail data query. Available columns: {', '.join(df.columns)}.
    Data sample: {df.head(2).to_dict()}

    Question: "{query}"

    Respond with JSON containing:
    - "filters": list of pandas query conditions
    - "group_by": columns for grouping
    - "aggregation": "sum/mean/max/min"
    - "viz_type": "line/bar/pie/table"
    - "interpretation": human-readable explanation
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        return eval(response.choices[0].message.content)
    except Exception as e:
        st.error(f"AI analysis failed: {str(e)}")
        return None

def apply_analysis(df, analysis):
    """Apply the analysis parameters to the dataframe"""
    try:
        # Apply filters
        if analysis.get('filters'):
            for condition in analysis['filters']:
                df = df.query(condition)
        
        # Apply grouping
        if analysis.get('group_by'):
            agg_func = analysis.get('aggregation', 'sum')
            df = df.groupby(analysis['group_by']).agg({'Amount': agg_func}).reset_index()
        
        return df
    except Exception as e:
        st.error(f"Data processing error: {str(e)}")
        return pd.DataFrame()

def render_visualization(df, viz_type):
    """Generate appropriate visualization"""
    if df.empty:
        return
        
    try:
        viz_type = viz_type.lower()
        if viz_type == 'line' and 'Month' in df.columns:
            fig = px.line(df, x='Month', y='Amount', 
                         color='Store' if 'Store' in df.columns else None,
                         title="Trend Analysis")
        elif viz_type == 'bar':
            fig = px.bar(df, x=df.columns[0], y='Amount',
                        color=df.columns[1] if len(df.columns) > 2 else None,
                        title="Comparative Analysis")
        elif viz_type == 'pie' and len(df) < 20:
            fig = px.pie(df, names=df.columns[0], values='Amount',
                        title="Distribution Analysis")
        else:
            fig = px.bar(df, x=df.columns[0], y='Amount')  # Default
            
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Visualization error: {str(e)}")

def show_data_summary(df):
    """Display key metrics summary"""
    if df.empty:
        return
        
    with st.expander("📊 Quick Summary", expanded=True):
        cols = st.columns(4)
        cols[0].metric("Total Stores", df['Store'].nunique())
        cols[1].metric("Time Period", 
                      f"{df['Month'].min().strftime('%b %Y')} to {df['Month'].max().strftime('%b %Y')}")
        cols[2].metric("Total Sales (Lakhs)", round(df['Amount'].sum(), 2))
        cols[3].metric("Avg Monthly Sales", round(df['Amount'].mean(), 2))

def main():
    st.title("🏪 Retail Analytics Dashboard")
    st.markdown("Analyze multi-store performance with natural language queries")
    
    # Load data
    df = load_data()
    if df.empty:
        st.warning("No data loaded. Please ensure sales_data.csv exists.")
        return
    
    # Initialize OpenAI
    initialize_openai()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        if not openai.api_key:
            api_key = st.text_input("Enter OpenAI API Key", type="password")
            if api_key:
                st.session_state.openai_api_key = api_key
                openai.api_key = api_key
                st.success("API key configured!")
        
        st.markdown("---")
        st.write("💡 Try these sample queries:")
        st.code("Show sales trend for ITPL store")
        st.code("Compare monthly sales between stores")
        st.code("Which store had highest sales last year?")
        st.markdown("---")
        st.write(f"Loaded {len(df)} records")
    
    # Main interface
    tab1, tab2 = st.tabs(["🔍 Smart Analysis", "📋 Data Explorer"])
    
    with tab1:
        query = st.text_input("Ask a question about your data:", 
                            placeholder="e.g. Show sales trends by store",
                            help="Use natural language to query your data")
        
        if st.button("Analyze", type="primary"):
            if query:
                with st.spinner("Analyzing your query..."):
                    analysis = analyze_with_openai(query, df)
                    
                    if analysis:
                        st.markdown(f"**Interpretation:** {analysis.get('interpretation', '')}")
                        result_df = apply_analysis(df, analysis)
                        
                        if not result_df.empty:
                            st.dataframe(result_df, use_container_width=True)
                            render_visualization(result_df, analysis.get('viz_type', 'table'))
                    else:
                        st.warning("Could not analyze query. Try standard view.")
    
    with tab2:
        st.header("Standard Data Exploration")
        show_data_summary(df)
        
        col1, col2 = st.columns(2)
        with col1:
            selected_metric = st.selectbox("Select Metric", df['Metric'].unique())
        with col2:
            selected_stores = st.multiselect("Select Stores", df['Store'].unique())
        
        filtered_df = df[df['Metric'] == selected_metric]
        if selected_stores:
            filtered_df = filtered_df[filtered_df['Store'].isin(selected_stores)]
        
        if not filtered_df.empty:
            fig = px.line(filtered_df, x='Month', y='Amount', color='Store',
                         title=f"{selected_metric} Trend")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(filtered_df.sort_values('Month'), use_container_width=True)

if __name__ == "__main__":
    main()
