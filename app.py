import streamlit as st
import pandas as pd
from io import BytesIO
import os

st.set_page_config(page_title="BOM Selector", layout="wide")
st.title("📦 Vertiv™ SmartSolutions™(IT Solutions)- Project BOM Builder, Drawings")

# Tab setup
tabs = {
    "SmartCloset": "Smart Closet Parent Partcode.xlsx",
    "SmartCabinet": "Smart Cabinet Parent Partcode.xlsx",
    "SmartCabinetP": "Smart CabinetP Parent Partcode.xlsx",
    "SmartRow": "Smart Row Parent Partcode.xlsx"
}

# Add extra Panel Drwg tab
tab_names = list(tabs.keys()) + ["Panel Drwg"]
selected_tab = st.tabs(tab_names)

# Render BOM tabs
for i, tab_label in enumerate(list(tabs.keys())):
    with selected_tab[i]:
        st.subheader(f"📁 {tab_label} BOM Selection")

        excel_file = tabs[tab_label]

        try:
            xls = pd.ExcelFile(excel_file)

            if "BOM" in xls.sheet_names:
                bom_df = pd.read_excel(xls, sheet_name="BOM")
                bom_display = bom_df.apply(lambda row: " | ".join(row.astype(str)), axis=1).tolist()
                bom_codes = bom_df.iloc[:, 0].dropna().tolist()
                label_to_code = dict(zip(bom_display, bom_codes))

                selected_label = st.selectbox(f"🔧 Select a BOM Entry for {tab_label}", sorted(bom_display))
                selected_part = label_to_code[selected_label]

                if selected_part in xls.sheet_names:
                    part_df = pd.read_excel(xls, sheet_name=selected_part)
                    st.markdown(f"### 🧾 Components for: `{selected_part}`")

                    part_df["Index"] = part_df.index  # To track selections
                    st.dataframe(part_df, use_container_width=True)

                    with st.form(f"{tab_label}_form"):
                        selected_rows = st.multiselect(
                            "✔️ Select rows to include in BOM (by index):",
                            options=part_df.index.tolist()
                        )
                        submitted = st.form_submit_button("✅ Create BOM")

                    if submitted:
                        final_bom = part_df.loc[selected_rows].drop(columns=["Index"])

                        if not final_bom.empty:
                            # If LP column exists, allow edit
                            if "LP" in final_bom.columns:
                                st.markdown("### 💰 Update LP (List Price) if needed")
                                edited = st.data_editor(
                                    final_bom[["LP"]],
                                    use_container_width=True,
                                    num_rows="dynamic",
                                    key=f"{tab_label}_lp_edit"
                                )
                                final_bom["LP"] = edited["LP"]

                            st.success("✅ Final Bill of Material")
                            st.dataframe(final_bom, use_container_width=True)

                            def to_excel(df):
                                output = BytesIO()
                                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                    df.to_excel(writer, index=False, sheet_name='Final BOM')
                                return output.getvalue()

                            excel_data = to_excel(final_bom)
                            st.download_button(
                                label="📥 Download BOM as Excel",
                                data=excel_data,
                                file_name=f"{tab_label}_Final_BOM.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            )
                        else:
                            st.warning("⚠️ Please select at least one item to generate BOM.")
                else:
                    st.error(f"❌ Sheet `{selected_part}` not found in Excel file.")
            else:
                st.error("❌ 'BOM' sheet not found in the Excel file.")

        except FileNotFoundError:
            st.error(f"❌ '{excel_file}' file not found. Please ensure it exists in the app directory.")

# Panel Drawing Tab
with selected_tab[-1]:
    st.subheader("📂 Panel Drawings Viewer")

    PANEL_ROOT = "panel drwg"
    SUBFOLDERS = ["DB panel", "POD"]

    if os.path.exists(PANEL_ROOT):
        selected_folder = st.selectbox("📁 Select Drawing Folder:", SUBFOLDERS)
        folder_path = os.path.join(PANEL_ROOT, selected_folder)

        if os.path.isdir(folder_path):
            pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

            if pdf_files:
                selected_pdf = st.selectbox("📝 Select a PDF to download:", pdf_files)
                pdf_path = os.path.join(folder_path, selected_pdf)

                with open(pdf_path, "rb") as f:
                    pdf_data = f.read()

                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_data,
                    file_name=selected_pdf,
                    mime="application/pdf"
                )
            else:
                st.warning("⚠️ No PDF files found in the selected folder.")
        else:
            st.error("❌ Selected folder does not exist.")
    else:
        st.error("❌ 'panel drwg' directory not found. Please make sure it's placed in the app folder.")
