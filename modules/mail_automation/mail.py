import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import pandas as pd
from sqlalchemy import create_engine
import streamlit as st

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

APP_PASSWORD = st.secrets["APP_PASSWORD"]

password = st.text_input("Enter Password", type="password")

if password != APP_PASSWORD:
    st.stop()


DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

def send_email(receiver_email, subject, html_content):

    sender_email = st.secrets["SENDER_EMAIL"]
    sender_password = st.secrets["SENDER_PASSWORD"]

    msg = MIMEMultipart()

    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(html_content, "html"))

    server = smtplib.SMTP("smtp.gmail.com", 587)

    server.starttls()

    server.login(sender_email, sender_password)

    server.send_message(msg)

    server.quit()

# Connection
engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Query
query = """
SELECT
    l.name AS case_name,

    lt.name AS loan_type,

    l.loan_amount,

    a.id AS application_no,

    a.loan_insurance_amount,

    d.loan_account_number AS lan_no,

    d.disbursement_amount,

    d.disbursement_date,

    d.pdd_cleared,

    d.otc_cleared,

    d.ln_commission_percent_for_payout AS payout_percent

FROM leads l

INNER JOIN loan_types lt
    ON l.loan_type_id = lt.id

INNER JOIN applications a
    ON l.id = a.lead_id

INNER JOIN disbursements d
    ON a.id = d.application_id

LIMIT 100;
"""

# Fetch data
df = pd.read_sql(query, engine)

import streamlit as st

st.title("Loan Network Dashboard")

# Search box
search = st.text_input("Search Customer Name")

# Loan type filter
loan_types = df["loan_type"].unique()
selected_loan_type = st.selectbox(
    "Select Loan Type",
    ["All"] + list(loan_types)
)

# Apply filters
filtered_df = df.copy()

if search:
    filtered_df = filtered_df[
        filtered_df["case_name"].str.contains(search, case=False, na=False)
    ]

if selected_loan_type != "All":
    filtered_df = filtered_df[
        filtered_df["loan_type"] == selected_loan_type
    ]

# Display filtered data
st.dataframe(filtered_df)

# Select application number
selected_application = st.selectbox(
    "Select Application Number",
    filtered_df["application_no"].unique()
)

# Get selected row
selected_row = filtered_df[
    filtered_df["application_no"] == selected_application
].iloc[0]

st.subheader("Generated Email Preview")

st.subheader("Generated Email Preview")

html_template = f"""
<div style="font-family: Arial, sans-serif; padding: 20px;">

<p>Hi Team,</p>

<p>Please find below secured case details.</p>

<br>

<table
border="1"
cellpadding="12"
cellspacing="0"
style="
border-collapse: collapse;
width: 700px;
font-size: 14px;
">

<tr style="background-color:#f2f2f2;">
    <th colspan="2" style="text-align:center; font-size:18px;">
        Secured Cases
    </th>
</tr>

<tr>
    <td style="font-weight:bold; width:40%;">
        Case Name
    </td>
    <td>
        {selected_row['case_name']}
    </td>
</tr>

<tr>
    <td style="font-weight:bold;">
        Application No.
    </td>
    <td>
        {selected_row['application_no']}
    </td>
</tr>

<tr>
    <td style="font-weight:bold;">
        LAN No.
    </td>
    <td>
        {selected_row['lan_no']}
    </td>
</tr>

<tr>
    <td style="font-weight:bold;">
        Loan Type
    </td>
    <td>
        {selected_row['loan_type']}
    </td>
</tr>

<tr>
    <td style="font-weight:bold;">
        Loan Amount
    </td>
    <td>
        ₹ {selected_row['loan_amount']}
    </td>
</tr>

<tr>
    <td style="font-weight:bold;">
        Insurance Amount Added
    </td>
    <td>
        ₹ {selected_row['loan_insurance_amount']}
    </td>
</tr>

<tr>
    <td style="font-weight:bold;">
        Disbursed Amount
    </td>
    <td>
        ₹ {selected_row['disbursement_amount']}
    </td>
</tr>

<tr>
    <td style="font-weight:bold;">
        Disbursement Date
    </td>
    <td>
        {selected_row['disbursement_date']}
    </td>
</tr>

<tr>
    <td style="font-weight:bold;">
        PDD Cleared
    </td>
    <td>
        {"Yes" if selected_row['pdd_cleared'] else "No"}
    </td>
</tr>

<tr>
    <td style="font-weight:bold;">
        OTC Cleared
    </td>
    <td>
        {"Yes" if selected_row['otc_cleared'] else "No"}
    </td>
</tr>

<tr>
    <td style="font-weight:bold;">
        Payout %
    </td>
    <td>
        {selected_row['payout_percent']}
    </td>
</tr>

</table>

<br><br>

<p>Regards,<br>
Loan Network Team</p>

</div>
"""


st.markdown(html_template, unsafe_allow_html=True)

receiver_email = st.text_input("Receiver Email")

if st.button("Send Email"):

    if receiver_email == "":
        st.error("Please Enter Receiver Email")

    else:
        send_email(
            receiver_email,
            "Secured Case Details",
            html_template
        )

        st.success("Email Sent Successfully")

st.subheader("HTML Email Code")

st.code(html_template, language="html")