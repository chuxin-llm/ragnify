
from functools import lru_cache
import importlib
from rag.common.utils import logger

from rag.module.post_retrieval.reranker import Reranker


@lru_cache()
def get_reranker(model_name_or_path: str,
                 reranker_type: str):

    logger.info(f"Loading {model_name_or_path} as model reranker")
    if reranker_type == "rank":
        reranker = Reranker(model_name_or_path)

    return reranker


from langchain_community.document_loaders import UnstructuredFileLoader


def get_loader(name):
    try:
        if "Customized" in name:
            customized_document_loaders_module = importlib.import_module("rag.module.indexing.loader")
            return getattr(customized_document_loaders_module, name)
        else:
            document_loaders_module = importlib.import_module("langchain.document_loaders")
            return getattr(document_loaders_module, name)
    except Exception as e:
        return UnstructuredFileLoader



