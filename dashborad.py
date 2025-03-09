import streamlit as st
import pandas as pd
import io
import os
import matplotlib.pyplot as plt

# --------------------- Page Configuration --------------------- #
st.set_page_config(page_title="Stock & Sales Dashboard", layout="wide")

# --------------------- Sidebar Styling --------------------- #
st.sidebar.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            background-color: #1E1E1E;
            padding: 20px;
        }
        .sidebar-title {
            font-size: 22px;
            font-weight: bold;
            color: #00d4ff;
            text-align: center;
            margin-bottom: 15px;
        }
        .sidebar-btn {
            background-color: #0083B0;
            color: white;
            border-radius: 10px;
            padding: 10px 15px;
            font-size: 16px;
            transition: 0.3s ease-in-out;
            width: 100%;
            text-align: center;
            border: none;
            cursor: pointer;
            margin-bottom: 10px;
            display: block;
        }
        .sidebar-btn:hover {
            background-color: #00d4ff;
            color: black;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------- Sidebar Navigation --------------------- #
st.sidebar.markdown('<p class="sidebar-title">📊 Dashboard Navigation</p>', unsafe_allow_html=True)

if st.sidebar.button("📦 Stock Order", key="stock"):
    st.session_state.page = "stock"

if st.sidebar.button("🛒 Sales Order", key="sales"):
    st.session_state.page = "sales"

st.sidebar.markdown("---")

if "page" not in st.session_state:
    st.session_state.page = "stock"

# --------------------- Stock Order Functionality --------------------- #
def process_stock_data(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, header=None)
        df.drop(index=[0, 1, 2, 3, 5, 6], columns=[1, 3, 4, 5, 8, 11, 12, 13, 14, 15, 16, 17, 18], inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)
        
        if 'Bale No.' not in df.columns:
            raise KeyError("'Bale No.' column not found!")
        
        df.dropna(subset=['Bale No.'], inplace=True)
        df['Bale No.'] = df['Bale No.'].astype(str)
        df = df[~df['Bale No.'].str.contains('(?i)^Total of')]
        
        if 'Bal.Pcs' in df.columns:
            df['Bal.Pcs'] = df['Bal.Pcs'].fillna(0).astype(int)
        else:
            raise KeyError("'Bal.Pcs' column not found!")
        
        if 'Quality Name' in df.columns:
            df['Quality Name All'] = df['Quality Name'].where(
                df['Quality Name'].isin(["BLEACHED GOODS", "FINISH GOODS", "GREY GOODS", "OTHER"])
            ).ffill()
        else:
            raise KeyError("'Quality Name' column not found!")
        
        return df
    except KeyError as ke:
        st.error(f"Missing column: {ke}")
    except Exception as e:
        st.error(f"Failed to process file: {e}")
    return None



# --------------------- Sales Order Functionality --------------------- #
def process_sales_data(uploaded_file):
    try:
        file_extension = os.path.splitext(uploaded_file.name)[1]

        if file_extension == ".csv":
            sales_order = pd.read_csv(uploaded_file, header=None)
        else:
            sales_order = pd.read_excel(uploaded_file, header=None)

        # Data Cleaning
        sales_order.drop(index=[0,1,2,3], inplace=True)
        sales_order.drop(columns=[0,1,3,4,5,6,7,8,9,10,11,15], inplace=True)
        sales_order.columns = ["Date", "Rate", "Order Qty", "Dsp Qty", "Bal Qty"]
        sales_order.dropna(subset=['Date'], inplace=True)

        sales_order.loc[
            sales_order["Date"].astype(str).str.startswith("Total of"), "Rate"
        ] = sales_order["Rate"].shift()

        df_cleaned = sales_order[sales_order["Date"].astype(str).str.startswith("Total of")]
        return df_cleaned

    except Exception as e:
        st.error(f"Failed to process file: {e}")
        return None



# --------------------- Main Page Logic --------------------- #
if st.session_state.page == "stock":
    st.title("📊 Stock Data Filter & Sort")
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])
    
    if uploaded_file:
        df = process_stock_data(uploaded_file)
        if df is not None:
            quality_all_options = ["All"] + list(df["Quality Name All"].dropna().unique())
            quality_options = ["All"] + list(df["Quality Name"].dropna().unique())
            grade_options = ["All"] + list(df["Grade"].dropna().unique())

            col1, col2, col3, col4 = st.columns(4)
            quality_all_filter = col1.selectbox("Quality Name All", quality_all_options)
            quality_filter = col2.selectbox("Quality Name", quality_options)
            grade_filter = col3.selectbox("Grade", grade_options)
            min_bal_pcs = col4.number_input("Min Bal.Pcs", min_value=0, step=1)

            filtered_df = df.copy()
            if quality_all_filter != "All":
                filtered_df = filtered_df[filtered_df["Quality Name All"] == quality_all_filter]
            if quality_filter != "All":
                filtered_df = filtered_df[filtered_df["Quality Name"] == quality_filter]
            if grade_filter != "All":
                filtered_df = filtered_df[filtered_df["Grade"] == grade_filter]
            if min_bal_pcs > 0:
                filtered_df = filtered_df[filtered_df["Bal.Pcs"] >= min_bal_pcs]

            st.write("### Filtered Data")
            st.dataframe(filtered_df)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='Filtered Data')
                writer.close()
            output.seek(0)
            st.download_button("Download Filtered Data", output, file_name="filtered_stock_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            if st.button("Show Count by Quality Name"):
                count_df = filtered_df.groupby("Quality Name").size().reset_index(name="Count")
                st.write("### Count of Quality Name")
                st.dataframe(count_df)
elif st.session_state.page == "sales":
    st.title("📊 Sales Order Management")

    uploaded_file = st.file_uploader("Upload an Excel or CSV file", type=["xlsx", "xls", "csv"])
    
    if uploaded_file:
        df_cleaned = process_sales_data(uploaded_file)

        if df_cleaned is not None:
            st.subheader("Cleaned Sales Order Data")
            st.dataframe(df_cleaned)

            processed_file = df_cleaned.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download CSV", data=processed_file, file_name="cleaned_sales_order.csv", mime="text/csv")

            st.subheader("Sales Order Chart")
            numeric_columns = df_cleaned.select_dtypes(include=["number"]).columns

            if len(numeric_columns) >= 2:
                fig, ax = plt.subplots(figsize=(8, 5))
                df_cleaned.plot(kind="bar", x=numeric_columns[0], y=numeric_columns[1], ax=ax)
                st.pyplot(fig)
            else:
                st.warning("Not enough numeric data for charting.")
