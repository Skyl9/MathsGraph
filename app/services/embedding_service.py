import logging
import typing
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def _load_model(self):
        if self._model is None:
            logger.info("Chargement du modèle NLP pour les embeddings...")
            # Modèle léger, rapide et multilingue (all-MiniLM-L6-v2) très performant
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Modèle NLP chargé.")

    def get_embedding(self, text: str) -> list[float]:
        """Génère l'embedding d'un texte."""
        if not text:
            return [0.0] * 384

        self._load_model()

        assert self._model is not None
        # Le modèle retourne un numpy array, on le convertit en liste de float
        embedding = self._model.encode(text)
        return typing.cast(list[float], embedding.tolist())


embedding_service = EmbeddingService()
