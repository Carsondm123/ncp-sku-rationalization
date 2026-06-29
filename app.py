import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="NCP · SKU Rationalization Console", layout="wide")
st.title("🧩 NCP · SKU Rationalization Console")
st.markdown("**ABCD Classification & Weighted Ranking Tool**")

uploaded_file = st.file_uploader("Upload your Sales Data Excel file", type=["xlsx"])

if uploaded_file:
    with st.spinner("Analyzing data..."):
        df = pd.read_excel(uploaded_file)
        
        # Aggregation by Itemkey
        item_grouped = df.groupby('Itemkey').agg({
            'NetVal': 'sum',
            'GAL': 'sum',
            'Custkey': 'nunique',
            'Oeordno': 'nunique',
            'CUSTOM2': 'first',
            'Customer_Name': 'first'
        }).reset_index()
        
        item_grouped = item_grouped.rename(columns={
            'NetVal': 'Total_Sales',
            'GAL': 'Total_Gallons',
            'Custkey': 'Active_Customers',
            'Oeordno': 'Total_Orders',
            'CUSTOM2': 'Technology'
        }).fillna({'Technology': 'Unknown'})
        
        # Weighted Score
        for col in ['Total_Sales', 'Total_Gallons', 'Total_Orders', 'Active_Customers']:
            maxv = item_grouped[col].max()
            item_grouped[col + '_Norm'] = item_grouped[col] / maxv if maxv > 0 else 0
        
        item_grouped['Weighted_Score'] = (
            item_grouped['Total_Sales_Norm'] * 0.40 +
            item_grouped['Total_Orders_Norm'] * 0.30 +
            item_grouped['Total_Gallons_Norm'] * 0.20 +
            item_grouped['Active_Customers_Norm'] * 0.10
        )
        
        item_grouped = item_grouped.sort_values('Weighted_Score', ascending=False).reset_index(drop=True)
        item_grouped['Rank'] = range(1, len(item_grouped)+1)
        
        total_sales = item_grouped['Total_Sales'].sum()
        item_grouped['Cum_Sales_Pct'] = (item_grouped['Total_Sales'].cumsum() / total_sales * 100).round(2)
        item_grouped['ABCD_Class'] = item_grouped['Cum_Sales_Pct'].apply(lambda x: 'A' if x <= 70 else 'B' if x <= 85 else 'C' if x <= 95 else 'D')
        
        # View Toggle
        view = st.radio("View Mode", ["Item Key View", "Customer View"], horizontal=True)
        
        if view == "Item Key View":
            final = item_grouped[['Rank', 'Itemkey', 'Technology', 'Total_Sales', 'Total_Gallons', 
                                'Total_Orders', 'Active_Customers', 'Weighted_Score', 
                                'ABCD_Class', 'Cum_Sales_Pct']].round(4)
            
            # Filters
            col1, col2, col3 = st.columns(3)
            tech_filter = col1.multiselect("Filter by Technology", options=sorted(final['Technology'].unique()), default=[])
            abcd_filter = col2.multiselect("Filter by ABCD Class", ['A','B','C','D'], default=['A','B'])
            search = col3.text_input("Search Itemkey", "")
            
            filtered = final.copy()
            if tech_filter:
                filtered = filtered[filtered['Technology'].isin(tech_filter)]
            if abcd_filter:
                filtered = filtered[filtered['ABCD_Class'].isin(abcd_filter)]
            if search:
                filtered = filtered[filtered['Itemkey'].str.contains(search, case=False, na=False)]
                
        else:  # Customer View
            # Aggregate by Customer
            cust_grouped = df.groupby('Customer_Name').agg({
                'NetVal': 'sum',
                'Itemkey': 'nunique',
                'Oeordno': 'nunique'
            }).reset_index()
            cust_grouped = cust_grouped.rename(columns={
                'NetVal': 'Total_Sales',
                'Itemkey': 'Unique_Items',
                'Oeordno': 'Total_Orders'
            })
            cust_grouped = cust_grouped.sort_values('Total_Sales', ascending=False).reset_index(drop=True)
            cust_grouped['Rank'] = range(1, len(cust_grouped)+1)
            final = cust_grouped
            
            search = st.text_input("Search Customer Name", "")
            filtered = final
            if search:
                filtered = filtered[filtered['Customer_Name'].str.contains(search, case=False, na=False)]
        
        st.dataframe(filtered, use_container_width=True, height=700)
        
        csv = filtered.to_csv(index=False).encode()
        st.download_button("📥 Download Current View", csv, "report.csv", "text/csv")
        
else:
    st.info("👆 Upload your Excel file to start")
