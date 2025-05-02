import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="BOM Selector", layout="wide")
st.title("📦 Project BOM Builder")

# Upload Excel file
uploaded_file = st.file_uploader("Upload the Excel file", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    if "BOM" in xls.sheet_names:
        bom_df = pd.read_excel(xls, sheet_name="BOM")
        bom_display = bom_df.apply(lambda row: " | ".join(row.astype(str)), axis=1).tolist()
        bom_codes = bom_df.iloc[:, 0].dropna().tolist()
        label_to_code = dict(zip(bom_display, bom_codes))

        selected_label = st.selectbox("🔧 Select a BOM Entry", sorted(bom_display))
        selected_part = label_to_code[selected_label]

        if selected_part in xls.sheet_names:
            part_df = pd.read_excel(xls, sheet_name=selected_part)
            st.markdown(f"### 🧾 Components for: `{selected_part}`")

            part_df["Select"] = False
            numeric_cols = part_df.select_dtypes(include='number').columns.tolist()
            last_numeric_col = numeric_cols[-1] if numeric_cols else None

            with st.form("select_items_form"):
                select_all = st.checkbox("✅ Select All")
                edited_df = part_df.copy()

                edited_df["Select"] = select_all  # Pre-fill selection if 'Select All' is checked

                st.dataframe(edited_df.drop(columns=["Select"]))  # View-only mode

                # Allow selection using table-like inputs
                selected_rows = st.multiselect(
                    "✔️ Select rows to include in BOM (by index):",
                    options=part_df.index.tolist(),
                    default=part_df.index.tolist() if select_all else []
                )

                for i in part_df.index:
                    part_df.at[i, "Select"] = i in selected_rows

                submitted = st.form_submit_button("✅ Create BOM")

            if submitted:
                final_bom = part_df[part_df["Select"] == True].drop(columns=["Select"])

                if not final_bom.empty:
                    st.success("✅ Final Bill of Material")
                    st.dataframe(final_bom, use_container_width=True)

                    # Show total for last numeric column
                    if last_numeric_col:
                        total = final_bom[last_numeric_col].sum()
                        st.markdown(f"**🔢 Total {last_numeric_col}: `{total}`**")

                    def to_excel(df):
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df.to_excel(writer, index=False, sheet_name='Final BOM')
                        return output.getvalue()

                    excel_data = to_excel(final_bom)
                    st.download_button(
                        label="📥 Download BOM as Excel",
                        data=excel_data,
                        file_name="Final_BOM.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                else:
                    st.warning("⚠️ Please select at least one item to generate BOM.")
        else:
            st.error(f"❌ Sheet `{selected_part}` not found in Excel file.")
    else:
        st.error("❌ 'BOM' sheet not found in the uploaded Excel file.")
else:
    st.info("📂 Please upload an Excel file to begin.")
