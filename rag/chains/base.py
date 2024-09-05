
"""Base interface that all RAG applications should implement."""

from abc import ABC, abstractmethod
from typing import Generator


class BaseIndexingChain(ABC):

    @abstractmethod
    def load(self, file, loader_name):
        pass

    @abstractmethod
    def split(self, docs, splitter):
        pass

    @abstractmethod
    def store(self, file, chunks):
        pass


class BaseRetrievalChain(ABC):

    @abstractmethod
    def pre_retrieval(self, query):
        pass

    @abstractmethod
    def retrieval(self, query):
        pass

    @abstractmethod
    def post_retrieval(self, query, docs):
        pass


class BaseGenerationChain(ABC):

    @abstractmethod
    def augment(self, query, docs):
        pass

    @abstractmethod
    def generate(self, prompt):
        pass

