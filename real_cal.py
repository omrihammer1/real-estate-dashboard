import streamlit as st
import pandas as pd
import altair as alt

# --- הגדרת העמוד ---
st.set_page_config(page_title="Real Estate Holding Strategy", layout="centered")

# --- הזרקת CSS ליישור לימין (RTL) ---
st.markdown("""
<style>
    /* הגדרת כיוון כללי של האפליקציה מימין לשמאל */
    .stApp, .block-container {
        direction: rtl;
        text-align: right;
        font-family: 'Heebo', 'Alef', 'Segoe UI', sans-serif;
    }
    
    /* יישור טקסט ספציפי לימין עבור כותרות ופסקאות */
    p, h1, h2, h3, h4, h5, h6, span, label, div {
        text-align: right !important;
    }
    
    /* תיקון שדות קלט למספרים כדי שהטקסט בתוכם יהיה מימין */
    input {
        text-align: right !important;
        direction: ltr !important; /* משאיר את המספרים עצמם בכיוון נכון */
    }
    
    /* סידור קוביות המדדים (Metrics) כך שיהיו מיושרות לימין */
    div[data-testid="metric-container"] {
        text-align: right;
    }
    
    /* תיקון גרפי לכפתורי בחירה (Radio / Checkbox) */
    .stCheckbox > div, .stRadio > div {
        direction: rtl;
    }
</style>
""", unsafe_allow_html=True)


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
        b1 = 6055070
        if price <= b1:
            tax = price * 0.08
        else:
            tax = b1 * 0.08 + (price - b1) * 0.10
    return tax

st.title("🏗️ דשבורד אסטרטגיות החזקת נדל\"ן")
st.markdown("---")

# --- נתוני הנכס והחזקה ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("נתוני הנכס")
    appraisal_value = st.number_input("ערך דירה לפי שמאות (₪)", min_value=0.0, value=2000000.0, step=50000.0)
    purchase_price = st.number_input("מחיר דירה בפועל (₪)", min_value=0.0, value=2000000.0, step=50000.0)
    
with col2:
    st.subheader("צפי והחזקה")
    holding_years = st.number_input("זמן החזקה מתוכנן (בשנים)", min_value=1, value=5, step=1)
    appreciation_rate = st.number_input("עליית שווי שנתית (%)", value=0.0, step=0.5, format="%0.1f")

st.markdown("---")

# --- הוצאות נלוות ומס רכישה ---
st.subheader("💼 מיסים והוצאות נלוות לרכישה")
tax_col1, tax_col2, tax_col3 = st.columns(3)

vat_rate = st.number_input("שיעור מע\"מ בסיסי לתוספת (%)", min_value=0.0, value=17.0, step=1.0)
vat_multiplier = 1.0 + (vat_rate / 100.0)

with tax_col1:
    st.markdown("**מס רכישה**")
    buyer_status = st.radio("סטטוס רוכש:", ["דירה יחידה", "דירה חלופית / נוספת (8%-10%)"])
    is_single_home = (buyer_status == "דירה יחידה")
    calculated_tax = calculate_purchase_tax(purchase_price, is_single_home)
    st.metric("מס רכישה מחושב", f"₪{calculated_tax:,.0f}")

with tax_col2:
    st.markdown("**אנשי מקצוע**")
    brokerage_pct = st.number_input("אחוז תיווך קנייה (%)", min_value=0.0, value=0.0, step=0.1)
    add_vat_brokerage = st.checkbox("➕ הוסף מע״מ לתיווך", value=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    lawyer_fee_raw = st.number_input("שכר טרחה עו״ד (₪)", min_value=0.0, value=0.0, step=1000.0)
    add_vat_lawyer = st.checkbox("➕ הוסף מע״מ לעו״ד", value=True)
    
with tax_col3:
    st.markdown("**יועצים והוצאות נוספות (₪)**")
    mortgage_advisor = st.number_input("יועץ משכנתא (₪)", min_value=0.0, value=0.0, step=500.0)
    add_vat_advisor = st.checkbox("➕ הוסף מע״מ ליועץ", value=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    other_expenses = st.number_input("הוצאות נוספות (שמאות/שיפוץ)", min_value=0.0, value=15000.0, step=1000.0)
    add_vat_other = st.checkbox("➕ הוסף מע״מ להוצאות", value=False)

brokerage_cost = purchase_price * (brokerage_pct / 100.0)
if add_vat_brokerage: brokerage_cost *= vat_multiplier
lawyer_cost = lawyer_fee_raw
if add_vat_lawyer: lawyer_cost *= vat_multiplier
advisor_cost = mortgage_advisor
if add_vat_advisor: advisor_cost *= vat_multiplier
other_cost = other_expenses
if add_vat_other: other_cost *= vat_multiplier

total_additional_expenses = calculated_tax + brokerage_cost + lawyer_cost + advisor_cost + other_cost

st.info(f"💡 **סה״כ הוצאות נלוות ומיסים:** ₪{total_additional_expenses:,.0f}")

st.markdown("---")

# --- מסלולי משכנתא ---
st.subheader("🏦 מסלולי משכנתא (שפיצר)")
num_tracks = st.slider("מספר מסלולים", min_value=1, max_value=4, value=2)

tracks_data = []
cols = st.columns(num_tracks)

for i in range(num_tracks):
    with cols[i]:
        st.markdown(f"**מסלול {i+1}**")
        amount = st.number_input(f"סכום (₪)", min_value=0.0, value=0.0, step=10000.0, key=f"amount_{i}")
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
principal_paid = total_loan_amount - total_outstanding_balance
interest_paid = total_mortgage_paid - principal_paid
net_profit = net_equity - initial_equity - total_mortgage_paid
ltv = (total_loan_amount / appraisal_value * 100) if appraisal_value > 0 else 0
total_investment = purchase_price + total_additional_expenses

equity_growth_pct = ((net_equity / initial_equity) - 1) * 100 if initial_equity > 0 else 0
roi = (net_profit / total_investment * 100) if total_investment > 0 else 0
roe = (net_profit / initial_equity * 100) if initial_equity > 0 else 0
yearly_roi = roe / holding_years if holding_years > 0 else 0

# --- הצגת תוצאות ---
st.markdown("---")
st.subheader("📊 תוצאות אסטרטגיית ההחזקה (לאחר {} שנים)".format(holding_years))

res_col1, res_col2 = st.columns(2)
with res_col1:
    st.metric("הון עצמי התחלתי (כולל הוצאות ומיסים)", f"₪{initial_equity:,.0f}")
    st.metric("שווי נכס עתידי", f"₪{future_value:,.0f}")
with res_col2:
    st.metric("יתרת משכנתא לסילוק", f"₪{total_outstanding_balance:,.0f}")
    st.metric("הון עצמי נטו בסוף התקופה", f"₪{net_equity:,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("**🔍 ניתוח משכנתא ותזרים בתקופת ההחזקה:**")
mort_col1, mort_col2 = st.columns(2)
with mort_col1:
    st.metric("סך החזר חודשי (התחלתי)", f"₪{total_monthly_payment:,.0f}")
    st.metric("סך הכל שולם לבנק", f"₪{total_mortgage_paid:,.0f}")
with mort_col2:
    st.metric("מתוכו שולם לקרן (נשאר אצלך)", f"₪{principal_paid:,.0f}")
    st.metric("מתוכו שולם לריבית (הוצאה)", f"₪{interest_paid:,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

fin_col1, fin_col2 = st.columns(2)
with fin_col1:
    st.metric("LTV (מינוף מול שמאות)", f"{ltv:,.1f}%")
    st.metric("Equity Growth (גידול בהון)", f"{equity_growth_pct:,.1f}%")
with fin_col2:
    st.metric("Net Profit (רווח נטו תזרימי)", f"₪{net_profit:,.0f}")
    st.metric("ROE (תשואה נטו על ההון)", f"{roe:,.1f}%")

st.markdown("---")

# --- הגרף ---
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
    equities_over_time.append(val_at_m - balance_at_m)

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
).properties(height=450).interactive() 

st.altair_chart(chart, use_container_width=True)

# --- סוכן הנדל"ן (ניתוח אסטרטגי) ---
st.markdown("---")
st.subheader("🤖 ניתוח אסטרטגי - יועץ השקעות מובנה")

advisor_messages = []

if total_loan_amount > 0:
    weighted_rate_sum = sum(t['amount'] * t['rate'] for t in tracks_data)
    avg_mortgage_rate = weighted_rate_sum / total_loan_amount
else:
    avg_mortgage_rate = 0

if holding_years <= 3:
    strategy_type = "עסקת אקזיט קצרת טווח (פליפ)"
elif 3 < holding_years <= 7:
    strategy_type = "עסקת השבחה לטווח בינוני"
else:
    strategy_type = "החזקה לטווח ארוך (גידול הון פנסיוני)"

advisor_messages.append(f"🎯 **פרופיל אסטרטגי:** המספרים מצביעים על {strategy_type}. נגזרות ניהול הסיכונים להלן מותאמות לפרק זמן זה:")

if total_loan_amount > 0:
    if avg_mortgage_rate > appreciation_rate and ltv > 40:
        advisor_messages.append(f"⚠️ **סיכון חשיפה (Negative Leverage):** עלות הכסף שלך (ריבית ממוצעת של כ-{avg_mortgage_rate:.1f}%) גבוהה מקצב צמיחת שווי הנכס ({appreciation_rate:.1f}%). בתרחיש כזה, המינוף פועל נגדך ושוחק את ההון העצמי מדי חודש. שקול הקטנת LTV, קיצור תקופת ההלוואה לחסכון בריבית, או בחינת חלופות השקעה אחרות.")
    elif appreciation_rate > avg_mortgage_rate + 1 and ltv > 40:
        advisor_messages.append(f"🚀 **מינוף חיובי (Positive Leverage):** קצב צמיחת הנכס הצפוי עוקף את עלות החוב שלך. זוהי אינדיקציה לכך שמינפת נכון - הכסף של הבנק עובד בשבילך ומייצר תשואה עודפת (ROE) על ההון העצמי שהשקעת.")

if net_profit > 0:
    expenses_to_profit_ratio = total_additional_expenses / net_profit
    if expenses_to_profit_ratio > 0.4:
        advisor_messages.append(f"💸 **משקולת הוצאות כבדה:** ההוצאות הנלוות והמיסים (₪{total_additional_expenses:,.0f}) מהווים יותר מ-{expenses_to_profit_ratio*100:.0f}% מהרווח הנקי העתידי שלך. בעסקאות קצרות מועד, עלויות כניסה ויציאה יכולות למחוק את הכדאיות. שווה לבדוק אם הארכת תוכנית העבודה (שנות ההחזקה) תפזר את ההוצאה ותשפר את ה-Yearly ROI.")
elif net_profit <= 0 and initial_equity > 0:
    advisor_messages.append(f"🛑 **שחיקת הון מוחלטת:** תחת הנחות עליית השווי הנוכחיות, יחד עם היעדר הכנסה משכירות, העסקה רושמת הפסד תזרימי. אסטרטגיה כזו כדאית אך ורק במצב של ציפייה מוצקה לשינוי ייעוד, פינוי-בינוי ודאי, או אם מדובר בנכס למגורים שמייתר תשלום שכירות חלופי.")

if total_monthly_payment > (purchase_price * 0.005) and ltv > 60:
    advisor_messages.append(f"🌊 **ניהול משברים ונזילות:** ההחזר החודשי יוצר עומס תזרימי כבד ביחס לשווי הנכס. כדי למנוע מצוקת נזילות בזמני משבר (למשל, קפיצה משמעותית בפריים או עלויות שיפוץ פתאומיות), מומלץ להכין 'באפר' (רזרבה נזילה) של 6-12 חודשי משכנתא מראש בחשבון נפרד.")

if 0 < yearly_roi < 4.0:
    advisor_messages.append(f"📊 **תשואה אלטרנטיבית:** התשואה השנתית נטו על ההון עומדת על {yearly_roi:.1f}%. בסביבת מאקרו שבה ריבית חסרת סיכון מגרדת את ה-4%, כדאי לוודא שפרמיית הסיכון של נדל\"ן (חוסר נזילות, התעסקות) שווה את התשואה, או לחשב מחדש את יעד שווי המכירה.")

if len(advisor_messages) == 1:
    advisor_messages.append("✅ **יציבות אסטרטגית:** על פניו, תמהיל המינוף, התזרים ותחזית הצמיחה מאוזנים. המספרים מציגים תוכנית עבודה יציבה, ללא נורות אזהרה בוהקות שמצריכות התערבות מיידית.")

for msg in advisor_messages:
    st.info(msg)
