import pandas as pd
import logging
import hashlib
from collections import defaultdict

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

def classify_status(score):
    """
    Maps similarity score to human-readable status:
    ≥0.8: Excellent Match
    ≥0.6: Good Match
    ≥0.4: Fair Match
    <0.4: Poor Match
    Returns (status_text, CSS_class)
    """
    if score >= 0.8:
        return "Excellent Match", "status-excellent"
    elif score >= 0.6:
        return "Good Match", "status-good"
    elif score >= 0.4:
        return "Fair Match", "status-fair"
    else:
        return "Poor Match", "status-poor"

def generate_content_hash(text):
    """
    Creates SHA-256 hash of cleaned text for duplicate detection.
    Handles None/empty text gracefully.
    """
    try:
        if not text:
            return hashlib.sha256("".encode('utf-8')).hexdigest()
        cleaned_text = clean_text(text).lower().strip()
        return hashlib.sha256(cleaned_text.encode('utf-8')).hexdigest()
    except Exception as e:
        logger.error(f"Error generating content hash: {e}")
        # Return a hash of the original text as fallback
        return hashlib.sha256(str(text).encode('utf-8')).hexdigest()

def detect_duplicates(candidates):
    """
    Identifies duplicate candidates using three strategies:
    1. Identical email addresses
    2. Identical content (after cleaning)
    3. Same name + email combination
    
    Returns (unique_candidates, info_about_removed_duplicates)
    """
    if not candidates:
        return [], []
    
    # Filter out invalid candidates (missing required fields)
    valid_candidates = []
    for i, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            logger.warning(f"Invalid candidate structure at index {i}: {candidate}")
            continue
        if "email" not in candidate or "name" not in candidate or "text" not in candidate:
            logger.warning(f"Missing required fields in candidate at index {i}: {candidate}")
            continue
        valid_candidates.append(candidate)
    
    if not valid_candidates:
        return [], []
    
    # Group candidates by duplicate detection criteria
    email_groups = defaultdict(list)
    content_hash_groups = defaultdict(list)
    name_email_groups = defaultdict(list)
    
    for i, candidate in enumerate(valid_candidates):
        email = candidate["email"].lower().strip() if candidate["email"] else ""
        content_hash = generate_content_hash(candidate["text"])
        name_email = f"{candidate['name'].lower().strip() if candidate['name'] else ''}_{email}"
        
        email_groups[email].append(i)
        content_hash_groups[content_hash].append(i)
        name_email_groups[name_email].append(i)
    
    # Find duplicates
    duplicates = set()
    duplicate_info = []
    
    # Detect duplicates by email (most reliable indicator)
    for email, indices in email_groups.items():
        if len(indices) > 1 and email not in ["no email found", ""]:
            logger.info(f"Found {len(indices)} candidates with duplicate email: {email}")
            for idx in indices[1:]:
                duplicates.add(idx)
                duplicate_info.append({
                    "type": "email_duplicate",
                    "candidate_id": valid_candidates[idx]["id"],
                    "name": valid_candidates[idx]["name"],
                    "email": valid_candidates[idx]["email"],
                    "reason": f"Duplicate email with candidate {valid_candidates[indices[0]]['id']}"
                })
    
    # Detect duplicates by content hash (identical resumes)
    for content_hash, indices in content_hash_groups.items():
        if len(indices) > 1:
            logger.info(f"Found {len(indices)} candidates with duplicate content")
            for idx in indices[1:]:
                if idx not in duplicates:
                    duplicates.add(idx)
                    duplicate_info.append({
                        "type": "content_duplicate",
                        "candidate_id": valid_candidates[idx]["id"],
                        "name": valid_candidates[idx]["name"],
                        "email": valid_candidates[idx]["email"],
                        "reason": f"Duplicate content with candidate {valid_candidates[indices[0]]['id']}"
                    })
    
    # Detect duplicates by name+email combination (manual entries)
    for name_email, indices in name_email_groups.items():
        if len(indices) > 1:
            logger.info(f"Found {len(indices)} candidates with duplicate name+email: {name_email}")
            for idx in indices[1:]:
                if idx not in duplicates:
                    duplicates.add(idx)
                    duplicate_info.append({
                        "type": "name_email_duplicate",
                        "candidate_id": valid_candidates[idx]["id"],
                        "name": valid_candidates[idx]["name"],
                        "email": valid_candidates[idx]["email"],
                        "reason": f"Duplicate name+email with candidate {valid_candidates[indices[0]]['id']}"
                    })
    
    # Return unique candidates and duplicate information
    unique_candidates = [candidate for i, candidate in enumerate(valid_candidates) if i not in duplicates]
    
    if duplicates:
        logger.info(f"Removed {len(duplicates)} duplicate candidates. {len(unique_candidates)} unique candidates remaining.")
    
    return unique_candidates, duplicate_info

def process_candidates(model, job_description, uploaded_files, manual_texts):
    """
    Main pipeline for candidate recommendation:
    1. Extract text from resumes (PDF/DOCX/manual input)
    2. Remove duplicates
    3. Generate embeddings using provided model
    4. Calculate similarity scores
    5. Sort and rank candidates
    6. Generate AI summaries for top matches
    
    Returns (DataFrame_with_ranked_candidates, duplicate_info)
    """
    candidates = []

    # Extract text from uploaded files (PDF/DOCX)
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

    # Process manually entered resume texts
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
        return pd.DataFrame(), []

    # Remove duplicates and log findings
    unique_candidates, duplicate_info = detect_duplicates(candidates)
    
    if duplicate_info:
        logger.info(f"Found {len(duplicate_info)} duplicates:")
        for dup in duplicate_info:
            logger.info(f"  - {dup['type']}: {dup['name']} ({dup['email']}) - {dup['reason']}")
    
    if not unique_candidates:
        logger.warning("No unique candidates remaining after duplicate removal.")
        return pd.DataFrame(), duplicate_info

    # Generate embeddings for job and resumes
    job_embedding = generate_embeddings(model, [job_description])[0]
    resume_texts = [c["text"] for c in unique_candidates]
    resume_embeddings = generate_embeddings(model, resume_texts)

    # Calculate similarity scores
    similarity_scores = calculate_similarity(job_embedding, resume_embeddings)

    # Build results with scores and status
    results = []
    for i, candidate in enumerate(unique_candidates):
        score = similarity_scores[i]
        status, status_class = classify_status(score)
        results.append({
            "Rank": i + 1,
            "Candidate ID": candidate["id"],
            "Name": candidate["name"],
            "Email": candidate["email"],
            "Phone": candidate["phone"],
            "Similarity Score": round(score, 4),
            "Status": status,
            "Status Class": status_class,
            "AI Summary": "",  # Will be filled for top 5
            "Source": candidate["source"],
            "text": candidate["text"]  # Keep for summary generation
        })

    # Sort by similarity score (descending)
    try:
        df = pd.DataFrame(results).sort_values("Similarity Score", ascending=False).reset_index(drop=True)
        df["Rank"] = df.index + 1
    except Exception as e:
        logger.error(f"Error sorting DataFrame: {e}")
        df = pd.DataFrame(results)
        df["Rank"] = range(1, len(df) + 1)

    # Generate AI summaries for top 5 candidates
    top_candidates_count = min(5, len(df))
    for i in range(top_candidates_count):
        if i < len(df):
            candidate_text = df.iloc[i]["text"]
            score = df.iloc[i]["Similarity Score"]
            summary = generate_summary(job_description, candidate_text, score)
            df.at[i, "AI Summary"] = summary

    # Clean up and return results
    df = df.drop(columns=["text"])
    
    return df, duplicate_info
