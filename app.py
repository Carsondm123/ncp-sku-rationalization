import streamlit as st
import pandas as pd

st.set_page_config(page_title="NCP SKU Console", layout="wide")
st.title("NCP · SKU Rationalization Console")

uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("File loaded!")
    st.dataframe(df.head(100))
else:
    st.info("Upload your file")
