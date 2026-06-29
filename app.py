import streamlit as st
import pandas as pd

st.set_page_config(page_title="NCP · SKU Rationalization Console", layout="wide")
st.title("🧩 NCP · SKU Rationalization Console")
st.markdown("**ABCD Classification & Weighted Ranking Tool**")

@st.cache_data
def load_and_process(uploaded_file):
    df = pd.read_excel(uploaded_file)
    # Item Key processing
    item = df.groupby('Itemkey').agg({
        'NetVal': 'sum',
        'GAL': 'sum',
        'Custkey': 'nunique',
        'Oeordno': 'nunique',
        'CUSTOM2': 'first',
        'Unitprice': 'mean'
    }).reset_index()
    
    item = item.rename(columns={
        'NetVal': 'Total_Sales',
        'GAL': 'Total_Gallons',
        'Custkey': 'Active_Customers',
        'Oeordno': 'Total_Orders',
        'CUSTOM2': 'Technology',
        'Unitprice': 'ASP'
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
    item['Cum_Sales_Pct'] = (item['Total_Sales'].cumsum() / total * 100).round(1)
    item['ABCD_Class'] = item['Cum_Sales_Pct'].apply(lambda x: 'A' if x <= 70 else 'B' if x <= 85 else 'C' if x <= 95 else 'D')
    
    return item, df

uploaded_file = st.file_uploader("Upload your Sales Data Excel file", type=["xlsx"])

if uploaded_file:
    with st.spinner("Processing..."):
        item_data, raw_df = load_and_process(uploaded_file)
    
    # Main Table
    final = item_data[['Rank', 'Itemkey', 'Technology', 'Total_Sales', 'ASP', 'ABCD_Class', 'Cum_Sales_Pct']]
    
    col1, col2 = st.columns(2)
    tech_filter = col1.multiselect("Technology", options=sorted(final['Technology'].unique()), default=[])
    abcd_filter = col2.multiselect("ABCD Class", ['A','B','C','D'], default=['A','B'])
    
    filtered = final
    if tech_filter:
        filtered = filtered[filtered['Technology'].isin(tech_filter)]
    if abcd_filter:
        filtered = filtered[filtered['ABCD_Class'].isin(abcd_filter)]
    
    st.dataframe(filtered.style.format({
        'Total_Sales': '${:,.0f}',
        'ASP': '${:,.2f}',
        'Cum_Sales_Pct': '{:.1f}%'
    }), use_container_width=True, height=600)
    
    # Drill-down
    st.subheader("Decision Detail - Click an Itemkey below")
    selected_item = st.selectbox("Select Itemkey", options=filtered['Itemkey'])
    
    if selected_item:
        detail = raw_df[raw_df['Itemkey'] == selected_item]
        top_customers = detail.groupby('Customer_Name')['NetVal'].sum().nlargest(5)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Item:** {selected_item}")
            st.write(f"**Technology:** {detail['CUSTOM2'].iloc[0] if 'CUSTOM2' in detail.columns else 'N/A'}")
            st.write(f"**Total Revenue:** ${detail['NetVal'].sum():,}")
            st.write(f"**Total Volume:** {detail['GAL'].sum():,} GAL")
            st.write(f"**ASP:** ${detail['NetVal'].sum() / detail['GAL'].sum():.2f}" if detail['GAL'].sum() > 0 else "N/A")
        with col2:
            st.write("**Top Customers**")
            for cust, sales in top_customers.items():
                st.write(f"{cust}: ${sales:,.0f} ({sales/detail['NetVal'].sum()*100:.1f}%)")
        
        st.write("**All Transactions for this Item**")
        st.dataframe(detail[['Customer_Name', 'NetVal', 'GAL', 'Qty', 'Invdate']].style.format({
            'NetVal': '${:,.0f}'
        }), use_container_width=True)
else:
    st.info("Upload your Excel file to begin")
