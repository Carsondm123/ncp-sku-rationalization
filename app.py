import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="NCP · SKU Rationalization Console", layout="wide")
st.title("🧩 NCP · SKU Rationalization Console")
st.markdown("**ABCD Classification & Weighted Ranking Tool**")

uploaded_file = st.file_uploader("Upload your Sales Data Excel file", type=["xlsx"])

if uploaded_file:
    with st.spinner("Analyzing data..."):
        df = pd.read_excel(uploaded_file)
        
        grouped = df.groupby('Itemkey').agg({
            'NetVal': 'sum',
            'GAL': 'sum',
            'Custkey': 'nunique',
            'Oeordno': 'nunique',
            'CUSTOM2': 'first'
        }).reset_index()
        
        grouped = grouped.rename(columns={
            'NetVal': 'Total_Sales',
            'GAL': 'Total_Gallons',
            'Custkey': 'Active_Customers',
            'Oeordno': 'Total_Orders',
            'CUSTOM2': 'Technology'
        }).fillna({'Technology': 'Unknown'})
        
        for col in ['Total_Sales', 'Total_Gallons', 'Total_Orders', 'Active_Customers']:
            maxv = grouped[col].max()
            grouped[col + '_Norm'] = grouped[col] / maxv if maxv > 0 else 0
        
        grouped['Weighted_Score'] = (
            grouped['Total_Sales_Norm'] * 0.40 +
            grouped['Total_Orders_Norm'] * 0.30 +
            grouped['Total_Gallons_Norm'] * 0.20 +
            grouped['Active_Customers_Norm'] * 0.10
        )
        
        grouped = grouped.sort_values('Weighted_Score', ascending=False).reset_index(drop=True)
        grouped['Rank'] = range(1, len(grouped)+1)
        
        total_sales = grouped['Total_Sales'].sum()
        grouped['Cum_Sales_Pct'] = (grouped['Total_Sales'].cumsum() / total_sales * 100).round(2)
        grouped['ABCD_Class'] = grouped['Cum_Sales_Pct'].apply(lambda x: 'A' if x <= 70 else 'B' if x <= 85 else 'C' if x <= 95 else 'D')
        
        final = grouped[['Rank', 'Itemkey', 'Technology', 'Total_Sales', 'Total_Gallons', 
                        'Total_Orders', 'Active_Customers', 'Weighted_Score', 
                        'ABCD_Class', 'Cum_Sales_Pct']].round(4)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total SKUs", len(final))
        col2.metric("Total Sales", f"${final['Total_Sales'].sum():,}")
        col3.metric("A Items", len(final[final['ABCD_Class']=='A']))
        col4.metric("B Items", len(final[final['ABCD_Class']=='B']))
        
        st.dataframe(final, use_container_width=True, height=600)
        
        csv = final.to_csv(index=False).encode()
        st.download_button("📥 Download Full Report", csv, "SKU_Rationalization_Report.csv", "text/csv")
else:
    st.info("Please upload your Excel file to begin analysis")