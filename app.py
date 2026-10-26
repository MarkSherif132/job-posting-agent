import streamlit as st

from agents.pipeline import run_pipeline
from job_details import DetailField, JobDetails

st.set_page_config(
    page_title="Job Posting Agent",
    page_icon="📝",
    layout="centered",
)

st.title("📝 Job Posting Agent")
st.caption("Enter the company name and job title, and the agent will generate a job posting for you.")


def detail_input(label: str, key: str, placeholder: str = "") -> DetailField:
    col_value, col_show = st.columns([4, 1], vertical_alignment="bottom")
    value = col_value.text_input(label, key=f"{key}_value", placeholder=placeholder)
    show = col_show.checkbox(
        "show",
        key=f"{key}_show",
        help="If not checked, the information will be used by the model but not displayed in the posting.",
    )
    return DetailField(value=value, show=show)


with st.form("job_posting_form"):
    company = st.text_input("Company name", key="company", placeholder="Example: Vodafone Egypt")
    role = st.text_input("Job title", key="role", placeholder="Example: Data Analyst")

    with st.expander("Additional Details (Optional)"):

        work_mode = detail_input("Work Mode", "work_mode", "remote / hybrid / on-site")
        location = detail_input("Location", "location", "Example: Cairo")
        salary = detail_input("Salary or Budget", "salary", "Example: 15000 EGP")
        experience = detail_input("Years of Experience", "experience_years", "Example: 3-5")
        contract = detail_input("Contract Type", "contract_type", "full-time / part-time / contract")
        apply_contact_value = st.text_input(
            "Email or Link", key="apply_contact_value", placeholder="careers@example.com"
        )
        apply_contact = DetailField(value=apply_contact_value, show=True)        
        company_website = st.text_input(
            "Company Official Website (For Research Only)", key="company_website", placeholder="https://..."
        )

        st.markdown("**Custom Fields**")
        custom = []
        for i in range(2):
            custom_name = st.text_input(f"Custom Field Name {i + 1}", key=f"custom_{i}_name")
            custom_field = detail_input("Value", f"custom_{i}")
            if custom_name.strip():
                custom.append((custom_name.strip(), custom_field))

    submitted = st.form_submit_button("Generate Posting")

details = JobDetails(
    work_mode=work_mode,
    location=location,
    salary=salary,
    experience_years=experience,
    contract_type=contract,
    apply_contact=apply_contact,
    company_website=company_website.strip(),
    custom=custom,
)

if submitted:
    st.session_state.pop("result", None)  # امسح النتيجة القديمة قبل أي تشغيل جديد
    if not company.strip() or not role.strip():
        st.warning("Please enter both the company name and the job title.")
    else:
        try:
            with st.spinner("Generating the posting... (can take up to two minutes)"):
                st.session_state["result"] = run_pipeline(company, role, details)
        except Exception as e:
            st.error(f"Something went wrong: {e}")

# النتيجة بتتعرض من session_state، فتفضل ظاهرة حتى لو الصفحة اتعملها rerun
# (مثلاً بعد الضغط على زرار التحميل).
result = st.session_state.get("result")
if result:
    for warning in result.warnings:
        st.error(warning)
    if not result.warnings:
        st.success("Done! Here's the generated job posting:")

    tab_posting, tab_requirements, tab_research = st.tabs(
        ["Job posting", "Requirements", "Company research"]
    )
    with tab_posting:
        st.markdown(result.job_posting)
        st.download_button(
            "Download posting (.md)",
            data=result.job_posting,
            file_name="job_posting.md",
            mime="text/markdown",
        )
    with tab_requirements:
        st.markdown(result.role_requirements)
    with tab_research:
        st.markdown(result.company_research)