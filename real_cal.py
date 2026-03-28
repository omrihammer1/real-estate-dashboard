import streamlit as st
import pandas as pd
import altair as alt

# --- אתחול משתני מערכת לשמירת אסטרטגיות ---
if 'saved_strategies' not in st.session_state:
    st.session_state.saved_strategies = {}

# רשימת המפתחות לשמירת וטעינת הנתונים
state_keys = [
    'strategy_type_rb', 'monthly_rent_num', 'imputed_rent_num',
    'appraisal_val', 'purchase_val', 'hold_years', 'appreciation', 'rent_increase_rate_num',
    'buyer_status_rb', 'vat_rate_num', 'brokerage_pct_num', 'add_vat_brokerage_cb',
    'lawyer_fee_raw_num', 'add_vat_lawyer_cb', 'mortgage_advisor_num', 'add_vat_advisor_cb',
    'other_expenses_num', 'add_vat_other_cb', 
    'sim_amt_key', 'sim_years_key', 'sim_rate_key', 'cpi_rate_key'
]
for i in range(4):
    state_keys.extend([f"amount_{i}", f"months_{i}", f"rate_{i}"])

# --- פונקציות חישוב ---
def calculate_mortgage_track(principal, annual_rate, total_months, holding_months, annual_cpi):
    if principal == 0 or total_months == 0: 
        return 0, 0, principal, 0
        
    r = (annual_rate / 100) / 12
    cpi = (annual_cpi / 100) / 12
    
    if r > 0:
        pmt_initial = principal * (r * (1 + r)**total_months) / ((1 + r)**total_months - 1)
    else:
        pmt_initial = principal / total_months
        
    balance = principal
    total_paid = 0
    pmt_current = pmt_initial
    
    months_to_run = min(holding_months, total_months)
    for m in range(months_to_run):
        interest_payment = balance * r
        principal_payment = pmt_current - interest_payment
        
        balance -= principal_payment
        total_paid += pmt_current
        
        if balance > 0:
            balance *= (1 + cpi)
            pmt_current *= (1 + cpi)
            
    if balance < 0: balance = 0
    return pmt_initial, pmt_current, balance, total_paid

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

# --- הגדרת העמוד והעיצוב (RTL) ---
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

# --- תפריט צד (Sidebar) ---
with st.sidebar:
    st.header("💾 ניהול אסטרטגיות")
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

# --- נתוני הנכס והחזקה ---
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("נתוני הנכס")
    strategy_type = st.radio("מטרת הרכישה:", ["מגורים", "השקעה (השכרה)"], horizontal=True, key="strategy_type_rb")
    
    if strategy_type == "השקעה (השכרה)":
        monthly_rent = st.number_input("שכר דירה חודשי צפוי (₪)", min_value=0, value=7500, step=100, key="monthly_rent_num")
        imputed_rent = 0
    else:
        monthly_rent = 0
        imputed_rent = st.number_input(
            "שכירות חלופית נחסכת (₪/חודש)", min_value=0, value=7500, step=100, key="imputed_rent_num",
            help="שכירות רעיונית (Imputed Rent): הסכום שהיית משלם בכל חודש על שכירת דירה חלופית למגוריך, לו לא היית רוכש את הנכס. הכללת הסכום כ'הכנסה נחסכת' מאפשרת השוואה כלכלית אמיתית ואובייקטיבית בין מגורים להשקעה."
        )
        
    appraisal_value = st.number_input("ערך דירה לפי שמאות (₪)", min_value=0, value=3500000, step=50000, key="appraisal_val")
    purchase_price = st.number_input("מחיר דירה בפועל (₪)", min_value=0, value=3500000, step=50000, key="purchase_val")
    
with col2:
    st.subheader("צפי והחזקה")
    holding_years = st.number_input("זמן החזקה מתוכנן (בשנים)", min_value=1, value=5, step=1, key="hold_years")
    appreciation_rate = st.number_input("עליית שווי נכס שנתית (%)", value=2.0, step=0.5, format="%0.1f", key="appreciation")
    rent_increase_rate = st.number_input(
        "עליית שכירות שנתית (%)", value=2.0, step=0.5, format="%0.1f", key="rent_increase_rate_num",
        help="הגידול הטבעי בשכר הדירה. המודל יעלה את סכום השכירות (או השכירות הנחסכת) פעם בשנה לפי אחוז זה, כדי לשקף תזרים ריאלי על פני השנים."
    )

# --- הוצאות נלוות ומס רכישה ---
st.markdown("---")
st.subheader("💼 מיסים והוצאות נלוות לרכישה")
tax_col1, tax_col2, tax_col3 = st.columns(3)

vat_rate = st.number_input("שיעור מע\"מ בסיסי לתוספת (%)", min_value=0.0, value=18.0, step=1.0, format="%0.1f", key="vat_rate_num")
vat_multiplier = 1.0 + (vat_rate / 100.0)

with tax_col1:
    st.markdown("**מס רכישה**")
    buyer_status = st.radio("סטטוס רוכש:", ["דירה יחידה", "דירה חלופית / נוספת (8%-10%)"], key="buyer_status_rb")
    is_single_home = (buyer_status == "דירה יחידה")
    calculated_tax = calculate_purchase_tax(purchase_price, is_single_home)
    st.metric("מס רכישה מחושב", f"₪{calculated_tax:,.0f}")

with tax_col2:
    st.markdown("**אנשי מקצוע**")
    brokerage_pct = st.number_input("אחוז תיווך קנייה (%)", min_value=0.0, value=0.0, step=0.1, format="%0.1f", key="brokerage_pct_num")
    add_vat_brokerage = st.checkbox("➕ הוסף מע״מ לתיווך", value=True, key="add_vat_brokerage_cb")
    
    st.markdown("<br>", unsafe_allow_html=True)
    lawyer_fee_pct = st.number_input("שכר טרחה עו״ד (%)", min_value=0.0, value=0.5, step=0.1, format="%0.1f", key="lawyer_fee_pct_num")
    add_vat_lawyer = st.checkbox("➕ הוסף מע״מ לעו״ד", value=True, key="add_vat_lawyer_cb")
    
with tax_col3:
    st.markdown("**יועצים והוצאות נוספות (₪)**")
    mortgage_advisor = st.number_input("יועץ משכנתא (₪)", min_value=0, value=0, step=500, key="mortgage_advisor_num")
    add_vat_advisor = st.checkbox("➕ הוסף מע״מ ליועץ", value=True, key="add_vat_advisor_cb")
    
    st.markdown("<br>", unsafe_allow_html=True)
    other_expenses = st.number_input("הוצאות נוספות (שמאות/שיפוץ)", min_value=0, value=15000, step=1000, key="other_expenses_num")
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

# --- תכנון משכנתא ---
st.subheader("🏦 תכנון משכנתא והצמדה למדד")

cpi_assumption = st.number_input(
    "צפי עליה שנתית במדד המחירים לצרכן (%)", 
    min_value=0.0, value=0.0, step=0.5, format="%0.1f", key="cpi_rate_key",
    help="המדד משפיע על יתרת קרן המשכנתא (במסלולים צמודים). בעשור האחרון (2014-2024), ממוצע העלייה במדד המחירים לצרכן בישראל עמד על כ-1.5% עד 2.0% בשנה. הזנת ערך כאן תחזיר סימולציה שמרנית המניחה שכלל המשכנתא צמודה לחומרה."
)

st.info("הזן את נתוני המשכנתא באחת מהאפשרויות בלבד (חישוב מהיר או מפורט). המערכת תזהה אוטומטית היכן הזנת סכום ותשתמש בנתונים אלו.")

col_s1, col_s2, col_s3 = st.columns(3)
sim_amt = col_s1.number_input("סכום המשכנתא (₪)", min_value=0, value=0, step=50000, key="sim_amt_key")
sim_years = col_s2.number_input("תקופת הלוואה (בשנים)", min_value=5, max_value=30, value=25, step=1, key="sim_years_key")
sim_rate = col_s3.number_input("ריבית ממוצעת משוערת (%)", min_value=1.0, max_value=10.0, value=4.0, step=0.1, format="%0.1f", key="sim_rate_key")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### אפשרות ב': חישוב מפורט (עד 4 מסלולים)")
st.caption("💡 הדרכה: פשוט השאר סכום 0 במסלולים שאינך צריך.")
detailed_tracks_data = []
cols = st.columns(4)

for i in range(4):
    with cols[i]:
        st.markdown(f"**מסלול {i+1}**")
        amount = st.number_input(f"סכום (₪)", min_value=0, value=0, step=10000, key=f"amount_{i}")
        months = st.number_input(f"תקופה (חודשים)", min_value=0, value=360, step=12, key=f"months_{i}")
        rate = st.number_input(f"ריבית (%)", value=4.0, step=0.1, format="%0.2f", key=f"rate_{i}")
        detailed_tracks_data.append({"amount": amount, "months": months, "rate": rate})

sum_detailed = sum(t["amount"] for t in detailed_tracks_data)
tracks_data = []

if sum_detailed > 0 and sim_amt > 0:
    st.error("⚠️ **שגיאת הזנה כפולה:** המערכת מסתמכת כעת רק על **החישוב המפורט**.")
    tracks_data = detailed_tracks_data
elif sum_detailed > 0:
    tracks_data = detailed_tracks_data
elif sim_amt > 0:
    tracks_data = [{"amount": sim_amt, "months": sim_years * 12, "rate": sim_rate}]
else:
    tracks_data = []

# --- חישובי ליבה ---
holding_months = holding_years * 12
future_value = purchase_price * ((1 + (appreciation_rate / 100)) ** holding_years)

total_loan_amount = sum(t['amount'] for t in tracks_data)
initial_equity = purchase_price + total_additional_expenses - total_loan_amount
total_investment = purchase_price + total_additional_expenses

total_initial_monthly_payment = 0
total_outstanding_balance = 0
total_mortgage_paid = 0

for track in tracks_data:
    pmt_init, pmt_curr, bal, paid = calculate_mortgage_track(
        track['amount'], track['rate'], track['months'], holding_months, cpi_assumption
    )
    total_initial_monthly_payment += pmt_init
    total_outstanding_balance += bal
    total_mortgage_paid += paid

net_equity = future_value - total_outstanding_balance
principal_paid = total_loan_amount - total_outstanding_balance
interest_and_cpi_paid = total_mortgage_paid - principal_paid

initial_rent_val = monthly_rent if strategy_type == "השקעה (השכרה)" else imputed_rent
current_rent = initial_rent_val
total_rent_income = 0

for m in range(holding_months):
    if m > 0 and m % 12 == 0:
        current_rent *= (1 + (rent_increase_rate / 100))
    total_rent_income += current_rent

cost_basis = purchase_price + total_additional_expenses
gross_profit_on_sale = future_value - cost_basis
capital_gains_tax = 0
if not is_single_home and gross_profit_on_sale > 0:
    capital_gains_tax = gross_profit_on_sale * 0.25 

net_profit = net_equity - initial_equity - total_mortgage_paid - capital_gains_tax + total_rent_income
ltv = (total_loan_amount / appraisal_value * 100) if appraisal_value > 0 else 0

equity_growth_pct = ((net_equity / initial_equity) - 1) * 100 if initial_equity > 0 else 0
roi = (net_profit / total_investment * 100) if total_investment > 0 else 0
roe = (net_profit / initial_equity * 100) if initial_equity > 0 else 0

gross_yield = (initial_rent_val * 12 / total_investment) * 100 if total_investment > 0 else 0
net_cash_flow = initial_rent_val - total_initial_monthly_payment

# --- הצגת תוצאות ---
st.markdown("---")
st.subheader("📊 תוצאות אסטרטגיית ההחזקה (לאחר {} שנים)".format(holding_years))

res_col1, res_col2 = st.columns(2)
with res_col1:
    st.metric("הון עצמי התחלתי (כולל הוצאות ומיסים)", f"₪{initial_equity:,.0f}")
    st.metric("שווי נכס עתידי במכירה", f"₪{future_value:,.0f}")
with res_col2:
    st.metric("יתרת משכנתא לסילוק (כולל קנסות אינפלציה)", f"₪{total_outstanding_balance:,.0f}")
    st.metric("הון עצמי נטו בסוף התקופה", f"₪{net_equity:,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("**🔍 ניתוח משכנתא בתקופת ההחזקה:**")
mort_col1, mort_col2 = st.columns(2)
with mort_col1:
    st.metric("סך החזר חודשי (התחלתי)", f"₪{total_initial_monthly_payment:,.0f}")
    st.metric("סך הכל שולם לבנק", f"₪{total_mortgage_paid:,.0f}")
with mort_col2:
    st.metric("מתוכו שולם לקרן (נשאר אצלך)", f"₪{principal_paid:,.0f}")
    st.metric("מתוכו שולם לריבית והצמדה (הוצאה)", f"₪{interest_and_cpi_paid:,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("**📉 מדדים פיננסיים ושורת הרווח:**")
fin_col1, fin_col2 = st.columns(2)
with fin_col1:
    st.metric("LTV (מינוף מול שמאות)", f"{ltv:,.1f}%", help="Loan-to-Value: אחוז המימון (המשכנתא) שלקחת ביחס להערכת השמאי. משפיע ישירות על רמת הסיכון ומדרגות הריבית בבנק. מעל 70% נחשב מינוף גבוה.")
    st.metric("Equity Growth (גידול בהון)", f"{equity_growth_pct:,.1f}%", help="מודד בכמה אחוזים צמח החלק 'שלך' בנכס. מחושב כיחס שבין ההון נטו שנשאר לך ביום המכירה לבין ההון ההתחלתי ששמת מהכיס.")
    
with fin_col2:
    st.metric("Net Profit (רווח נטו כולל תזרים)", f"₪{net_profit:,.0f}", help="הרווח הטהור בכיס לאחר כל ההוצאות. מחושב כשווי המכירה + כלל ההכנסות (או החיסכון) משכירות, פחות: הון התחלתי, סך תשלומי משכנתא, וקיזוז מס שבח מלא.")
    st.metric("ROE (תשואה נטו על ההון)", f"{roe:,.1f}%", help="Return on Equity: כמה הרווח הנקי מהווה באחוזים מתוך ההון ההתחלתי שהשקעת. זה המדד האמיתי שבוחן אם הכסף שלך 'עבד קשה' בזכות המינוף.")

st.markdown("<br>", unsafe_allow_html=True)
if strategy_type == "השקעה (השכרה)":
    st.markdown("**🏢 נתוני השכרה ותזרים (לפי נתוני פתיחה):**")
    rent_col1, rent_col2 = st.columns(2)
    with rent_col1:
        st.metric("Gross Yield (תשואה גולמית שנתית)", f"{gross_yield:,.2f}%", help="חישוב: (שכירות חודשית בסיסית * 12) חלקי סך ההשקעה הכולל בנכס. משקף את התשואה השנתית הבסיסית מהשכרה בלבד.")
    with rent_col2:
        flow_color = "🟢" if net_cash_flow > 0 else "🔴"
        st.metric(f"Net Cash Flow (תזרים חודשי נטו) {flow_color}", f"₪{net_cash_flow:,.0f}", help="חישוב: שכירות חודשית פחות ההחזר החודשי ההתחלתי של המשכנתא. מראה אם הנכס מייצר תזרים חיובי נזיל או דורש הזרמת הון לכיסוי ההלוואה.")
else:
    st.markdown("**🏠 חיסכון בשכירות (מגורים):**")
    rent_col1, rent_col2 = st.columns(2)
    with rent_col1:
        st.metric("סך שכירות נחסכת (מצטבר)", f"₪{total_rent_income:,.0f}", help="סך כל הכסף שנשאר אצלך בכיס לאורך התקופה בזכות העובדה שלא שילמת שכר דירה חלופי, כולל עליות המחירים השנתיות שהגדרת.")
    with rent_col2:
        equiv_cash_flow = net_cash_flow
        flow_color = "🟢" if equiv_cash_flow > 0 else "🔴"
        st.metric(f"פער תזרימי חודשי התחלתי {flow_color}", f"₪{equiv_cash_flow:,.0f}", help="ההפרש בין מה שהיית משלם על שכירות לבין תשלום המשכנתא החודשי שלך. ערך חיובי אומר שעלות המשכנתא נמוכה מעלות השכירות החלופית.")

st.markdown("<br>", unsafe_allow_html=True)
st.metric("מס שבח משוער לתשלום בעת מכירה", f"₪{capital_gains_tax:,.0f}", help="מס השבח בישראל עומד על 25% מהרווח הריאלי על הנכס (לאחר קיזוז הוצאות מוכרות ואינפלציה). המודל כאן מחשב 25% מהרווח הנומינלי לשם פשטות. המס פטור לחלוטין במכירת דירה יחידה (בתנאי שעמדה בתנאי הפטור).")

st.markdown("---")

# --- הגרף ---
st.markdown("### 📈 התפתחות השווי והחוב על פני זמן (תחזית עתידית)")
months_list = list(range(holding_months + 1))
values_over_time = []
balances_over_time = []
equities_over_time = [] 

for m in months_list:
    monthly_appreciation_rate = (1 + (appreciation_rate / 100)) ** (1/12) - 1
    val_at_m = purchase_price * ((1 + monthly_appreciation_rate) ** m)
    values_over_time.append(val_at_m)
    
    balance_at_m = 0
    for t in tracks_data:
        _, _, b, _ = calculate_mortgage_track(t['amount'], t['rate'], t['months'], m, cpi_assumption)
        balance_at_m += b
        
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
    x=alt.X('Month', title='חודש החזקה עתידי'),
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
    strategy_type_txt = "עסקת אקזיט קצרת טווח (פליפ)"
elif 3 < holding_years <= 7:
    strategy_type_txt = "עסקת השבחה לטווח בינוני"
else:
    strategy_type_txt = "החזקה לטווח ארוך (גידול הון פנסיוני)"

advisor_messages.append(f"🎯 **פרופיל אסטרטגי:** המספרים מצביעים על {strategy_type_txt}. נגזרות ניהול הסיכונים להלן מותאמות לפרק זמן זה:")

if net_cash_flow < 0:
    if strategy_type == "השקעה (השכרה)":
        advisor_messages.append(f"🩸 **תזרים מזומנים שלילי:** השכירות לא מכסה את המשכנתא. תצטרך להזרים מכיסך כ-₪{abs(net_cash_flow):,.0f} בכל חודש.")
    else:
        advisor_messages.append(f"⚖️ **פער תזרימי למגורים:** עלות המשכנתא גבוהה ב-₪{abs(net_cash_flow):,.0f} ממה שהיית משלם על שכירות בדירה מקבילה.")
elif net_cash_flow > 1000:
    if strategy_type == "השקעה (השכרה)":
        advisor_messages.append(f"💰 **תזרים מזומנים חיובי:** הנכס משלם על עצמו ומשאיר לך עודף בחודש.")

if total_loan_amount > 0:
    if avg_mortgage_rate > appreciation_rate and ltv > 40:
        advisor_messages.append(f"⚠️ **סיכון חשיפה (Negative Leverage):** עלות הכסף שלך (ריבית ממוצעת של כ-{avg_mortgage_rate:.1f}%) גבוהה מקצב צמיחת שווי הנכס ({appreciation_rate:.1f}%).")

if net_profit > 0:
    expenses_to_profit_ratio = total_additional_expenses / net_profit
    if expenses_to_profit_ratio > 0.4:
        advisor_messages.append(f"💸 **משקולת הוצאות כבדה:** ההוצאות הנלוות מהוות יותר מ-{expenses_to_profit_ratio*100:.0f}% מהרווח הנקי העתידי.")

if cpi_assumption > 2.5 and total_loan_amount > 0:
    advisor_messages.append(f"🔥 **שחיקת אינפלציה:** צפי מדד גבוה ({cpi_assumption}%). שים לב איך זה מנפח את יתרת המשכנתא.")

if len(advisor_messages) == 1:
    advisor_messages.append("✅ **יציבות אסטרטגית:** תמהיל המינוף, התזרים ותחזית הצמיחה מאוזנים ואינם מדליקים נורות אזהרה בוהקות.")

for msg in advisor_messages:
    st.info(msg)
