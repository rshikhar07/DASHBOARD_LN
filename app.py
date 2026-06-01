import streamlit as st

st.set_page_config(
    page_title="Loan Network Dashboard",
    layout="wide"
)

st.title("Loan Network Dashboard")

st.sidebar.title("Loan Network")

module = st.sidebar.radio(

    "",

    [

        "All Leads",

        "Billing",

        "Collection",

        "Overview",

        "Mail Automation"

    ]

)

if module == "Mail Automation":

    from modules.mail_automation.mail import *

elif module == "All Leads":

    from modules.dashboard.dashboard import *

elif module == "Invoice Generation":

    st.write("Invoice Module Coming Soon")