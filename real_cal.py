import streamlit as st
import pandas as pd
import altair as alt

# --- פונקציות חישוב ---

def calculate_monthly_payment(principal, annual_rate, total_months):
    if principal == 0 or total_months == 0:
        return 0
    if annual_rate == 0:
        return principal / total_months
    r = (annual_rate / 100) / 12
    return principal * (r * (1 + r)**total_months) / ((1 + r)**total_months - 1)

def calculate_balance(principal, annual_rate, total_months, elapsed_months):
    if principal == 0 or elapsed_months == 0:
        return principal
    if elapsed_months >= total_months:
        return 0
    if annual_rate == 0:
        return principal - (principal / total_months) * elapsed_months
    r = (annual_rate / 100) / 12
    return principal * (((1 + r)**total_months - (1 + r)**elapsed_months) / ((1 + r)**total_months - 1))

def calculate_purchase_tax(price, is_single_home):
    # מדרגות מס רכישה משוערות
    tax = 0
    if is_single_home:
        b1, b2, b3, b4 = 1978745, 2347040, 6055070, 20183565
        if price <= b1:
            tax = 0
        elif price <= b2:
            tax = (price - b1) * 0.035
        elif price <= b3:
            tax = (b2 - b1) * 0.035 + (price - b2) * 0.05
        elif price <= b4:
            tax = (b2 - b1) * 0.035 + (b3 - b2) * 0.05 + (price - b3) * 0.08
        else:
            tax = (b2 - b1) * 0.035 + (b3 - b2) * 0.05 + (b4 - b3) * 0.08 + (price - b4) * 0.10
    else:
        # דירה נוספת / משקיע
        b1 = 6055070
        if price <= b1:
            tax = price * 0.08
        else:
            tax = b1 * 0.08 + (price - b1) * 0.10
    return tax

# --- הגדרת העמוד ---
st.set_page_config(page_title="Real Estate Holding Strategy")

st.title("🏗️ דשבורד אסטרטגיות החזקת נדל\"ן")
st.markdown("---")

# --- נתוני הנכס והחזקה ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("נתוני הנכס")
    appraisal_value = st.number_input("ערך דירה לפי שמאות (₪)", min_value=0, value=2000000, step=50000)
    purchase_price = st.number_input("מחיר דירה בפועל (₪)", min_value=0, value=2000000, step=50000)
    
with col2:
    st.subheader("צפי והחזקה")
    holding_years = st.number_input("זמן החזקה מתוכנן (בשנים)", min_value=1, value=5, step=1)
    appreciation_rate = st.number_input("עליית שווי שנתית (%)", value=0.0, step=0.5, format="%0.1f")

st.markdown("---")

# --- הוצאות נלוות ומס רכישה ---
st.subheader("💼 מיסים והוצאות נלוות לרכישה")
tax_col1, tax_col2, tax_col3 = st.columns(3)

with tax_col1:
    st.markdown("**מס רכישה**")
    buyer_status = st.radio("סטטוס רוכש:", ["דירה יחידה", "דירה חלופית / נוספת (8%-10%)"])
    is_single_home = (buyer_status == "דירה יחידה")
    calculated_tax = calculate_purchase_tax(purchase_price, is_single_home)
    st.metric("מס רכישה לתשלום", f"₪{calculated_tax:,.0f}")

with tax_col2:
    st.markdown("**אנשי מקצוע (אחוזים)**")
    brokerage_pct = st.number_input("אחוז תיווך קנייה (%)", min_value=0.0, value=0.0, step=0.1)
    lawyer_pct = st.number_input("שכר טרחה עו״ד (%)", min_value=0.0, value=0.0, step=0.1)

with tax_col3:
    st.markdown("**הוצאות קבועות (₪)**")
    mortgage_advisor = st.number_input("יועץ משכנתא (₪)", min_value=0, value=0, step=500)
    other_expenses = st.number_input("הוצאות נוספות (שמאות/שיפוץ)", min_value=0, value=15000, step=1000)

# סכום ההוצאות
brokerage_cost = purchase_price * (brokerage_pct / 100)
lawyer_cost = purchase_price * (lawyer_pct / 100)
total_additional_expenses = calculated_tax + brokerage_cost + lawyer_cost + mortgage_advisor + other_expenses

# שורת הסיכום החדשה שהוספנו
st.info(f"💡 **סה״כ הוצאות נלוות ומיסים (מעבר למחיר הדירה):** ₪{total_additional_expenses:,.0f}")

st.markdown("---")

# --- מסלולי משכנתא ---
st.subheader("🏦 מסלולי משכנתא (שפיצר)")
num_tracks = st.slider("מספר מסלולים", min_value=1, max_value=4, value=2)

tracks_data = []
cols = st.columns(num_tracks)

for i in range(num_tracks):
    with cols[i]:
        st.markdown(f"**מסלול {i+1}**")
        amount = st.number_input(f"סכום (₪)", min_value=0, value=0, step=10000, key=f"amount_{i}")
        months = st.number_input(f"תקופה (חודשים)", min_value=0, value=360, step=12, key=f"months_{i}")
        rate = st.number_input(f"ריבית שנתית (%)", value=4.0, step=0.1, format="%0.2f", key=f"rate_{i}")
        tracks_data.append({"amount": amount, "months": months, "rate": rate})

# --- חישובי ליבה ---
holding_months = holding_years * 12
future_value = purchase_price * ((1 + (appreciation_rate / 100)) ** holding_years)

total_loan_amount = sum(t['amount'] for t in tracks_data)
initial_equity = purchase_price + total_additional_expenses - total_loan_amount

total_monthly_payment = 0
total_outstanding_balance = 0
total_mortgage_paid = 0

for track in tracks_data:
    pmt = calculate_monthly_payment(track['amount'], track['rate'], track['months'])
    bal = calculate_balance(track['amount'], track['rate'], track['months'], holding_months)
    months_paid = min(holding_months, track['months']) 
    
    total_monthly_payment += pmt
    total_outstanding_balance += bal
    total_mortgage_paid += (pmt * months_paid)

net_equity = future_value - total_outstanding_balance

# פירוק תשלום המשכנתא
principal_paid = total_loan_amount - total_outstanding_balance
interest_paid = total_mortgage_paid - principal_paid

# מדדים פיננסיים
net_profit = net_equity - initial_equity - total_mortgage_paid
ltv = (total_loan_amount / appraisal_value * 100) if appraisal_value > 0 else 0
total_investment = purchase_price + total_additional_expenses

equity_growth_pct = ((net_equity / initial_equity) - 1) * 100 if initial_equity > 0 else 0
roi = (net_profit / total_investment * 100) if total_investment > 0 else 0
roe = (net_profit / initial_equity * 100) if initial_equity > 0 else 0

# --- הצגת תוצאות ---
st.markdown("---")
st.subheader("📊 תוצאות אסטרטגיית ההחזקה (לאחר {} שנים)".format(holding_years))

# שורה 1: שווי והון
res_col1, res_col2 = st.columns(2)
with res_col1:
    st.metric("הון עצמי התחלתי (כולל הוצאות ומיסים)", f"₪{initial_equity:,.0f}")
    st.metric("שווי נכס עתידי", f"₪{future_value:,.0f}")
with res_col2:
    st.metric("יתרת משכנתא לסילוק", f"₪{total_outstanding_balance:,.0f}")
    st.metric("הון עצמי נטו בסוף התקופה", f"₪{net_equity:,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

# שורה 2: ניתוח תזרימי ומשכנתא
st.markdown("**🔍 ניתוח משכנתא ותזרים בתקופת ההחזקה:**")
mort_col1, mort_col2 = st.columns(2)
with mort_col1:
    st.metric("סך החזר חודשי (התחלתי)", f"₪{total_monthly_payment:,.0f}")
    st.metric("סך הכל שולם לבנק", f"₪{total_mortgage_paid:,.0f}")
with mort_col2:
    st.metric("מתוכו שולם לקרן (נשאר אצלך)", f"₪{principal_paid:,.0f}")
    st.metric("מתוכו שולם לריבית (הוצאה)", f"₪{interest_paid:,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

# שורה 3: מדדים פיננסיים
fin_col1, fin_col2 = st.columns(2)
with fin_col1:
    st.metric("LTV (מינוף מול שמאות)", f"{ltv:,.1f}%")
    st.metric("Equity Growth (גידול בהון)", f"{equity_growth_pct:,.1f}%")
with fin_col2:
    st.metric("Net Profit (רווח נטו תזרימי)", f"₪{net_profit:,.0f}")
    st.metric("ROE (תשואה נטו על ההון)", f"{roe:,.1f}%")

st.markdown("---")

# --- הגרף הריבועי הממורכז ---
st.markdown("### 📈 התפתחות השווי והחוב על פני זמן")
months_list = list(range(holding_months + 1))
values_over_time = []
balances_over_time = []
equities_over_time = [] 

for m in months_list:
    monthly_appreciation_rate = (1 + (appreciation_rate / 100)) ** (1/12) - 1
    val_at_m = purchase_price * ((1 + monthly_appreciation_rate) ** m)
    values_over_time.append(val_at_m)
    
    balance_at_m = sum([calculate_balance(t['amount'], t['rate'], t['months'], m) for t in tracks_data])
    balances_over_time.append(balance_at_m)
    
    equity_at_m = val_at_m - balance_at_m
    equities_over_time.append(equity_at_m)

df_chart = pd.DataFrame({
    "Month": months_list,
    "Property Value": values_over_time,
    "Mortgage Balance": balances_over_time,
    "Net Equity (Your Share)": equities_over_time
}).set_index("Month")

df_melted = df_chart.reset_index().melt('Month', var_name='Metric', value_name='Value')

chart = alt.Chart(df_melted).mark_line().encode(
    x=alt.X('Month', title='חודש החזקה'),
    y=alt.Y('Value', title='סכום (₪)', scale=alt.Scale(domainMin=0)),
    color=alt.Color('Metric', legend=alt.Legend(title="מקרא", orient='top'))
).properties(
    height=450 
).interactive() 

st.altair_chart(chart, use_container_width=True)
