# candidate_recommender/engine/summarizer.py

import openai
import os
import logging

logger = logging.getLogger(__name__)

def generate_summary(job_description, resume_text, similarity_score):
    """
    Generate an AI-based summary explaining why a candidate is a good fit.
    Falls back to static template if OpenAI API key is not set.

    Parameters:
        job_description (str): The job description
        resume_text (str): The candidate's resume text
        similarity_score (float): The similarity score between job and resume

    Returns:
        str: A brief summary
    """
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return fallback_summary(similarity_score)

        openai.api_key = openai_api_key

        prompt = f"""
        Job Description: {job_description[:1000]}

        Candidate Resume: {resume_text[:1000]}

        Similarity Score: {similarity_score:.3f}

        Based on the job description and resume above, provide a professional 2–3 sentence summary explaining why this candidate is a good fit. Focus on:
        - Skills and experience alignment
        - Relevant qualifications
        - Overall suitability
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert technical recruiter evaluating candidates."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"OpenAI summary generation failed: {e}")
        return fallback_summary(similarity_score)

def fallback_summary(similarity_score):
    """
    Fallback summary if OpenAI API is not available.
    Uses similarity score to generate a basic template-based summary.
    """
    if similarity_score > 0.8:
        return f"This candidate demonstrates excellent alignment with the job requirements. The high similarity score of {similarity_score:.3f} suggests a strong potential fit."
    elif similarity_score > 0.6:
        return f"This candidate shows good alignment with the job requirements, supported by a similarity score of {similarity_score:.3f}."
    elif similarity_score > 0.4:
        return f"This candidate has a moderate match for the job, with a similarity score of {similarity_score:.3f} indicating some relevant qualifications."
    else:
        return f"This candidate has limited overlap with the job requirements, as indicated by a low similarity score of {similarity_score:.3f}."
