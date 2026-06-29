import streamlit as st
import pandas as pd

st.set_page_config(page_title="NCP · SKU Rationalization Console", layout="wide")
st.title("🧩 NCP · SKU Rationalization Console")
st.markdown("**ABCD Classification & Weighted Ranking Tool**")

uploaded_file = st.file_uploader("Upload your Sales Data Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # Simple processing for now
    item = df.groupby('Itemkey').agg({
        'NetVal': 'sum',
        'GAL': 'sum',
        'CUSTOM2': 'first'
    }).reset_index()
    
    item = item.rename(columns={
        'NetVal': 'Total_Sales',
        'GAL': 'Total_Gallons',
        'CUSTOM2': 'Technology'
    }).fillna({'Technology': 'Unknown'})
    
    item['Rank'] = range(1, len(item)+1)
    total = item['Total_Sales'].sum()
    item['Cum_Sales_Pct'] = (item['Total_Sales'].cumsum() / total * 100).round(1)
    item['ABCD_Class'] = item['Cum_Sales_Pct'].apply(lambda x: 'A' if x <= 70 else 'B' if x <= 85 else 'C' if x <= 95 else 'D')
    
    final = item[['Rank', 'Itemkey', 'Technology', 'Total_Sales', 'ABCD_Class', 'Cum_Sales_Pct']]
    
    st.dataframe(final.style.format({
        'Total_Sales': '${:,.0f}',
        'Cum_Sales_Pct': '{:.1f}%'
    }), use_container_width=True, height=700)
    
    st.download_button("Download Report", final.to_csv(index=False), "report.csv", "text/csv")
else:
    st.info("Upload your Excel file to begin")
