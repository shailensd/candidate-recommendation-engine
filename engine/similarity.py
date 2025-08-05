from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

def generate_embeddings(model, texts):
    """
    Generates sentence embeddings for a list of texts.

    Parameters:
        model: Pre-loaded SentenceTransformer model
        texts (List[str]): List of input texts

    Returns:
        List of embeddings (vectors)
    """
    try:
        return model.encode(texts, convert_to_tensor=False)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise

def calculate_similarity(job_embedding, candidate_embeddings):
    """
    Calculates cosine similarity between job embedding and each candidate embedding.

    Parameters:
        job_embedding (np.ndarray): Embedding vector for the job description
        candidate_embeddings (List[np.ndarray]): List of embedding vectors for candidates

    Returns:
        List of cosine similarity scores
    """
    try:
        return cosine_similarity([job_embedding], candidate_embeddings)[0]
    except Exception as e:
        logger.error(f"Cosine similarity calculation failed: {e}")
        raise
