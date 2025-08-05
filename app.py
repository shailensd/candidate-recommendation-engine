import streamlit as st

st.set_page_config(page_title="Candidate Recommender", layout="wide")

st.title("🧠 Candidate Recommendation Engine")

# Input job description
job_desc = st.text_area("Paste Job Description", height=300)

# Upload resumes
uploaded_files = st.file_uploader("Upload Candidate Resumes (PDF or DOCX)", type=['pdf', 'docx'], accept_multiple_files=True)

# Submit button
if st.button("Recommend Candidates"):
    if not job_desc:
        st.warning("Please enter a job description.")
    elif not uploaded_files:
        st.warning("Please upload at least one resume.")
    else:
        st.success("Processing resumes... (functionality coming next!)")
