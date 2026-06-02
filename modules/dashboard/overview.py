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

l.id lead_id,

l.loan_amount,

lt.name loan_type,

d.disbursement_amount,

d.commission_amount

FROM leads l

LEFT JOIN loan_types lt
ON l.loan_type_id=lt.id

LEFT JOIN applications a
ON l.id=a.lead_id

LEFT JOIN disbursements d
ON a.id=d.application_id

LIMIT 1000

"""

df=pd.read_sql(
query,
engine
)

#################################

st.title(
"Overview Dashboard"
)

#################################

k1,k2,k3,k4=st.columns(4)

k1.metric(

"Total Leads",

df["lead_id"].nunique()

)

k2.metric(

"Loan Volume",

f"₹ {(df['loan_amount'].fillna(0).sum()/10000000):,.1f} Cr"

)

k3.metric(

"Disbursed",

f"₹ {(df['disbursement_amount'].fillna(0).sum()/10000000):,.1f} Cr"

)

k4.metric(

"Commission",

f"₹ {df['commission_amount'].fillna(0).sum():,.0f}"

)

#################################

st.subheader(
"Loan Type Breakdown"
)

breakdown=(

df.groupby(
"loan_type"
)

["lead_id"]

.count()

.sort_values(
ascending=False
)

)

st.bar_chart(
breakdown
)

#################################

st.subheader(
"Business Summary"
)

summary=pd.DataFrame({

"Metric":[

"Leads",

"Disbursed",

"Commission"

],

"Value":[

df["lead_id"].nunique(),

df["disbursement_amount"].fillna(0).sum(),

df["commission_amount"].fillna(0).sum()

]

})

st.dataframe(
summary,
hide_index=True
)