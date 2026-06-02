import streamlit as st
import pandas as pd
from sqlalchemy import create_engine


DB_USER=st.secrets["DB_USER"]
DB_PASSWORD=st.secrets["DB_PASSWORD"]
DB_HOST=st.secrets["DB_HOST"]
DB_PORT=st.secrets["DB_PORT"]
DB_NAME=st.secrets["DB_NAME"]

engine=create_engine(

f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

)

query="""

SELECT

d.id,

l.name customer_name,

a.branch_name bank,

lt.name loan_type,

l.dsa_id,

d.disbursement_date,

d.disbursement_amount,

d.ln_commission_percent_for_payout payout,

d.commission_amount gross_commission,

d.invoice_number,

d.invoice_date,

l.status

FROM disbursements d

LEFT JOIN applications a
ON d.application_id=a.id

LEFT JOIN leads l
ON a.lead_id=l.id

LEFT JOIN loan_types lt
ON l.loan_type_id=lt.id

LIMIT 500

"""

df=pd.read_sql(query,engine)

st.title("Billing & Invoicing")

#################################

c1,c2,c3=st.columns(3)

search=c1.text_input(
    "Search Customer"
)

bank_filter=c2.selectbox(

    "Bank",

    ["All"]+

    sorted(
        df["bank"]
        .dropna()
        .unique()
    )

)

loan_filter=c3.selectbox(

    "Loan Type",

    ["All"]+

    sorted(
        df["loan_type"]
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


if bank_filter!="All":

    filtered=filtered[
        filtered["bank"]
        ==bank_filter
    ]


if loan_filter!="All":

    filtered=filtered[
        filtered["loan_type"]
        ==loan_filter
    ]


#################################

gross=filtered[
    "gross_commission"
].fillna(0)

gst=gross*0.18

total=gross+gst


k1,k2,k3,k4=st.columns(4)

k1.metric(

    "Cases",

    len(filtered)

)

k2.metric(

    "Disbursed",

    f"₹ {(filtered['disbursement_amount'].fillna(0).sum()/10000000):,.1f} Cr"

)

k3.metric(

    "Gross Comm",

    f"₹ {gross.sum():,.0f}"

)

k4.metric(

    "Invoice Value",

    f"₹ {total.sum():,.0f}"

)

#################################

table=filtered.copy()

table["GST"]=gst

table["Total Commission"]=total

table=table[[

"id",

"customer_name",

"bank",

"loan_type",

"disbursement_date",

"disbursement_amount",

"payout",

"gross_commission",

"GST",

"Total Commission"

]]

edited=st.data_editor(

table,

use_container_width=True,

hide_index=True,

num_rows="fixed"

)

#################################

if st.button(
    "Generate Invoice"
):

    st.success(

        "Invoice generation will come next"

    )