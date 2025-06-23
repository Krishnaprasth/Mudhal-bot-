import pandas as pd

def get_highest_sales_store(df, month=None):
    if month:
        df = df[df['Month'].str.lower() == month.lower()]
    if 'Net Sales' not in df.columns:
        raise KeyError("'Net Sales' column not found in dataframe")
    return df.loc[df['Net Sales'].idxmax()][['Store', 'Net Sales']]

def get_store_sales_trend(df, store):
    if 'Net Sales' not in df.columns or 'Month' not in df.columns or 'Store' not in df.columns:
        raise KeyError("Required columns not found in dataframe")
    df = df[df['Store'].str.lower() == store.lower()]
    return df[['Month', 'Net Sales']].sort_values(by='Month')

def compute_ebitda(df):
    required_cols = ['Net Sales', 'COGS (food +packaging)', 'Aggregator commission',
                     'Marketing & advertisement', 'store Labor Cost', 'Utility Cost', 'Other opex expenses']
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"'{col}' not found in dataframe")
    df['EBITDA'] = df['Net Sales'] - df[['COGS (food +packaging)', 'Aggregator commission',
                                         'Marketing & advertisement', 'store Labor Cost',
                                         'Utility Cost', 'Other opex expenses']].sum(axis=1)
    return df[['Month', 'Store', 'EBITDA']]

def gross_margin_pct(df):
    if 'Gross margin' not in df.columns or 'Gross Sales' not in df.columns:
        raise KeyError("Required columns 'Gross margin' or 'Gross Sales' not found")
    df['Gross_Margin_Pct'] = 100 * df['Gross margin'] / df['Gross Sales']
    return df[['Month', 'Store', 'Gross_Margin_Pct']]

def top_n_stores_by_metric(df, metric, n=5):
    if metric not in df.columns:
        raise KeyError(f"'{metric}' not found in dataframe")
    return df.sort_values(by=metric, ascending=False).head(n)[['Month', 'Store', metric]]

def monthly_change(df, metric):
    if metric not in df.columns:
        raise KeyError(f"'{metric}' not found in dataframe")
    df = df.sort_values(['Store', 'Month'])
    df['MoM_Change'] = df.groupby('Store')[metric].pct_change()
    return df[['Month', 'Store', 'MoM_Change']]

def yearly_change(df, metric):
    if metric not in df.columns:
        raise KeyError(f"'{metric}' not found in dataframe")
    df = df.sort_values(['Store', 'Month'])
    df['YoY_Change'] = df.groupby('Store')[metric].pct_change(periods=12)
    return df[['Month', 'Store', 'YoY_Change']]

def detect_anomalies(df, metric):
    if metric not in df.columns:
        raise KeyError(f"'{metric}' not found in dataframe")
    mean = df[metric].mean()
    std = df[metric].std()
    return df[(df[metric] - mean).abs() > 3 * std][['Month', 'Store', metric]]
