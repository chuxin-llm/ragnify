
from abc import ABC, abstractmethod
import operator


class KnowledgeGraph(ABC):
    """base class for knowledge graph implementations"""

    @abstractmethod
    def get_schema(self):
        pass

    @abstractmethod
    def call(self, question):
        pass
