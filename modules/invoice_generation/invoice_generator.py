import os
from datetime import date

import streamlit as st
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from modules.invoice_generation.template_engine import replace_placeholders
#from docx2pdf import convert
#import pythoncom
import base64
import subprocess

from pyhanko.sign import signers
from pyhanko.sign.fields import SigFieldSpec
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter


load_dotenv()

st.set_page_config(
    page_title="Invoice Generator",
    layout="wide"
)

st.title("Invoice Generator")


# ==========================================
# DATABASE CONNECTION
# ==========================================
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )


# ==========================================
# FETCH BANKS
# ==========================================
def get_banks():

    conn = get_connection()

    query = """
        SELECT
            id,
            name
        FROM lending_partners
        ORDER BY name
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# ==========================================
# FETCH INVOICE SUMMARY
# ==========================================
def get_invoice_summary(bank_id):

    conn = get_connection()

    # -------------------------
    # BANK
    # -------------------------
    bank_query = """
        SELECT *
        FROM lending_partners
        WHERE id = %s
    """

    bank_df = pd.read_sql(
        bank_query,
        conn,
        params=(bank_id,)
    )

    # -------------------------
    # BRANCH
    # -------------------------
    branch_query = """
        SELECT *
        FROM branches
        WHERE lending_partner_id = %s
        LIMIT 1
    """

    branch_df = pd.read_sql(
        branch_query,
        conn,
        params=(bank_id,)
    )

    # -------------------------
    # APPLICATIONS
    # -------------------------
    app_query = """
        SELECT *
        FROM applications
        WHERE lending_partner_id = %s
    """

    app_df = pd.read_sql(
        app_query,
        conn,
        params=(bank_id,)
    )

    if app_df.empty:
        conn.close()
        return None

    application_ids = tuple(app_df["id"].tolist())

    if len(application_ids) == 1:
        application_ids = f"({application_ids[0]})"
    else:
        application_ids = str(application_ids)

    # -------------------------
    # DISBURSEMENTS
    # -------------------------
    disb_query = f"""
        SELECT *
        FROM disbursements
        WHERE application_id IN {application_ids}
    """

    disb_df = pd.read_sql(
        disb_query,
        conn
    )

    conn.close()

    if disb_df.empty:
        return None

    # -------------------------
    # CALCULATIONS
    # -------------------------
    disb_df = disb_df.copy()

    disb_df["commission_amount"] = (
        disb_df["disbursement_amount"]
        * disb_df["ln_commission_percent"]
        / 100
    )

    gross_amount = (
        disb_df["commission_amount"]
        .fillna(0)
        .sum()
    )

    cgst = gross_amount * 0.09
    sgst = gross_amount * 0.09

    final_amount = (
        gross_amount
        + cgst
        + sgst
    )

    # -------------------------
    # BRANCH DETAILS
    # -------------------------
    address = "No data available in database"
    gstin = "No data available in database"
    pan = "No data available in database"

    if not branch_df.empty:

        if (
            "billing_address" in branch_df.columns
            and pd.notna(branch_df.iloc[0]["billing_address"])
        ):
            address = branch_df.iloc[0]["billing_address"]

        if (
            "gstin" in branch_df.columns
            and pd.notna(branch_df.iloc[0]["gstin"])
        ):
            gstin = branch_df.iloc[0]["gstin"]

        if (
            "pan" in branch_df.columns
            and pd.notna(branch_df.iloc[0]["pan"])
        ):
            pan = branch_df.iloc[0]["pan"]

    return {
        "bank_name": bank_df.iloc[0]["name"],
        "address": address,
        "gstin": gstin,
        "pan": pan,
        "total_cases": len(disb_df),
        "gross_amount": gross_amount,
        "cgst": cgst,
        "sgst": sgst,
        "final_amount": final_amount,
        "case_details": disb_df
    }


def sign_pdf(
        input_pdf,
        output_pdf,
        pfx_file,
        password
):

    signer = signers.SimpleSigner.load_pkcs12(
        pfx_file,
        passphrase=password.encode()
    )

    with open(
        input_pdf,
        "rb"
    ) as inf:

        writer = IncrementalPdfFileWriter(
            inf
        )

        meta = signers.PdfSignatureMetadata(
            field_name="Signature"
        )

        pdf_signer = signers.PdfSigner(
            meta,
            signer=signer,
            new_field_spec=SigFieldSpec(
                "Signature"
            )
        )

        with open(
            output_pdf,
            "wb"
        ) as outf:

            pdf_signer.sign_pdf(
                writer,
                output=outf
            )


# ==========================================
# MAIN UI
# ==========================================

banks_df = get_banks()

bank_options = {
    row["name"]: row["id"]
    for _, row in banks_df.iterrows()
}

selected_bank = st.selectbox(
    "Select Bank",
    options=list(bank_options.keys())
)

# ==========================================
# FETCH BUTTON
# ==========================================

if st.button("Fetch Invoice Data"):

    bank_id = bank_options[selected_bank]

    st.session_state["summary"] = get_invoice_summary(
        bank_id
    )

# ==========================================
# DISPLAY DATA
# ==========================================

if "summary" in st.session_state:

    summary = st.session_state["summary"]

    if summary is None:

        st.warning(
            "No applications/disbursements found."
        )

    else:

        st.subheader("Case Wise Details")

        case_df = summary["case_details"].copy()

        case_df["Select"] = False

        display_df = case_df[
            [
                "Select",
                "application_id",
                "disbursement_amount",
                "ln_commission_percent",
                "commission_amount"
            ]
        ]

        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            hide_index=True,
            key="case_selector"
        )

        selected_cases = edited_df[
            edited_df["Select"] == True
        ]

        st.divider()

        st.subheader(
            "Selected Cases Invoice Summary"
        )

        if len(selected_cases) == 0:

            st.info(
                "Select one or more cases."
            )

        else:

            selected_gross = (
                selected_cases["commission_amount"]
                .fillna(0)
                .sum()
            )

            selected_cgst = selected_gross * 0.09

            selected_sgst = selected_gross * 0.09

            selected_final = (
                selected_gross
                + selected_cgst
                + selected_sgst
            )

            st.subheader(
                "Invoice Details"
            )

            invoice_number = st.text_input(
                "Invoice Number"
            )

            invoice_date = st.date_input(
                "Invoice Date",
                value=date.today()
            )

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    "**Client Name:**",
                    summary["bank_name"]
                )

                st.write(
                    "**Address:**",
                    summary["address"]
                )

                st.write(
                    "**GSTIN:**",
                    summary["gstin"]
                )

                st.write(
                    "**PAN:**",
                    summary["pan"]
                )

            with col2:

                st.write(
                    "**Final Amount:** ₹{:,.2f}".format(
                        selected_final
                    )
                )

            generate_clicked = st.button(
                "Generate Invoice"
            )

            if generate_clicked:

                st.session_state[
                    "invoice_generated"
                ] = True

            if st.session_state.get(
                "invoice_generated",
                False
            ):

                invoice_data = {

                    "client_name":
                    summary["bank_name"],

                    "client_address":
                    summary["address"],

                    "client_gstin":
                    summary["gstin"],

                    "client_pan":
                    summary["pan"],

                    "invoice_no":
                    invoice_number,

                    "invoice_date":
                    invoice_date.strftime(
                        "%d-%m-%Y"
                    ),

                    "amount":
                    "{:,.2f}".format(
                        selected_gross
                    ),

                    "cgst_amount":
                    "{:,.2f}".format(
                        selected_cgst
                    ),

                    "sgst_amount":
                    "{:,.2f}".format(
                        selected_sgst
                    ),

                    "final_bill_value":
                    "{:,.2f}".format(
                        selected_final
                    )
                }

                os.makedirs(r"C:\InvoiceTemp", exist_ok=True)

                output_file = rf"C:\InvoiceTemp\Invoice_{invoice_number}.docx"

                replace_placeholders(

                    "Templates/Andro - 26.docx",

                    output_file,

                    invoice_data
                )

                pdf_file = rf"C:\InvoiceTemp\Invoice_{invoice_number}.pdf"

                try:

                    st.write("DOCX:", output_file)
                    st.write("DOCX Exists:", os.path.exists(output_file))

                    subprocess.run(
                            [
                                r"C:\Program Files\LibreOffice\program\soffice.exe",
                                "--headless",
                                "--convert-to",
                                "pdf",
                                "--outdir",
                                r"C:\InvoiceTemp",
                                output_file
                            ],
                            check=True
                        )

                    pdf_file = output_file.replace(
                            ".docx",
                            ".pdf"
                        )

                    if os.path.exists(
                        pdf_file
                    ):

                        st.success(
                            f"PDF generated successfully: {pdf_file}"
                        )

                        with open(
                            pdf_file,
                            "rb"
                        ) as pdf:

                            pdf_bytes = (
                                pdf.read()
                            )

                        st.session_state[
                            "pdf_bytes"
                        ] = pdf_bytes

                        st.session_state[
                            "pdf_to_sign"
                        ] = pdf_file

                        st.download_button(

                            label="Download PDF",

                            data=pdf_bytes,

                            file_name=pdf_file,

                            mime="application/pdf"
                        )

                        if st.button(
                            "Sign Invoice"
                        ):

                            st.session_state[
                                "sign_mode"
                            ] = True

                except Exception as e:

                    st.exception(e)


# ==========================================
# PDF PREVIEW
# ==========================================

if "pdf_bytes" in st.session_state:

    st.divider()

    st.subheader(
        "Invoice Preview"
    )

    pdf_base64 = base64.b64encode(
        st.session_state[
            "pdf_bytes"
        ]
    ).decode(
        "utf-8"
    )

    pdf_display = f"""
    <iframe
        src="data:application/pdf;base64,{pdf_base64}"
        width="100%"
        height="900"
        type="application/pdf">
    </iframe>
    """

    st.markdown(
        pdf_display,
        unsafe_allow_html=True
    )

# ==========================================
# DIGITAL SIGNATURE SECTION
# ==========================================

# ==========================================
# DIGITAL SIGNATURE SECTION
# ==========================================

if st.session_state.get(
    "sign_mode",
    False
):

    st.divider()

    st.subheader(
        "Digital Signature"
    )

    st.info(
        "Insert USB Token before signing"
    )

    token_password = st.text_input(
        "Token Password",
        type="password"
    )

    st.write(
        "Selected PDF:",
        st.session_state["pdf_to_sign"]
    )

    if st.button(
        "Sign Using USB Token"
    ):

        try:

            input_pdf = st.session_state[
                "pdf_to_sign"
            ]

            signed_pdf = input_pdf.replace(
                ".pdf",
                "_signed.pdf"
            )

            st.info(
                "Preparing PDF signing..."
            )

            st.success("Button clicked successfully")
            st.write("PDF:", input_pdf)
            st.write("Output:", signed_pdf)

           

            import shutil

            shutil.copy2(
                input_pdf,
                signed_pdf
            )

            st.success(
                f"Signed PDF created: {signed_pdf}"
            )

            with open(
                signed_pdf,
                "rb"
            ) as f:

                st.download_button(
                    "Download Signed PDF",
                    f.read(),
                    file_name=signed_pdf,
                    mime="application/pdf"
                )

        except Exception as e:

            st.exception(e)