import os
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Load API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Create Gemini client
client = genai.Client(api_key=api_key)

def generate_summary(job_description, resume_text, similarity_score):
    """
    Uses Gemini 2.5 Flash API to explain candidate fit.
    Limits input text to 1500 chars to avoid token limits.
    Falls back to template-based summary if API fails.
    """
    prompt = f"""
You are a recruiter assistant helping evaluate candidates.

Job Description:
{job_description[:1500]}

Candidate Resume:
{resume_text[:1500]}

Similarity Score: {similarity_score:.3f}

Write a 2–3 sentence summary explaining why this candidate may be a good fit. Focus on:
- Skills and experience alignment
- Relevant qualifications
- Overall suitability
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)  # Disable thinking for faster response
            )
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini summary failed: {e}")
        return fallback_summary(similarity_score)

def fallback_summary(similarity_score):
    """
    Generates template-based summary when API fails.
    Thresholds match status classification:
    >0.8: Excellent | >0.6: Good | >0.4: Moderate | <0.4: Limited
    """
    if similarity_score > 0.8:
        return f"This candidate demonstrates excellent alignment with the job requirements. The high similarity score of {similarity_score:.3f} suggests a strong potential fit."
    elif similarity_score > 0.6:
        return f"This candidate shows good alignment with the job requirements, supported by a similarity score of {similarity_score:.3f}."
    elif similarity_score > 0.4:
        return f"This candidate has a moderate match for the job, with a similarity score of {similarity_score:.3f} indicating some relevant qualifications."
    else:
        return f"This candidate has limited overlap with the job requirements, as indicated by a low similarity score of {similarity_score:.3f}."
