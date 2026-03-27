import streamlit as st
import pandas as pd
import altair as alt

# --- אתחול משתני מערכת לשמירת אסטרטגיות ---
if 'saved_strategies' not in st.session_state:
    st.session_state.saved_strategies = {}

# רשימת המפתחות שצריך לשמור כדי לטעון אסטרטגיה חזרה
state_keys = [
    'appraisal_val', 'purchase_val', 'hold_years', 'appreciation',
    'buyer_status_rb', 'vat_rate_num', 'brokerage_pct_num', 'add_vat_brokerage_cb',
    'lawyer_fee_raw_num', 'add_vat_lawyer_cb', 'mortgage_advisor_num', 'add_vat_advisor_cb',
    'other_expenses_num', 'add_vat_other_cb', 'mortgage_mode_rb',
    'simple_mortgage_amt', 'simple_mortgage_years', 'simple_mortgage_rate',
    'num_tracks_radio'
]
for i in range(4):
    state_keys.extend([f"amount_{i}", f"months_{i}", f"rate_{i}"])

# --- פונקציות חישוב ---
def calculate_monthly_payment(principal, annual_rate, total_months):
    if principal == 0 or total_months == 0: return 0
    if annual_rate == 0: return principal / total_months
    r = (annual_rate / 100) / 12
    return principal * (r * (1 + r)**total_months) / ((1 + r)**total_months - 1)

def calculate_balance(principal, annual_rate, total_months, elapsed_months):
    if principal == 0 or elapsed_months == 0: return principal
    if elapsed_months >= total_months: return 0
    if annual_rate == 0: return principal - (principal / total_months) * elapsed_months
    r = (annual_rate / 100) / 12
    return principal * (((1 + r)**total_months - (1 + r)**elapsed_months) / ((1 + r)**total_months - 1))

def calculate_purchase_tax(price, is_single_home):
    tax = 0
    if is_single_home:
        b1, b2, b3, b4 = 1978745, 2347040, 6055070, 20183565
        if price <= b1: tax = 0
        elif price <= b2: tax = (price - b1) * 0.035
        elif price <= b3: tax = (b2 - b1) * 0.035 + (price - b2) * 0.05
        elif price <= b4: tax = (b2 - b1) * 0.035 + (b3 - b2) * 0.05 + (price - b3) * 0.08
        else: tax = (b2 - b1) * 0.035 + (b3 - b2) * 0.05 + (b4 - b3) * 0.08 + (price - b4) * 0.10
    else:
        b1 = 6055070
        if price <= b1: tax = price * 0.08
        else: tax = b1 * 0.08 + (price - b1) * 0.10
    return tax

# --- הגדרת העמוד והעיצוב ---
st.set_page_config(page_title="Real Estate Holding Strategy", layout="centered")

st.markdown("""
<style>
    .stApp, .block-container { direction: rtl; text-align: right; font-family: 'Heebo', 'Alef', sans-serif; }
    p, h1, h2, h3, h4, h5, h6, span, label, div { text-align: right !important; }
    input { text-align: right !important; direction: ltr !important; }
    div[data-testid="metric-container"] { text-align: right; }
    .stCheckbox > div, .stRadio > div { direction: rtl; }
</style>
""", unsafe_allow_html=True)

# --- תפריט צד (Sidebar) לניהול אסטרטגיות ---
with st.sidebar:
    st.header("💾 ניהול אסטרטגיות")
    st.markdown("כאן תוכל לשמור את הנתונים שהזנת תחת שם, ולחזור אליהם בקלות מאוחר יותר.")
    
    new_strat_name = st.text_input("שם האסטרטגיה לשמירה:")
    if st.button("📥 שמור תרחיש נוכחי"):
        if new_strat_name:
            current_state = {k: st.session_state[k] for k in state_keys if k in st.session_state}
            st.session_state.saved_strategies[new_strat_name] = current_state
            st.success(f"התרחיש '{new_strat_name}' נשמר בהצלחה!")
        else:
            st.warning("אנא הזן שם לאסטרטגיה.")
            
    st.markdown("---")
    saved_names = list(st.session_state.saved_strategies.keys())
    if saved_names:
        selected_strat = st.selectbox("📂 בחר אסטרטגיה לטעינה:", options=saved_names)
        if st.button("🔄 טען נתונים"):
            for k, v in st.session_state.saved_strategies[selected_strat].items():
                st.session_state[k] = v
            st.rerun()

st.title("🏗️ דשבורד אסטרטגיות החזקת נדל\"ן")
st.markdown("---")

# --- נתוני הנכס והחזקה ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("נתוני הנכס")
    appraisal_value = st.number_input("ערך דירה לפי שמאות (₪)", min_value=0.0, value=2000000.0, step=50000.0, key="appraisal_val")
    purchase_price = st.number_input("מחיר דירה בפועל (₪)", min_value=0.0, value=2000000.0, step=50000.0, key="purchase_val")
    
with col2:
    st.subheader("צפי והחזקה")
    holding_years = st.number_input("זמן החזקה מתוכנן (בשנים)", min_value=1, value=5, step=1, key="hold_years")
    appreciation_rate = st.number_input("עליית שווי שנתית (%)", value=0.0, step=0.5, format="%0.1f", key="appreciation")

st.markdown("---")

# --- הוצאות נלוות ומס רכישה ---
st.subheader("💼 מיסים והוצאות נלוות לרכישה")
tax_col1, tax_col2, tax_col3 = st.columns(3)

vat_rate = st.number_input("שיעור מע\"מ בסיסי לתוספת (%)", min_value=0.0, value=17.0, step=1.0, key="vat_rate_num")
vat_multiplier = 1.0 + (vat_rate / 100.0)

with tax_col1:
    st.markdown("**מס רכישה**")
    buyer_status = st.radio("סטטוס רוכש:", ["דירה יחידה", "דירה חלופית / נוספת (8%-10%)"], key="buyer_status_rb")
    is_single_home = (buyer_status == "דירה יחידה")
    calculated_tax = calculate_purchase_tax(purchase_price, is_single_home)
    st.metric("מס רכישה מחושב", f"₪{calculated_tax:,.0f}")

with tax_col2:
    st.markdown("**אנשי מקצוע**")
    brokerage_pct = st.number_input("אחוז תיווך קנייה (%)", min_value=0.0, value=0.0, step=0.1, key="brokerage_pct_num")
    add_vat_brokerage = st.checkbox("➕ הוסף מע״מ לתיווך", value=True, key="add_vat_brokerage_cb")
    
    st.markdown("<br>", unsafe_allow_html=True)
    lawyer_fee_raw = st.number_input("שכר טרחה עו״ד (₪)", min_value=0.0, value=0.0, step=1000.0, key="lawyer_fee_raw_num")
    add_vat_lawyer = st.checkbox("➕ הוסף מע״מ לעו״ד", value=True, key="add_vat_lawyer_cb")
    
with tax_col3:
    st.markdown("**יועצים והוצאות נוספות (₪)**")
    mortgage_advisor = st.number_input("יועץ משכנתא (₪)", min_value=0.0, value=0.0, step=500.0, key="mortgage_advisor_num")
    add_vat_advisor = st.checkbox("➕ הוסף מע״מ ליועץ", value=True, key="add_vat_advisor_cb")
    
    st.markdown("<br>", unsafe_allow_html=True)
    other_expenses = st.number_input("הוצאות נוספות (שמאות/שיפוץ)", min_value=0.0, value=15000.0, step=1000.0, key="other_expenses_num")
    add_vat_other = st.checkbox("➕ הוסף מע״מ להוצאות", value=False, key="add_vat_other_cb")

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

# --- תכנון משכנתא (ממשק כפול) ---
st.subheader("🏦 תכנון משכנתא")
mortgage_mode = st.radio("בחר תצורת חישוב משכנתא:", ["חישוב מהיר (מסלול ממוצע)", "תכנון מפורט (עד 4 מסלולים)"], horizontal=True, key="mortgage_mode_rb")

tracks_data = []

if mortgage_mode == "חישוב מהיר (מסלול ממוצע)":
    st.markdown("סליידרים אופקיים לחישוב זריז של משכנתא אחידה:")
    sim_amt = st.slider("סכום המשכנתא (₪)", min_value=0, max_value=int(purchase_price*1.2), value=int(purchase_price*0.6), step=50000, key="simple_mortgage_amt")
    sim_years = st.slider("תקופת הלוואה (בשנים)", min_value=5, max_value=30, value=25, step=1, key="simple_mortgage_years")
    sim_rate = st.slider("ריבית שנתית ממוצעת (%)", min_value=1.0, max_value=10.0, value=4.0, step=0.1, key="simple_mortgage_rate")
    
    sim_pmt = calculate_monthly_payment(sim_amt, sim_rate, sim_years * 12)
    st.success(f"**החזר חודשי משוער:** ₪{sim_pmt:,.0f}")
    tracks_data.append({"amount": sim_amt, "months": sim_years * 12, "rate": sim_rate})

else:
    # ממשק 4 מסלולים אופקי - השורה שתוקנה באופן מפורש
    num_tracks = st.radio("מספר מסלולים פעילים:", options=, horizontal=True, key="num_tracks_radio")
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

# --- חישוב מס שבח ---
cost_basis = purchase_price + total_additional_expenses
gross_profit_on_sale = future_value - cost_basis
capital_gains_tax = 0

if not is_single_home and gross_profit_on_sale > 0:
    capital_gains_tax = gross_profit_on_sale * 0.25 

# רווח נקי ופיננסי (כולל ניכוי מס שבח עתידי)
net_profit = net_equity - initial_equity - total_mortgage_paid - capital_gains_tax
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
    st.metric("שווי נכס עתידי במכירה", f"₪{future_value:,.0f}")
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

# תגיות המידע למדדים (Tooltips)
st.markdown("**📉 מדדים פיננסיים ושורת הרווח:**")
fin_col1, fin_col2 = st.columns(2)
with fin_col1:
    st.metric("LTV (מינוף מול שמאות)", f"{ltv:,.1f}%", help="Loan-to-Value: אחוז המימון (המשכנתא) שלקחת ביחס להערכת השמאי. משפיע ישירות על רמת הסיכון ומדרגות הריבית בבנק. מעל 70% נחשב מינוף גבוה.")
    st.metric("Equity Growth (גידול בהון)", f"{equity_growth_pct:,.1f}%", help="מודד בכמה אחוזים צמח החלק 'שלך' בנכס. מחושב כיחס שבין ההון נטו שנשאר לך ביום המכירה לבין ההון ההתחלתי ששמת מהכיס.")
    
with fin_col2:
    st.metric("Net Profit (רווח נטו תזרימי)", f"₪{net_profit:,.0f}", help="הרווח הטהור בכיס לאחר כל ההוצאות. מחושב כשווי המכירה פחות: הון התחלתי, סך תשלומי משכנתא (קרן+ריבית), וקיזוז מס שבח מלא.")
    st.metric("ROE (תשואה נטו על ההון)", f"{roe:,.1f}%", help="Return on Equity: כמה הרווח הנקי מהווה באחוזים מתוך ההון ההתחלתי שהשקעת. זה המדד האמיתי שבוחן אם הכסף שלך 'עבד קשה' בזכות המינוף.")

# הצגת מס השבח
st.markdown("<br>", unsafe_allow_html=True)
st.metric("מס שבח משוער לתשלום בעת מכירה", f"₪{capital_gains_tax:,.0f}", help="מס השבח בישראל עומד על 25% מהרווח הריאלי על הנכס (לאחר קיזוז הוצאות מוכרות ואינפלציה). המודל כאן מחשב 25% מהרווח הנומינלי לצורך פשטות הניתוח. המס פטור לחלוטין במכירת דירה יחידה מזכה.")

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
        advisor_messages.append(f"⚠️ **סיכון חשיפה (Negative Leverage):** עלות הכסף שלך (ריבית ממוצעת של כ-{avg_mortgage_rate:.1f}%) גבוהה מקצב צמיחת שווי הנכס ({appreciation_rate:.1f}%). המינוף שוחק את ההון העצמי מדי חודש. כדאי לבחון קיצור תקופת הלוואה או הגדלת הון עצמי.")
    elif appreciation_rate > avg_mortgage_rate + 1 and ltv > 40:
        advisor_messages.append(f"🚀 **מינוף חיובי (Positive Leverage):** קצב צמיחת הנכס הצפוי עוקף את עלות החוב שלך. זו אינדיקציה מעולה לכך שהכסף של הבנק עובד בשבילך ומייצר תשואה עודפת.")

if net_profit > 0:
    expenses_to_profit_ratio = total_additional_expenses / net_profit
    if expenses_to_profit_ratio > 0.4:
        advisor_messages.append(f"💸 **משקולת הוצאות כבדה:** ההוצאות הנלוות מהוות יותר מ-{expenses_to_profit_ratio*100:.0f}% מהרווח הנקי העתידי שלך. ייתכן שעלויות הכניסה והיציאה (מס שבח/רכישה) מוחקות את כדאיות העסקה. שווה לבחון הארכת תקופת ההחזקה לפריסת ההוצאה.")
elif net_profit <= 0 and initial_equity > 0:
    advisor_messages.append(f"🛑 **שחיקת הון מוחלטת:** העסקה רושמת הפסד תזרימי. אסטרטגיה זו כדאית רק במצב של השבחה ודאית (כמו פינוי-בינוי מתקדם) או לטובת מגורים ארוכי טווח.")

if total_monthly_payment > (purchase_price * 0.005) and ltv > 60:
    advisor_messages.append(f"🌊 **ניהול משברים ונזילות:** ההחזר החודשי יוצר עומס תזרימי כבד. מומלץ להכין 'באפר' (רזרבה נזילה) של לפחות 6 חודשי משכנתא מראש בעו\"ש כדי לא להיקלע למצוקה בתקופות של קפיצת ריביות.")

if capital_gains_tax > 0:
    advisor_messages.append(f"🏛️ **תכנון מס:** שים לב שמס השבח נוגס משמעותית ברווח הסופי (כ-₪{capital_gains_tax:,.0f}). מומלץ להתייעץ עם עו\"ד מקרקעין על פטורים אפשריים או הכרה בהוצאות שיפוץ וריביות משכנתא שיקטינו את המס הריאלי שיוטל עליך בפועל.")

if len(advisor_messages) == 1:
    advisor_messages.append("✅ **יציבות אסטרטגית:** על פניו, תמהיל המינוף, התזרים ותחזית הצמיחה מאוזנים ואינם מדליקים נורות אזהרה בוהקות.")

for msg in advisor_messages:
    st.info(msg)
