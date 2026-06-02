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

l.name customer,

d.invoice_number,

d.commission_amount expected_amount,

d.invoice_date,

d.commission_amount collected_amount

FROM disbursements d

LEFT JOIN applications a
ON d.application_id=a.id

LEFT JOIN leads l
ON a.lead_id=l.id

LIMIT 500

"""

df=pd.read_sql(
query,
engine
)


df["expected_amount"]=df[
"expected_amount"
].fillna(0)

df["collected_amount"]=df[
"collected_amount"
].fillna(0)

df["difference"]=(
df["expected_amount"]
-
df["collected_amount"]
)

df["status"]=df[
"difference"
].apply(

lambda x:
"Matched"
if x==0
else "Pending"

)

#################################

st.title(
"Collection & Reconciliation"
)

k1,k2,k3,k4=st.columns(4)

k1.metric(

"Expected",

f"₹ {df['expected_amount'].sum():,.0f}"

)

k2.metric(

"Collected",

f"₹ {df['collected_amount'].sum():,.0f}"

)

k3.metric(

"Pending",

f"₹ {df['difference'].sum():,.0f}"

)

k4.metric(

"Mismatch Cases",

df[
df["status"]!="Matched"
].shape[0]

)

#################################

st.dataframe(

df[[

"customer",

"invoice_number",

"expected_amount",

"collected_amount",

"difference",

"status"

]],

use_container_width=True,

hide_index=True

)