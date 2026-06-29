import streamlit as st
import pandas as pd

st.set_page_config(page_title="NCP · SKU Rationalization Console", layout="wide")

# Header like the original
st.markdown("""
<style>
    .header {font-size: 2.2rem; font-weight: bold; color: #1E3A8A;}
    .subheader {color: #666; margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://via.placeholder.com/180x60/1E3A8A/FFFFFF?text=NCP", width=180)
with col2:
    st.markdown('<p class="header">NCP · SKU Rationalization Console</p>', unsafe_allow_html=True)
    st.markdown('<p class="subheader">Advanced ABCD Analysis & Decision Support</p>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Sales Data", type=["xlsx"], help="qryARLineItemsLiteGALProdTechnology.xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # Item processing
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
    item['Cum_Sales_Pct'] = (item['Total_Sales'].cumsum() / total * 100).round(1)
    item['ABCD_Class'] = item['Cum_Sales_Pct'].apply(lambda x: 'A' if x <= 70 else 'B' if x <= 85 else 'C' if x <= 95 else 'D')
    
    # Main Table
    st.subheader("SKU Ranking")
    final = item[['Rank', 'Itemkey', 'Technology', 'Total_Sales', 'ABCD_Class', 'Cum_Sales_Pct']]
    st.dataframe(final.style.format({
        'Total_Sales': '${:,.0f}',
        'Cum_Sales_Pct': '{:.1f}%'
    }), use_container_width=True, height=600)
    
    # Drill-down
    st.subheader("Decision Detail - Click a row to inspect one SKU")
    selected_item = st.selectbox("Select Itemkey", options=final['Itemkey'])
    
    if selected_item:
        detail = df[df['Itemkey'] == selected_item]
        top_cust = detail.groupby('Customer_Name')['NetVal'].sum().nlargest(5)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Item:** {selected_item}")
            st.write(f"**Product Class:** {detail['CUSTOM2'].iloc[0] if not detail.empty else 'N/A'}")
            st.write(f"**Revenue 12m:** ${detail['NetVal'].sum():,}")
            st.write(f"**Volume 12m:** {detail['GAL'].sum():,}")
            if detail['GAL'].sum() > 0:
                st.write(f"**ASP:** ${detail['NetVal'].sum() / detail['GAL'].sum():.0f}")
        with col2:
            st.write("**Customer Basket**")
            for cust, sales in top_cust.items():
                pct = sales / detail['NetVal'].sum() * 100 if detail['NetVal'].sum() > 0 else 0
                st.write(f"{cust} ${sales:,.0f} ({pct:.0f}%)")
else:
    st.info("Upload your file to begin")
