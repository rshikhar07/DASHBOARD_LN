import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os


DB_USER = st.secrets["DB_USER"]

DB_PASSWORD = st.secrets["DB_PASSWORD"]

DB_HOST = st.secrets["DB_HOST"]

DB_PORT = st.secrets["DB_PORT"]

DB_NAME = st.secrets["DB_NAME"]


engine=create_engine(

f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

)


query="""

SELECT

l.id AS lead_id,

l.updated_at,

l.name AS customer_name,

l.status AS lead_status,

l.loan_amount,

l.dsa_id,

lt.name AS loan_type,

a.id AS application_no,

a.branch_name AS bank,

a.is_from_external_dsa,

d.disbursement_amount,

d.disbursement_date,

d.invoice_number,

d.invoice_date,

d.commission_amount

FROM leads l

LEFT JOIN loan_types lt
ON l.loan_type_id=lt.id

LEFT JOIN applications a
ON l.id=a.lead_id

LEFT JOIN disbursements d
ON a.id=d.application_id

LIMIT 500

"""


df=pd.read_sql(query,engine)


st.title("All Leads")

#################################

col1,col2,col3=st.columns(3)

search=col1.text_input(
    "Search Customer"
)

loan_filter=col2.selectbox(

    "Loan Type",

    ["All"]+

    sorted(
        df["loan_type"]
        .dropna()
        .unique()
    )

)

status_filter=col3.selectbox(

    "Status",

    ["All"]+

    sorted(
        df["lead_status"]
        .dropna()
        .unique()
    )

)

#################################

filtered=df.copy()

if search:

    filtered=filtered[
        filtered["customer_name"]
        .str.contains(
            search,
            case=False,
            na=False
        )
    ]

if loan_filter!="All":

    filtered=filtered[
        filtered["loan_type"]
        ==loan_filter
    ]

if status_filter!="All":

    filtered=filtered[
        filtered["lead_status"]
        ==status_filter
    ]

#################################

c1,c2,c3,c4=st.columns(4)

c1.metric(
    "Total Leads",
    len(filtered)
)

c2.metric(

    "Total Loan Amount",

    f"₹ {(filtered['loan_amount'].fillna(0).sum()/10000000):,.1f} Cr"

)

c3.metric(

    "Disbursed Amount",

    f"₹ {(filtered['disbursement_amount'].fillna(0).sum()/10000000):,.1f} Cr"

)

c4.metric(

    "External DSA",

    filtered[
        filtered["is_from_external_dsa"]==True
    ].shape[0]

)

#################################

table = filtered[[
"updated_at",
"lead_id",
"customer_name",
"bank",
"loan_type",
"loan_amount",
"disbursement_amount",
"lead_status"
]]

table.columns=[

"Updated",

"Lead ID",

"Customer",

"Bank",

"Loan Type",

"Loan Amount",

"Disbursement",

"Status"

]

st.dataframe(

table,

use_container_width=True,

hide_index=True

)
