import streamlit as st
import pandas as pd

st.set_page_config(page_title="NCP · SKU Rationalization Console", layout="wide")
st.title("🧩 NCP · SKU Rationalization Console")
st.markdown("**ABCD Classification & Weighted Ranking Tool**")

@st.cache_data
def load_and_process(uploaded_file):
    df = pd.read_excel(uploaded_file)
    # Item Key
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
    
    # Customer
    cust = df.groupby('Customer_Name').agg({
        'NetVal': 'sum',
        'Itemkey': 'nunique',
        'Oeordno': 'nunique'
    }).reset_index()
    cust = cust.rename(columns={'NetVal': 'Total_Sales', 'Itemkey': 'Unique_Items'})
    cust = cust.sort_values('Total_Sales', ascending=False).reset_index(drop=True)
    cust['Rank'] = range(1, len(cust)+1)
    total_c = cust['Total_Sales'].sum()
    cust['Cum_Sales_Pct'] = (cust['Total_Sales'].cumsum() / total_c * 100).round(2)
    cust['ABCD_Class'] = cust['Cum_Sales_Pct'].apply(lambda x: 'A' if x <= 70 else 'B' if x <= 85 else 'C' if x <= 98 else 'D')
    
    return item, cust, df

uploaded_file = st.file_uploader("Upload your Sales Data Excel file", type=["xlsx"])

if uploaded_file:
    with st.spinner("Processing..."):
        df = pd.read_excel(uploaded_file)
        item_data, cust_data, raw_df = load_and_process(uploaded_file)
    
    view = st.radio("View Mode", ["Item Key View", "Customer View"], horizontal=True)
    
    if view == "Item Key View":
        final = item_data[['Rank', 'Itemkey', 'Technology', 'Total_Sales', 'ABCD_Class', 'Cum_Sales_Pct']]
        
        col1, col2 = st.columns(2)
        tech_filter = col1.multiselect("Technology", options=sorted(final['Technology'].unique()), default=[])
        abcd_filter = col2.multiselect("ABCD Class", ['A','B','C','D'], default=['A','B'])
        
        filtered = final
        if tech_filter:
            filtered = filtered[filtered['Technology'].isin(tech_filter)]
        if abcd_filter:
            filtered = filtered[filtered['ABCD_Class'].isin(abcd_filter)]
        
        # Format Total Sales as currency
        st.dataframe(filtered.style.format({'Total_Sales': '${:,.0f}'}), use_container_width=True, height=700)
        
    else:  # Customer View
        final = cust_data[['Rank', 'Customer_Name', 'Total_Sales', 'Unique_Items', 'ABCD_Class']]
        
        abcd_filter = st.multiselect("ABCD Class", ['A','B','C','D'], default=['A','B'])
        filtered = final if not abcd_filter else final[final['ABCD_Class'].isin(abcd_filter)]
        
        st.dataframe(filtered.style.format({'Total_Sales': '${:,.0f}'}), use_container_width=True, height=700)
        
        customer = st.selectbox("Select Customer to see items bought", options=[""] + list(filtered['Customer_Name']))
        if customer:
            items = raw_df[raw_df['Customer_Name'] == customer]
            st.write(f"**Items bought by {customer}**")
            st.dataframe(items[['Itemkey', 'Desc1', 'NetVal', 'GAL']].style.format({'NetVal': '${:,.0f}'}), use_container_width=True)
    
    st.download_button("📥 Download Current View", filtered.to_csv(index=False), "report.csv", "text/csv")
else:
    st.info("Upload your Excel file to begin")
