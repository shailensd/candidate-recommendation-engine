from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

def generate_embeddings(model, texts):
    """
    Converts text to dense vectors using SentenceTransformer.
    Raises exception if embedding generation fails.
    """
    try:
        return model.encode(texts, convert_to_tensor=False)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise

def calculate_similarity(job_embedding, candidate_embeddings):
    """
    Computes cosine similarity between job and each candidate.
    Score range: 0 (different) to 1 (identical).
    Raises exception if calculation fails.
    """
    try:
        return cosine_similarity([job_embedding], candidate_embeddings)[0]
    except Exception as e:
        logger.error(f"Cosine similarity calculation failed: {e}")
        raise
