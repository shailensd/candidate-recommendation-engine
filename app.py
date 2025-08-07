import streamlit as st
import pandas as pd
import plotly.express as px
import logging
from datetime import datetime

# Import modular components
from ml_utils.embedding_model import load_embedding_model
from engine.recommender import process_candidates

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit page config
st.set_page_config(
    page_title="Candidate Recommendation Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Authentication Section ---

def login():
    st.markdown("""
        <div style="text-align: center; margin-top: 2rem;">
            <h3>🔐 Login</h3>
        </div>
        <style>
            .stTextInput > div > div > input {
                padding: 0.4rem;
                font-size: 0.9rem;
            }
            .stButton button {
                padding: 0.3rem 0.8rem;
                font-size: 0.9rem;
            }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.5, 2, 1.5])
    with col2:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", key="username_input")
            password = st.text_input("Password", type="password", key="password_input")
            submitted = st.form_submit_button("Login")  # Enter now works here

            if submitted:
                if username and password == "sprouts123":  # Replace with real logic
                    st.session_state.user = username
                    st.success(f"Welcome, {username}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")



if "user" not in st.session_state:
    login()
    st.stop()

# Header
st.markdown("""
    <h1 style='text-align: center; font-size: 2.5rem;'>🧠 Candidate Recommendation Engine</h1>
    <hr>
""", unsafe_allow_html=True)

# Sidebar: Reset Button
with st.sidebar:
    # Show logged-in user info at the top
    if "user" in st.session_state:
        st.markdown(f"👤 **{st.session_state.user}**")
        if st.button("🚪 Logout"):
            del st.session_state.user
            st.rerun()

    st.header("Settings")

    if st.button("🔄 Start New Search"):
        st.session_state["upload_key"] = f"upload_{datetime.now().timestamp()}"
        st.session_state["jd_key"] = f"jd_{datetime.now().timestamp()}"
        for key in list(st.session_state.keys()):
            if key not in ["upload_key", "jd_key", "user"]:  # Preserve login
                del st.session_state[key]
        st.session_state["manual_count"] = 0
        st.rerun()


# Load embedding model
if 'embedding_model' not in st.session_state:
    with st.spinner("Loading AI model..."):
        st.session_state.embedding_model = load_embedding_model()
    st.success("✅ Model loaded")

# Job description
st.subheader("📄 Job Description")
job_description = st.text_area("Enter the job description", height=250, key=st.session_state.get("jd_key", "jd_1"))

# Candidate input
st.subheader("📥 Candidate Resumes")
uploaded_files = st.file_uploader(
    "Upload PDF or DOCX resumes",
    type=["pdf", "docx"],
    accept_multiple_files=True,
    key=st.session_state.get("upload_key", "upload_1")
)

st.markdown("Or enter resume texts manually:")
manual_count = st.number_input("Number of manual resumes", min_value=0, max_value=50, key = "manual_count")
manual_texts = [st.text_area(f"Manual Resume {i+1}", height=150) for i in range(manual_count)]

# Process button
if st.button("🚀 Recommend Candidates"):
    if not job_description.strip():
        st.error("Please enter a job description.")
    elif not uploaded_files and not any(t.strip() for t in manual_texts):
        st.error("Please provide at least one candidate resume.")
    else:
        with st.spinner("Analyzing candidates..."):
            # Use the centralized recommender function
            df = process_candidates(
                model=st.session_state.embedding_model,
                job_description=job_description,
                uploaded_files=uploaded_files,
                manual_texts=manual_texts
            )
            
            if df.empty:
                st.error("No valid resumes found.")
                st.stop()
            
            # Store results and CSV data
            st.session_state.results = df
            st.session_state.csv_data = df.to_csv(index=False)
            st.success("✅ Recommendations generated!")

# Show results if available
if 'results' in st.session_state:
    df = st.session_state.results
    st.subheader("👑 Top Candidates")

    for _, row in df.head(5).iterrows():
        st.markdown(f"""
            <div class="candidate-card">
            <h4>#{row['Rank']} - {row['Name']}</h4>
            <p><strong>Email:</strong> {row['Email']}</p>
            <p><strong>Phone:</strong> {row['Phone']}</p>
            <p><strong>Score:</strong> {row['Similarity Score']}</p>
            <p><strong>Status:</strong> <span class="{row['Status Class']}">{row['Status']}</span></p>
            <p><strong>Summary:</strong> {row['AI Summary']}</p>
            </div>
        """, unsafe_allow_html=True)

    # Visualization: Top Candidate Scores
    st.subheader("📊 Top Candidate Scores")
    fig_bar = px.bar(
        df.head(10),
        x='Name',
        y='Similarity Score',
        color='Similarity Score',
        color_continuous_scale='blues',
        title='Top 10 Candidates by Similarity Score'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Download CSV
    if 'csv_data' in st.session_state:
        st.download_button(
            "📥 Download Results as CSV",
            st.session_state.csv_data,
            file_name=f"recommendations_{datetime.now().strftime('%Y%m%d')}.csv",mime="text/csv")
    else:
        st.info("No data available for download. Please run a recommendation first.")

