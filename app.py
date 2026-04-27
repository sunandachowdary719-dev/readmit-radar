import streamlit as st
import anthropic
import plotly.graph_objects as go
from disclaimer import DISCLAIMER

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="ReadmitRadar",
    page_icon="🏥",
    layout="wide"
)

# ── Header ───────────────────────────────────────────────────
st.title("🏥 ReadmitRadar")
st.markdown("**AI-Powered Hospital Readmission Risk Scorer**")
st.warning(DISCLAIMER)
st.markdown("---")

# ── API Key ──────────────────────────────────────────────────
api_key = st.sidebar.text_input(
    "Enter your Anthropic API Key",
    type="password",
    help="Get your key at console.anthropic.com"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### About ReadmitRadar")
st.sidebar.markdown("""
ReadmitRadar helps clinical teams assess 
30-day readmission risk at the point of discharge.

**Built on:**
- CMS HRRP data (2,833 hospitals)
- Claude AI (Anthropic)
- Real clinical risk factors

**For portfolio & educational use only.**
""")

# ── Patient Form ─────────────────────────────────────────────
st.subheader("Patient Information")
st.markdown("Fill in the patient details below to generate a readmission risk assessment.")

col1, col2, col3 = st.columns(3)

with col1:
    age = st.slider("Patient Age", 18, 100, 65)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    insurance = st.selectbox("Insurance Type", [
        "Medicare", "Medicaid", "Private", "Self-pay", "Other"
    ])

with col2:
    diagnosis = st.selectbox("Primary Diagnosis", [
        "Heart Failure",
        "Pneumonia",
        "COPD",
        "Hip/Knee Replacement",
        "Acute Myocardial Infarction",
        "Coronary Artery Bypass Graft",
        "Diabetes",
        "Sepsis",
        "Other"
    ])
    length_of_stay = st.slider("Length of Stay (days)", 1, 30, 5)
    num_medications = st.slider("Number of Medications", 1, 30, 8)

with col3:
    prior_admissions = st.selectbox("Prior Admissions (last 12 months)", [
        "None", "1", "2", "3 or more"
    ])
    lives_alone = st.selectbox("Living Situation", [
        "Lives with family/caregiver",
        "Lives alone",
        "Assisted living facility",
        "Nursing home"
    ])
    discharge_to = st.selectbox("Discharge Destination", [
        "Home",
        "Home with home health",
        "Skilled nursing facility",
        "Rehabilitation facility",
        "Another hospital"
    ])

st.markdown("---")

# ── Additional Clinical Factors ───────────────────────────────
st.subheader("Additional Clinical Factors")
col4, col5 = st.columns(2)

with col4:
    comorbidities = st.multiselect(
        "Comorbidities",
        ["Diabetes", "Hypertension", "CKD", "COPD",
         "Depression/Anxiety", "Obesity", "Atrial Fibrillation",
         "Cancer", "Dementia"]
    )

with col5:
    follow_up = st.selectbox("Follow-up Appointment Scheduled", [
        "Yes — within 7 days",
        "Yes — within 14 days",
        "Yes — within 30 days",
        "No appointment scheduled"
    ])
    health_literacy = st.selectbox("Patient Health Literacy", [
        "High — understands discharge instructions",
        "Medium — needs some clarification",
        "Low — significant barriers to understanding"
    ])

st.markdown("---")

# ── Risk Score Calculator ─────────────────────────────────────
def calculate_base_risk(age, length_of_stay, num_medications,
                         prior_admissions, lives_alone, diagnosis,
                         comorbidities, follow_up, discharge_to,
                         health_literacy):
    score = 0

    # Age factor
    if age >= 80: score += 25
    elif age >= 70: score += 18
    elif age >= 60: score += 10
    else: score += 5

    # Diagnosis factor
    diagnosis_scores = {
        "Heart Failure": 20,
        "COPD": 18,
        "Pneumonia": 16,
        "Acute Myocardial Infarction": 18,
        "Coronary Artery Bypass Graft": 15,
        "Sepsis": 20,
        "Diabetes": 12,
        "Hip/Knee Replacement": 14,
        "Other": 10
    }
    score += diagnosis_scores.get(diagnosis, 10)

    # Length of stay
    if length_of_stay > 14: score += 15
    elif length_of_stay > 7: score += 10
    elif length_of_stay > 3: score += 5

    # Medications
    if num_medications > 15: score += 15
    elif num_medications > 10: score += 10
    elif num_medications > 5: score += 5

    # Prior admissions
    prior_scores = {"None": 0, "1": 10, "2": 18, "3 or more": 25}
    score += prior_scores.get(prior_admissions, 0)

    # Living situation
    if lives_alone == "Lives alone": score += 15
    elif lives_alone == "Assisted living facility": score += 5

    # Discharge destination
    if discharge_to == "Home": score += 10
    elif discharge_to == "Home with home health": score += 5

    # Comorbidities
    score += min(len(comorbidities) * 4, 20)

    # Follow-up
    if follow_up == "No appointment scheduled": score += 15
    elif "30 days" in follow_up: score += 8
    elif "14 days" in follow_up: score += 4

    # Health literacy
    if "Low" in health_literacy: score += 10
    elif "Medium" in health_literacy: score += 5

    # Normalize to percentage
    risk_pct = min(round((score / 180) * 100, 1), 99)
    return risk_pct


# ── Generate Button ───────────────────────────────────────────
if st.button("🔍 Generate Risk Assessment", type="primary"):

    if not api_key:
        st.error("Please enter your Anthropic API key in the sidebar.")
    else:
        risk_score = calculate_base_risk(
            age, length_of_stay, num_medications,
            prior_admissions, lives_alone, diagnosis,
            comorbidities, follow_up, discharge_to,
            health_literacy
        )

        # Risk level
        if risk_score >= 65:
            risk_level = "HIGH"
            risk_color = "red"
            risk_emoji = "🔴"
        elif risk_score >= 35:
            risk_level = "MEDIUM"
            risk_color = "orange"
            risk_emoji = "🟡"
        else:
            risk_level = "LOW"
            risk_color = "green"
            risk_emoji = "🟢"

        # ── Gauge Chart ───────────────────────────────────────
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score,
            title={"text": f"{risk_emoji} {risk_level} RISK"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": risk_color},
                "steps": [
                    {"range": [0, 35], "color": "#d4edda"},
                    {"range": [35, 65], "color": "#fff3cd"},
                    {"range": [65, 100], "color": "#f8d7da"}
                ],
                "threshold": {
                    "line": {"color": "black", "width": 4},
                    "thickness": 0.75,
                    "value": risk_score
                }
            },
            number={"suffix": "%"}
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

        # ── AI Analysis ───────────────────────────────────────
        with st.spinner("Generating AI clinical assessment..."):
            try:
                client = anthropic.Anthropic(api_key=api_key)

                prompt = f"""You are a clinical decision support AI helping 
a hospital care team assess readmission risk at discharge.

Patient Profile:
- Age: {age}, Gender: {gender}
- Primary Diagnosis: {diagnosis}
- Length of Stay: {length_of_stay} days
- Number of Medications: {num_medications}
- Prior Admissions (12 months): {prior_admissions}
- Living Situation: {lives_alone}
- Discharge Destination: {discharge_to}
- Comorbidities: {', '.join(comorbidities) if comorbidities else 'None reported'}
- Follow-up Scheduled: {follow_up}
- Health Literacy: {health_literacy}
- Insurance: {insurance}
- Calculated Risk Score: {risk_score}% ({risk_level} RISK)

Please provide:

1. **Risk Summary** (2-3 sentences explaining the key drivers of this patient's readmission risk in plain English)

2. **Top 3 Risk Factors** (bullet points — the specific factors from this patient's profile driving the risk most)

3. **Recommended Actions Before Discharge** (4-5 specific, actionable steps the care team should take)

4. **Post-Discharge Follow-up Plan** (3-4 specific recommendations for what should happen after the patient leaves)

5. **One Key Warning** (the single most important thing to watch for with this specific patient)

Be specific to this patient's profile. Be concise and clinical but accessible.
End with: 'This assessment is for educational purposes only and does not constitute medical advice.'"""

                message = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )

                ai_response = message.content[0].text

                st.markdown("---")
                st.subheader("📋 AI Clinical Assessment")
                st.markdown(ai_response)

            except Exception as e:
                st.error(f"API Error: {str(e)}")
                st.info("Check your API key and try again.")

        # ── CMS Context ───────────────────────────────────────
        st.markdown("---")
        st.subheader("📊 How This Compares to National Data")

        cms_rates = {
            "Heart Failure": 21.4,
            "COPD": 19.8,
            "Pneumonia": 16.2,
            "Acute Myocardial Infarction": 15.9,
            "Coronary Artery Bypass Graft": 10.8,
            "Hip/Knee Replacement": 4.8,
            "Sepsis": 18.3,
            "Diabetes": 14.2,
            "Other": 15.0
        }

        national_rate = cms_rates.get(diagnosis, 15.0)
        st.markdown(f"""
        - **This patient's predicted risk:** {risk_score}%
        - **National 30-day readmission rate for {diagnosis}:** {national_rate}%
        - **Your patient is {'above' if risk_score > national_rate else 'below'} 
        the national average by {abs(round(risk_score - national_rate, 1))} points**
        
        *National rates sourced from CMS Hospital Readmissions Reduction 
        Program data (FY2026, 2,833 hospitals analyzed)*
        """)

st.markdown("---")
st.caption("ReadmitRadar | Built by Sunanda Chavalamudi | "
           "Portfolio Project | Not for clinical use | "
           "Data: CMS HRRP FY2026")
