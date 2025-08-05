import pandas as pd
import logging

from engine.parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
    clean_text,
    extract_candidate_info
)

from engine.similarity import (
    generate_embeddings,
    calculate_similarity
)

from engine.summarizer import generate_summary

logger = logging.getLogger(__name__)

def process_candidates(model, job_description, uploaded_files, manual_texts):
    """
    Process job description and candidate resumes to generate ranked recommendations.

    Parameters:
        model: Pre-loaded SentenceTransformer model
        job_description (str): The job description text
        uploaded_files (List[UploadedFile]): List of PDF/DOCX resume files
        manual_texts (List[str]): Manually entered resume texts

    Returns:
        pd.DataFrame: DataFrame containing ranked candidate matches
    """
    candidates = []

    # 1. Process uploaded resume files
    for i, file in enumerate(uploaded_files):
        if file:
            ext = file.name.split(".")[-1].lower()
            if ext == "pdf":
                text = extract_text_from_pdf(file)
            elif ext == "docx":
                text = extract_text_from_docx(file)
            else:
                logger.warning(f"Unsupported file type: {file.name}")
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

    # 2. Process manually entered resume texts
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
        logger.warning("No valid candidate data provided.")
        return pd.DataFrame()

    # 3. Generate embeddings
    job_embedding = generate_embeddings(model, [job_description])[0]
    resume_texts = [c["text"] for c in candidates]
    resume_embeddings = generate_embeddings(model, resume_texts)

    # 4. Compute similarity scores
    similarity_scores = calculate_similarity(job_embedding, resume_embeddings)

    # 5. Build result rows
    results = []
    for i, candidate in enumerate(candidates):
        score = similarity_scores[i]
        summary = generate_summary(job_description, candidate["text"], score)
        results.append({
            "Rank": i + 1,
            "Candidate ID": candidate["id"],
            "Name": candidate["name"],
            "Email": candidate["email"],
            "Phone": candidate["phone"],
            "Similarity Score": round(score, 4),
            "AI Summary": summary,
            "Source": candidate["source"]
        })

    # 6. Sort by similarity score
    df = pd.DataFrame(results).sort_values("Similarity Score", ascending=False).reset_index(drop=True)
    df["Rank"] = df.index + 1

    return df
