import streamlit as st
import uuid
import json
import requests

import textwrap

def render_job(job, success=True):
    border_color = "#2ecc71" if success else "#e74c3c"
    status_text = "✅ Applied Successfully" if success else "❌ Application Failed"

    preferred = job.get("preferred_qualification", [])
    preferred_text = ", ".join(preferred) if preferred else "Not specified"

    html = f"""
<div style="border:2px solid {border_color}; border-radius:10px; padding:15px; margin-bottom:15px;">
  <h4>{job['company_name']} — {job['role']}</h4>

  <p><b>Status:</b> {status_text}</p>
  <p><b>Location:</b> {job.get('location', 'N/A')}</p>
  <p><b>Remote:</b> {job.get('remote_status', 'N/A')}</p>
  <p><b>Visa Required:</b> {job.get('visa', 'N/A')}</p>
  <p><b>Start Date:</b> {job.get('start_date', 'N/A')}</p>

  <p><b>Requirements:</b> {", ".join(job.get('requirements', []))}</p>
  <p><b>Responsibilities:</b> {", ".join(job.get('responsibilities', []))}</p>
  <p><b>Preferred:</b> {preferred_text}</p>

  <p><a href="{job['link']}" target="_blank">🔗 Job Link</a></p>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)





# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="Student Apply Policy",
    layout="centered"
)

st.title("📄 Student Apply Policy Setup")

st.caption("Upload your resume and define strict application constraints")

# ------------------ UUID ------------------
user_id = str(uuid.uuid4())
st.text_input("User UUID", value=user_id, disabled=True)

# ------------------ FILE UPLOAD ------------------
uploaded_file = st.file_uploader(
    "Upload Resume (PDF)",
    type=["pdf"]
)

st.divider()

# ------------------ BOOLEAN TOGGLES ------------------
st.subheader("Eligibility & Preferences")

authorized = st.toggle(
    "Authorized to work in target country",
    value=True
)

visa_required = st.toggle(
    "Requires visa sponsorship",
    value=False
)

remote_ok = st.toggle(
    "Open to remote roles",
    value=True
)

relocate = st.toggle(
    "Willing to relocate",
    value=False
)

st.divider()

# ------------------ NUMERIC CONSTRAINTS ------------------
st.subheader("Application Limits")

industry_experience = st.number_input(
    "Years of industry experience",
    min_value=0,
    value=0,
    step=1
)

max_appl_per_day = st.number_input(
    "Max applications per day",
    min_value=1,
    value=10,
    step=1
)

match_threshold = st.slider(
    "Minimum match threshold (%)",
    min_value=0,
    max_value=100,
    value=70
)

st.divider()

# ------------------ LIST INPUTS ------------------
st.subheader("Blocked Targets")

blocked_companies = st.text_area(
    "Blocked companies (comma-separated)",
    placeholder="CompanyA, CompanyB"
)

blocked_roles = st.text_area(
    "Blocked roles / keywords (comma-separated)",
    placeholder="Sales, HR, Marketing"
)

# ------------------ BUILD PAYLOAD ------------------
constraints = {
    "uid": user_id,
    "authorized": authorized,
    "visa_required": visa_required,
    "remote_ok": remote_ok,
    "relocate": relocate,
    "industry_experience": industry_experience,
    "max_appl_per_day": max_appl_per_day,
    "match_threshold": match_threshold,
    "blocked_companies": [
        c.strip() for c in blocked_companies.split(",") if c.strip()
    ],
    "blocked_roles": [
        r.strip() for r in blocked_roles.split(",") if r.strip()
    ]
}

# ------------------ SUBMIT ------------------
if st.button("🚀 Submit to Agent", type="primary"):

    if not uploaded_file:
        st.error("Please upload a resume PDF.")
    else:
        with st.spinner("Sending data to backend..."):

            response = requests.post(
                url="http://localhost:8000/input_data",
                files={
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type
                    )
                },
                data={
                    "data": json.dumps(constraints)
                }
            )

        if response.status_code == 200:
            st.success("Data successfully sent to backend ✅")

            result = response.json()
            successful = result.get("successful", {})
            failure = result.get("failure", {})

            # -------- SUMMARY --------
            col1, col2 = st.columns(2)
            col1.metric("✅ Successful", len(successful))
            col2.metric("❌ Failed", len(failure))

            st.divider()

            # -------- SUCCESSFUL JOBS --------
            st.subheader("🟢 Successful Applications")

            if not successful:
                st.info("No successful applications yet.")
            else:
                for job_id, job in successful.items():
                    render_job(job, success=True)

            st.divider()

            # -------- FAILED JOBS --------
            st.subheader("🔴 Failed Applications")

            if not failure:
                st.info("No failed applications 🎉")
            else:
                for job_id, job in failure.items():
                    render_job(job, success=False)

        else:
            st.error("Backend error ❌")
            st.text(response.text)
