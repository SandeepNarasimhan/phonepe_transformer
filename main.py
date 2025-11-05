import os
import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
from io import BytesIO

from pdf_to_df import PDFtoDataFrame

## Load password for pdf decryption
# load_dotenv()
# password = os.getenv('password')


st.set_page_config(page_title="PDF Transaction Visualizer", layout="wide")

st.title("Transaction Visualizer")

# Sidebar Section
st.sidebar.header("File Upload")
st.sidebar.info(
    "Upload a password-protected PDF statement and visualize your transactions easily."
)

uploaded_pdf = st.sidebar.file_uploader("📂 Upload your PDF file", type=["pdf"])
password = st.sidebar.text_input(
    "🔒 Enter PDF password (if protected)", type="password"
)


# Session State
if "df" not in st.session_state:
    st.session_state.df = None

# Process button
process_btn = st.sidebar.button("🚀 Process PDF")

if process_btn and uploaded_pdf:
    try:
        with st.spinner("Extracting data... Please wait"):
            with open("temp.pdf", "wb") as f:
                f.write(uploaded_pdf.read())

            parser = PDFtoDataFrame("temp.pdf", password)
            df = parser.convert()
            st.session_state.df = df

        st.sidebar.success("PDF successfully processed!")

    except Exception as e:
        st.error(f"Failed to read PDF: {e}")

elif process_btn and not uploaded_pdf:
    st.sidebar.warning("⚠️ Please upload a PDF file before processing.")
else:
    st.sidebar.warning("⚠️ Please upload a PDF file before processing.")

if st.session_state.df is not None:
    df = st.session_state.df.copy()

    df["Date"] = df["Datetime"].dt.date
    df["Hour"] = df["Datetime"].dt.hour
    df["DayOfWeek"] = df["Datetime"].dt.day_name()

    st.title("Personal Transaction Dashboard")
    st.markdown("Visualize your spending and income patterns interactively")

    # Date Range Filter
    min_date, max_date = df["Date"].min(), df["Date"].max()
    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date,
    )

    filtered_df = df[
        (df["Datetime"] >= pd.to_datetime(start_date))
        & (df["Datetime"] <= pd.to_datetime(end_date))
    ]

    # Sidebar Filters
    st.sidebar.header("🔍 Additional Filters")

    # Merchant / Description filter
    merchants = filtered_df["Description"].unique()
    selected_merchants = st.sidebar.multiselect(
        "Select Merchants", merchants, default=merchants
    )

    # Day of the week filter
    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    selected_days = st.sidebar.multiselect("Select Days of Week", days, default=days)

    # Transaction type filter
    types = filtered_df["Type"].unique()
    selected_types = st.sidebar.multiselect(
        "Select Transaction Type", types, default=types
    )

    # Amount range filter
    min_amount, max_amount = float(filtered_df["Amount"].min()), float(
        filtered_df["Amount"].max()
    )
    selected_amount = st.sidebar.slider(
        "Select Amount Range", min_amount, max_amount, (min_amount, max_amount)
    )

    # Apply all filters
    filtered_df = filtered_df[
        (filtered_df["Description"].isin(selected_merchants))
        & (filtered_df["DayOfWeek"].isin(selected_days))
        & (filtered_df["Type"].isin(selected_types))
        & (filtered_df["Amount"] >= selected_amount[0])
        & (filtered_df["Amount"] <= selected_amount[1])
    ]

    # KPIs
    total_debit = filtered_df.loc[filtered_df["Type"] == "Debited", "Amount"].sum()
    total_credit = filtered_df.loc[filtered_df["Type"] == "Credited", "Amount"].sum()
    net_flow = total_credit - total_debit

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Debited", f"₹{total_debit:,.2f}")
    col2.metric("Total Credited", f"₹{total_credit:,.2f}")
    col3.metric("Net Flow", f"₹{net_flow:,.2f}", delta_color="inverse")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📈 Time Series",
            "🏪 Merchants",
            "🕒 Time Patterns",
            "📊 Summary Table",
            "📦 Export & Outliers",
        ]
    )

    # Tab 1 Time Series
    with tab1:
        st.subheader("Daily Debit vs Credit")
        daily = filtered_df.groupby(["Date", "Type"])["Amount"].sum().reset_index()
        fig = px.line(daily, x="Date", y="Amount", color="Type")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Weekly & Monthly Summary")
        weekly = (
            filtered_df.groupby(filtered_df["Datetime"].dt.to_period("W"))["Amount"]
            .sum()
            .to_timestamp()
        )
        monthly = (
            filtered_df.groupby(filtered_df["Datetime"].dt.to_period("M"))["Amount"]
            .sum()
            .to_timestamp()
        )
        st.line_chart(weekly.rename("Weekly Spend"))
        st.line_chart(monthly.rename("Monthly Spend"))

        st.subheader("Cumulative Cash Flow")
        filtered_df["DebitAmount"] = filtered_df.apply(
            lambda x: x["Amount"] if x["Type"] == "Debited" else 0, axis=1
        )
        filtered_df["CreditAmount"] = filtered_df.apply(
            lambda x: x["Amount"] if x["Type"] == "Credited" else 0, axis=1
        )
        cumulative = filtered_df.groupby("Date")[["CreditAmount", "DebitAmount"]].sum()
        cumulative["Net"] = cumulative["CreditAmount"] - cumulative["DebitAmount"]
        cumulative["CumulativeNet"] = cumulative["Net"].cumsum()
        st.line_chart(cumulative["CumulativeNet"], use_container_width=True)

    # Tab 2: Merchants & Categories
    with tab2:
        st.subheader("Top 10 Spending Merchants")
        top_merchants = (
            filtered_df.groupby("Description")["Amount"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )
        fig = px.bar(
            top_merchants,
            x=top_merchants.values,
            y=top_merchants.index,
            orientation="h",
            labels={"x": "Amount (INR)", "y": "Merchant"},
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Spending by Categories")

        def categorize(desc):
            desc = str(desc).lower()
            if any(x in desc for x in ["zomato", "restaurant", "cafe", "bar", "hotel", "veg", "swiggy"]):
                return "Food"
            if any(x in desc for x in ["uber", "ola", "taxi", "travel", "ksrtc", 'depot', 'bmtc']):
                return "Travel"
            if any(x in desc for x in ["amazon", "flipkart", "shopping", 'store', 'myntra']):
                return "Shopping"
            if any(x in desc for x in ["bill", "electricity", "water", "utility"]):
                return "Utilities"
            if any(x in desc for x in ["hospital", "pharma", "medical", "doctor"]):
                return "Medical"
            return "Other"

        filtered_df["Category"] = filtered_df["Description"].apply(categorize)
        category_sum = filtered_df.groupby("Category")["Amount"].sum()
        fig = px.pie(
            values=category_sum.values,
            names=category_sum.index,
            title="Spending by Category",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Tab 3: Time Patterns
    with tab3:
        st.subheader("Spending by Hour of Day")
        hourly = filtered_df.groupby(["Hour", "Type"])["Amount"].sum().reset_index()
        fig1 = px.bar(hourly, x="Hour", y="Amount", color="Type")
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("Spending by Day of Week")
        dow = filtered_df.groupby(["DayOfWeek", "Type"])["Amount"].sum().reset_index()
        order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        dow["DayOfWeek"] = pd.Categorical(
            dow["DayOfWeek"], categories=order, ordered=True
        )
        fig2 = px.bar(dow, x="DayOfWeek", y="Amount", color="Type")
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Heatmap: Day vs Hour")
        pivot = filtered_df.pivot_table(
            values="Amount",
            index="DayOfWeek",
            columns="Hour",
            aggfunc="sum",
            fill_value=0,
        )
        pivot = pivot.reindex(order)
        fig, ax = plt.subplots(figsize=(12, 5))
        sns.heatmap(pivot, cmap="YlGnBu", ax=ax)
        ax.set_title("Spending Heatmap (Day vs Hour)")
        st.pyplot(fig)

    # Tab 4: Summary Table
    with tab4:
        st.subheader("Filtered Transactions")
        st.dataframe(
            filtered_df.sort_values("Datetime", ascending=False).reset_index(drop=True)
        )

    #  Tab 5: Export & Outliers
    with tab5:
        st.subheader("Export Filtered Data")

        def convert_df(df):
            return df.to_csv(index=False).encode("utf-8")

        csv = convert_df(filtered_df)
        st.download_button(
            "📥 Download Filtered Data",
            data=csv,
            file_name="filtered_transactions.csv",
            mime="text/csv",
        )

        st.subheader("Unusually Large Transactions")
        threshold = filtered_df["Amount"].mean() + 2 * filtered_df["Amount"].std()
        outliers = filtered_df[filtered_df["Amount"] > threshold]
        st.dataframe(outliers[["Datetime", "Description", "Amount"]], height=250)
