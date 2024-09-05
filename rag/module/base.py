
from rag.common.configuration import settings
from .utils import get_reranker

reranker = get_reranker(settings.reranker.model_name_or_path, settings.reranker.type)
