
import os
import chromadb
import hashlib
import uuid
from typing import List, Tuple

from chromadb.api.types import (GetResult, QueryResult)
from langchain_core.embeddings import Embeddings
from langchain.docstore.document import Document

from rag.connector.database.utils import KnowledgeFile
from rag.connector.database.base import KB_ROOT_PATH
from rag.connector.vectorstore.base import VectorStoreBase
from rag.common.configuration import settings
from rag.common.utils import logger


CHROMA_PERSISTENT_PATH = os.path.join(KB_ROOT_PATH, 'chroma_persistent')

def md5_encryption(data):
    md5 = hashlib.md5()
    md5.update(data.encode('utf-8'))
    return md5.hexdigest()


class ChromaVectorStore(VectorStoreBase):

    def __init__(self,
                 embedding_model: Embeddings,
                 collection_name: str):
        self.embeddings = embedding_model
        self.knowledge_base_name = collection_name
        self.collection_name = collection_name
        self.config = settings.vector_store

        self.client = chromadb.PersistentClient(path=CHROMA_PERSISTENT_PATH)
        self.create_vectorstore()

    def create_vectorstore(self):
        metadata = self.config.kwargs.get("metadata", None)
        self.collection = self.client.get_or_create_collection(name=self.collection_name,
                                                               metadata=metadata)

    def drop_vectorstore(self):
        try:
            self.client.delete_collection(self.collection_name)
        except ValueError as e:
            if not str(e) == f"Collection {self.collection_name} does not exist.":
                raise e

    def clear_vectorstore(self):
        self.drop_vectorstore()
        self.create_vectorstore()

    def add_doc(self, file: KnowledgeFile, docs, **kwargs):
        doc_ids, doc_text, doc_metadata = [], [], []
        for doc in docs:
            doc_text.append(doc.page_content)

            doc.metadata["source"] = md5_encryption(file.filename)
            doc.metadata["filename"] = file.filename
            for k, v in doc.metadata.items():
                doc.metadata[k] = str(v)
            doc_metadata.append(doc.metadata)

            doc_id = doc.metadata.get("id", str(uuid.uuid4()))
            doc_ids.append(doc_id)
        embeddings = self.embeddings.embed_documents(doc_text)

        print("doc_ids:", doc_ids)
        print("documents", doc_text)
        print("metadatas", doc_metadata)
        print("embeddings", self.embeddings.embed_documents(doc_text))
        self.collection.add(ids=doc_ids, documents=doc_text,
                            metadatas=doc_metadata,
                            embeddings=embeddings)
        doc_infos = [{"id": id, "metadata": doc.metadata} for id, doc in zip(doc_ids, docs)]
        return doc_infos

    def delete_doc(self, filename):
        """
        删除指定文件的所有chunk记录
        :param filename:
        :return:
        """
        return self.collection.delete(where={"source": md5_encryption(filename)})

    def update_doc(self, file: KnowledgeFile, docs: List[Document]):

        """
        插入/更新向量数据库中的记录
        更新：若该文件的chunk已经存在，需要先将原信息删除后重新插入
        :param file:
        :param docs:
        :return:
        """
        self.delete_doc(file.filename)
        return self.add_doc(file, docs=docs)

    def search_docs(self, text, top_k, threshold, **kwargs):
        """
        :param text:
        :param top_k:
        :param threshold:
        :return: List[Tuple[Document, float]]: Result doc and score.
        """
        text_embeddings = self.embeddings.embed_query(text)
        query_result: QueryResult = self.collection.query(query_embeddings=text_embeddings, n_results=top_k)
        return self._results_to_docs_and_scores(query_result)

    def _results_to_docs_and_scores(self, results) -> List[Tuple[Document, float]]:
        """
        from langchain_community.vectorstores.chroma import Chroma
        """
        return [
            (Document(page_content=result[0], metadata=result[1] or {}), 1 - result[2])  # 这里要把距离转换成相似度
            for result in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]

