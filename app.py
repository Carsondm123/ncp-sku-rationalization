import streamlit as st
import pandas as pd

st.set_page_config(page_title="NCP · SKU Rationalization Console", layout="wide")

st.title("🧩 NCP · SKU Rationalization Console")
st.caption("ABCD Classification & Weighted Ranking Tool")

uploaded_file = st.file_uploader("Upload Sales Data Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # Item Key View
    item_grouped = df.groupby('Itemkey').agg({
        'NetVal': 'sum',
        'GAL': 'sum',
        'Custkey': 'nunique',
        'Oeordno': 'nunique',
        'CUSTOM2': 'first'
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
    
    st.subheader("Ranked Items")
    st.dataframe(item_grouped[['Rank', 'Itemkey', 'Technology', 'Total_Sales', 'ABCD_Class']], use_container_width=True)
    
    st.download_button("Download Report", item_grouped.to_csv(index=False), "report.csv")
    
else:
    st.info("Upload your Excel file to begin analysis")
