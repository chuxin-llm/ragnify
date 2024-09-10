
from typing import List
import torch

from langchain_core.embeddings import Embeddings
from langchain_community.embeddings import (
    HuggingFaceEmbeddings,
    HuggingFaceBgeEmbeddings
)
from rag.common.utils import logger
from rag.common.configuration import settings


class LocalEmbeddings(Embeddings):

    def __init__(self,
                 model_name_or_path: str,
                 model_engine: str = "huggingface"):
        self.model_name_or_path = model_name_or_path
        self.model_engine = model_engine

        self._init_embedding_model()

    def _init_embedding_model(self):
        model_kwargs = {"device": "cpu"}
        if torch.cuda.is_available() and 'cuda' in settings.embeddings.device:
            model_kwargs["device"] = settings.embeddings.device
        encode_kwargs = {"normalize_embeddings": True}

        logger.info(f"Using {self.model_engine} as model engine to load embeddings")
        if self.model_engine == "huggingface":
            func_class = HuggingFaceBgeEmbeddings if 'bge' in self.model_name_or_path \
                            else HuggingFaceEmbeddings
            hf_embeddings = func_class(
                model_name=self.model_name_or_path,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs,
            )
            self.embeddings = hf_embeddings
        else:
            pass

    def embed_documents(self, docs: List[str]):
        return self.embeddings.embed_documents(docs)

    def embed_query(self, query: str):
        return self.embeddings.embed_query(query)

