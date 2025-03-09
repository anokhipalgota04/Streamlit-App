import streamlit as st
import pandas as pd
import io
import dashborad
def process_data(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, header=None)
        
        # Remove unwanted rows and columns
        df.drop(index=[0, 1, 2, 3, 5, 6], columns=[1, 3, 4, 5, 8, 11, 12, 13, 14, 15, 16, 17, 18], inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        # Set first row as headers
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)
        
        if 'Bale No.' not in df.columns:
            raise KeyError("'Bale No.' column not found!")
        
        df.dropna(subset=['Bale No.'], inplace=True)
        df['Bale No.'] = df['Bale No.'].astype(str)
        df = df[~df['Bale No.'].str.startswith('Total_of')]
        
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

def main():
    st.title("📊 Stock Data Filter & Sort")
    
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])
    
    if uploaded_file:
        df = process_data(uploaded_file)
        if df is not None:
            # Filter options
            quality_all_options = ["All"] + list(df["Quality Name All"].dropna().unique())
            quality_options = ["All"] + list(df["Quality Name"].dropna().unique())
            grade_options = ["All"] + list(df["Grade"].dropna().unique())
            
            col1, col2, col3, col4 = st.columns(4)
            
            quality_all_filter = col1.selectbox("Quality Name All", quality_all_options)
            quality_filter = col2.selectbox("Quality Name", quality_options)
            grade_filter = col3.selectbox("Grade", grade_options)
            min_bal_pcs = col4.number_input("Min Bal.Pcs", min_value=0, step=1)
            
            # Apply filters
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
            
            # Download filtered data
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='Filtered Data')
                writer.close()
            output.seek(0)
            st.download_button("Download Filtered Data", output, file_name="filtered_stock_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()


