
from collections import defaultdict
from collections.abc import Hashable
from itertools import chain
from typing import (
    Union,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    TypeVar,
    Optional
)

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from rag.chains.base import BaseRetrievalChain
from rag.common.utils import DocumentWithVSId, logger
from rag.connector.vectorstore.base import VectorStoreBase
# from rag.connector.knowledge_graph.base import KnowledgeGraph
from rag.module.post_retrieval.reranker import Reranker
from rag.module.pre_retrieval.multi_query import generate_queries
from rag.module.pre_retrieval.route_query import route_query_to_files

T = TypeVar("T")
H = TypeVar("H", bound=Hashable)


def unique_by_key(iterable: Iterable[T], key: Callable[[T], H]) -> Iterator[T]:
    seen = set()
    for e in iterable:
        if (k := key(e)) not in seen:
            seen.add(k)
            yield e


@dataclass
class RetrievalChain(BaseRetrievalChain):

    vectorstore: Optional[VectorStoreBase]
    retrievers: List[BaseRetriever] = None
    top_k: int = 5
    score_threshold: Union[None, float] = 0.
    multi_query: bool = False
    route_query: bool = False

    def __post_init__(self):
        self.reranker = get_reranker(settings.reranker.model_name_or_path, settings.reranker.type) \
                if settings.reranker.model_name_or_path and settings.reranker.type else None

    def _reciprocal_rank(
        self, doc_lists: List[List[Document]], weights: List[float]=None, k=60
    ):
        """
        Perform weighted Reciprocal Rank Fusion on multiple rank lists.
        You can find more details about RRF here:
        https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf

        Args:
            doc_lists: A list of rank lists, where each rank list contains unique items.

        Returns:
            list: The final aggregated list of items sorted by their weighted RRF
                    scores in descending order and scores.
        """

        # Associate each doc's content with its RRF score for later sorting by it
        # Duplicated contents across retrievers are collapsed & scored cumulatively
        rrf_score: Dict[str, float] = defaultdict(float)
        if weights is None: weights = [1.0 for i in range(len(doc_lists))]
        for doc_list, weight in zip(doc_lists, weights):
            for rank, doc in enumerate(doc_list, start=1):
                rrf_score[doc.page_content] += weight / (rank + k)

        # Docs are deduplicated by their contents then sorted by their scores
        all_docs = chain.from_iterable(doc_lists)
        sorted_docs = sorted(
            unique_by_key(all_docs, lambda doc: doc.page_content),
            reverse=True,
            key=lambda doc: rrf_score[doc.page_content],
        )
        sorted_scores = [rrf_score[doc.page_content] for doc in sorted_docs]
        return sorted_docs, sorted_scores

    def pre_retrieval(self, query: str):
        if self.multi_query:
            return generate_queries(query)
        return []

    def retrieval(self, query: str) -> Dict[str, List[Document]]:
        ensemble_docs = {}
        if self.vectorstore:
            kwargs = {}
            documents = []
            docs = self.vectorstore.search_docs(query,
                                                self.top_k,
                                                self.score_threshold,
                                                **kwargs)
            documents.extend([DocumentWithVSId(**x[0].dict(), score=x[1], id=x[0].metadata.get("id")) for x in docs])
            ensemble_docs["vectorstore_retrieval_0"] = documents

        # retrieval by using predefined retrievers
        if self.retrievers:
            for i, retriever in enumerate(self.retrievers):
                try:
                    r_docs = retriever.invoke(
                            query,
                        )
                    if len(r_docs) > 0:
                        ensemble_docs[retriever.__name__ + "_" + str(i+1)] = r_docs
                except Exception as e:
                    msg = f"使用预定义的召回器 {retriever.__name__} 检索召回文档时出错：{e}"
                    logger.error(f'{e.__class__.__name__}: {msg}', exc_info=e)

        return ensemble_docs

    def post_retrieval(self,
                       query: str,
                       docs: Dict[str, List[Document]],):
        f_documents = []
        if len(docs) == 0:
            return []

        elif len(docs) > 1:     # rank by rrf
            sorted_docs, sorted_scores = self._reciprocal_rank([docs[x] for x in docs])
            f_documents.extend([DocumentWithVSId(page_content=x.page_content,
                                                 metadata=x.metadata,
                                                 score=sorted_scores[i],
                                                 id=x.metadata.get("id"))
                                                 for i, x in enumerate(sorted_docs)])

        else:
            ids, documents = [], docs[list(docs.keys())[0]]
            for doc in documents:
                if doc.id not in ids:
                    ids.append(doc.id)
                    f_documents.append(doc)

        # rerank by pre-trained model
        if self.reranker is not None and len(f_documents) > 1:
            f_documents = self.reranker.rank(query, f_documents, self.top_k)
        else:
            f_documents = [{"document": doc} for doc in f_documents]
        return f_documents

    def chain(self,
              query: str):
        queries = self.pre_retrieval(query)
        docs = self.retrieval(query)
        # multi query
        for i, q in enumerate(queries):
            q_docs = self.retrieval(q)
            for r_k in q_docs: docs[str(i+1) + "_" + r_k] = q_docs[r_k]

        docs = self.post_retrieval(query, docs)
        for d in docs: print(d)
        return docs


