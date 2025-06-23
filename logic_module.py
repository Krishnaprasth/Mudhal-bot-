def compute_ebitda(df):
    df['EBITDA'] = df['Net Sales'] - df[
        ['COGS (food +packaging)', 'Aggregator commission', 'Marketing & advertisement', 
         'store Labor Cost', 'Utility Cost', 'Other opex expenses']].sum(axis=1)
    return df[['Month', 'Store', 'EBITDA']]

def store_trend(df, store, metric):
    return df[df['Store'] == store][['Month', 'Store', metric]].sort_values(by='Month')

def top_store_by_metric(df, metric, month):
    df_month = df[df['Month'] == month]
    return df_month.sort_values(by=metric, ascending=False).head(1)[['Month', 'Store', metric]]

def get_mom_change(df, metric):
    df = df.sort_values(['Store', 'Month'])
    df['MoM Change'] = df.groupby('Store')[metric].pct_change()
    return df[['Month', 'Store', 'MoM Change']]

def get_yoy_growth(df, metric):
    df = df.sort_values(['Store', 'Month'])
    df['YoY Growth'] = df.groupby('Store')[metric].pct_change(periods=12)
    return df[['Month', 'Store', 'YoY Growth']]

def metric_percent_of_sales(df, metric):
    col_name = f"{metric} %"
    df[col_name] = 100 * df[metric] / df['Net Sales']
    return df[['Month', 'Store', col_name]]

def detect_anomaly(df, metric):
    mean = df[metric].mean()
    std = df[metric].std()
    return df[(df[metric] - mean).abs() > 3 * std][['Month', 'Store', metric]]

def profitability_ranking(df):
    return df.groupby('Store')['Net Sales'].sum().sort_values(ascending=False).reset_index().rename(columns={'Net Sales': 'Total Revenue'})
