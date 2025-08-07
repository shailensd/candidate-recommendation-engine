from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

def load_embedding_model(model_name='all-MiniLM-L6-v2'):
    """
    Loads the SentenceTransformer model for text embeddings.
    Default: all-MiniLM-L6-v2 (good balance of speed/accuracy)
    Raises RuntimeError if loading fails.
    """
    try:
        model = SentenceTransformer(model_name)
        logger.info(f"Model '{model_name}' loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Error loading model '{model_name}': {e}")
        raise RuntimeError(f"Failed to load model '{model_name}'")
