import streamlit as st

st.set_page_config(
    page_title="Loan Network Dashboard",
    layout="wide"
)

st.title("Loan Network Dashboard")

module = st.sidebar.selectbox(
    "Select Module",
    [
        "Mail Automation",
        "Dashboard",
        "Invoice Generation"
    ]
)

if module == "Mail Automation":

    from modules.mail_automation.mail import *

elif module == "Dashboard":

    st.write("Dashboard Module Coming Soon")

elif module == "Invoice Generation":

    st.write("Invoice Module Coming Soon")