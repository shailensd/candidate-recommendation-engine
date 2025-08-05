from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

def load_embedding_model(model_name='all-MiniLM-L6-v2'):
    """
    Load and return the Sentence Transformer model.

    Parameters:
        model_name (str): Name of the pre-trained model to load.

    Returns:
        SentenceTransformer: Loaded model object.

    Raises:
        RuntimeError: If the model fails to load.
    """
    try:
        model = SentenceTransformer(model_name)
        logger.info(f"Model '{model_name}' loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Error loading model '{model_name}': {e}")
        raise RuntimeError(f"Failed to load model '{model_name}'")
