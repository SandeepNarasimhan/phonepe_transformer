import streamlit as st

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv

from pdf_to_df import PDFtoDataFrame

## Load password for pdf decryption
#load_dotenv()
#password = os.getenv('password')


st.set_page_config(page_title="PDF Transaction Visualizer", layout="wide")

st.title("Transaction Visualizer")

# Sidebar Section
st.sidebar.header("File Upload")
st.sidebar.info("Upload a password-protected PDF statement and visualize your transactions easily.")

uploaded_pdf = st.sidebar.file_uploader("📂 Upload your PDF file", type=["pdf"])
password = st.sidebar.text_input("🔒 Enter PDF password (if protected)", type="password")

# Process button
process_btn = st.sidebar.button("🚀 Process PDF")

if process_btn and uploaded_pdf:
    try:
        with st.spinner("Extracting data... Please wait"):
            with open("temp.pdf", "wb") as f:
                f.write(uploaded_pdf.read())

            parser = PDFtoDataFrame("temp.pdf", password)
            df = parser.convert()

        st.sidebar.success("PDF successfully processed!")

        # Display Data
        st.subheader("📄 Extracted Transactions")
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to read PDF: {e}")
elif process_btn and not uploaded_pdf:
    st.sidebar.warning("⚠️ Please upload a PDF file before processing.")
else:
     st.sidebar.warning("⚠️ Please upload a PDF file before processing.")