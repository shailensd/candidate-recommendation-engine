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
    Classify candidate status based on similarity score.
    
    Parameters:
        score (float): Similarity score between 0 and 1
        
    Returns:
        tuple: (status_text, status_class)
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
    Generate a hash of the cleaned text content for duplicate detection.
    
    Parameters:
        text (str): The text content to hash
        
    Returns:
        str: SHA-256 hash of the cleaned text
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
    Detect and handle duplicate candidates based on email, content hash, and name.
    
    Parameters:
        candidates (list): List of candidate dictionaries
        
    Returns:
        tuple: (unique_candidates, duplicate_info)
    """
    if not candidates:
        return [], []
    
    # Validate candidate structure and filter out invalid candidates
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
    
    # Track duplicates by different criteria
    email_groups = defaultdict(list)
    content_hash_groups = defaultdict(list)
    name_email_groups = defaultdict(list)
    
    # Group candidates by different duplicate criteria
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
    
    # Check for duplicate emails (most reliable)
    for email, indices in email_groups.items():
        if len(indices) > 1 and email not in ["no email found", ""]:
            logger.info(f"Found {len(indices)} candidates with duplicate email: {email}")
            # Keep the first one, mark others as duplicates
            for idx in indices[1:]:
                duplicates.add(idx)
                duplicate_info.append({
                    "type": "email_duplicate",
                    "candidate_id": valid_candidates[idx]["id"],
                    "name": valid_candidates[idx]["name"],
                    "email": valid_candidates[idx]["email"],  # Use original email case
                    "reason": f"Duplicate email with candidate {valid_candidates[indices[0]]['id']}"
                })
    
    # Check for duplicate content (exact same resume)
    for content_hash, indices in content_hash_groups.items():
        if len(indices) > 1:
            logger.info(f"Found {len(indices)} candidates with duplicate content")
            # Keep the first one, mark others as duplicates
            for idx in indices[1:]:
                if idx not in duplicates:  # Only if not already marked as email duplicate
                    duplicates.add(idx)
                    duplicate_info.append({
                        "type": "content_duplicate",
                        "candidate_id": valid_candidates[idx]["id"],
                        "name": valid_candidates[idx]["name"],
                        "email": valid_candidates[idx]["email"],
                        "reason": f"Duplicate content with candidate {valid_candidates[indices[0]]['id']}"
                    })
    
    # Check for duplicate name+email combinations (manual entries)
    for name_email, indices in name_email_groups.items():
        if len(indices) > 1:
            logger.info(f"Found {len(indices)} candidates with duplicate name+email: {name_email}")
            # Keep the first one, mark others as duplicates
            for idx in indices[1:]:
                if idx not in duplicates:  # Only if not already marked
                    duplicates.add(idx)
                    duplicate_info.append({
                        "type": "name_email_duplicate",
                        "candidate_id": valid_candidates[idx]["id"],
                        "name": valid_candidates[idx]["name"],
                        "email": valid_candidates[idx]["email"],
                        "reason": f"Duplicate name+email with candidate {valid_candidates[indices[0]]['id']}"
                    })
    
    # Filter out duplicates
    unique_candidates = [candidate for i, candidate in enumerate(valid_candidates) if i not in duplicates]
    
    if duplicates:
        logger.info(f"Removed {len(duplicates)} duplicate candidates. {len(unique_candidates)} unique candidates remaining.")
    
    return unique_candidates, duplicate_info

def process_candidates(model, job_description, uploaded_files, manual_texts):
    """
    Process job description and candidate resumes to generate ranked recommendations.

    Parameters:
        model: Pre-loaded SentenceTransformer model
        job_description (str): The job description text
        uploaded_files (List[UploadedFile]): List of PDF/DOCX resume files
        manual_texts (List[str]): Manually entered resume texts

    Returns:
        tuple: (pd.DataFrame, list) - DataFrame containing ranked candidate matches and list of duplicate information
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
        return pd.DataFrame(), []

    # 3. Detect and remove duplicates
    unique_candidates, duplicate_info = detect_duplicates(candidates)
    
    if duplicate_info:
        logger.info(f"Found {len(duplicate_info)} duplicates:")
        for dup in duplicate_info:
            logger.info(f"  - {dup['type']}: {dup['name']} ({dup['email']}) - {dup['reason']}")
    
    if not unique_candidates:
        logger.warning("No unique candidates remaining after duplicate removal.")
        return pd.DataFrame(), duplicate_info

    # 4. Generate embeddings
    job_embedding = generate_embeddings(model, [job_description])[0]
    resume_texts = [c["text"] for c in unique_candidates]
    resume_embeddings = generate_embeddings(model, resume_texts)

    # 5. Compute similarity scores
    similarity_scores = calculate_similarity(job_embedding, resume_embeddings)

    # 6. Build result rows with scores and sort by similarity score
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
            "AI Summary": "",  # Placeholder - will be filled for top 5
            "Source": candidate["source"],
            "text": candidate["text"]  # Keep text for summary generation
        })

    # 7. Sort by similarity score
    try:
        df = pd.DataFrame(results).sort_values("Similarity Score", ascending=False).reset_index(drop=True)
        df["Rank"] = df.index + 1
    except Exception as e:
        logger.error(f"Error sorting DataFrame: {e}")
        # Create a simple DataFrame if sorting fails
        df = pd.DataFrame(results)
        df["Rank"] = range(1, len(df) + 1)

    # 8. Generate summaries only for top 5 candidates
    top_candidates_count = min(5, len(df))
    for i in range(top_candidates_count):
        if i < len(df):  # Ensure we don't exceed DataFrame bounds
            candidate_text = df.iloc[i]["text"]
            score = df.iloc[i]["Similarity Score"]
            summary = generate_summary(job_description, candidate_text, score)
            df.at[i, "AI Summary"] = summary

    # 9. Remove the temporary text column and return
    df = df.drop(columns=["text"])
    
    return df, duplicate_info
