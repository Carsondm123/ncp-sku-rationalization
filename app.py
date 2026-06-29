import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="NCP · SKU Rationalization Console", layout="wide")
st.title("🧩 NCP · SKU Rationalization Console")
st.markdown("**ABCD Classification & Weighted Ranking Tool**")

@st.cache_data
def process_data(df):
    # Item Key View
    item = df.groupby('Itemkey').agg({
        'NetVal': 'sum',
        'GAL': 'sum',
        'Custkey': 'nunique',
        'Oeordno': 'nunique',
        'CUSTOM2': 'first'
    }).reset_index()
    
    item = item.rename(columns={
        'NetVal': 'Total_Sales',
        'GAL': 'Total_Gallons',
        'Custkey': 'Active_Customers',
        'Oeordno': 'Total_Orders',
        'CUSTOM2': 'Technology'
    }).fillna({'Technology': 'Unknown'})
    
    for col in ['Total_Sales', 'Total_Gallons', 'Total_Orders', 'Active_Customers']:
        maxv = item[col].max()
        item[col + '_Norm'] = item[col] / maxv if maxv > 0 else 0
    
    item['Weighted_Score'] = (
        item['Total_Sales_Norm'] * 0.40 +
        item['Total_Orders_Norm'] * 0.30 +
        item['Total_Gallons_Norm'] * 0.20 +
        item['Active_Customers_Norm'] * 0.10
    )
    
    item = item.sort_values('Weighted_Score', ascending=False).reset_index(drop=True)
    item['Rank'] = range(1, len(item)+1)
    total = item['Total_Sales'].sum()
    item['Cum_Sales_Pct'] = (item['Total_Sales'].cumsum() / total * 100).round(2)
    item['ABCD_Class'] = item['Cum_Sales_Pct'].apply(lambda x: 'A' if x <= 70 else 'B' if x <= 85 else 'C' if x <= 95 else 'D')
    
    # Customer View
    cust = df.groupby('Customer_Name').agg({
        'NetVal': 'sum',
        'Itemkey': 'nunique',
        'Oeordno': 'nunique'
    }).reset_index()
    cust = cust.rename(columns={'NetVal': 'Total_Sales', 'Itemkey': 'Unique_Items'})
    cust = cust.sort_values('Total_Sales', ascending=False).reset_index(drop=True)
    cust['Rank'] = range(1
