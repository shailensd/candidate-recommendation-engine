import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import logging
from datetime import datetime

# Import modular components
from ml_utils.embedding_model import load_embedding_model
from engine.parser import extract_text_from_pdf, extract_text_from_docx, clean_text, extract_candidate_info
from engine.similarity import generate_embeddings, calculate_similarity
from engine.summarizer import generate_summary

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
    with st.sidebar:
        st.subheader("🔐 Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            # Replace this with a proper auth method or user DB
            if username and password == "sprouts123":  # basic check
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
    st.header("Settings")

    if st.button("🔄 Start New Search"):
        st.session_state["upload_key"] = f"upload_{datetime.now().timestamp()}"
        st.session_state["jd_key"] = f"jd_{datetime.now().timestamp()}"
        for key in list(st.session_state.keys()):
            if key != "upload_key" and key != "jd_key":
                del st.session_state[key]
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
manual_count = st.number_input("Number of manual resumes", min_value=0, max_value=10, value=0)
manual_texts = [st.text_area(f"Manual Resume {i+1}", height=150) for i in range(manual_count)]

# Process button
if st.button("🚀 Recommend Candidates"):
    if not job_description.strip():
        st.error("Please enter a job description.")
    elif not uploaded_files and not any(t.strip() for t in manual_texts):
        st.error("Please provide at least one candidate resume.")
    else:
        with st.spinner("Analyzing candidates..."):
            candidates = []

            # Uploaded files
            for i, file in enumerate(uploaded_files):
                ext = file.name.split('.')[-1].lower()
                if ext == 'pdf':
                    text = extract_text_from_pdf(file)
                elif ext == 'docx':
                    text = extract_text_from_docx(file)
                else:
                    st.warning(f"Unsupported format: {file.name}")
                    continue

                if text:
                    info = extract_candidate_info(text)
                    candidates.append({
                        "id": f"File_{i+1}",
                        "name": info["name"],
                        "email": info["email"],
                        "phone": info["phone"],
                        "text": clean_text(text),
                        "source": "file"
                    })

            # Manual entries
            for i, text in enumerate(manual_texts):
                if text.strip():
                    info = extract_candidate_info(text)
                    candidates.append({
                        "id": f"Text_{i+1}",
                        "name": info["name"],
                        "email": info["email"],
                        "phone": info["phone"],
                        "text": clean_text(text),
                        "source": "manual"
                    })

            if not candidates:
                st.error("No valid resumes found.")
                st.stop()

            # Generate embeddings and similarity
            job_emb = generate_embeddings(st.session_state.embedding_model, [job_description])[0]
            texts = [c['text'] for c in candidates]
            cand_embs = generate_embeddings(st.session_state.embedding_model, texts)
            sims = calculate_similarity(job_emb, cand_embs)

            # Build results
            results = []
            for i, c in enumerate(candidates):
                score = round(sims[i], 4)
                if score >= 0.8:
                    status, badge = "Excellent Match", "status-excellent"
                elif score >= 0.6:
                    status, badge = "Good Match", "status-good"
                elif score >= 0.4:
                    status, badge = "Fair Match", "status-fair"
                else:
                    status, badge = "Poor Match", "status-poor"

                summary = generate_summary(job_description, c['text'], score)
                results.append({
                    "Rank": i+1,
                    "Candidate ID": c['id'],
                    "Name": c['name'],
                    "Email": c['email'],
                    "Phone": c['phone'],
                    "Similarity Score": score,
                    "Status": status,
                    "Status Class": badge,
                    "AI Summary": summary,
                    "Source": c['source']
                })

            df = pd.DataFrame(results).sort_values("Similarity Score", ascending=False).reset_index(drop=True)
            df["Rank"] = df.index + 1
            st.session_state.results = df
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
    csv = df.to_csv(index=False)
    st.download_button("📥 Download Results as CSV", csv, file_name=f"recommendations_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")